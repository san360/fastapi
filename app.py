# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
FastAPI application entry point that can be used directly with uvicorn.
Run with: uvicorn app:app --host localhost --port 3978 --reload
"""

# enable logging for Microsoft Agents library
import logging
ms_agents_logger = logging.getLogger("microsoft.agents")
ms_agents_logger.addHandler(logging.StreamHandler())
ms_agents_logger.setLevel(logging.INFO)

# Import the FastAPI app from our implementation
from src.fastapi_agent import app

if __name__ == "__main__":
    import uvicorn
    from os import environ
    
    port = int(environ.get("PORT", 3978))
    host = environ.get("HOST", "localhost")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level="info",
        reload=True
    )
