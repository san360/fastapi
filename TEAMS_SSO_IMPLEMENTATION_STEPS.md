# Teams SSO Implementation Guide - Microsoft Agents SDK

## Overview

This guide shows how to configure Teams Single Sign-On (SSO) for your bot using **Microsoft Agents SDK for Python**. By following these steps, you'll enable seamless authentication for Teams users.

### What You'll Achieve

**Current State**: Users must click "Sign in" and complete OAuth flow every time (10-15 seconds)

**After SSO Configuration**:
- First time: One-click inline consent (2 seconds)
- Every subsequent time: Instant response (< 1 second, no sign-in!)

### How Teams SSO Works

Teams SSO eliminates the need for users to manually sign in to your bot. When properly configured:

1. **First time**: User sees inline consent dialog (one-click approval)
2. **All subsequent times**: Instant authentication (no prompts)
3. **Automatic token management**: Framework handles token exchange and storage

The Microsoft Agents SDK provides built-in SSO support through the `auth_handlers` parameter on route decorators.

### Prerequisites

- ✅ Microsoft Agents SDK installed (you have this)
- ✅ Azure Bot Service resource created (you have this)
- ✅ Microsoft Entra ID app registration (cc451968-4dc2-46f3-9b4f-f8eae2782b25)
- ✅ Admin access to Azure Portal

### Estimated Time

- **Code verification**: 5 minutes
- **Azure/Entra configuration**: 20 minutes
- **Teams app creation**: 10 minutes
- **Testing**: 10 minutes
- **Total**: ~45 minutes

---

## Quick Start Summary

```text
1. Verify your code uses auth_handlers decorators (you already have this)
2. Configure Entra ID (Application ID URI + scopes)
3. Update Azure Bot OAuth (enable token exchange)
4. Create Teams app manifest with webApplicationInfo
5. Package and upload to Teams
6. Test - SSO works automatically!
```

---

## PART 1: CODE VERIFICATION

### Your Code is Already Correct!

Your existing code in `src/agent.py` already follows the correct pattern:

```python
# ✅ THIS IS THE CORRECT PATTERN (you already have this!)
@AGENT_APP.message(
    re.compile(r"^/(me|profile)$", re.IGNORECASE),
    auth_handlers=["GRAPH"]  # ← This triggers automatic SSO!
)
async def profile_request(context: TurnContext, state: TurnState) -> None:
    """
    Get Microsoft Graph profile.

    The auth_handlers parameter tells the framework to require authentication.
    The framework automatically handles signin/tokenExchange for Teams SSO.
    """
    logger.info("=== Profile Request ===")

    # Get token (framework handles SSO automatically)
    user_token_response = await AGENT_APP.auth.get_token(context, "GRAPH")

    if user_token_response and user_token_response.token:
        # Use the token
        user_info = await get_user_info(user_token_response.token)
        await context.send_activity(MessageFactory.attachment(create_profile_card(user_info)))
    else:
        await context.send_activity(MessageFactory.text("Unable to get token"))
```

### Invoke Handler Pattern

Your invoke handler should be minimal (the framework processes tokenExchange internally):

```python
# ✅ CORRECT - Minimal invoke handler
@AGENT_APP.activity(ActivityTypes.invoke)
async def handle_invoke_activity(context: TurnContext, _state: TurnState) -> None:
    """
    Handle invoke activities.

    Note: signin/tokenExchange is handled automatically by the Microsoft Agents SDK's
    internal OAuth flow. No custom code needed for Teams SSO token exchange.
    """
    logger.info(f"Invoke activity received: {context.activity.name}")

    # Simple acknowledgment - framework handles tokenExchange automatically
    await context.send_activity(
        MessageFactory.text(f"Invoke activity received: {context.activity.name}")
    )
```

### SSO Authentication Flow

When SSO is properly configured in Azure:

```text
User sends /me command
  ↓
Framework checks for existing token → None found
  ↓
Framework requests authentication
  ↓
Teams displays inline consent dialog (first time only)
  ↓
User clicks "Continue"
  ↓
Teams exchanges token with bot automatically
  ↓
Token stored → Profile displayed instantly
```

All subsequent `/me` commands use the stored token with no user interaction required.

---

## PART 2: MICROSOFT ENTRA ID CONFIGURATION

### Step 2.1: Navigate to Your App Registration

```text
1. Open Azure Portal: https://portal.azure.com
2. Search for "Microsoft Entra ID" (or "Azure Active Directory")
3. Click "App registrations" (left menu)
4. Find your bot: cc451968-4dc2-46f3-9b4f-f8eae2782b25
```

