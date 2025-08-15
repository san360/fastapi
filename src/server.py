# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Server startup logic for the FastAPI Auto Sign-In Agent.
Handles server configuration and startup.
"""

import uvicorn
from .config import config, logger
from .app_factory import create_app

def start_server():
    """Start the FastAPI server with configured settings."""
    logger.info(f"Starting FastAPI simple server on {config.host}:{config.port}")
    
    # Create the application
    app = create_app()
    
    # Start the server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    start_server()
