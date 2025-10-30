# Teams SSO Implementation Guide - Complete Steps

## Overview

This guide provides **everything** you need to implement Teams Single Sign-On (SSO) using **only Microsoft Agents SDK** - no deprecated Bot Framework SDK required.

### What You'll Achieve

**Current State**: Users must click "Sign in" and complete OAuth flow every time (10-15 seconds)

**After Implementation**:

- First time: One-click inline consent (2 seconds)
- Every subsequent time: Instant response (< 1 second, no sign-in!)

### Prerequisites

- ✅ Your bot deployed on Azure App Service (you have this)
- ✅ Microsoft Agents SDK installed (you have this)
- ✅ Azure Bot Service resource created (you have this)
- ✅ Microsoft Entra ID app registration (you have this: cc451968-4dc2-46f3-9b4f-f8eae2782b25)
- ✅ Admin access to Azure Portal

### Estimated Time

- **Code changes**: 5 minutes
- **Azure/Entra configuration**: 20 minutes
- **Teams app creation**: 10 minutes
- **Testing**: 10 minutes
- **Total**: ~45 minutes

---

## Quick Start Summary

```text
1. Update agent.py (add 2 code blocks)
2. Configure Entra ID (Application ID URI + scopes)
3. Update Azure Bot OAuth (enable token exchange)
4. Create Teams app manifest
5. Package and sideload to Teams
6. Test and verify SSO works
```

---

## PART 1: CODE CHANGES

### Step 1.1: Add Teams SSO Handler Import

**File**: `src/agent.py`

**Location**: After line 59 (after existing imports)

**Add this import**:

```python
# Existing imports (keep these - lines 48-59)
from microsoft_agents.hosting.core import (
    Authorization,
    TurnContext,
    MessageFactory,
    MemoryStorage,
    AgentApplication,
    TurnState,
)
from microsoft_agents.activity import activity, load_configuration_from_env, ActivityTypes, Activity
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager

# ADD THIS NEW IMPORT (after line 59):
from .teams_sso_handler import handle_teams_sso_token_exchange
```

### Step 1.2: Replace Invoke Handler

**File**: `src/agent.py`

**Location**: Lines 245-250

**Replace this code**:

```python
@AGENT_APP.activity(ActivityTypes.invoke)
async def invoke(context: TurnContext, state: TurnState) -> None:
    """
    Handle invoke activities.
    """
    await context.send_activity(MessageFactory.text("Invoke activity received in FastAPI server."))
```

**With this code**:

```python
@AGENT_APP.activity(ActivityTypes.invoke)
async def handle_invoke_activity(context: TurnContext, state: TurnState) -> None:
    """
    Handle invoke activities including Teams SSO token exchange.

    Supported invoke types:
    - signin/tokenExchange: Teams SSO token exchange (automatic sign-in)
    - Other: Generic invoke handling
    """

    activity_name = context.activity.name
    logger.info(f"Invoke activity received: {activity_name}")

    # Check if this is a Teams SSO token exchange request
    if activity_name == "signin/tokenExchange":
        # Use Microsoft Agents SDK to exchange Teams token for Graph/GitHub token
        await handle_teams_sso_token_exchange(context, state, AGENT_APP.auth)
    else:
        # Handle other invoke types
        await context.send_activity(
            MessageFactory.text(f"Invoke activity '{activity_name}' received")
        )
```

### Step 1.3: Verify teams_sso_handler.py Exists

**File**: `src/teams_sso_handler.py`

This file was already created for you. Verify it exists:

```bash
# Check file exists
ls src/teams_sso_handler.py
```

If it doesn't exist, you have the full implementation in your codebase already created.

### Step 1.4: Deploy Code Changes