### Step 2.2: Configure Application ID URI

This URI identifies your bot to Teams for SSO.

```text
1. Click "Expose an API" (left menu)

2. Click "Add" next to "Application ID URI"

3. IMPORTANT: Set it to (add "botid-" prefix):
   api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25

4. Click "Save"
```

**Why this format?** Teams requires `api://botid-{AppId}` for bot SSO.

### Step 2.3: Add OAuth Scope

```text
1. Still in "Expose an API" section

2. Click "Add a scope"

3. Fill in:
   Scope name: access_as_user
   Who can consent?: Admins and users
   Admin consent display name: Access bot as user
   Admin consent description: Allows Teams to call the bot's APIs as the current user
   User consent display name: Access bot as you
   User consent description: Allows the bot to access Microsoft Graph on your behalf
   State: Enabled

4. Click "Add scope"
```

You should now see: `api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25/access_as_user`

### Step 2.4: Authorize Teams Clients

Pre-authorize Teams apps to request tokens without consent prompts.

```text
1. Still in "Expose an API" → "Authorized client applications"

2. Click "Add a client application"

3. Add Teams Desktop/Mobile:
   Client ID: 1fec8e78-bce4-4aaf-ab1b-5451cc387264
   ✓ Check: api://botid-{YourAppId}/access_as_user
   Click "Add application"

4. Click "Add a client application" again

5. Add Teams Web:
   Client ID: 5e3ce6c0-2b1f-4285-8d4b-75ee78787346
   ✓ Check: api://botid-{YourAppId}/access_as_user
   Click "Add application"

You should now see 2 authorized applications.
```

### Step 2.5: Grant Admin Consent

```text
1. Click "API permissions" (left menu)

2. You should see: Microsoft Graph → User.Read (Delegated)

3. Click "Grant admin consent for [Your Organization]"

4. Click "Yes"

5. Status should show: "Granted for [Your Org]" with green checkmark
```

---

## PART 3: AZURE BOT SERVICE CONFIGURATION

### Step 3.1: Navigate to Bot OAuth Settings

```text
1. Azure Portal → Search for your bot resource
2. Click "Configuration" (left menu)
3. Scroll to "OAuth Connection Settings" section
4. Click on your "GRAPH" connection
```

### Step 3.2: Enable Token Exchange

This is the **critical step** that enables Teams SSO!

```text
1. In the OAuth connection configuration form

2. Scroll down to find "Token Exchange URL" field (textbox)

3. In the "Token Exchange URL" textbox, enter:
   https://token.botframework.com/api/oauth/token

4. Verify other settings:
   Service Provider: Azure Active Directory v2
   Client ID: cc451968-4dc2-46f3-9b4f-f8eae2782b25
   Client Secret: (your secret - hidden)
   Tenant ID: 2bab7b85-25a5-40d1-a83e-77d201b4da49
   Scopes: openid profile offline_access User.Read

5. Click "Save"

6. Wait for "Successfully saved" confirmation
```

**Critical**: Connection name "GRAPH" must match your .env:
```bash
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=GRAPH
```

### Step 3.3: Verify Teams Channel

```text
1. Click "Channels" (left menu)
2. Microsoft Teams should show status "Running"
3. If not enabled, click the Teams icon → Apply
```

---

## PART 4: CREATE TEAMS APP MANIFEST

### Step 4.1: Manifest Configuration

Your manifest at `teams-app/manifest.json` should have:

**Critical SSO Configuration:**

```json
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.22/MicrosoftTeams.schema.json",
  "manifestVersion": "1.22",
  "version": "1.0.0",

  "id": "cc451968-4dc2-46f3-9b4f-f8eae2782b25",

  "name": {
    "short": "FastAPI Auto Sign-In Agent",
    "full": "FastAPI Auto Sign-In Agent"
  },

  "developer": {
    "name": "Microsoft",
    "websiteUrl": "https://www.microsoft.com",
    "privacyUrl": "https://www.microsoft.com/info/privacy",
    "termsOfUseUrl": "https://www.microsoft.com/info/tc"
  },

  "description": {
    "short": "FastAPI Auto Sign-In Agent - Teams bot with SSO",
    "full": "A FastAPI bot with Teams SSO and GitHub integration"
  },

  "icons": {
    "outline": "outline.png",
    "color": "color.png"
  },

  "accentColor": "#a6ffd2",

  "bots": [{
    "botId": "cc451968-4dc2-46f3-9b4f-f8eae2782b25",
    "scopes": ["personal"],
    "supportsFiles": false,
    "isNotificationOnly": false
  }],

  "permissions": ["identity", "messageTeamMembers"],

  "validDomains": [
    "token.botframework.com"
  ],

  "webApplicationInfo": {
    "id": "cc451968-4dc2-46f3-9b4f-f8eae2782b25",
    "resource": "api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25"
  }
}
```

