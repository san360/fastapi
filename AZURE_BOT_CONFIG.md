# Azure Bot Configuration Guide

## 📋 Quick Setup Checklist

### 1. Messaging Endpoint Configuration

**Location:** Azure Portal → Your Bot Resource → Configuration → Messaging endpoint

**Value depends on your environment:**

**For Local Development (DevTunnel):**
```
https://[your-devtunnel-url].devtunnels.ms/api/messages
```

**For Production (Azure App Service):**
```
https://[your-app-name].azurewebsites.net/api/messages
```

**Steps:**
1. Determine your environment (local dev with DevTunnel or production Azure)
2. Get your endpoint URL:
   - **DevTunnel**: Start DevTunnel locally and copy URL from terminal output
   - **Azure**: Use your App Service URL (e.g., `https://app-fastapi-agent-1755331446.azurewebsites.net`)
3. Go to Azure Portal → Bot Resource → Configuration
4. Update **Messaging endpoint** with the appropriate URL + `/api/messages`
5. Click **Apply**

**Important:**
- ✅ Must use HTTPS (both DevTunnel and Azure provide this)
- ✅ Must end with `/api/messages`
- ✅ No port number needed in the URL
- ✅ **Always update this when switching between local dev and production**
- ✅ Production endpoint remains constant once deployed
- ✅ DevTunnel URL changes each time you restart the tunnel (use persistent tunnels)
- ❌ Don't use localhost URLs (not publicly accessible)

---

### 2. Create Azure AD App Registration (Required for OAuth)

Before configuring OAuth connections, you need to create an Azure AD App Registration:

**Steps:**

1. **Go to Azure Portal** → **Azure Active Directory** → **App registrations** → **+ New registration**

2. **Register an application:**
   - **Name**: `[Your Bot Name] - Graph API`
   - **Supported account types**: 
     - Select `Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts`
   - **Redirect URI**: 
     - Platform: `Web`
     - URI: `https://token.botframework.com/.auth/web/redirect`
   - Click **Register**

3. **Configure API Permissions:**
   - Go to **API permissions** → **+ Add a permission**
   - Select **Microsoft Graph** → **Delegated permissions**
   - Add these permissions:
     - ✅ `User.Read`
     - ✅ `openid`
     - ✅ `offline_access`
     - ✅ `profile`
   - Click **Add permissions**
   - Optionally: Click **Grant admin consent** (if you have admin rights)

4. **Create Client Secret:**
   - Go to **Certificates & secrets** → **Client secrets** → **+ New client secret**
   - **Description**: `Bot OAuth Secret`
   - **Expires**: Choose expiration period (recommended: 24 months)
   - Click **Add**
   - **⚠️ Copy the secret value immediately** - you won't be able to see it again!