```bash
# Option A: Git push (if using GitHub Actions)
git add src/agent.py src/teams_sso_handler.py
git commit -m "feat: Add Teams SSO support using Microsoft Agents SDK"
git push

# Option B: Direct Azure deployment
az webapp up --name app-fastapi-agent-1755331446 --resource-group rg-fastapi-agent

# Option C: Docker (if using containers)
docker build -t fastapibot:latest .
docker push <your-acr>.azurecr.io/fastapibot:latest
az webapp restart --name app-fastapi-agent-1755331446 --resource-group rg-fastapi-agent
```

---

## PART 2: MICROSOFT ENTRA ID (AZURE AD) CONFIGURATION

### Step 2.1: Navigate to Your App Registration

```text
1. Open Azure Portal: https://portal.azure.com
2. Search for "Microsoft Entra ID" (or "Azure Active Directory")
3. Click on it
4. In left menu, click "App registrations"
5. Find and click your bot's app: cc451968-4dc2-46f3-9b4f-f8eae2782b25
   (Search by Client ID or app name)
```

### Step 2.2: Configure Application ID URI

This URI identifies your bot to Teams for SSO.

```text
1. In your app registration, click "Expose an API" (left menu)

2. Click "Add" next to "Application ID URI" (at the top)

3. You'll see a pre-filled value like:
   api://cc451968-4dc2-46f3-9b4f-f8eae2782b25

4. CHANGE IT TO (add "botid-" prefix):
   api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25

5. Click "Save"
```

**Why this format?** Teams expects `api://botid-{AppId}` for bot SSO.

### Step 2.3: Add OAuth Scope

This scope allows Teams to request access on behalf of the user.

```text
1. Still in "Expose an API" section

2. Click "Add a scope" button

3. Fill in the form:

   Scope name: access_as_user

   Who can consent?: Admins and users

   Admin consent display name: Access bot as user

   Admin consent description:
   Allows Teams to call the bot's web APIs as the current user

   User consent display name: Access bot as you

   User consent description:
   Allows the bot to access Microsoft Graph on your behalf

   State: Enabled

4. Click "Add scope"

5. You should now see: api://botid-{AppId}/access_as_user
```

### Step 2.4: Authorize Teams Clients

Teams has two client applications (desktop/mobile and web) that need pre-authorization.

```text
1. Still in "Expose an API" section

2. Scroll down to "Authorized client applications"

3. Click "Add a client application"

4. Add Teams Desktop/Mobile client:
   Client ID: 1fec8e78-bce4-4aaf-ab1b-5451cc387264
   ✓ Check: api://botid-{YourAppId}/access_as_user
   Click "Add application"

5. Click "Add a client application" again

6. Add Teams Web client:
   Client ID: 5e3ce6c0-2b1f-4285-8d4b-75ee78787346
   ✓ Check: api://botid-{YourAppId}/access_as_user
   Click "Add application"

7. You should now see 2 authorized applications listed
```

**What this does**: Pre-authorizes Teams to request tokens without showing consent to users each time.

### Step 2.5: Verify API Permissions

Ensure your app has the correct Microsoft Graph permissions.

```text
1. Click "API permissions" (left menu)

2. You should see:
   - Microsoft Graph → User.Read (Delegated) → Granted for [Your Org]

3. If "Granted for [Your Org]" status is not there:
   Click "Grant admin consent for [Your Organization]"
   Click "Yes" to confirm

4. Status should change to green checkmark: "Granted for [Your Org]"
```

### Step 2.6: Verify Authentication Settings (Optional)

Check that your app accepts tokens correctly.

```text
1. Click "Authentication" (left menu)

2. Under "Platform configurations", you should see:
   - Web platform with redirect URIs including:
     https://token.botframework.com/.auth/web/redirect

3. Under "Supported account types":
   - Should be: "Accounts in this organizational directory only"
     OR "Accounts in any organizational directory"

4. Under "Implicit grant and hybrid flows":
   - NOT needed for bot SSO (can be unchecked)

5. No changes needed here, just verify it looks correct
```

---

## PART 3: AZURE BOT SERVICE CONFIGURATION

### Step 3.1: Navigate to Bot Resource