**Critical fields for SSO:**

- `id` and `botId`: Must be your Azure AD App ID
- `webApplicationInfo.id`: Same App ID
- `webApplicationInfo.resource`: Must match Application ID URI from Step 2.2
- `validDomains`: Required for Bot Framework OAuth

### Step 4.2: Icon Requirements

You need proper icons:

**color.png:**
- Size: 192x192 pixels
- Format: PNG with transparency

**outline.png:**
- Size: 32x32 pixels
- Format: PNG with transparency
- White outline on transparent background

Your icons are already created at correct dimensions ✓

### Step 4.3: Package the App

Use the provided PowerShell script to package your Teams app:

```powershell
# Run the packaging script
.\package-teams-app.ps1
```

This script will:

- Verify all required files exist (manifest.json, color.png, outline.png)
- Create FastAPIBot.zip with proper structure
- Validate the ZIP contents

**Note**: Files must be in the root of the ZIP, not in a subfolder.

---

## PART 5: DEPLOY TO TEAMS

### Step 5.1: Upload to Teams

```text
1. Open Microsoft Teams (desktop or web)

2. Click "Apps" in left sidebar

3. Click "Manage your apps" (bottom left)

4. Click "Upload an app" → "Upload a custom app"

5. Select FastAPIBot.zip

6. Click "Add" to install
```

### Step 5.2: Start Chat with Bot

```text
1. In Teams, go to "Chat"

2. Click "New chat"

3. Search for "FastAPI Auto Sign-In Agent"

4. Select your bot

5. Ready to test!
```

---

## PART 6: TEST AND VERIFY

### Step 6.1: Test Basic Command

```text
Type in Teams chat: /status

Expected response:
"Welcome to the FastAPI auto-signin demo
Graph status: Not connected
GitHub status: Not connected"

✅ If this works, bot is responding correctly
```

### Step 6.2: Test SSO (First Time)

```text
Type in Teams chat: /me

Expected behavior (first time):
1. Inline consent dialog appears in Teams:
   "FastAPI Bot wants to access your profile"
   [Continue] [Cancel]

2. Click "Continue"

3. Profile appears within 1-2 seconds:
   - Display name
   - Email
   - Job title
   - Profile picture

4. NO SEPARATE SIGN-IN CARD should appear
```

**If you see a sign-in card with "Sign in" button:**
- SSO is NOT configured correctly
- Teams is falling back to standard OAuth
- Review Azure configuration (Parts 2 & 3)

### Step 6.3: Test Subsequent Requests

```text
Type in Teams chat: /me

Expected behavior (subsequent times):
- Profile appears INSTANTLY (< 1 second)
- NO consent dialog
- NO sign-in card

✅ This confirms SSO is working!
```

### Step 6.4: Check Logs (Diagnostic)

If you added diagnostic logging to your invoke handler:

```bash
# View Azure App Service logs
az webapp log tail \
  --name app-fastapi-agent-1755331446 \
  --resource-group rg-fastapi-agent
```

**When SSO is working**, you'll see:

```text
🔍 DIAGNOSTIC - Invoke activity received
🔍 Activity Type: invoke
🔍 Activity Name: signin/tokenExchange
```

**When SSO is NOT configured**, you'll see:

```text
🔍 DIAGNOSTIC - Incoming Activity Details:
🔍 Activity Type: message  ← NOT invoke!
🔍 Activity Text: /me
```

If you see `type: message` instead of `type: invoke`, Teams is not sending SSO requests. Review Azure configuration.

---

## PART 7: TROUBLESHOOTING

### Issue 1: Still See Sign-In Card (SSO Not Working)

**Symptoms**: OAuth sign-in card appears instead of instant profile

**Possible Causes:**

```text
A. Token Exchange URL not set
   Fix: Go to Part 3, Step 3.2
   Verify: https://token.botframework.com/api/oauth/token

B. Application ID URI missing or wrong format
   Fix: Go to Part 2, Step 2.2
   Must be: api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25
   NOT: api://cc451968-4dc2-46f3-9b4f-f8eae2782b25 (missing botid-)

C. webApplicationInfo missing from manifest
   Fix: Verify manifest.json has webApplicationInfo section
   Resource must match Application ID URI exactly

D. Teams clients not authorized
   Fix: Go to Part 2, Step 2.4
   Add both Teams client IDs

E. Old Teams app cached
   Fix: Remove bot from Teams, reinstall fresh ZIP
```

