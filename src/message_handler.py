# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Message handling logic for Bot Framework messages.
Processes incoming messages using the existing aiohttp infrastructure.
"""

import json
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from microsoft.agents.hosting.aiohttp import start_agent_process
from .request_adapter import FastAPIToAioHttpRequestAdapter

logger = logging.getLogger(__name__)

class MessageHandler:
    """Handler for Bot Framework message processing."""
    
    def __init__(self, agent_configuration, agent_app, adapter):
        self.agent_configuration = agent_configuration
        self.agent_app = agent_app
        self.adapter = adapter
    
    async def handle_message(self, request: Request) -> JSONResponse:
        """
        Process Bot Framework message using existing aiohttp infrastructure.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JSONResponse with processing result
            
        Raises:
            HTTPException: On processing errors
        """
        try:
            # Enhanced logging for debugging
            logger.info(f"Received {request.method} request to {request.url}")
            logger.debug(f"Request headers: {dict(request.headers)}")
            
            # Validate and get request body
            body = await self._get_request_body(request)
            
            # Create and configure adapter
            aiohttp_request = self._create_adapter(request, body)
            
            logger.debug("Calling start_agent_process with aiohttp adapter")
            
            # Process using existing infrastructure
            response = await start_agent_process(
                aiohttp_request,
                self.agent_app,
                self.adapter,
            )
            
            logger.debug(f"Got response from start_agent_process: {response}")
            
            return self._convert_response(response)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def _get_request_body(self, request: Request) -> bytes:
        """Get and validate request body."""
        body = await request.body()
        if not body:
            logger.warning("Request body is empty")
            raise HTTPException(status_code=400, detail="Request body is empty")
        
        logger.debug(f"Request body length: {len(body)}")
        return body
    
    def _create_adapter(self, request: Request, body: bytes) -> FastAPIToAioHttpRequestAdapter:
        """Create and configure FastAPI to aiohttp request adapter."""
        adapter = FastAPIToAioHttpRequestAdapter(request, body)
        adapter.configure_app_state(
            self.agent_configuration,
            self.agent_app,
            self.adapter
        )
        return adapter
    
    def _convert_response(self, response) -> JSONResponse:
        """Convert aiohttp response to FastAPI JSONResponse."""
        if hasattr(response, 'body') and response.body:
            response_data = json.loads(response.body.decode('utf-8')) if response.body else {}
            logger.debug(f"Response data: {response_data}")
            return JSONResponse(content=response_data, status_code=response.status)
        else:
            logger.debug("Returning default OK response")
            return JSONResponse(content={"status": "ok"}, status_code=200)
