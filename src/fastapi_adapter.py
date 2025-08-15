# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
FastAPI Adapter for Microsoft Agents SDK.
This provides a bridge between FastAPI and the Microsoft Agents framework.
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from microsoft.agents.hosting.core import AgentApplication
from microsoft.agents.hosting.aiohttp import CloudAdapter
from microsoft.agents.activity import Activity

logger = logging.getLogger(__name__)

class FastAPIAdapter:
    """
    Adapter class to bridge FastAPI requests with Microsoft Agents SDK.
    """
    
    def __init__(self, cloud_adapter: CloudAdapter):
        self.cloud_adapter = cloud_adapter
    
    async def process_activity(
        self, 
        request: Request, 
        agent_app: AgentApplication
    ) -> JSONResponse:
        """
        Process an incoming activity from FastAPI request.
        """
        try:
            # Get request body
            body = await request.body()
            if not body:
                raise HTTPException(status_code=400, detail="Request body is empty")
            
            # Parse the activity
            try:
                activity_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
            
            # Get authorization header
            auth_header = request.headers.get("Authorization", "")
            
            # Create a mock aiohttp-style request object for compatibility
            mock_request = MockAioHttpRequest(
                body=body,
                headers=dict(request.headers),
                method=request.method
            )
            
            # Process through the cloud adapter
            # Note: This is a simplified implementation
            # In production, you'd need proper request/response conversion
            response_activity = await self.cloud_adapter.process_activity(
                activity_data, 
                auth_header, 
                agent_app.on_turn
            )
            
            if response_activity:
                return JSONResponse(
                    content=response_activity,
                    status_code=200
                )
            else:
                return JSONResponse(
                    content={"status": "ok"},
                    status_code=200
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing activity: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing activity: {str(e)}"
            )


class MockAioHttpRequest:
    """
    Mock aiohttp request object for compatibility with existing agent code.
    """
    
    def __init__(self, body: bytes, headers: Dict[str, str], method: str):
        self._body = body
        self._headers = headers
        self._method = method
        self.app = {}  # Mock app state
    
    @property
    def headers(self):
        return self._headers
    
    @property
    def method(self):
        return self._method
    
    async def read(self):
        return self._body
    
    async def text(self):
        return self._body.decode('utf-8')
    
    async def json(self):
        return json.loads(self._body.decode('utf-8'))
