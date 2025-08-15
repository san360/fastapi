# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
API route definitions for the FastAPI Auto Sign-In Agent.
Defines all endpoints and their response structures.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .message_handler import MessageHandler

def create_routes(message_handler: MessageHandler) -> APIRouter:
    """Create and configure API routes."""
    router = APIRouter()
    
    @router.post("/api/messages")
    async def handle_messages(request: Request) -> JSONResponse:
        """Main endpoint for handling Bot Framework messages."""
        return await message_handler.handle_message(request)
    
    @router.get("/")
    async def root():
        """Root endpoint with service information."""
        return {
            "message": "Auto Sign-In Agent FastAPI Server is running (Simple wrapper)",
            "framework": "FastAPI + aiohttp hosting",
            "docs": "/docs",
            "health": "/health"
        }
    
    @router.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy", 
            "service": "auto-signin-agent-fastapi-simple",
            "version": "1.0.0"
        }
    
    return router
