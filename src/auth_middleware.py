# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
JWT Authentication middleware for FastAPI.
Handles token validation using Microsoft Agents SDK.
"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from microsoft.agents.hosting.core.authorization import JwtTokenValidator

logger = logging.getLogger(__name__)

class JWTAuthMiddleware:
    """JWT Authentication middleware handler."""
    
    def __init__(self, auth_config):
        self.auth_config = auth_config
        self.token_validator = JwtTokenValidator(auth_config) if auth_config else None
        
    async def authenticate_request(self, request: Request) -> tuple[bool, JSONResponse | None]:
        """
        Authenticate request and return (success, error_response).
        Returns (True, None) on success, (False, error_response) on failure.
        """
        if request.url.path != "/api/messages":
            return True, None
            
        logger.debug("Processing /api/messages request - validating JWT token")
        
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            return await self._validate_token(request, auth_header)
        else:
            return self._handle_missing_header(request)
    
    async def _validate_token(self, request: Request, auth_header: str) -> tuple[bool, JSONResponse | None]:
        """Validate JWT token from Authorization header."""
        logger.debug(f"Authorization header found: {auth_header[:20]}...")
        
        try:
            token = self._extract_token(auth_header)
            if not token:
                return False, JSONResponse(
                    {"error": "Invalid Authorization header format"}, 
                    status_code=401
                )
                
            logger.debug(f"Validating JWT token: {token[:20]}...")
            claims = self.token_validator.validate_token(token)
            logger.debug(f"JWT token validated successfully. Claims: {claims.claims}")
            
            request.state.claims_identity = claims
            return True, None
            
        except ValueError as e:
            logger.error(f"JWT validation error: {e}")
            return False, JSONResponse(
                {"error": f"JWT validation failed: {str(e)}"}, 
                status_code=401
            )
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {e}")
            return False, JSONResponse(
                {"error": f"Authentication error: {str(e)}"}, 
                status_code=401
            )
    
    def _extract_token(self, auth_header: str) -> str | None:
        """Extract Bearer token from Authorization header."""
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0] != "Bearer":
            logger.error(f"Invalid Authorization header format: {auth_header}")
            return None
        return parts[1]
    
    def _handle_missing_header(self, request: Request) -> tuple[bool, JSONResponse | None]:
        """Handle requests without Authorization header."""
        logger.debug("No Authorization header found")
        
        if not self.auth_config or not hasattr(self.auth_config, 'CLIENT_ID') or not self.auth_config.CLIENT_ID:
            logger.debug("No CLIENT_ID configured - using anonymous claims")
            request.state.claims_identity = self.token_validator.get_anonymous_claims()
            return True, None
        else:
            logger.error("Authorization header required but not found")
            return False, JSONResponse(
                {"error": "Authorization header not found"}, 
                status_code=401
            )
