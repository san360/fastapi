# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
FastAPI application factory.
Creates and configures the FastAPI application with all dependencies.
"""

from fastapi import FastAPI, Request
from .config import config, logger
from .auth_middleware import JWTAuthMiddleware
from .message_handler import MessageHandler
from .api_routes import create_routes
from .agent import AGENT_APP, CONNECTION_MANAGER

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with configuration
    app = FastAPI(
        title=config.title,
        description=config.description,
        version=config.version,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure app state
    _configure_app_state(app)
    
    # Add middleware
    _add_middleware(app)
    
    # Add routes
    _add_routes(app)
    
    logger.info("FastAPI application created and configured")
    return app

def _configure_app_state(app: FastAPI):
    """Configure application state with agent components."""
    app.state.agent_configuration = CONNECTION_MANAGER.get_default_connection_configuration()
    app.state.agent_app = AGENT_APP
    app.state.adapter = AGENT_APP.adapter

def _add_middleware(app: FastAPI):
    """Add authentication middleware to the application."""
    auth_middleware = JWTAuthMiddleware(app.state.agent_configuration)
    
    @app.middleware("http")
    async def jwt_auth_middleware(request: Request, call_next):
        """JWT authorization middleware wrapper."""
        success, error_response = await auth_middleware.authenticate_request(request)
        
        if not success:
            return error_response
        
        response = await call_next(request)
        return response

def _add_routes(app: FastAPI):
    """Add API routes to the application."""
    message_handler = MessageHandler(
        app.state.agent_configuration,
        app.state.agent_app,
        app.state.adapter
    )
    
    router = create_routes(message_handler)
    app.include_router(router)