```text
1. Azure Portal → Search for "Bot Service" or your bot name
2. Click on your bot resource
3. In left menu, click "Configuration"
```

### Step 3.2: Enable Token Exchange for OAuth Connection

```text
1. Scroll down to "OAuth Connection Settings" section

2. Click on your "GRAPH" connection (or whatever you named it)

3. You'll see the OAuth connection configuration form

4. Scroll down and find "Token Exchange URL" field (it's a textbox)

5. In the "Token Exchange URL" textbox, enter:
   https://token.botframework.com/api/oauth/token

6. Verify other settings are correct:
   Service Provider: Azure Active Directory v2
   Client ID: cc451968-4dc2-46f3-9b4f-f8eae2782b25
   Client Secret: (your secret - hidden)
   Tenant ID: 2bab7b85-25a5-40d1-a83e-77d201b4da49
   Scopes: openid profile offline_access User.Read

7. Click "Save" at the bottom

8. Wait for "Successfully saved" message
```

**Critical**: The connection name in Azure ("GRAPH") must EXACTLY match your .env file:

```bash
AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=GRAPH
```

### Step 3.3: Verify Teams Channel is Enabled

```text
1. In your bot resource, click "Channels" (left menu)

2. You should see "Microsoft Teams" with status "Running"

3. If not enabled:
   - Click "Microsoft Teams" icon
   - Click "Apply"
   - Teams channel will be enabled
```

---

## PART 4: CREATE TEAMS APP MANIFEST

### Step 4.1: Create Directory Structure

```bash
# Create directory for Teams app
mkdir teams-app
cd teams-app
```

### Step 4.2: Create manifest.json

**File**: `teams-app/manifest.json`

**Content** (copy this exactly, it's ready to use):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
  "manifestVersion": "1.17",
  "version": "1.0.0",
  "id": "cc451968-4dc2-46f3-9b4f-f8eae2782b25",
  "packageName": "com.yourcompany.fastapibot",
  "developer": {
    "name": "Your Company Name",
    "websiteUrl": "https://yourcompany.com",
    "privacyUrl": "https://yourcompany.com/privacy",
    "termsOfUseUrl": "https://yourcompany.com/terms"
  },
  "icons": {
    "color": "color.png",
    "outline": "outline.png"
  },
  "name": {
    "short": "FastAPI Bot",
    "full": "FastAPI Auto Sign-In Agent with SSO"
  },
  "description": {
    "short": "Bot with Teams SSO",
    "full": "FastAPI bot demonstrating automatic sign-in using Teams SSO with Microsoft Agents SDK"
  },
  "accentColor": "#FFFFFF",
  "bots": [
    {
      "botId": "cc451968-4dc2-46f3-9b4f-f8eae2782b25",
      "scopes": ["personal"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["personal"],
          "commands": [
            {
              "title": "status",
              "description": "Check authentication status"
            },
            {
              "title": "me",
              "description": "Get your Microsoft Graph profile (with SSO!)"
            },
            {
              "title": "prs",
              "description": "Get GitHub pull requests"
            },
            {
              "title": "logout",
              "description": "Sign out from all services"
            },
            {
              "title": "test",
              "description": "Test OAuth configuration"
            }
          ]
        }
      ]
    }
  ],
  "permissions": [
    "identity",
    "messageTeamMembers"
  ],
  "validDomains": [
    "token.botframework.com"
  ],
  "webApplicationInfo": {
    "id": "cc451968-4dc2-46f3-9b4f-f8eae2782b25",
    "resource": "api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25"
  }
}
```

**Critical Fields Explained**:

- `id` and `botId`: Your bot's Azure AD App ID
- `webApplicationInfo.id`: Same App ID
- `webApplicationInfo.resource`: MUST match the Application ID URI from Step 2.2
- `validDomains`: Required for Bot Framework OAuth flows

**Customize** (optional):

- `packageName`: Use your company domain
- `developer.*`: Update with your company info
- `name.short`: Keep under 30 characters
- `description.short`: Keep under 80 characters

### Step 4.3: Create Icons

You need two icon files:

**color.png**:

- Size: 192x192 pixels
- Format: PNG with transparency
- Usage: Full color bot logo/avatar

**outline.png**:

- Size: 32x32 pixels
- Format: PNG with transparency
- Content: White outline icon on transparent background

**Quick icon creation options**:

```bash
# Option 1: Use online tools
# - https://favicon.io/ (convert text/emoji to icons)
# - https://www.canva.com/ (design custom icons)

