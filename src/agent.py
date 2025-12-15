# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Microsoft Agents SDK integration for FastAPI Bot Framework application.

TROUBLESHOOTING EMPTY SIGN-IN PAGE:

If clicking "Sign in" opens an empty page, check these common issues:

1. **OAuth Connection Name Mismatch**
   - Environment variable names MUST match Azure Bot Service OAuth Connection Settings
   - Check: AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME
   - Verify in Azure Portal: Bot Service → Configuration → OAuth Connection Settings
   - Connection names are CASE-SENSITIVE

2. **Missing OAuth Connection in Azure**
   - Go to Azure Portal → Your Bot → Configuration → Add OAuth Connection Setting
   - For Microsoft Graph: Use "graph" or "GRAPH" (match your .env file)
   - For GitHub: Use "github" or "GITHUB" (match your .env file)

3. **Incorrect Redirect URI**
   - Azure App Registration → Authentication → Redirect URIs
   - Should be: https://token.botframework.com/.auth/web/redirect
   - For local testing: Add http://localhost:3978/.auth/web/redirect

4. **Bot Endpoint Not Accessible**
   - Ensure your bot messaging endpoint is publicly accessible
   - Azure: https://your-app.azurewebsites.net/api/messages
   - Local: Use ngrok or Bot Framework Emulator

5. **Client ID/Secret Mismatch**
   - Verify CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID matches Azure Bot
   - Verify CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET is current

Commands to test:
- /test or /debug - Shows OAuth configuration
- /status - Shows connection status
- /me - Tests Microsoft Graph sign-in
- /prs - Tests GitHub sign-in
"""

import re
import logging, json
from os import environ, path
from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    Authorization,
    TurnContext,
    MessageFactory,
    MemoryStorage,
    AgentApplication,
    TurnState,
    MemoryStorage,
)
from microsoft_agents.activity import (
    activity,
    load_configuration_from_env,
    ActivityTypes,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager

from .github_api_client import get_current_profile, get_pull_requests
from .user_graph_client import get_user_info
from .cards import create_profile_card, create_pr_card
from .openai_handler import handle_openai_message, handle_clear_history, handle_help

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
    Check authorization status for all configured handlers.
    This handler checks token availability without triggering OAuth flows.
    """
    # DIAGNOSTIC: Log activity details
    logger.info("=" * 80)
    logger.info("🔍 DIAGNOSTIC - Incoming Activity Details:")
    logger.info(f"🔍 Activity Type: {context.activity.type}")
    logger.info(f"🔍 Activity Name: {getattr(context.activity, 'name', 'N/A')}")
    logger.info(f"🔍 Activity Text: {context.activity.text}")
    logger.info(f"🔍 Channel ID: {context.activity.channel_id}")
    logger.info("=" * 80)

    await context.send_activity(MessageFactory.text("Welcome to the FastAPI auto-signin demo"))
    
    # Log OAuth connection configuration for debugging
    logger.info("=== OAuth Connection Configuration ===")
    logger.info(f"GRAPH Connection Name: {environ.get('AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME')}")
    logger.info(f"GITHUB Connection Name: {environ.get('AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GITHUB__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME')}")
    logger.info(f"Client ID: {environ.get('CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID', 'NOT SET')}")
    logger.info("======================================")
    
    # Check GRAPH token (gracefully handle errors)
    status_graph = False
    try:
        logger.info("🔍 Attempting to get GRAPH token for status check...")
        tok_graph = await AGENT_APP.auth.get_token(context, "GRAPH")
        status_graph = tok_graph and tok_graph.token is not None
        logger.info(f"🔍 GRAPH token available: {status_graph}")
    except Exception as e:
        logger.warning(f"⚠️ Error checking GRAPH token: {e}")
    
    # Check GITHUB token (gracefully handle errors for unconfigured connections)
    status_github = False
    try:
        logger.info("🔍 Attempting to get GITHUB token for status check...")
        tok_github = await AGENT_APP.auth.get_token(context, "GITHUB")
        status_github = tok_github and tok_github.token is not None
        logger.info(f"🔍 GITHUB token available: {status_github}")
    except Exception as e:
        logger.warning(f"⚠️ Error checking GITHUB token (connection may not be configured): {e}")
    
    logger.info(f"Graph token available: {status_graph}")
    logger.info(f"GitHub token available: {status_github}")
    
    await context.send_activity(
        MessageFactory.text(
            f"Graph status: {'Connected' if status_graph else 'Not connected'}\n"
            f"GitHub status: {'Connected' if status_github else 'Not connected (connection may not be configured)'}"
        )
    )


