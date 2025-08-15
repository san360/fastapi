#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Main entry point for the FastAPI Auto Sign-In Agent.
This application demonstrates Microsoft Agents SDK integration with FastAPI.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    try:
        logger.info("🚀 Starting FastAPI Auto Sign-In Agent")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import and start the server from our refactored code
        from src.server import start_server
        start_server()
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
