#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Main entry point for the FastAPI simple auto-signin agent.
This version reuses the existing aiohttp infrastructure.
"""

import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    logger.info("Starting Auto Sign-In Agent with FastAPI (Simple wrapper)")
    
    # Load environment variables
    load_dotenv()
    
    # Import and start the server
    from src.fastapi_simple import start_server
    start_server()

if __name__ == "__main__":
    main()