### Issue 2: Consent Appears Every Time

**Symptoms**: Consent dialog on every `/me` command

**Causes:**

```text
A. Admin consent not granted
   Fix: Part 2, Step 2.5 - Grant admin consent

B. Token not being stored
   Fix: Verify MemoryStorage is configured in agent.py
   Note: MemoryStorage loses tokens on restart
   Consider: Implement persistent storage (BlobStorage)
```

### Issue 3: Bot Not Responding

**Symptoms**: No response to any commands

**Causes:**

```text
A. Bot not deployed or not running
   Fix: Check Azure App Service status
   az webapp show --name app-fastapi-agent-1755331446 --query state

B. Teams channel not enabled
   Fix: Part 3, Step 3.3

C. Messaging endpoint incorrect
   Fix: Azure Bot → Configuration → Messaging endpoint:
   https://app-fastapi-agent-1755331446.azurewebsites.net/api/messages
```

### Debugging Checklist

```text
Code:
□ Routes use auth_handlers=["GRAPH"] parameter
□ Invoke handler is minimal (doesn't manually handle tokenExchange)
□ Bot is deployed and running

Entra ID:
□ Application ID URI: api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25
□ Scope created: access_as_user
□ Teams clients authorized (2 client IDs)
□ Admin consent granted (green checkmark)

Azure Bot Service:
□ OAuth connection: GRAPH
□ Token Exchange URL: https://token.botframework.com/api/oauth/token
□ Connection name matches .env file
□ Teams channel enabled

Teams App:
□ manifest.json id matches bot App ID
□ webApplicationInfo.resource matches Application ID URI
□ validDomains includes token.botframework.com
□ ZIP has files in root (not subfolder)
□ App uploaded to Teams

Testing:
□ /status works
□ /me shows inline consent (first time)
□ /me shows profile instantly (subsequent times)
□ NO sign-in card appears
```

---

## SUMMARY

### What Makes SSO Work

**Three critical configurations:**

1. **Entra ID**: Application ID URI = `api://botid-{AppId}` + authorized Teams clients
2. **Azure Bot OAuth**: Token Exchange URL = `https://token.botframework.com/api/oauth/token`
3. **Teams Manifest**: `webApplicationInfo` with matching `resource` URI

### Required Configuration Components

**Code (already in place):**
- Routes decorated with `auth_handlers=["GRAPH"]` parameter
- Minimal invoke handler (framework handles token exchange automatically)

**Azure Configuration (must be configured):**
- Entra ID Application ID URI with `api://botid-` prefix
- OAuth scope `access_as_user` exposed
- Teams clients pre-authorized
- Bot Service Token Exchange URL enabled

**Teams App (must be deployed):**
- Manifest with `webApplicationInfo` section
- Matching Application ID URI in `resource` field

### Key Files

**Your code** (already correct):
- `src/agent.py` - Uses auth_handlers decorators ✓

**Teams app** (created):
- `teams-app/manifest.json` - SSO configuration ✓
- `teams-app/color.png` - 192x192 icon ✓
- `teams-app/outline.png` - 32x32 icon ✓
- `teams-app/FastAPIBot.zip` - Deployable package ✓

### Verification

✅ **SSO is working when:**
- **First `/me` command**: Inline consent dialog appears in Teams (one-click)
- **User clicks "Continue"**: Profile displays within 2 seconds
- **Subsequent `/me` commands**: Profile appears instantly (< 1 second)
- **No sign-in card**: Users never see a separate "Sign in" button

❌ **SSO is NOT working when:**
- **Sign-in card appears**: Blue "Sign in" button displayed in chat
- **Browser window opens**: OAuth authentication happens outside Teams
- **Repeated consent**: Consent dialog appears every time
- **Slow authentication**: Takes 10-15 seconds each time

### References

- [Official Microsoft Auto Sign-In Sample](https://github.com/microsoft/Agents/tree/main/samples/python/auto-signin)
- [Microsoft Agents SDK Overview](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/agents-sdk-overview)
- [Teams Bot SSO Documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/authentication/bot-sso-code)

---

**Total Implementation Time**: ~45 minutes

**Result**: Zero-friction authentication in Teams! 🎉
