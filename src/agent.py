# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
import logging, json
from os import environ, path
from dotenv import load_dotenv

from microsoft.agents.hosting.core import (
    Authorization,
    TurnContext,
    MessageFactory,
    MemoryStorage,
    AgentApplication,
    TurnState,
    MemoryStorage,
)
from microsoft.agents.activity import activity, load_configuration_from_env, ActivityTypes, Activity
from microsoft.agents.hosting.aiohttp import CloudAdapter
from microsoft.agents.authentication.msal import MsalConnectionManager

from .github_api_client import get_current_profile, get_pull_requests
from .user_graph_client import get_user_info
from .cards import create_profile_card, create_pr_card

logger = logging.getLogger(__name__)

# Load configuration from environment
load_dotenv()
agents_sdk_config = load_configuration_from_env(environ)

# Create storage and connection manager
STORAGE = MemoryStorage()
CONNECTION_MANAGER = MsalConnectionManager(**agents_sdk_config)
ADAPTER = CloudAdapter(connection_manager=CONNECTION_MANAGER)
AUTHORIZATION = Authorization(STORAGE, CONNECTION_MANAGER, **agents_sdk_config)

AGENT_APP = AgentApplication[TurnState](
    storage=STORAGE, adapter=ADAPTER, authorization=AUTHORIZATION, **agents_sdk_config
)

# Ensure .env is loaded from the current directory
load_dotenv(path.join(path.dirname(__file__), ".env"))


@AGENT_APP.message(re.compile(r"^/(status|auth status|check status)", re.IGNORECASE))
async def status(context: TurnContext, state: TurnState) -> bool:
    """
    Internal method to check authorization status for all configured handlers.
    Returns True if at least one handler has a valid token.
    """
    await context.send_activity(MessageFactory.text("Welcome to the FastAPI auto-signin demo"))
    tok_graph = await AGENT_APP.auth.get_token(context, "GRAPH")
    tok_github = await AGENT_APP.auth.get_token(context, "GITHUB")
    status_graph = tok_graph.token is not None
    status_github = tok_github.token is not None
    await context.send_activity(
        MessageFactory.text(
            f"Graph status: {'Connected' if status_graph else 'Not connected'}\n"
            f"GitHub status: {'Connected' if status_github else 'Not connected'}"
        )
    )


@AGENT_APP.message("/logout")
async def logout(context: TurnContext, state: TurnState) -> None:
    """
    Sign out the user from all authentication handlers.
    """
    await AGENT_APP.auth.sign_out(context, state)
    await context.send_activity(MessageFactory.text("You have been logged out."))


@AGENT_APP.message(
    re.compile(r"^/(me|profile)$", re.IGNORECASE), auth_handlers=["GRAPH"]
)
async def profile_request(context: TurnContext, state: TurnState) -> None:
    """
    Get user profile information from Microsoft Graph API.
    """
    user_token_response = await AGENT_APP.auth.get_token(context, "GRAPH")
    if user_token_response and user_token_response.token is not None:
        try:
            user_info = await get_user_info(user_token_response.token)
            activity = MessageFactory.attachment(create_profile_card(user_info))
            await context.send_activity(activity)
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            await context.send_activity(
                MessageFactory.text(f"Error getting user profile: {str(e)}")
            )
    else:
        await context.send_activity(
            MessageFactory.text('Token not available. Enter "login" to sign in.')
        )


@AGENT_APP.message(
    re.compile(r"^/(prs|pull requests)$", re.IGNORECASE), auth_handlers=["GITHUB"]
)
async def pull_requests(context: TurnContext, state: TurnState) -> None:
    """
    Get user's GitHub profile and pull requests from a public repository.
    """
    user_token_response = await AGENT_APP.auth.get_token(context, "GITHUB")
    if user_token_response and user_token_response.token is not None:
        try:
            # Get GitHub profile
            gh_prof = await get_current_profile(user_token_response.token)
            await context.send_activity(
                MessageFactory.attachment(create_profile_card(gh_prof))
            )

            # Get pull requests from a public repository
            prs = await get_pull_requests("octocat", "Hello-World", user_token_response.token)
            for pr in prs:
                card = create_pr_card(pr)
                await context.send_activity(MessageFactory.attachment(card))
                
        except Exception as e:
            logger.error(f"Error getting GitHub data: {e}")
            await context.send_activity(
                MessageFactory.text(f"Error getting GitHub data: {str(e)}")
            )
    else:
        try:
            token_response = await AGENT_APP.auth.begin_or_continue_flow(
                context, state, "GITHUB"
            )
            logger.warning(f"GitHub token: {json.dumps(token_response)}")
            if token_response and token_response.token is not None:
                await context.send_activity(
                    MessageFactory.text(f"GitHub token length: {len(token_response.token)}")
                )
            else:
                await context.send_activity(
                    MessageFactory.text("Failed to obtain GitHub token.")
                )
        except Exception as e:
            logger.error(f"Error in GitHub auth flow: {e}")
            await context.send_activity(
                MessageFactory.text(f"Error in GitHub authentication: {str(e)}")
            )


@AGENT_APP.activity(ActivityTypes.invoke)
async def invoke(context: TurnContext, state: TurnState) -> None:
    """
    Handle invoke activities.
    """
    await context.send_activity(MessageFactory.text("Invoke activity received in FastAPI server."))


@AGENT_APP.activity(ActivityTypes.message)
async def message(context: TurnContext, state: TurnState) -> None:
    """
    Handle general message activities.
    """
    await context.send_activity(
        MessageFactory.text(f"You said: {context.activity.text} (processed by FastAPI)")
    )
