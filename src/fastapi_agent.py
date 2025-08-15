# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
FastAPI implementation of the auto-signin agent.
This creates a proper integration between FastAPI and the Microsoft Agents SDK.
"""

import json
import logging
from os import environ
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import the properly configured agent from the agent module
from .agent import AGENT_APP, CONNECTION_MANAGER, ADAPTER

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Auto Sign-In Agent - FastAPI",
    description="Microsoft Agents SDK Auto Sign-In Sample using FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Store components in app state
app.state.agent_app = AGENT_APP
app.state.adapter = ADAPTER
app.state.connection_manager = CONNECTION_MANAGER

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests for debugging."""
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/api/messages")
async def handle_messages(request: Request):
    """
    Main endpoint for handling Bot Framework messages.
    This integrates with the existing Agent SDK properly.
    """
    try:
        # Get the agent and adapter from app state
        agent_app = request.app.state.agent_app
        adapter = request.app.state.adapter
        
        # Get request body
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Request body is empty")
        
        # Parse the activity
        try:
            activity_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
        
        # Get authorization header
        auth_header = request.headers.get("Authorization", "")
        
        # Create a mock request object that mimics what the aiohttp version expects
        mock_request = MockAioHttpRequest(body, dict(request.headers))
        mock_request.app = {
            "agent_app": agent_app,
            "adapter": adapter,
            "agent_configuration": app.state.connection_manager.get_default_connection_configuration()
        }
        
        # Use the agent's built-in processing
        # This is similar to how start_agent_process works in the aiohttp version
        response_data = await process_bot_request(mock_request, activity_data, auth_header)
        
        return JSONResponse(content=response_data or {"status": "ok"}, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def process_bot_request(request, activity_data, auth_header):
    """
    Process a bot request using the agent framework.
    This mimics the behavior of start_agent_process from the aiohttp hosting.
    """
    try:
        agent_app = request.app["agent_app"]
        adapter = request.app["adapter"]
        
        # The agent app should handle the activity processing
        # This is a simplified version - the actual implementation would be more complex
        from microsoft.agents.activity import Activity
        
        activity = Activity(**activity_data)
        
        # Let the agent process the activity
        # The agent decorators will handle routing to the appropriate handlers
        await adapter.process_activity(activity, auth_header, agent_app.on_turn)
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error in process_bot_request: {str(e)}")
        raise

class MockAioHttpRequest:
    """
    Mock aiohttp request object for compatibility.
    """
    def __init__(self, body: bytes, headers: Dict[str, str]):
        self._body = body
        self._headers = headers
        self.app = {}
    
    @property
    def headers(self):
        return self._headers
    
    async def read(self):
        return self._body

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Auto Sign-In Agent FastAPI Server is running",
        "framework": "FastAPI",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "auto-signin-agent-fastapi",
        "version": "1.0.0"
    }

def start_server():
    """Start the FastAPI server."""
    port = int(environ.get("PORT", 3978))
    host = environ.get("HOST", "localhost")
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    
    uvicorn.run(
        "src.fastapi_agent:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    start_server()
