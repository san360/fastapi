# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Simple FastAPI wrapper for the auto-signin agent.
This approach reuses the existing aiohttp infrastructure with minimal changes.
"""

import json
import logging
from os import environ
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import the existing aiohttp-based components
from microsoft.agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)
from microsoft.agents.hosting.core.authorization import (
    JwtTokenValidator,
    ClaimsIdentity,
)

# Import the properly configured agent from the original implementation
from .agent import AGENT_APP, CONNECTION_MANAGER

logger = logging.getLogger(__name__)

# Enhanced logging for debugging
logging.basicConfig(level=logging.DEBUG)
agents_logger = logging.getLogger("microsoft.agents")
agents_logger.setLevel(logging.DEBUG)

# Create FastAPI app
app = FastAPI(
    title="Auto Sign-In Agent - FastAPI Simple",
    description="Microsoft Agents SDK Auto Sign-In Sample using FastAPI (Simple wrapper)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Store components in app state (same as aiohttp version)
app.state.agent_configuration = CONNECTION_MANAGER.get_default_connection_configuration()
app.state.agent_app = AGENT_APP
app.state.adapter = AGENT_APP.adapter

# Add middleware for proper JWT authorization
@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    """
    JWT authorization middleware that validates tokens using Microsoft Agents SDK.
    This implements the same validation logic as jwt_authorization_middleware.
    """
    if request.url.path != "/api/messages":
        # Only validate JWT for /api/messages endpoint
        return await call_next(request)
        
    logger.debug("Processing /api/messages request - validating JWT token")
    
    # Get auth configuration from app state
    auth_config = app.state.agent_configuration
    token_validator = JwtTokenValidator(auth_config)
    
    # Get Authorization header
    auth_header = request.headers.get("Authorization")
    
    if auth_header:
        logger.debug(f"Authorization header found: {auth_header[:20]}...")
        try:
            # Extract the token from the Authorization header
            parts = auth_header.split(" ")
            if len(parts) != 2 or parts[0] != "Bearer":
                logger.error(f"Invalid Authorization header format: {auth_header}")
                return JSONResponse({"error": "Invalid Authorization header format"}, status_code=401)
                
            token = parts[1]
            logger.debug(f"Validating JWT token: {token[:20]}...")
            
            # Validate the token
            claims = token_validator.validate_token(token)
            logger.debug(f"JWT token validated successfully. Claims: {claims.claims}")
            
            # Store claims_identity in request state for later use
            request.state.claims_identity = claims
            
        except ValueError as e:
            logger.error(f"JWT validation error: {e}")
            return JSONResponse({"error": f"JWT validation failed: {str(e)}"}, status_code=401)
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {e}")
            return JSONResponse({"error": f"Authentication error: {str(e)}"}, status_code=401)
    else:
        logger.debug("No Authorization header found")
        if not auth_config or not auth_config.CLIENT_ID:
            logger.debug("No CLIENT_ID configured - using anonymous claims")
            # Use anonymous claims for development/testing
            request.state.claims_identity = token_validator.get_anonymous_claims()
        else:
            logger.error("Authorization header required but not found")
            return JSONResponse({"error": "Authorization header not found"}, status_code=401)

    response = await call_next(request)
    return response

class CaseInsensitiveDict:
    """A case-insensitive dictionary wrapper that mimics aiohttp headers behavior."""
    def __init__(self, data: dict):
        self._data = {key.lower(): value for key, value in data.items()}
        self._original_keys = {key.lower(): key for key in data.keys()}
    
    def __getitem__(self, key):
        return self._data[key.lower()]
    
    def __contains__(self, key):
        return key.lower() in self._data
    
    def get(self, key, default=None):
        return self._data.get(key.lower(), default)
    
    def items(self):
        return [(self._original_keys[k], v) for k, v in self._data.items()]

class FastAPIToAioHttpRequestAdapter:
    """
    Adapter to make FastAPI requests work with aiohttp-based start_agent_process.
    """
    def __init__(self, fastapi_request: Request, body: bytes):
        self._fastapi_request = fastapi_request
        self._body = body
        self.app = {}  # Will be set below
        self._data = {}  # Store additional data like claims_identity
        
        # Transfer claims_identity from FastAPI request state to aiohttp-style request
        if hasattr(fastapi_request.state, 'claims_identity'):
            self._data['claims_identity'] = fastapi_request.state.claims_identity
            logger.debug(f"Transferred claims_identity to adapter: {fastapi_request.state.claims_identity}")
        else:
            logger.warning("No claims_identity found in request state")
        
    @property
    def headers(self):
        """Return headers with case-insensitive access like aiohttp does"""
        # Create headers dict with original casing but case-insensitive access
        headers_dict = dict(self._fastapi_request.headers)
        
        # Ensure content-type is set
        if 'content-type' not in headers_dict and 'Content-Type' not in headers_dict:
            headers_dict['Content-Type'] = 'application/json'
            
        logger.debug(f"Request headers: {headers_dict}")
        return CaseInsensitiveDict(headers_dict)
    
    @property
    def method(self):
        return self._fastapi_request.method
        
    def get(self, key, default=None):
        """Get method like aiohttp Request object"""
        return self._data.get(key, default)
        
    def __setitem__(self, key, value):
        """Set method to store data in request"""
        self._data[key] = value
        
    def __getitem__(self, key):
        """Get method to access data in request"""
        return self._data[key]
    
    async def read(self):
        return self._body
    
    async def text(self):
        return self._body.decode('utf-8')
    
    async def json(self):
        try:
            text_content = self._body.decode('utf-8')
            logger.debug(f"Request body: {text_content}")
            return json.loads(text_content)
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            raise

@app.post("/api/messages")
async def handle_messages(request: Request):
    """
    Main endpoint for handling Bot Framework messages.
    This uses the existing aiohttp infrastructure.
    """
    try:
        # Enhanced logging for debugging
        logger.info(f"Received {request.method} request to {request.url}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Get request body
        body = await request.body()
        if not body:
            logger.warning("Request body is empty")
            raise HTTPException(status_code=400, detail="Request body is empty")
        
        logger.debug(f"Request body length: {len(body)}")
        
        # Create adapter to make FastAPI request look like aiohttp request
        aiohttp_request = FastAPIToAioHttpRequestAdapter(request, body)
        aiohttp_request.app = {
            "agent_configuration": request.app.state.agent_configuration,
            "agent_app": request.app.state.agent_app,
            "adapter": request.app.state.adapter
        }
        
        logger.debug("Calling start_agent_process with aiohttp adapter")
        
        # Use the existing start_agent_process from aiohttp hosting
        response = await start_agent_process(
            aiohttp_request,
            request.app.state.agent_app,
            request.app.state.adapter,
        )
        
        logger.debug(f"Got response from start_agent_process: {response}")
        
        # Convert aiohttp response to FastAPI response
        if hasattr(response, 'body') and response.body:
            response_data = json.loads(response.body.decode('utf-8')) if response.body else {}
            logger.debug(f"Response data: {response_data}")
            return JSONResponse(content=response_data, status_code=response.status)
        else:
            logger.debug("Returning default OK response")
            return JSONResponse(content={"status": "ok"}, status_code=200)
            
    except HTTPException as he:
        logger.error(f"HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Auto Sign-In Agent FastAPI Server is running (Simple wrapper)",
        "framework": "FastAPI + aiohttp hosting",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "auto-signin-agent-fastapi-simple",
        "version": "1.0.0"
    }

def start_server():
    """Start the FastAPI server."""
    port = int(environ.get("PORT", 3978))
    host = environ.get("HOST", "localhost")
    
    logger.info(f"Starting FastAPI simple server on {host}:{port}")
    
    uvicorn.run(
        "src.fastapi_simple:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    start_server()
