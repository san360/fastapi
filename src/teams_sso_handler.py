# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Teams SSO Token Exchange Handler using Microsoft Agents SDK.

This module provides Teams Single Sign-On (SSO) support without using
the deprecated Bot Framework SDK v4. It uses only Microsoft Agents SDK components.
"""

import logging
from typing import Optional

from microsoft_agents.hosting.core import TurnContext, MessageFactory, TurnState
from microsoft_agents.activity import (
    TokenExchangeInvokeRequest,
    TokenExchangeInvokeResponse,
    ActivityTypes,
    Activity
)

logger = logging.getLogger(__name__)


async def handle_teams_sso_token_exchange(
    context: TurnContext,
    state: TurnState,
    agent_auth
) -> None:
    """
    Handle Teams SSO token exchange using Microsoft Agents SDK.

    Flow:
    1. Teams sends invoke activity with user's Azure AD token
    2. Extract token from activity.value
    3. Use agent_auth.exchange_token() to exchange for Graph/GitHub token
    4. Token is automatically stored in Bot Framework Token Store
    5. Send success/failure response back to Teams

    Args:
        context: The turn context for the current conversation turn
        state: The turn state containing conversation state
        agent_auth: The Authorization instance from AgentApplication

    Returns:
        None (sends response directly to context)

    Raises:
        Exception: Any errors are caught and sent as failure response to Teams
    """

    try:
        # Parse the token exchange request from Teams
        # Teams sends: { id, connectionName, token }
        token_exchange_request = TokenExchangeInvokeRequest(
            **context.activity.value
        )

        logger.info("=== Teams SSO Token Exchange ===")
        logger.info(f"Request ID: {token_exchange_request.id}")
        logger.info(f"Connection Name: {token_exchange_request.connection_name}")
        logger.info(f"Token received: {bool(token_exchange_request.token)}")
        logger.info(f"Token length: {len(token_exchange_request.token) if token_exchange_request.token else 0}")

        # Determine which auth handler to use
        # Teams sends the connection name (e.g., "GRAPH"), or we default to GRAPH
        auth_handler_id = token_exchange_request.connection_name or "GRAPH"

        logger.info(f"Exchanging token for auth handler: {auth_handler_id}")

        # Exchange the Teams AAD token for a Graph/GitHub token
        # This method from Microsoft Agents SDK:
        # 1. Takes the incoming Teams Azure AD token
        # 2. Calls Bot Framework Token Service API
        # 3. Exchanges it for handler-specific token (Graph/GitHub)
        # 4. Automatically stores token in Bot Framework Token Store
        # 5. Returns TokenResponse with the exchanged token
        token_response = await agent_auth.exchange_token(
            context=context,
            auth_handler_id=auth_handler_id,
            exchange_connection=token_exchange_request.connection_name
        )

        if token_response and token_response.token:
            logger.info("✅ Token exchange successful!")
            logger.info(f"Token stored for connection: {token_response.connection_name}")
            logger.info(f"Exchanged token length: {len(token_response.token)}")

            # Send success response back to Teams
            # Teams expects an invoke_response activity with status 200
            await send_token_exchange_success(
                context,
                token_exchange_request.id,
                auth_handler_id
            )

            logger.info("Success response sent to Teams")

        else:
            logger.error("❌ Token exchange failed - no token returned")
            await send_token_exchange_failure(
                context,
                token_exchange_request.id,
                "Token exchange returned no token"
            )

    except ValueError as e:
        # Pydantic validation error when parsing TokenExchangeInvokeRequest
        logger.error(f"❌ Invalid token exchange request format: {e}", exc_info=True)
        await send_token_exchange_failure(
            context,
            None,
            f"Invalid request format: {str(e)}"
        )

    except Exception as e:
        # Any other errors during token exchange
        logger.error(f"❌ Token exchange error: {e}", exc_info=True)

        request_id = None
        if 'token_exchange_request' in locals():
            request_id = token_exchange_request.id

        await send_token_exchange_failure(
            context,
            request_id,
            str(e)
        )


async def send_token_exchange_success(
    context: TurnContext,
    request_id: str,
    connection_name: str
) -> None:
    """
    Send success response to Teams for token exchange.

    Args:
        context: The turn context
        request_id: The ID from the original token exchange request
        connection_name: The OAuth connection name (e.g., "GRAPH")
    """

    response = Activity(
        type=ActivityTypes.invoke_response,
        value={
            "status": 200,
            "body": TokenExchangeInvokeResponse(
                id=request_id,
                connection_name=connection_name
            ).model_dump()
        }
    )

    await context.send_activity(response)


async def send_token_exchange_failure(
    context: TurnContext,
    request_id: Optional[str],
    error_message: str
) -> None:
    """
    Send failure response to Teams for token exchange.

    Args:
        context: The turn context
        request_id: The ID from the original token exchange request (if available)
        error_message: Description of the error
    """

    response = Activity(
        type=ActivityTypes.invoke_response,
        value={
            "status": 500,
            "body": {
                "id": request_id,
                "error": error_message,
                "failureDetail": "Token exchange failed"
            }
        }
    )

    await context.send_activity(response)
    logger.info(f"Failure response sent to Teams: {error_message}")