# Option 2: Use placeholders for testing
# Download generic icons:
# - Search "bot icon png 192x192" for color.png
# - Search "bot icon outline 32x32" for outline.png

# Option 3: Use your company logo
# - Resize to 192x192 (color.png)
# - Create white outline version at 32x32 (outline.png)
```

Place both files in the `teams-app` directory:

```text
teams-app/
├── manifest.json
├── color.png (192x192)
└── outline.png (32x32)
```

---

## PART 5: PACKAGE AND DEPLOY TO TEAMS

### Step 5.1: Create Teams App Package

```bash
# Navigate to teams-app directory
cd teams-app

# Verify all files are present
ls
# Should see: manifest.json, color.png, outline.png

# Create ZIP package
# Windows PowerShell:
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath FastAPIBot.zip -Force

# Linux/Mac:
zip FastAPIBot.zip manifest.json color.png outline.png

# Verify ZIP was created
ls FastAPIBot.zip
```

**Important**: Files must be in the ROOT of the ZIP, not in a subfolder.

```text
✓ Correct:
  FastAPIBot.zip
  ├── manifest.json
  ├── color.png
  └── outline.png

✗ Wrong:
  FastAPIBot.zip
  └── teams-app/
      ├── manifest.json
      ├── color.png
      └── outline.png
```

### Step 5.2: Sideload App to Teams

**Option A: Via Teams Desktop/Web App**:

```text
1. Open Microsoft Teams (desktop or web app)

2. Click "Apps" in the left sidebar

3. At the bottom left, click "Manage your apps"

4. Click "Upload an app"

5. Select "Upload a custom app"

6. Browse and select FastAPIBot.zip

7. Click "Add" to install for yourself
   (Or "Add to a team" to install for a team)

8. The bot should now appear in your "Apps built for your org" section
```

**Option B: Via Teams Admin Center (for org-wide deployment)**:

```text
1. Go to https://admin.teams.microsoft.com

2. In left menu, expand "Teams apps" → click "Manage apps"

3. Click "Upload new app" (top right)

4. Upload FastAPIBot.zip

5. Review and approve the app

6. Set policies to make it available to users

7. Users can find it in Teams app store
```

### Step 5.3: Add Bot to Chat

```text
1. In Teams, go to "Chat"

2. Click "New chat" button

3. In the search bar, type "FastAPI Bot"

4. Select your bot from the results

5. A new chat window opens

6. You're ready to test!
```

---

## PART 6: TEST AND VERIFY

### Step 6.1: Test Basic Functionality

First, verify the bot works without SSO:

```text
In Teams chat with your bot, type:

/status

Expected response:
"Welcome to the FastAPI auto-signin demo
Graph status: Not connected
GitHub status: Not connected"
```

If this works, your bot is responding correctly. ✓

### Step 6.2: Test Teams SSO Flow (First Time)

Now test the SSO authentication:

```text
In Teams chat, type:

/me

Expected behavior (first time):
1. Consent dialog appears (inline in Teams):
   "FastAPI Bot wants to access your profile"
   [Continue] [Cancel]

2. Click "Continue"

3. Profile card appears within 1-2 seconds showing:
   - Your display name
   - Your email
   - Your job title
   - Profile picture

4. NO SIGN-IN CARD should appear
   (If you see a sign-in card, SSO is not working - see troubleshooting)
```

### Step 6.3: Test Subsequent Interactions

Test that tokens are cached:

```text
In Teams chat, type:

/me

