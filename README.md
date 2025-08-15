# Auto Sign-In Sample - FastAPI Version

This Agent has been created using [Microsoft 365 Agents SDK](https://github.com/microsoft/agents-for-python) with FastAPI instead of aiohttp, showing how to use Auto SignIn user authorization in your Agent with a modern FastAPI web framework.

This sample demonstrates the same functionality as the original auto-signin sample but uses FastAPI for better performance, automatic API documentation, and enhanced developer experience.

## Key Features

- **FastAPI Integration**: Modern Python web framework with automatic API documentation
- **Authentication Handlers**: Support for Microsoft Graph and GitHub OAuth
- **Health Check Endpoints**: Built-in health monitoring endpoints
- **Enhanced Error Handling**: Improved error responses and logging
- **Type Safety**: Better type hints and validation

## API Endpoints

The FastAPI implementation provides additional endpoints:

- `POST /api/messages` - Main bot framework message endpoint
- `GET /` - Root endpoint for basic status
- `GET /health` - Health check endpoint
- `GET /docs` - Automatic API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## Agent Commands

This sample uses different routes configured with auth handlers:

```python
@AGENT_APP.message("/status")
@AGENT_APP.message("/logout") 
@AGENT_APP.message("/me", auth_handlers=["GRAPH"])
@AGENT_APP.message("/prs", auth_handlers=["GITHUB"])
```

### Available Commands

- `/status` or `/auth status` - Check authentication status for all handlers
- `/logout` - Sign out from all authentication handlers
- `/me` or `/profile` - Get user profile from Microsoft Graph (requires GRAPH auth)
- `/prs` or `/pull requests` - Get GitHub profile and pull requests (requires GITHUB auth)

## Prerequisites

- [Python](https://www.python.org/) version 3.9 or higher
- [dev tunnel](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started?tabs=windows) (for local development)

## Local Setup

### Configure Azure Bot Service

1. [Create an Azure Bot](https://aka.ms/AgentsSDK-CreateBot)
   - Record the Application ID, the Tenant ID, and the Client Secret for use below

2. Configuring the token connection in the Agent settings
   1. Open the `env.TEMPLATE` file in the root of the sample project, rename it to `.env` and configure the following values:
      1. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID** to the AppId of the bot identity
      2. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET** to the Secret that was created for your identity
      3. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID** to the Tenant Id where your application is registered

3. [Add OAuth to your bot](https://aka.ms/AgentsSDK-AddAuth) using the _Azure Active Directory v2_ Provider

4. Create a second Azure Bot **OAuth Connection** using the _GitHub_ provider
   
   > To configure OAuth for GitHub you need a GitHub account, under settings/developer settings/OAuth apps, create a new OAuth app, and set the callback URL to `https://token.botframework.com/.auth/web/redirect`. Then provide the clientId and clientSecret, and required scopes: `user repo`

5. Configure the authorization handlers in the `.env` file:
   ```env
   AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=your-graph-connection-name
   AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GITHUB__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=your-github-connection-name
   ```

6. Run `dev tunnels`. See [Create and host a dev tunnel](https://learn.microsoft.com/azure/developer/dev-tunnels/get-started?tabs=windows):
   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

7. Take note of the URL shown after `Connect via browser:`

8. On the Azure Bot, select **Settings**, then **Configuration**, and update the **Messaging endpoint** to `{tunnel-url}/api/messages`

### Running the Agent

1. Open this folder from your IDE or Terminal
2. (Optional but recommended) Set up virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux  
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI application:
   ```bash
   python -m src.main
   ```
   
   Or alternatively, you can use uvicorn directly:
   ```bash
   uvicorn src.main:app --host localhost --port 3978 --reload
   ```

At this point you should see the message:
```text
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:3978 (Press CTRL+C to quit)
```

The agent is ready to accept messages.

## FastAPI Specific Features

### Automatic API Documentation

Once the server is running, you can access:

- **Swagger UI**: `http://localhost:3978/docs`
- **ReDoc**: `http://localhost:3978/redoc`

These provide interactive API documentation automatically generated from your FastAPI application.

### Health Monitoring

- **Root Endpoint**: `GET http://localhost:3978/` - Basic status check
- **Health Check**: `GET http://localhost:3978/health` - Detailed health information

### Enhanced Error Handling

The FastAPI version includes improved error handling with:
- Structured error responses
- Better logging of exceptions
- HTTP status codes that follow REST conventions

## Accessing the Agent

### Using the Agent in WebChat

1. Go to your Azure Bot Service resource in the Azure Portal and select **Test in WebChat**
2. When the conversation starts, you will be greeted with a welcome message
3. Send `/status` to check authentication status
4. Send `/me` to trigger the Microsoft Graph OAuth flow and display your profile
5. Send `/prs` to trigger the GitHub OAuth flow and display pull requests

### Development and Testing

For local development, you can also test the endpoints directly:

```bash
# Check health
curl http://localhost:3978/health

# View API documentation
# Open http://localhost:3978/docs in your browser
```

## Differences from Original Implementation

### 1. **Web Framework**: 
   - **Original**: aiohttp
   - **FastAPI**: FastAPI with uvicorn

### 2. **Server Startup**:
   - **Original**: `run_app()` from aiohttp
   - **FastAPI**: `uvicorn.run()` with FastAPI app

### 3. **Middleware**:
   - **Original**: aiohttp middleware
   - **FastAPI**: FastAPI middleware decorators

### 4. **Error Handling**:
   - **Original**: Basic exception handling
   - **FastAPI**: HTTP exceptions with proper status codes

### 5. **Additional Features**:
   - Automatic API documentation
   - Health check endpoints
   - Better type hints and validation
   - Enhanced logging and error messages

## Troubleshooting

1. **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
2. **Port Conflicts**: Change the PORT environment variable if 3978 is in use
3. **Authentication Issues**: Verify your `.env` file has the correct OAuth connection names
4. **Dev Tunnel**: Make sure your dev tunnel is running and the messaging endpoint is correctly configured

## Next Steps

- Explore the automatic API documentation at `/docs`
- Add custom FastAPI endpoints for additional functionality  
- Implement request/response models using Pydantic
- Add FastAPI dependencies for dependency injection
- Configure CORS if needed for web client integration
