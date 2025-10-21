# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
JWT Authentication middleware for FastAPI.
Handles token validation using Microsoft Agents SDK.

⚠️ SECURITY WARNING:
- Set LOG_JWT_TOKENS=true ONLY in development/testing environments
- NEVER enable JWT token logging in production
- JWT tokens contain sensitive authentication information
- Logged tokens can be used to impersonate users if exposed
"""

import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from microsoft_agents.hosting.core.authorization import JwtTokenValidator

logger = logging.getLogger(__name__)

# ⚠️ SECURITY: Enable JWT token logging only for debugging (DO NOT USE IN PRODUCTION)
LOG_JWT_TOKENS = os.environ.get("LOG_JWT_TOKENS", "false").lower() == "true"

if LOG_JWT_TOKENS:
    logger.warning("=" * 80)
    logger.warning("⚠️  SECURITY WARNING: JWT TOKEN LOGGING IS ENABLED ⚠️")
    logger.warning("JWT tokens will be logged in plaintext - USE ONLY FOR TESTING!")
    logger.warning("NEVER enable this in production environments!")
    logger.warning("Set LOG_JWT_TOKENS=false to disable token logging")
    logger.warning("=" * 80)

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
            
            # ⚠️ SECURITY: Log full JWT token ONLY if LOG_JWT_TOKENS is enabled (testing only)
            if LOG_JWT_TOKENS:
                logger.warning("=" * 80)
                logger.warning("⚠️  FULL JWT TOKEN (SENSITIVE - FOR TESTING ONLY):")
                logger.warning(f"Token: {token}")
                logger.warning(f"Length: {len(token)} characters")
                logger.warning("=" * 80)
            else:
                logger.debug(f"Validating JWT token: {token[:20]}...{token[-20:]} (truncated)")
            
            claims = self.token_validator.validate_token(token)
            
            # Log claims information
            logger.debug(f"JWT token validated successfully. Claims: {claims.claims}")
            
            if LOG_JWT_TOKENS:
                logger.warning("⚠️  DECODED TOKEN CLAIMS (SENSITIVE - FOR TESTING ONLY):")
                logger.warning(f"Issuer (iss): {claims.claims.get('iss')}")
                logger.warning(f"Audience (aud): {claims.claims.get('aud')}")
                logger.warning(f"Subject (sub): {claims.claims.get('sub')}")
                logger.warning(f"Expiration (exp): {claims.claims.get('exp')}")
                logger.warning(f"Service URL: {claims.claims.get('serviceurl')}")
                logger.warning(f"All claims: {claims.claims}")
                logger.warning("=" * 80)
            
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