Expected behavior (subsequent times):
- Profile appears INSTANTLY (< 1 second)
- NO consent dialog
- NO sign-in card
- Just your profile card
```

### Step 6.4: Verify Logs

Check Azure logs to confirm SSO token exchange:

```bash
# View live logs
az webapp log tail \
  --name app-fastapi-agent-1755331446 \
  --resource-group rg-fastapi-agent

# Or view in Azure Portal:
# 1. Go to your App Service
# 2. Left menu → Monitoring → Log stream
# 3. Watch for log messages
```

**Look for these log messages** when you type `/me`:

```text
✅ "Invoke activity received: signin/tokenExchange"
✅ "=== Teams SSO Token Exchange ==="
✅ "Request ID: abc-123-..."
✅ "Connection Name: GRAPH"
✅ "Token received: True"
✅ "✅ Token exchange successful!"
✅ "Token stored for connection: GRAPH"
✅ "Success response sent to Teams"
```

**If you see errors**:

```text
❌ "❌ Token exchange failed - no token returned"
❌ "Invalid token exchange request format"
```

See troubleshooting section below.

### Step 6.5: Test Across Sessions

```text
1. Close Teams completely (or use different device)

2. Open Teams again

3. Navigate to your bot chat

4. Type: /me

5. Expected: Profile still appears instantly (token persisted)
```

---

## PART 7: TROUBLESHOOTING

### Issue 1: No SSO - Still See Sign-In Card

**Symptoms**: When typing `/me`, you see the old OAuth sign-in card instead of instant profile.

**Possible Causes & Fixes**:

```text
A. Token exchange not enabled in Azure Bot

Fix:
→ Go to Part 3, Step 3.2
→ Verify "Token Exchange URL" is checked and set to:
  https://token.botframework.com/api/oauth/token
→ Save changes

B. webApplicationInfo missing from manifest

Fix:
→ Open teams-app/manifest.json
→ Verify "webApplicationInfo" section exists:
  {
    "id": "cc451968-4dc2-46f3-9b4f-f8eae2782b25",
    "resource": "api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25"
  }
→ Repackage ZIP and redeploy

C. Application ID URI not configured

Fix:
→ Go to Part 2, Step 2.2
→ Verify Entra ID app has Application ID URI:
  api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25
```

### Issue 2: "SSO is not enabled for bot on Teams channel"

**Symptoms**: Error message shown in Teams.

**Causes & Fixes**:

```text
A. Wrong resource format in manifest

Fix:
→ manifest.json → webApplicationInfo.resource must be:
  api://botid-{AppId}
  NOT: api://{AppId}
  NOT: https://...

B. validDomains missing

Fix:
→ manifest.json → add:
  "validDomains": ["token.botframework.com"]
```

### Issue 3: Token Exchange Fails in Logs

**Symptoms**: Logs show "Token exchange returned no token"

**Causes & Fixes**:

```text
A. Connection name mismatch

Check:
→ .env file: AGENTAPPLICATION__...CONNECTIONNAME=GRAPH
→ Azure Bot OAuth connection name: GRAPH
→ Both must match EXACTLY (case-sensitive)

B. OAuth connection not configured for token exchange

Fix:
→ Part 3, Step 3.2 - set Token Exchange URL

C. Invalid scopes

Fix:
→ Azure Bot OAuth connection must have scopes:
  openid profile offline_access User.Read
```

### Issue 4: Consent Dialog Appears Every Time

**Symptoms**: First-time consent keeps appearing on every `/me` command.

**Causes & Fixes**:

```text
A. Admin consent not granted

Fix:
→ Go to Part 2, Step 2.5
→ Grant admin consent for your organization

B. Token not being stored

Fix:
→ Check STORAGE in agent.py is configured
→ Currently using MemoryStorage (loses tokens on restart)
→ Consider implementing persistent storage (see bonus section)
```

### Issue 5: Bot Not Responding at All

**Symptoms**: No response to any commands in Teams.

**Causes & Fixes**:

```text
A. Code not deployed

