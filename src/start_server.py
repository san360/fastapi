from os import environ
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from microsoft.agents.hosting.core import AgentApplication, AgentAuthConfiguration
from microsoft.agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)

def start_server(
    agent_application: AgentApplication, 
    auth_configuration: AgentAuthConfiguration
):
    """
    Start the FastAPI server with the agent application.
    """
    app = FastAPI(
        title="Auto Sign-In Agent",
        description="Microsoft Agent SDK Auto Sign-In Sample using FastAPI",
        version="1.0.0"
    )
    
    # Store agent configuration in app state
    app.state.agent_configuration = auth_configuration
    app.state.agent_app = agent_application
    app.state.adapter = agent_application.adapter
    
    # Custom middleware to handle JWT authorization
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        """
        Custom middleware to handle JWT authorization similar to aiohttp implementation.
        """
        try:
            # For now, we'll let the agent handle authentication
            response = await call_next(request)
            return response
        except Exception as e:
            return JSONResponse(
                status_code=500, 
                content={"error": f"Middleware error: {str(e)}"}
            )
    
    @app.post("/api/messages")
    async def messages_endpoint(request: Request) -> JSONResponse:
        """
        Main endpoint for receiving bot framework messages.
        """
        try:
            agent: AgentApplication = request.app.state.agent_app
            adapter: CloudAdapter = request.app.state.adapter
            
            # Convert FastAPI request to format expected by start_agent_process
            # This is a simplified approach - in production you'd need proper conversion
            response = await start_agent_process(
                request,
                agent,
                adapter,
            )
            return response
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error))
    
    @app.get("/")
    async def root():
        """
        Root endpoint for health check.
        """
        return {"message": "Auto Sign-In Agent FastAPI Server is running"}
    
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint.
        """
        return {"status": "healthy", "service": "auto-signin-agent"}
    
    # Start the server
    port = int(environ.get("PORT", 3978))
    host = environ.get("HOST", "localhost")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except Exception as error:
        raise error
