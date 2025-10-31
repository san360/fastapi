# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
OpenAI message handler for the Teams bot.
Handles user messages and generates responses using Azure OpenAI with streaming.
"""

import os
import re
import logging
import asyncio
from typing import Optional, Dict, List
from microsoft_agents.hosting.core import (
    TurnContext,
    TurnState,
    MessageFactory,
)
from microsoft_agents.activity import ActivityTypes, Activity

from .openai_service import get_openai_service, OpenAIService
from .prompts import (
    get_system_prompt,
    get_prompt_category,
    get_thinking_message,
    get_processing_message,
    should_use_streaming_ux,
)
from .cards import create_openai_response_card

logger = logging.getLogger(__name__)


class ConversationState:
    """
    Simple conversation state management.
    Stores conversation history per user/conversation.
    """

    def __init__(self, max_history: int = 10):
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        self.max_history = max_history

    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a specific conversation."""
        return self.conversations.get(conversation_id, [])

    def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation history."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append({
            "role": role,
            "content": content
        })

        # Trim to max history
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]

    def clear_history(self, conversation_id: str):
        """Clear conversation history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]


# Global conversation state
conversation_state = ConversationState()


async def handle_openai_message(
    context: TurnContext,
    state: TurnState,
    use_conversation_history: bool = False,
    enable_visible_streaming: Optional[bool] = None
) -> None:
    """
    Handle user message with OpenAI integration.

    This function supports two modes:
    1. Visible streaming (enable_visible_streaming=True): Shows chunks as they arrive
    2. Complete response (enable_visible_streaming=False): Buffers with progress indicators

    Args:
        context: Turn context from the agent
        state: Turn state
        use_conversation_history: Whether to include conversation history
        enable_visible_streaming: Override streaming setting (None=use env variable)
    """
    user_message = context.activity.text.strip()

    # Skip empty messages
    if not user_message:
        return

    # Get streaming configuration from environment if not explicitly set
    if enable_visible_streaming is None:
        enable_visible_streaming = os.getenv("OPENAI_ENABLE_STREAMING", "true").lower() == "true"

    logger.info("=" * 80)
    logger.info("=== OpenAI Message Handler Called ===")
    logger.info(f"User message: {user_message[:100]}...")
    logger.info(f"Message length: {len(user_message)} characters")
    logger.info(f"Visible streaming: {enable_visible_streaming} (from env: {os.getenv('OPENAI_ENABLE_STREAMING', 'true')})")

    # Get conversation ID for history tracking
    conversation_id = context.activity.conversation.id

    # Determine message category and get appropriate prompts
    category = get_prompt_category(user_message)
    system_prompt = get_system_prompt(user_message)
    thinking_msg = get_thinking_message(category)

    logger.info(f"Message category: {category}")
    logger.info(f"System prompt type: {category}")

    try:
        # Step 1: Send typing indicator
        await context.send_activity(Activity(type=ActivityTypes.typing))

        # Step 2: Send thinking message
        await context.send_activity(MessageFactory.text(thinking_msg))

        # Step 3: Get OpenAI service
        openai_service = get_openai_service()

        # Step 4: Get conversation history if enabled
        conversation_history = None
        if use_conversation_history:
            conversation_history = conversation_state.get_history(conversation_id)
            logger.info(f"Using conversation history: {len(conversation_history)} messages")

        # Step 5: Stream or buffer response
        logger.info("Calling OpenAI service...")

        if enable_visible_streaming:
            # VISIBLE STREAMING: Send chunks as they arrive
            response = await _stream_response_with_chunks(
                context=context,
                openai_service=openai_service,
                user_message=user_message,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                category=category
            )
        else:
            # BUFFERED RESPONSE WITH PROGRESS INDICATORS
            response = await _buffer_response_with_progress(
                context=context,
                openai_service=openai_service,
                user_message=user_message,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                category=category
            )

        # Step 6: Track conversation history
        if use_conversation_history:
            conversation_state.add_message(conversation_id, "user", user_message)
            conversation_state.add_message(conversation_id, "assistant", response)

        # Log token usage
        token_usage = openai_service.get_last_token_usage()
        if token_usage:
            logger.info(
                f"Token usage - Prompt: {token_usage.prompt_tokens}, "
                f"Completion: {token_usage.completion_tokens}, "
                f"Total: {token_usage.total_tokens}, "
                f"Cost: ${token_usage.estimated_cost:.4f}"
            )

        logger.info("=== OpenAI Handler Completed Successfully ===")

    except Exception as e:
        logger.error(f"Error in OpenAI handler: {e}", exc_info=True)

        # Send user-friendly error message
        error_message = (
            "I apologize, but I encountered an error while processing your request. "
            "Please try again, or rephrase your question."
        )

        # If the error message from OpenAI service is user-friendly, use it
        if isinstance(e, Exception) and str(e).startswith("I"):
            error_message = str(e)

        await context.send_activity(MessageFactory.text(f"❌ {error_message}"))

    logger.info("=" * 80)


async def _stream_response_with_chunks(
    context: TurnContext,
    openai_service,
    user_message: str,
    system_prompt: str,
    conversation_history: Optional[List[Dict[str, str]]],
    category: str,
    chunk_size: Optional[int] = None
) -> str:
    """
    Stream response by sending visible chunks to the user as they arrive.

    Supports multiple streaming modes:
    - Character-based: Send after N characters (default 150)
    - Sentence-based: Send complete sentences only (chunk_size=0)

    Args:
        context: Turn context
        openai_service: OpenAI service instance
        user_message: User's message
        system_prompt: System prompt
        conversation_history: Conversation history
        category: Message category
        chunk_size: Chars before sending (0=sentence-only, None=use env default)

    Returns:
        Complete response string
    """
    # Get configuration from environment
    if chunk_size is None:
        chunk_size = int(os.getenv("OPENAI_STREAMING_CHUNK_SIZE", "150"))

    streaming_delay = float(os.getenv("OPENAI_STREAMING_DELAY", "0.3"))
    streaming_mode = os.getenv("OPENAI_STREAMING_MODE", "chunked")  # chunked or sentence

    buffer = ""
    complete_response = ""
    chunk_count = 0

    logger.info(
        f"Starting visible streaming (mode={streaming_mode}, "
        f"chunk_size={chunk_size}, delay={streaming_delay}s)..."
    )

    async for text_chunk in openai_service.stream_response(
        user_message=user_message,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
    ):
        buffer += text_chunk
        complete_response += text_chunk

        # Determine when to send based on mode
        should_send = False

        if streaming_mode == "sentence":
            # Send only on sentence boundaries
            if text_chunk.endswith((".", "!", "?", "\n")) and len(buffer.strip()) > 20:
                should_send = True
        else:
            # Default: send when buffer reaches threshold OR at sentence end
            if len(buffer) >= chunk_size or text_chunk.endswith((".", "!", "?", "\n")):
                should_send = True

        if should_send and buffer.strip():
            chunk_count += 1
            logger.info(f"Sending chunk {chunk_count}: {len(buffer)} characters")
            await context.send_activity(MessageFactory.text(buffer.strip()))
            buffer = ""

            # Small delay to prevent overwhelming Teams
            await asyncio.sleep(streaming_delay)

    # Send any remaining buffer
    if buffer.strip():
        chunk_count += 1
        logger.info(f"Sending final chunk {chunk_count}: {len(buffer)} characters")
        await context.send_activity(MessageFactory.text(buffer.strip()))

    logger.info(f"Streaming completed: {len(complete_response)} total characters in {chunk_count} chunks")

    # Send token usage summary as final message
    token_usage = openai_service.get_last_token_usage()
    if token_usage:
        summary = (
            f"_✅ Complete - {token_usage.total_tokens} tokens "
            f"(~${token_usage.estimated_cost:.4f})_"
        )
        await context.send_activity(MessageFactory.text(summary))

    return complete_response


async def _buffer_response_with_progress(
    context: TurnContext,
    openai_service,
    user_message: str,
    system_prompt: str,
    conversation_history: Optional[List[Dict[str, str]]],
    category: str
) -> str:
    """
    Buffer complete response while showing progress indicators to user.

    Updates a single message in place to show progress rather than
    sending multiple messages.

    Args:
        context: Turn context
        openai_service: OpenAI service instance
        user_message: User's message
        system_prompt: System prompt
        conversation_history: Conversation history
        category: Message category

    Returns:
        Complete response string
    """
    # Get configuration
    show_progress = os.getenv("OPENAI_SHOW_PROGRESS_MESSAGES", "true").lower() == "true"
    progress_interval = float(os.getenv("OPENAI_PROGRESS_UPDATE_INTERVAL", "3"))
    use_message_updates = os.getenv("OPENAI_USE_MESSAGE_UPDATES", "true").lower() == "true"

    # Progress messages based on category
    progress_messages = {
        "general": [
            "💭 Thinking deeply about your question...",
            "🔍 Analyzing the details...",
            "✨ Crafting a comprehensive response...",
            "📝 Almost done...",
        ],
        "technical": [
            "⚙️ Processing technical details...",
            "🔧 Analyzing architecture and patterns...",
            "📊 Gathering best practices...",
            "💡 Finalizing recommendations...",
        ],
        "code_helper": [
            "💻 Writing code...",
            "🔨 Optimizing implementation...",
            "✅ Adding examples and tests...",
            "📚 Preparing documentation...",
        ],
        "creative": [
            "🎨 Generating creative ideas...",
            "💡 Crafting unique content...",
            "🌟 Refining the narrative...",
            "📖 Polishing the final draft...",
        ],
        "data_analysis": [
            "📊 Analyzing data patterns...",
            "📈 Computing statistics...",
            "🔍 Identifying insights...",
            "💡 Formulating recommendations...",
        ],
        "business": [
            "📈 Analyzing business context...",
            "💼 Evaluating options...",
            "🎯 Developing strategy...",
            "📋 Creating action plan...",
        ],
        "learning": [
            "📚 Preparing educational content...",
            "🎓 Structuring explanation...",
            "💡 Creating examples...",
            "✍️ Finalizing lesson...",
        ],
        "summarization": [
            "📝 Reading content...",
            "🔍 Extracting key points...",
            "📋 Organizing information...",
            "✅ Creating summary...",
        ],
    }

    messages = progress_messages.get(category, progress_messages["general"])

    # Start async task to get response
    response_task = asyncio.create_task(
        openai_service.get_complete_response(
            user_message=user_message,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
        )
    )

    # Show progress messages while waiting
    message_index = 0
    progress_activity = None

    if show_progress:
        if use_message_updates:
            # Send initial progress message and update it in place
            progress_activity = await context.send_activity(MessageFactory.text(messages[0]))
            message_index = 1

            while not response_task.done():
                try:
                    # Wait for either task completion or progress interval
                    await asyncio.wait_for(asyncio.shield(response_task), timeout=progress_interval)
                    break  # Task completed
                except asyncio.TimeoutError:
                    # Update progress message
                    if message_index < len(messages):
                        # Create updated activity
                        updated_activity = MessageFactory.text(messages[message_index])
                        updated_activity.id = progress_activity.id

                        try:
                            await context.update_activity(updated_activity)
                            logger.info(f"Updated progress message to: {messages[message_index]}")
                        except Exception as e:
                            logger.warning(f"Failed to update activity: {e}. Falling back to new message.")
                            # If update fails, send new message instead
                            await context.send_activity(MessageFactory.text(messages[message_index]))

                        message_index += 1
                    else:
                        # Keep showing typing indicator if we run out of messages
                        await context.send_activity(Activity(type=ActivityTypes.typing))
        else:
            # Fallback: send separate messages (original behavior)
            while not response_task.done():
                try:
                    await asyncio.wait_for(asyncio.shield(response_task), timeout=progress_interval)
                    break
                except asyncio.TimeoutError:
                    if message_index < len(messages):
                        await context.send_activity(MessageFactory.text(messages[message_index]))
                        message_index += 1
                    else:
                        await context.send_activity(Activity(type=ActivityTypes.typing))

    # Get the completed response
    response = await response_task

    logger.info(f"OpenAI buffered response received: {len(response)} characters")

    # Delete progress message if it exists and we're sending a new one
    if progress_activity and use_message_updates:
        try:
            await context.delete_activity(progress_activity.id)
            logger.info("Deleted progress message")
        except Exception as e:
            logger.warning(f"Failed to delete progress activity: {e}")

    # Send response
    if len(response) > 500:
        logger.info("Sending response as Adaptive Card")
        card = create_openai_response_card(
            response=response,
            category=category,
            token_usage=openai_service.get_last_token_usage()
        )
        await context.send_activity(MessageFactory.attachment(card))
    else:
        logger.info("Sending response as plain text")
        await context.send_activity(MessageFactory.text(response))

    return response


async def handle_clear_history(context: TurnContext, state: TurnState) -> None:
    """
    Clear conversation history for the current conversation.

    Usage: /clear or /reset
    """
    conversation_id = context.activity.conversation.id
    conversation_state.clear_history(conversation_id)

    await context.send_activity(
        MessageFactory.text("✅ Conversation history cleared. Starting fresh!")
    )

    logger.info(f"Cleared conversation history for: {conversation_id}")


async def handle_help(context: TurnContext, state: TurnState) -> None:
    """
    Show help message with available commands.

    Usage: /help or /commands
    """
    # Get current streaming configuration
    streaming_enabled = os.getenv("OPENAI_ENABLE_STREAMING", "true").lower() == "true"
    streaming_mode = os.getenv("OPENAI_STREAMING_MODE", "chunked")

    if streaming_enabled:
        streaming_status = f"🌊 Real-time streaming ({streaming_mode} mode)"
    else:
        streaming_status = "📝 Buffered responses with progress indicators"

    help_text = f"""
**🤖 AI Assistant - Available Commands**

**General Chat:**
- Just type your question or message naturally!
- Examples:
  - "Explain how neural networks work"
  - "Write a Python function to sort a list"
  - "What are the benefits of microservices?"

**Special Commands:**
- `/help` or `/commands` - Show this help message
- `/clear` or `/reset` - Clear conversation history
- `/status` - Check authentication status
- `/me` - Get your Microsoft Graph profile
- `/prs` - Get GitHub pull requests
- `/logout` - Sign out from all services

**Features:**
- 🧠 Powered by GPT-4o for intelligent responses
- {streaming_status}
- 💬 Supports multi-turn conversations
- 📊 Can help with code, analysis, writing, and more
- 🎨 Formats responses for easy reading

**Tips:**
- Be specific in your questions for better results
- For code requests, mention the programming language
- Ask follow-up questions to dive deeper into topics
"""

    await context.send_activity(MessageFactory.text(help_text))

    logger.info("Help message sent")


# Export handler functions
__all__ = [
    "handle_openai_message",
    "handle_clear_history",
    "handle_help",
    "conversation_state",
]