@AGENT_APP.message("/ping")
async def ping(context: TurnContext, state: TurnState) -> None:
    """
    Simple test command to verify no duplication.
    """
    logger.info("=" * 80)
    logger.info("=== PING Handler Called ===")
    logger.info(f"Activity ID: {context.activity.id}")
    logger.info("=" * 80)

    await context.send_activity(MessageFactory.text("🏓 Pong!"))

    logger.info("=== PING Handler Completed ===")


@AGENT_APP.message("/logout")
async def logout(context: TurnContext, state: TurnState) -> None:
    """
    Sign out the user from all authentication handlers.
    """
    logger.info("=" * 80)
    logger.info("=== LOGOUT Handler Called ===")

    # Sign out from GRAPH
    try:
        await AGENT_APP.auth.sign_out(context, "GRAPH")
        logger.info("Signed out from GRAPH")
    except Exception as e:
        logger.error(f"Error signing out from GRAPH: {e}")

    # Sign out from GITHUB
    try:
        await AGENT_APP.auth.sign_out(context, "GITHUB")
        logger.info("Signed out from GITHUB")
    except Exception as e:
        logger.error(f"Error signing out from GITHUB: {e}")

    await context.send_activity(MessageFactory.text("✅ Signed out from all services."))

    logger.info("=== LOGOUT Handler Completed ===")
    logger.info("=" * 80)


@AGENT_APP.message(re.compile(r"^/(test|debug)$", re.IGNORECASE))
async def test_oauth_config(context: TurnContext, state: TurnState) -> None:
    """
    Test OAuth configuration and display diagnostic information.
    """
    logger.info("=== OAuth Configuration Test ===")
    
    # Get environment variables
    graph_conn = environ.get('AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME', 'NOT SET')
    github_conn = environ.get('AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GITHUB__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME', 'NOT SET')
    client_id = environ.get('CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID', 'NOT SET')
    
    logger.info(f"Graph Connection: {graph_conn}")
    logger.info(f"GitHub Connection: {github_conn}")
    logger.info(f"Client ID: {client_id[:10]}..." if client_id != 'NOT SET' else "NOT SET")
    
    # Check if connections are configured
    message = (
        "🔍 **OAuth Configuration Diagnostic**\n\n"
        f"**Microsoft Graph Connection:** `{graph_conn}`\n"
        f"**GitHub Connection:** `{github_conn}`\n"
        f"**Bot Client ID:** `{client_id[:10]}...`\n\n"
        "**⚠️ Important:**\n"
        "1. These connection names MUST match exactly with Azure Bot Service OAuth settings\n"
        "2. Go to Azure Portal → Bot Service → Configuration → OAuth Connection Settings\n"
        "3. Verify connection names match (case-sensitive)\n"
        "4. Check that redirect URI is configured correctly\n\n"
        "**Common Issues:**\n"
        "- Empty sign-in page = Connection name mismatch or not configured in Azure\n"
        "- Wrong redirect URI in OAuth app registration\n"
        "- Bot messaging endpoint not publicly accessible\n"
    )
    
    await context.send_activity(MessageFactory.text(message))
    logger.info("===================================")