Fix:
→ Verify Step 1.4 was completed
→ Check Azure App Service is running:
  az webapp show --name app-fastapi-agent-1755331446 --query state

B. Teams channel not enabled

Fix:
→ Part 3, Step 3.3 - enable Teams channel

C. Bot endpoint incorrect

Fix:
→ Azure Bot → Configuration → Messaging endpoint should be:
  https://app-fastapi-agent-1755331446.azurewebsites.net/api/messages
```

### Debugging Checklist

Use this checklist to diagnose issues:

```text
Code Deployment:
□ teams_sso_handler.py exists in src/
□ agent.py updated with new import
□ agent.py invoke handler replaced
□ Code deployed to Azure
□ App Service is running

Entra ID Configuration:
□ Application ID URI set: api://botid-{AppId}
□ Scope created: access_as_user
□ Teams clients authorized (2 client IDs)
□ Admin consent granted (green checkmark)

Azure Bot Service:
□ OAuth connection exists (GRAPH)
□ Token Exchange URL is set
□ Connection name matches .env
□ Teams channel enabled

Teams App:
□ manifest.json has webApplicationInfo
□ resource matches Application ID URI
□ validDomains includes token.botframework.com
□ ZIP file created correctly (files in root)
□ App uploaded to Teams

Testing:
□ /status command works
□ Logs show "signin/tokenExchange" invoke
□ Logs show "✅ Token exchange successful!"
□ /me returns profile without sign-in card
```

---

## PART 8: VERIFICATION & SUCCESS CRITERIA

### How to Confirm SSO is Working

✅ **SSO is working correctly if**:

1. First `/me` command shows ONE-CLICK consent (not full OAuth flow)
2. Subsequent `/me` commands show profile INSTANTLY
3. NO sign-in card appears
4. Logs show: "✅ Token exchange successful!"
5. Works across Teams sessions (close/reopen Teams)
6. Works on mobile Teams app too

❌ **SSO is NOT working if**:

1. You see the old sign-in card (blue button)
2. Browser window opens for OAuth
3. Consent appears every time you run `/me`
4. Logs show: "❌ Token exchange failed"

### Before vs After Comparison

**Before (Standard OAuth)**:

```text
User: /me
Bot: [Shows sign-in card with blue button]
User: [Clicks sign-in button]
Browser: [Opens OAuth consent page]
User: [Enters credentials, grants consent]
Browser: [Redirects back to Teams]
Bot: [Shows profile]
Time: 10-15 seconds
```

**After (Teams SSO)**:

```text
First time:
User: /me
Teams: [Shows inline consent - one click]
User: [Clicks Continue]
Bot: [Shows profile]
Time: 2 seconds

Every subsequent time:
User: /me
Bot: [Shows profile instantly]
Time: < 1 second
```

---

## PART 9: NEXT STEPS & OPTIMIZATION

### Optional Enhancements

#### A. Add Persistent Token Storage

Currently using `MemoryStorage` which loses tokens on restart. Upgrade to persistent storage:

```python
# src/agent.py - Replace MemoryStorage with BlobStorage

from microsoft_agents.hosting.core import BlobStorage
from os import environ

STORAGE = BlobStorage(
    container_name="bot-state",
    account_name=environ.get("AZURE_STORAGE_ACCOUNT"),
    account_key=environ.get("AZURE_STORAGE_KEY")
)
```

Benefits:

- Tokens survive bot restarts
- Users never need to re-authenticate (until token expires ~90 days)

#### B. Deploy Org-Wide

After successful testing:

```text
1. Teams Admin Center → Manage apps → Upload FastAPIBot.zip
2. Set policies to make available to all users
3. Users find it in Teams app store
4. No individual sideloading needed
```

#### C. Add GitHub SSO

Enable SSO for GitHub too:

```text
1. Follow same steps for GITHUB OAuth connection
2. Update manifest.json to request GitHub scopes
3. Test /prs command with SSO
```

### Monitoring & Analytics

Track SSO success rate:

```python
# Add telemetry to teams_sso_handler.py

