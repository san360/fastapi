# OpenAI Integration with Streaming for Microsoft Teams Bot

Complete guide for the OpenAI-powered Teams bot with configurable streaming capabilities.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Configuration](#configuration)
5. [Streaming Modes](#streaming-modes)
6. [Usage Examples](#usage-examples)
7. [System Prompts](#system-prompts)
8. [Troubleshooting](#troubleshooting)
9. [Architecture](#architecture)
10. [Cost Management](#cost-management)

---

## Overview

This implementation adds Azure OpenAI (GPT-4o) integration to your Microsoft Teams bot with **fully configurable streaming** via environment variables. Users can see AI responses appearing in real-time or with interactive progress indicators.

### Key Features

- ✅ **Azure OpenAI GPT-4o** - Intelligent, context-aware responses
- ✅ **Configurable Streaming** - Choose from 3 streaming modes via `.env`
- ✅ **Smart Progress Indicators** - Category-aware messages when not streaming
- ✅ **Multi-turn Conversations** - Maintains conversation history
- ✅ **8 Query Categories** - Auto-adapts system prompts (technical, creative, code, etc.)
- ✅ **Token Usage Tracking** - Monitor costs per request
- ✅ **Error Handling** - Automatic retries and user-friendly errors
- ✅ **Adaptive Cards** - Rich formatting for longer responses

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Azure OpenAI

1. Create **Azure OpenAI resource** in [Azure Portal](https://portal.azure.com)
2. Deploy **gpt-4o** or **gpt-4o-mini** model
3. Copy API key and endpoint

### 3. Configure Environment

Copy `.env.example` to `.env` and add your credentials:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Streaming (enabled by default)
OPENAI_ENABLE_STREAMING=true
OPENAI_STREAMING_MODE=chunked
```

### 4. Run the Bot

```bash
python -m src.server
```

### 5. Test in Teams

```
You: Explain how neural networks work
Bot: 🤔 Analyzing your question...
Bot: Neural networks are computational models...
Bot: [more chunks appearing progressively]
Bot: ✅ Complete - 1,234 tokens (~$0.0185)
```

---

## Features

### Streaming Modes

The bot supports 3 distinct streaming experiences:

#### 1. Chunked Streaming (Default - Recommended)

**Configuration:**
```bash
OPENAI_ENABLE_STREAMING=true
OPENAI_STREAMING_MODE=chunked
OPENAI_STREAMING_CHUNK_SIZE=150
```

**User Experience:**
- Response appears in ~150 character chunks
- Natural sentence breaks
- Smooth, engaging flow
- **5-7 messages** for 500-word response

**Best for:** General use, balanced experience

#### 2. Sentence Streaming (Cleaner)

**Configuration:**
```bash
OPENAI_ENABLE_STREAMING=true
OPENAI_STREAMING_MODE=sentence
```

**User Experience:**
- Complete sentences only
- More deliberate pace
- Clean message history
- **10-12 messages** for 500-word response

**Best for:** Professional/formal environments

#### 3. Non-Streaming with Progress Updates (Single Message)

**Configuration:**
```bash
OPENAI_ENABLE_STREAMING=false
OPENAI_SHOW_PROGRESS_MESSAGES=true
OPENAI_USE_MESSAGE_UPDATES=true
```

**User Experience:**
- Single message that updates in place
- Category-aware progress indicators
- Complete response at end
- **2 messages total** (progress + final)

**Progress Example:**
```
You: Write a creative story
Bot: 🎨 Generating creative ideas...
     ↓ (updates every 3 seconds)
Bot: ✨ Crafting unique content...
     ↓
Bot: 🌟 Refining the narrative...
     ↓
Bot: 📖 Polishing the final draft...
     ↓ (progress deleted)
Bot: [Complete story with Adaptive Card]
```

**Best for:** Clean chat history, minimal messages

### Category-Aware Progress Messages

When non-streaming mode is enabled, progress messages adapt to query type:

| Category | Progress Messages |
|----------|------------------|
| **General** | "💭 Thinking deeply...", "🔍 Analyzing details..." |
| **Technical** | "⚙️ Processing technical details...", "📊 Gathering best practices..." |
| **Code** | "💻 Writing code...", "🔨 Optimizing implementation..." |
| **Creative** | "🎨 Generating ideas...", "✨ Crafting content..." |
| **Data Analysis** | "📊 Analyzing patterns...", "📈 Computing statistics..." |
| **Business** | "📈 Analyzing context...", "🎯 Developing strategy..." |
| **Learning** | "📚 Preparing content...", "💡 Creating examples..." |
| **Summarization** | "📝 Reading content...", "🔍 Extracting key points..." |

---

## Configuration

### All Environment Variables

```bash
# ===== Azure OpenAI Configuration (Required) =====
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21

# ===== OpenAI Settings (Optional) =====
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=30
OPENAI_MAX_RETRIES=3
OPENAI_MAX_HISTORY_MESSAGES=10

# ===== Streaming Settings (Optional) =====
# Master toggle
OPENAI_ENABLE_STREAMING=true

# Streaming mode settings (when enabled)
OPENAI_STREAMING_MODE=chunked
OPENAI_STREAMING_CHUNK_SIZE=150
OPENAI_STREAMING_DELAY=0.3

# Non-streaming mode settings (when disabled)
OPENAI_SHOW_PROGRESS_MESSAGES=true
OPENAI_PROGRESS_UPDATE_INTERVAL=3
OPENAI_USE_MESSAGE_UPDATES=true
```

### Quick Configuration Examples

#### Configuration 1: Default (Recommended)
```bash
OPENAI_ENABLE_STREAMING=true
OPENAI_STREAMING_MODE=chunked
OPENAI_STREAMING_CHUNK_SIZE=150
OPENAI_STREAMING_DELAY=0.3
```
**Result:** Smooth streaming, balanced experience

#### Configuration 2: Professional/Formal
```bash
OPENAI_ENABLE_STREAMING=false
OPENAI_SHOW_PROGRESS_MESSAGES=true
OPENAI_USE_MESSAGE_UPDATES=true
OPENAI_PROGRESS_UPDATE_INTERVAL=3
```
**Result:** Single updating message, clean history

#### Configuration 3: Fast & Dynamic
```bash
OPENAI_ENABLE_STREAMING=true
OPENAI_STREAMING_MODE=chunked
OPENAI_STREAMING_CHUNK_SIZE=100
OPENAI_STREAMING_DELAY=0.2
```
**Result:** Smaller chunks, faster streaming

#### Configuration 4: Sentence-Only
```bash
OPENAI_ENABLE_STREAMING=true
OPENAI_STREAMING_MODE=sentence
OPENAI_STREAMING_DELAY=0.5
```
**Result:** Complete sentences, deliberate pace

---

## Streaming Modes

### Comparison Table

| Mode | Config | Messages (500 words) | User Experience | Best For |
|------|--------|---------------------|-----------------|----------|
| **Chunked** | `ENABLE_STREAMING=true`<br>`MODE=chunked` | 5-7 | ⭐⭐⭐⭐⭐ Smooth, engaging | General use |
| **Sentence** | `ENABLE_STREAMING=true`<br>`MODE=sentence` | 10-12 | ⭐⭐⭐⭐ Clean, deliberate | Professional |
| **Progress Updates** | `ENABLE_STREAMING=false`<br>`USE_MESSAGE_UPDATES=true` | 2 | ⭐⭐⭐⭐⭐ Single updating msg | Minimal clutter |
| **Progress Separate** | `ENABLE_STREAMING=false`<br>`USE_MESSAGE_UPDATES=false` | 5 | ⭐⭐⭐ Multiple messages | Fallback |

### Why Not Per-Token Streaming?

**Hypothetical per-token streaming would create:**
- 750+ separate messages for 500-word response
- Unreadable (character by character: "Neural", " networks", " are"...)
- Teams UI flooded with timestamps/avatars
- Rate limiting issues
- 750 HTTP requests

**Chunking is necessary to:**
- ✅ Buffer tokens into readable chunks
- ✅ Natural sentence breaks
- ✅ 5-10 messages instead of 750
- ✅ Smooth, readable experience
- ✅ Rate limit safe

---

## Usage Examples

### Available Commands

```
/help or /commands     - Show help message
/clear or /reset       - Clear conversation history
/status                - Check authentication status
/me                    - Get Microsoft Graph profile
/prs                   - Get GitHub pull requests
/logout                - Sign out from services
```

### Example Queries

#### General Questions
```
What is Python?
Explain how neural networks work
What are the benefits of microservices?
```

#### Technical Questions
```
How do I implement OAuth 2.0 authentication?
Explain Docker containerization
What are REST API design best practices?
```

#### Code Generation
```
Write a Python function to implement binary search
Create a React component for user authentication
Write SQL queries to analyze user engagement
```

#### Creative Content
```
Write a creative story about AI and humans
Brainstorm marketing ideas for a new app
Create a product description for a SaaS tool
```

#### Data Analysis
```
Analyze trends in this data
What patterns do you see in these numbers?
Calculate the average and standard deviation
```

---

## System Prompts

The bot automatically selects appropriate system prompts based on query content:

### Available Prompt Categories

1. **General** - Default helpful assistant
2. **Technical** - Technical expert with best practices
3. **Code Helper** - Coding assistant with examples and tests
4. **Data Analysis** - Data expert with insights and visualizations
5. **Creative** - Creative writing and brainstorming
6. **Business** - Business strategy and decision-making
7. **Learning** - Educational tutor with explanations
8. **Summarization** - Content summarization expert

### Customizing System Prompts

Edit `src/prompts.py` to customize:

```python
SYSTEM_PROMPTS = {
    "general": """Your custom general prompt here...""",
    "technical": """Your custom technical prompt here...""",
    # Add more...
}
```

### Prompt Keywords

The system automatically detects query type based on keywords:

- **Technical**: "api", "framework", "architecture", "infrastructure"
- **Code**: "code", "function", "algorithm", "debug", "python", "javascript"
- **Creative**: "write", "create", "brainstorm", "story", "content"
- **Data Analysis**: "analyze", "data", "chart", "trend", "calculate"
- And more...

---

## Troubleshooting

### Error: "No response returned"

**Fixed!** All handlers now return `True` to indicate completion.

If you still see this error, ensure you're on the latest version.

### Error: "Missing required environment variables"

**Solution:** Add to `.env`:
```bash
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

### Too Many Messages (Streaming)

**Solution 1:** Increase chunk size
```bash
OPENAI_STREAMING_CHUNK_SIZE=300
```

**Solution 2:** Disable streaming
```bash
OPENAI_ENABLE_STREAMING=false
```

### Streaming Feels Too Slow

**Solution:**
```bash
OPENAI_STREAMING_DELAY=0.1
OPENAI_STREAMING_CHUNK_SIZE=100
```

### Not Enough Feedback When Waiting

**Solution:**
```bash
OPENAI_ENABLE_STREAMING=false
OPENAI_SHOW_PROGRESS_MESSAGES=true
OPENAI_PROGRESS_UPDATE_INTERVAL=2
```

### Progress Messages Not Updating in Place

**Reason:** Teams environment may not support `update_activity()`

**Solution:** Disable message updates (falls back to separate messages)
```bash
OPENAI_USE_MESSAGE_UPDATES=false
```

### OpenAI Timeout

**Solution:**
```bash
OPENAI_TIMEOUT=60  # Increase to 60 seconds
```

### Rate Limiting

**Solution:**
- Wait a few moments
- Check Azure OpenAI quota in Azure Portal
- Consider increasing quota

---

## Architecture

### System Flow

```
User Message (Teams)
    ↓
FastAPI Endpoint (/api/messages)
    ↓
Agent Message Handler
    ↓
OpenAI Handler
    ├── Detect query category
    ├── Select system prompt
    ├── Get conversation history
    └── Call Azure OpenAI
        ↓
    IF Streaming Enabled:
        ├── Stream chunks as they arrive
        ├── Buffer ~150 characters
        ├── Send chunks to Teams
        └── Send token summary
    ELSE:
        ├── Show progress indicators
        ├── Update message in place
        ├── Buffer complete response
        └── Send formatted response
    ↓
Teams Client (Display to user)
```

### Code Structure

```
src/
├── openai_service.py      # OpenAI client with async streaming
├── openai_handler.py       # Message handling and progress indicators
├── prompts.py              # System prompts and categorization
├── cards.py                # Adaptive Card templates
├── agent.py                # Agent message routing
└── ...
```

### Key Components

**`openai_service.py`:**
- `OpenAIService` - Main service class
- `stream_response()` - Stream response chunks
- `get_complete_response()` - Buffer complete response
- Error handling and retry logic

**`openai_handler.py`:**
- `handle_openai_message()` - Main message handler
- `_stream_response_with_chunks()` - Visible streaming
- `_buffer_response_with_progress()` - Progress indicators
- `ConversationState` - Conversation history manager

**`prompts.py`:**
- `SYSTEM_PROMPTS` - 8 specialized prompts
- `get_system_prompt()` - Smart prompt selection
- `get_thinking_message()` - Category-specific thinking messages
- `should_use_streaming_ux()` - Determine streaming need

---

## Cost Management

### Token Usage Tracking

The bot tracks token usage for each request and displays it:

```
✅ Complete - 1,234 tokens (~$0.0185)
```

### GPT-4o Pricing (as of 2025)

- **Input:** $0.005 per 1K tokens
- **Output:** $0.015 per 1K tokens

### Example Costs

| Query Type | Tokens | Cost |
|-----------|--------|------|
| Simple question (200 words) | ~300 | ~$0.003 |
| Complex analysis (1000 words) | ~1500 | ~$0.023 |
| Code generation (500 words) | ~750 | ~$0.011 |

### Optimization Tips

1. **Use gpt-4o-mini for simple queries** - 10x cheaper
2. **Limit conversation history** - Set `OPENAI_MAX_HISTORY_MESSAGES=5`
3. **Set appropriate max_tokens** - `OPENAI_MAX_TOKENS=2000`
4. **Clear history when switching topics** - `/clear` command
5. **Monitor usage** - Check token counts in responses

### Model Recommendations

| Use Case | Model | Cost | Quality |
|----------|-------|------|---------|
| Simple Q&A | gpt-4o-mini | $ | Good |
| Complex analysis | gpt-4o | $$ | Excellent |
| Maximum quality | gpt-4-turbo | $$$ | Best |

---

## Advanced Configuration

### Per-Request Overrides

You can override settings in code:

```python
# Force streaming on for specific request
await handle_openai_message(context, state, enable_visible_streaming=True)

# Force streaming off
await handle_openai_message(context, state, enable_visible_streaming=False)

# Use environment variable (default)
await handle_openai_message(context, state, enable_visible_streaming=None)
```

### Custom Temperature and Max Tokens

Modify in `openai_service.py`:

```python
response = await openai_service.get_complete_response(
    user_message=user_message,
    system_prompt=system_prompt,
    temperature=0.9,  # More creative
    max_tokens=2000,  # Shorter responses
)
```

### Disable Conversation History

In `agent.py`:

```python
# Stateless interactions
await handle_openai_message(context, state, use_conversation_history=False)
```

---

## Testing

### Manual Testing

```bash
# 1. Start bot
python -m src.server

# 2. Test queries in Teams
/help                                    # Show available commands
What is Python?                          # Simple question
Explain microservices architecture      # Complex analysis
Write a Python function to sort a list   # Code generation
/clear                                   # Clear history
```

### Check Logs

Monitor for:

```
[INFO] OpenAI service initialized with deployment: gpt-4o
[INFO] Message category: technical
[INFO] Visible streaming: True
[INFO] Starting visible streaming (chunk_size=150, delay=0.3s)
[INFO] Sending chunk 1: 152 characters
[INFO] Streaming completed: 554 total characters in 4 chunks
[INFO] Token usage - Total: 567, Cost: $0.0085
```

### Test Streaming Modes

**Test chunked streaming:**
```bash
OPENAI_ENABLE_STREAMING=true
OPENAI_STREAMING_MODE=chunked
```
Restart, ask: "Explain neural networks"
Expected: 5-7 chunks appearing

**Test sentence streaming:**
```bash
OPENAI_STREAMING_MODE=sentence
```
Restart, ask: "Explain neural networks"
Expected: 10-12 sentences appearing

**Test progress updates:**
```bash
OPENAI_ENABLE_STREAMING=false
OPENAI_USE_MESSAGE_UPDATES=true
```
Restart, ask: "Explain neural networks"
Expected: Single message updating with progress, then complete response

---

## Production Deployment

### Security Checklist

- ✅ Never commit `.env` to git
- ✅ Use Azure Key Vault for secrets
- ✅ Enable Azure OpenAI content filtering
- ✅ Set rate limits per user (10 requests/minute recommended)
- ✅ Monitor token usage and costs
- ✅ Implement user authentication

### Azure App Service

1. Deploy to Azure App Service
2. Set environment variables in Configuration
3. Enable Application Insights
4. Set up auto-scaling

### Monitoring

**Key Metrics:**
- Request latency (p50, p95, p99)
- Token usage per request
- Error rate
- Cost per user/day
- Popular query categories

---

## FAQ

### Q: Why chunking instead of per-token streaming?

**A:** Per-token would create 750+ messages for a single response. Chunking at 150 characters gives smooth streaming without flooding Teams with hundreds of tiny messages.

### Q: Can I use OpenAI instead of Azure OpenAI?

**A:** The code is designed for Azure OpenAI, but you can modify `openai_service.py` to use OpenAI API directly by changing the client initialization.

### Q: Does streaming cost more?

**A:** No! Streaming has the same token cost. It just delivers tokens progressively instead of waiting for the complete response.

### Q: What if message updates don't work?

**A:** Set `OPENAI_USE_MESSAGE_UPDATES=false` to fall back to separate messages. Some Teams configurations don't support `update_activity()`.

### Q: How do I switch models?

**A:** Change `AZURE_OPENAI_DEPLOYMENT_NAME` in `.env` to your deployed model name (e.g., `gpt-4o-mini`).

### Q: Can I customize progress messages?

**A:** Yes! Edit `progress_messages` dictionary in `src/openai_handler.py` function `_buffer_response_with_progress()`.

---

## Summary

✅ **Fully configurable** via `.env` - no code changes needed
✅ **3 streaming modes** - chunked, sentence, progress updates
✅ **Category-aware** - auto-adapts prompts and progress messages
✅ **Message updates** - single updating message in non-streaming mode
✅ **Multi-turn conversations** - maintains context
✅ **Token tracking** - monitor costs per request
✅ **Error handling** - automatic retries and fallbacks
✅ **Production ready** - secure, scalable, monitored

---

## Support

For issues or questions:
1. Check logs for error details
2. Review troubleshooting section above
3. Verify environment variables are set correctly
4. Check Azure OpenAI service health
5. Review Microsoft Teams bot documentation

---

## License

Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