@AGENT_APP.message(
    re.compile(r"^/(me|profile)$", re.IGNORECASE), auth_handlers=["GRAPH"]
)
async def profile_request(context: TurnContext, state: TurnState) -> None:
    """
    Get user profile information from Microsoft Graph API.
    """
    logger.info("=" * 80)
    logger.info("=== Profile Request Handler Called ===")
    logger.info(f"Activity ID: {context.activity.id}")
    logger.info(f"Activity Type: {context.activity.type}")
    logger.info(f"Activity Text: {context.activity.text}")
    logger.info(f"Activity Timestamp: {context.activity.timestamp}")
    logger.info(f"Attempting to get GRAPH token...")

    user_token_response = await AGENT_APP.auth.get_token(context, "GRAPH")

    logger.info(f"Token response received: {user_token_response is not None}")
    if user_token_response:
        logger.info(f"Token available: {user_token_response.token is not None}")
        if user_token_response.token:
            logger.info(f"Token length: {len(user_token_response.token)}")

    if user_token_response and user_token_response.token is not None:
        try:
            logger.info("✅ Token obtained - fetching user profile from Microsoft Graph")
            user_info = await get_user_info(user_token_response.token)
            logger.info(f"📊 Microsoft Graph API Response: {json.dumps(user_info, indent=2)}")
            activity = MessageFactory.attachment(create_profile_card(user_info))
            logger.info("📤 Sending profile card to user")
            await context.send_activity(activity)
            logger.info("✅ Profile card sent successfully")
        except Exception as e:
            logger.error(f"Error getting user profile: {e}", exc_info=True)
            await context.send_activity(
                MessageFactory.text(f"Error getting user profile: {str(e)}")
            )
    else:
        # DO NOT send any message - the framework will automatically send the sign-in card
        # and continue this handler after authentication succeeds
        logger.info("⚠️  No token available - framework will handle OAuth flow and continuation")

    logger.info("=== Profile Request Handler Completed ===")
    logger.info("=" * 80)


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


@AGENT_APP.activity(ActivityTypes.invoke)
async def handle_invoke_activity(context: TurnContext, _state: TurnState) -> None:
    """
    Handle invoke activities.

    Note: signin/tokenExchange is handled automatically by the Microsoft Agents SDK's
    internal OAuth flow which sends its own InvokeResponse. This handler only logs
    for diagnostic purposes - the framework handles the actual response.
    """
    # DIAGNOSTIC - Log all invoke activities for troubleshooting
    logger.info("=" * 80)
    logger.info("🔍 DIAGNOSTIC - Invoke activity received")
    logger.info(f"🔍 Activity ID: {context.activity.id}")
    logger.info(f"🔍 Activity Type: {context.activity.type}")
    logger.info(f"🔍 Activity Name: {context.activity.name}")
    logger.info(f"🔍 Activity Timestamp: {context.activity.timestamp}")

    # Log token exchange resource ID for diagnostic purposes
    if context.activity.name == "signin/tokenExchange" and context.activity.value:
        token_exchange_id = context.activity.value.get("id")
        if token_exchange_id:
            logger.info(f"🔍 Token Exchange Resource ID: {token_exchange_id}")

    logger.info("=" * 80)

    # DO NOT send response - the framework's _OAuthFlow already handles signin/tokenExchange
    # and sends the appropriate InvokeResponse automatically


# OpenAI-powered message handlers

@AGENT_APP.message(re.compile(r"^/(help|commands)$", re.IGNORECASE))
async def help_command(context: TurnContext, state: TurnState) -> bool:
    """
    Display help message with available commands.
    """
    await handle_help(context, state)
    return True


@AGENT_APP.message(re.compile(r"^/(clear|reset)$", re.IGNORECASE))
async def clear_command(context: TurnContext, state: TurnState) -> bool:
    """
    Clear conversation history.
    """
    await handle_clear_history(context, state)
    return True


@AGENT_APP.message(re.compile(r"^(?!/).*", re.IGNORECASE))
async def openai_message_handler(context: TurnContext, state: TurnState) -> bool:
    """
    Handle all non-command messages with OpenAI.

    This catches any message that doesn't start with '/' and processes it
    through the OpenAI service for intelligent responses.
    """
    await handle_openai_message(context, state, use_conversation_history=True)
    return True