# Log successful exchanges
logger.info(f"SSO_SUCCESS user={context.activity.from_property.id}")

# Log failures
logger.error(f"SSO_FAILED user={context.activity.from_property.id} error={error}")

# Analyze logs to calculate:
# - SSO success rate
# - Most common errors
# - User adoption
```

---

## PART 10: ROLLOUT STRATEGY

### Phase 1: Personal Testing (Week 1)

```text
✓ Sideload app to yourself
✓ Test all commands
✓ Verify SSO works end-to-end
✓ Check logs for errors
✓ Document any issues
```

### Phase 2: Pilot Group (Week 2)

```text
✓ Sideload to 5-10 pilot users
✓ Gather feedback on SSO experience
✓ Monitor logs for errors
✓ Fix any issues discovered
✓ Measure sign-in time improvements
```

### Phase 3: Team Deployment (Week 3)

```text
✓ Submit to Teams Admin Center
✓ Admin reviews and approves
✓ Deploy to specific departments
✓ Provide user documentation
✓ Monitor adoption and feedback
```

### Phase 4: Organization-Wide (Week 4+)

```text
✓ Make available in Teams app store
✓ Announce via company channels
✓ Track usage metrics
✓ Provide ongoing support
✓ Iterate based on feedback
```

---

## SUMMARY

### What We Accomplished

✅ **Code**: Updated agent.py to handle Teams SSO token exchange

✅ **Entra ID**: Configured Application ID URI, scopes, and authorized Teams clients

✅ **Azure Bot**: Enabled token exchange for OAuth connections

✅ **Teams App**: Created manifest with SSO configuration

✅ **Deployment**: Packaged and sideloaded to Teams for testing

### Key Takeaways

1. **Microsoft Agents SDK has everything** - No Bot Framework SDK v4 needed
2. **Token exchange is automatic** - `AGENT_APP.auth.exchange_token()` handles it
3. **Configuration is critical** - All IDs, URIs, and names must match exactly
4. **SSO eliminates friction** - From 10-15 seconds to < 1 second

### Files Created

- `src/teams_sso_handler.py` - Token exchange logic
- `teams-app/manifest.json` - Teams app configuration
- `teams-app/FastAPIBot.zip` - Deployable Teams app package

### Files Modified

- `src/agent.py` - Added SSO invoke handler

### Azure Resources Configured

- Microsoft Entra ID App Registration
- Azure Bot Service OAuth Connection
- Teams Channel

---

## APPENDIX: QUICK REFERENCE

### Your Bot Details

```text
Bot Name: FastAPI Auto Sign-In Agent
App ID: cc451968-4dc2-46f3-9b4f-f8eae2782b25
Tenant ID: 2bab7b85-25a5-40d1-a83e-77d201b4da49
Application ID URI: api://botid-cc451968-4dc2-46f3-9b4f-f8eae2782b25
Messaging Endpoint: https://app-fastapi-agent-1755331446.azurewebsites.net/api/messages
OAuth Connection Name: GRAPH
```

### Teams Client IDs

```text
Teams Desktop/Mobile: 1fec8e78-bce4-4aaf-ab1b-5451cc387264
Teams Web: 5e3ce6c0-2b1f-4285-8d4b-75ee78787346
```

### Important URLs

```text
Azure Portal: https://portal.azure.com
Entra ID: https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade
Teams Admin: https://admin.teams.microsoft.com
Bot Service: https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/Microsoft.BotService%2FbotServices
```

### Test Commands

```text
/status - Check authentication status
/test - Show OAuth configuration
/me - Get Microsoft Graph profile (tests SSO)
/prs - Get GitHub pull requests
/logout - Sign out from all services
```

---

**Total Implementation Time**: ~45 minutes

**Result**: Zero-friction authentication in Teams! 🎉

---

**Need help?** Review the troubleshooting section or check Azure logs for error messages.
