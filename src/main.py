# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# enable logging for Microsoft Agents library
import logging
ms_agents_logger = logging.getLogger("microsoft.agents")
ms_agents_logger.addHandler(logging.StreamHandler())
ms_agents_logger.setLevel(logging.INFO)

from .fastapi_agent import start_server

if __name__ == "__main__":
    start_server()
