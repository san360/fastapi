# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Configuration management for the FastAPI Auto Sign-In Agent.
Centralizes all environment variables and configuration settings.
"""

import logging
from os import environ
from dotenv import load_dotenv
from microsoft.agents.activity import load_configuration_from_env

class AppConfig:
    """Application configuration manager."""
    
    def __init__(self):
        load_dotenv()
        self.agents_sdk_config = load_configuration_from_env(environ)
        
        # Server configuration
        self.port = int(environ.get("PORT", 3978))
        self.host = environ.get("HOST", "localhost")
        
        # App metadata
        self.title = "Auto Sign-In Agent - FastAPI Simple"
        self.description = "Microsoft Agents SDK Auto Sign-In Sample using FastAPI (Simple wrapper)"
        self.version = "1.0.0"
        
    @property
    def has_client_id(self) -> bool:
        """Check if CLIENT_ID is configured."""
        return bool(self.agents_sdk_config and getattr(self.agents_sdk_config, 'CLIENT_ID', None))

class LoggingConfig:
    """Logging configuration manager."""
    
    @staticmethod
    def setup_logging():
        """Configure logging for the application."""
        logging.basicConfig(level=logging.DEBUG)
        
        # Enhanced logging for agents SDK
        agents_logger = logging.getLogger("microsoft.agents")
        agents_logger.setLevel(logging.DEBUG)
        
        return logging.getLogger(__name__)

# Global configuration instances
config = AppConfig()
logger = LoggingConfig.setup_logging()
