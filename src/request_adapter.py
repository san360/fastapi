# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
FastAPI to aiohttp request adapter.
Bridges FastAPI requests to work with aiohttp-based start_agent_process.
"""

import json
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

class CaseInsensitiveDict:
    """A case-insensitive dictionary wrapper that mimics aiohttp headers behavior."""
    
    def __init__(self, data: dict):
        self._data = {key.lower(): value for key, value in data.items()}
        self._original_keys = {key.lower(): key for key in data.keys()}
    
    def __getitem__(self, key):
        return self._data[key.lower()]
    
    def __contains__(self, key):
        return key.lower() in self._data
    
    def get(self, key, default=None):
        return self._data.get(key.lower(), default)
    
    def items(self):
        return [(self._original_keys[k], v) for k, v in self._data.items()]

class FastAPIToAioHttpRequestAdapter:
    """
    Adapter to make FastAPI requests work with aiohttp-based start_agent_process.
    Provides aiohttp-compatible interface for existing agent infrastructure.
    """
    
    def __init__(self, fastapi_request: Request, body: bytes):
        self._fastapi_request = fastapi_request
        self._body = body
        self.app = {}  # Will be configured with app state
        self._data = {}  # Store additional data like claims_identity
        
        self._transfer_claims_identity()
        
    def _transfer_claims_identity(self):
        """Transfer claims_identity from FastAPI request state."""
        if hasattr(self._fastapi_request.state, 'claims_identity'):
            self._data['claims_identity'] = self._fastapi_request.state.claims_identity
            logger.debug(f"Transferred claims_identity to adapter: {self._fastapi_request.state.claims_identity}")
        else:
            logger.warning("No claims_identity found in request state")
    
    def configure_app_state(self, agent_configuration, agent_app, adapter):
        """Configure the app state with agent components."""
        self.app = {
            "agent_configuration": agent_configuration,
            "agent_app": agent_app,
            "adapter": adapter
        }
    
    @property
    def headers(self):
        """Return headers with case-insensitive access like aiohttp does."""
        headers_dict = dict(self._fastapi_request.headers)
        
        # Ensure content-type is set
        if 'content-type' not in headers_dict and 'Content-Type' not in headers_dict:
            headers_dict['Content-Type'] = 'application/json'
            
        logger.debug(f"Request headers: {headers_dict}")
        return CaseInsensitiveDict(headers_dict)
    
    @property
    def method(self):
        return self._fastapi_request.method
    
    def get(self, key, default=None):
        """Get method like aiohttp Request object."""
        return self._data.get(key, default)
        
    def __setitem__(self, key, value):
        """Set method to store data in request."""
        self._data[key] = value
        
    def __getitem__(self, key):
        """Get method to access data in request."""
        return self._data[key]
    
    async def read(self):
        return self._body
    
    async def text(self):
        return self._body.decode('utf-8')
    
    async def json(self):
        try:
            text_content = self._body.decode('utf-8')
            logger.debug(f"Request body: {text_content}")
            return json.loads(text_content)
        except Exception as e:
            logger.error(f"Error parsing JSON: {e}")
            raise