5. **Note these values** (you'll need them for OAuth configuration):
   - **Application (client) ID** - from the Overview page
   - **Directory (tenant) ID** - from the Overview page
   - **Client secret value** - the value you just copied

**Important:**
- ⚠️ Keep the Client Secret secure and never commit it to version control
- ⚠️ Add it to your `.env` file (which should be in `.gitignore`)
- ⚠️ The redirect URI must be exactly: `https://token.botframework.com/.auth/web/redirect`
- ⚠️ Client secrets expire - set a reminder to renew before expiration

---

### 3. OAuth Connection: GRAPH (Microsoft User Profile)

**Purpose:** Enables `/me` command to fetch user profile from Microsoft Graph

**Location:** Azure Portal → Bot Resource → Configuration → OAuth Connection Settings → + New Connection Setting

**Configuration:**

| Field | Value |
|-------|-------|
| **Name** | `GRAPH` (case-sensitive, must match .env) |
| **Service Provider** | `Azure Active Directory v2` |
| **Client ID** | `[Your Azure AD App Registration Client ID]` |
| **Client Secret** | `[Your Azure AD App Registration Client Secret]` |
| **Token Exchange URL** | [Leave empty or as configured] |
| **Tenant ID** | `[Your Azure AD Tenant ID]` |
| **Scopes** | `openid profile offline_access User.Read` |

**Steps:**
1. Click **+ New Connection Setting**
2. Fill in all fields as shown above
3. Click **Save**
4. Click **Test Connection** to verify
5. Ensure connection status shows as working

**Critical Notes:**
- ⚠️ Connection name `GRAPH` must EXACTLY match your `.env` file
- ⚠️ Use your own Azure AD Tenant ID (find it in Azure AD overview)
- ⚠️ Use your own Client ID from Azure AD App Registration
- ⚠️ Case-sensitive: `GRAPH` ≠ `graph`
- ⚠️ Keep Client Secret secure and never commit to version control

**In your .env file, ensure:**
```bash
CONNECTIONS__SERVICE_CONNECTION__NAME=GRAPH
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=[Your-Azure-AD-Client-ID]
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=[Your-Client-Secret]
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SCOPES=openid,profile,offline_access,User.Read
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=[Your-Tenant-ID]
```

---

### 4. Create GitHub OAuth App (Required for GitHub Integration)

Before configuring GitHub OAuth connection, you need to create a GitHub OAuth App:

**Steps:**

1. **Go to GitHub** → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**

2. **Register a new OAuth application:**
   - **Application name**: `[Your Bot Name] - GitHub Integration`
   - **Homepage URL**: `https://[your-bot].azurewebsites.net` (or your bot's public URL)
   - **Application description**: (optional) `Bot Framework integration for pull requests`
   - **Authorization callback URL**: `https://token.botframework.com/.auth/web/redirect`
   - Click **Register application**

3. **Get Client Credentials:**
   - **Client ID** is displayed on the app page
   - Click **Generate a new client secret**
   - **⚠️ Copy the client secret immediately** - you won't be able to see it again!

4. **Note these values** (you'll need them for OAuth configuration):
   - **Client ID** - from the app page
   - **Client secret** - the value you just generated

**Important:**
- ⚠️ The callback URL must be exactly: `https://token.botframework.com/.auth/web/redirect`
- ⚠️ Keep the Client Secret secure and never commit it to version control
- ⚠️ Client secrets don't expire on GitHub, but you can regenerate them if compromised

---

### 5. OAuth Connection: GITHUB (GitHub Pull Requests)

**Purpose:** Enables `/prs` command to fetch GitHub pull requests

**Location:** Azure Portal → Bot Resource → Configuration → OAuth Connection Settings → + New Connection Setting

**Configuration:**

| Field | Value |
|-------|-------|
| **Name** | `GITHUB` (case-sensitive, must match .env) |
| **Service Provider** | `GitHub` |
| **Client ID** | [Your GitHub OAuth App Client ID] |
| **Client Secret** | [Your GitHub OAuth App Client Secret] |
| **Scopes** | `repo user` |

**Steps:**
1. Click **+ New Connection Setting**
2. Fill in all fields as shown above
3. Click **Save**
4. Click **Test Connection** to verify

**Critical Notes:**
- ⚠️ Connection name `GITHUB` must EXACTLY match your `.env` file
- ⚠️ Case-sensitive: `GITHUB` ≠ `github`
- ⚠️ Callback URL must be Bot Framework's redirect URL

**In your .env file, ensure:**
```bash
CONNECTIONS__GITHUB_CONNECTION__NAME=GITHUB
CONNECTIONS__GITHUB_CONNECTION__SETTINGS__SCOPES=repo,user
```

---

## 🔍 Verification Steps

### 1. Test Messaging Endpoint
- Send a message to your bot in Test in Web Chat (Azure Portal)
- Check DevTunnel terminal for incoming requests
- Check FastAPI logs for message processing

### 2. Test OAuth Connections

**In your bot chat, type:**
```
/test    # Shows OAuth configuration summary
/debug   # Shows detailed connection information
```

**Expected output:**
- Connection names: GRAPH, GITHUB
- Client IDs displayed
- Scopes listed

### 3. Test User Profile (GRAPH)
**In your bot chat, type:**
```
/me
```

**Expected flow:**
1. Bot shows sign-in card
2. Click "Sign In" button
3. Microsoft login page appears
4. After sign-in, bot displays your profile (name, email, etc.)

**If you see an empty page:**
- ✅ Check connection name is exactly `GRAPH` in Azure
- ✅ Verify `.env` has `CONNECTIONS__SERVICE_CONNECTION__NAME=GRAPH`
- ✅ Run `/debug` command to see connection details
- ✅ Test connection in Azure Portal

### 4. Test GitHub Pull Requests (GITHUB)
**In your bot chat, type:**
```
/prs
```

**Expected flow:**
1. Bot shows sign-in card
2. Click "Sign In" button
3. GitHub authorization page appears
4. After authorization, bot displays your open pull requests

---

## 🚨 Troubleshooting

### Issue: Empty Sign-In Page

**Most common cause:** Connection name mismatch

**Solution:**
1. Run `/debug` in bot chat to see configured connection names
2. Check Azure Bot OAuth Connection Settings names
3. Ensure names match exactly (case-sensitive)
4. Restart bot after changing configuration

### Issue: "The bot encountered an error or bug"

**Possible causes:**
- Messaging endpoint not configured correctly
- Bot application not running
- DevTunnel not running
- Port mismatch

**Solution:**
1. Check DevTunnel is running: `devtunnel show fastapi-bot`
2. Verify FastAPI is running on localhost:3978
3. Check messaging endpoint in Azure matches DevTunnel URL
4. Check bot logs for detailed error messages

### Issue: OAuth Sign-In Times Out

**Possible causes:**
- Client ID/Secret incorrect
- Tenant ID mismatch (for GRAPH)
- Scopes not configured correctly

**Solution:**
1. Click "Test Connection" in Azure Portal
2. Verify Client ID matches App Registration
3. Check Client Secret hasn't expired
4. Ensure scopes in Azure match `.env` file

### Issue: "Cannot read token"

**Possible causes:**
- Connection not authorized yet
- Token expired
- User hasn't signed in

**Solution:**
1. User must complete sign-in flow first
2. After sign-in, retry the command
3. Check token expiration (tokens expire after some time)

---

## 📝 Configuration File Reference

### .env File Example

```bash
# Bot Framework Configuration
BOT_ID=[Your Azure Bot Client ID]
BOT_PASSWORD=[Your Azure Bot Client Secret/Password]

# Microsoft Graph Connection
CONNECTIONS__SERVICE_CONNECTION__NAME=GRAPH
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=[Your-Azure-AD-Client-ID]
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=[Your-Azure-AD-Client-Secret]
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__SCOPES=openid,profile,offline_access,User.Read
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=[Your-Azure-AD-Tenant-ID]

# GitHub Connection
CONNECTIONS__GITHUB_CONNECTION__NAME=GITHUB
CONNECTIONS__GITHUB_CONNECTION__SETTINGS__SCOPES=repo,user

# Logging (Development only)
LOG_JWT_TOKENS=false  # Set to true only for debugging, NEVER in production
```

### Azure Bot Configuration Summary

**Messaging endpoint:**

Local Development:
```
https://[your-devtunnel-url].devtunnels.ms/api/messages
```

Production:
```
https://[your-app-name].azurewebsites.net/api/messages
```

**OAuth Connections:**
- `GRAPH` → Azure AD v2 → User profile access
- `GITHUB` → GitHub → Repository and PR access

---

## 🎯 Quick Start Commands

### Start Development Environment

**Terminal 1: DevTunnel**
```bash
# Windows PowerShell
.\start-devtunnel.ps1

# macOS/Linux
./start-devtunnel.sh
```

**Terminal 2: Already handled by scripts above**
```bash
# Or manually:
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows
python main.py
```

### Bot Commands

```
/me      # Show my Microsoft profile
/prs     # Show my GitHub pull requests
/test    # Show OAuth configuration
/debug   # Show detailed connection info
```

---

## 📚 Additional Resources

- [DevTunnel Documentation](https://learn.microsoft.com/azure/developer/dev-tunnels/)
- [Bot Framework OAuth](https://learn.microsoft.com/azure/bot-service/bot-builder-authentication)
- [Microsoft Graph API](https://learn.microsoft.com/graph/)
- [GitHub OAuth Apps](https://docs.github.com/apps/oauth-apps)

---

## ✅ Final Checklist

Before testing your bot, ensure:

- [ ] DevTunnel is installed and running
- [ ] FastAPI application is running on localhost:3978
- [ ] Messaging endpoint in Azure points to DevTunnel URL + `/api/messages`
- [ ] GRAPH OAuth connection configured with correct Client ID
- [ ] GRAPH OAuth connection name matches `.env` exactly
- [ ] GITHUB OAuth connection configured (if using GitHub features)
- [ ] GITHUB OAuth connection name matches `.env` exactly
- [ ] All Client IDs and Secrets are correct and not expired
- [ ] Tenant ID in Azure matches your Azure AD tenant
- [ ] Connection names are case-sensitive and exact matches
- [ ] "Test Connection" passes for all OAuth connections in Azure Portal
- [ ] `.env` file has all required environment variables
- [ ] `LOG_JWT_TOKENS` is set to `false` (or removed) for production

🎉 **You're ready to test your bot!**
