# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Simple FastAPI wrapper for the auto-signin agent.
Refactored entry point using clean architecture principles.
"""

from .app_factory import create_app
from .server import start_server

# Create the application instance for external use
app = create_app()

if __name__ == "__main__":
    start_server()
