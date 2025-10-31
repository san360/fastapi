# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
OpenAI service for streaming responses with Azure OpenAI.
Provides async streaming capabilities with error handling and retry logic.
"""

import os
import asyncio
import logging
from typing import AsyncIterator, Optional, List, Dict, Any
from dataclasses import dataclass
from openai import AsyncAzureOpenAI, APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage statistics for OpenAI requests."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def estimated_cost(self) -> float:
        """Estimate cost based on GPT-4o pricing ($0.005/1K prompt, $0.015/1K completion)."""
        prompt_cost = (self.prompt_tokens / 1000) * 0.005
        completion_cost = (self.completion_tokens / 1000) * 0.015
        return prompt_cost + completion_cost


@dataclass
class OpenAIConfig:
    """Configuration for Azure OpenAI service."""
    api_key: str
    endpoint: str
    deployment: str
    api_version: str = "2024-10-21"
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create configuration from environment variables."""
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

        if not api_key or not endpoint:
            raise ValueError(
                "Missing required environment variables: "
                "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set"
            )

        return cls(
            api_key=api_key,
            endpoint=endpoint,
            deployment=deployment,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
        )


class OpenAIService:
    """
    Service for interacting with Azure OpenAI with streaming support.

    Features:
    - Async streaming responses
    - Automatic retry with exponential backoff
    - Token usage tracking
    - Error handling and timeouts
    - Conversation history support
    """

    def __init__(self, config: OpenAIConfig):
        """Initialize OpenAI service with configuration."""
        self.config = config
        self.client = AsyncAzureOpenAI(
            api_key=config.api_key,
            api_version=config.api_version,
            azure_endpoint=config.endpoint,
            timeout=config.timeout,
        )
        self.last_token_usage: Optional[TokenUsage] = None
        logger.info(
            f"OpenAI service initialized with deployment: {config.deployment}, "
            f"max_tokens: {config.max_tokens}, temperature: {config.temperature}"
        )

    async def stream_response(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream OpenAI response chunks.

        Args:
            user_message: User's message/question
            system_prompt: System prompt to guide the AI
            conversation_history: Optional list of previous messages
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Yields:
            Chunks of the AI response as they're generated

        Raises:
            Exception: On API errors after all retries exhausted
        """
        messages = self._build_messages(system_prompt, user_message, conversation_history)

        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"Streaming OpenAI request (attempt {attempt + 1}/{self.config.max_retries}): "
                    f"{len(user_message)} chars"
                )

                async with asyncio.timeout(self.config.timeout):
                    stream = await self.client.chat.completions.create(
                        model=self.config.deployment,
                        messages=messages,
                        stream=True,
                        temperature=temperature or self.config.temperature,
                        max_tokens=max_tokens or self.config.max_tokens,
                        stream_options={"include_usage": True}
                    )

                    token_count = 0
                    async for chunk in stream:
                        # Handle content chunks
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            token_count += 1
                            yield content

                        # Handle usage information (comes in final chunk)
                        if hasattr(chunk, 'usage') and chunk.usage:
                            self.last_token_usage = TokenUsage(
                                prompt_tokens=chunk.usage.prompt_tokens,
                                completion_tokens=chunk.usage.completion_tokens,
                                total_tokens=chunk.usage.total_tokens,
                            )
                            logger.info(
                                f"OpenAI streaming completed: {self.last_token_usage.total_tokens} tokens, "
                                f"estimated cost: ${self.last_token_usage.estimated_cost:.4f}"
                            )

                    # Success - exit retry loop
                    return

            except asyncio.TimeoutError:
                logger.warning(f"OpenAI request timeout (attempt {attempt + 1})")
                if attempt == self.config.max_retries - 1:
                    raise Exception(
                        "I apologize, but I'm taking too long to respond. "
                        "Please try asking a simpler question or try again later."
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except RateLimitError as e:
                logger.warning(f"OpenAI rate limit hit (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise Exception(
                        "I'm currently experiencing high demand. "
                        "Please try again in a few moments."
                    )
                await asyncio.sleep(2 ** attempt)

            except APIError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise Exception(
                        "I encountered an error while processing your request. "
                        "Please try again or rephrase your question."
                    )
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"Unexpected error during OpenAI streaming: {e}", exc_info=True)
                raise Exception(
                    "I encountered an unexpected error. Please try again."
                )

    async def get_complete_response(
        self,
        user_message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get complete response (buffer all streaming chunks).

        This is useful when you want to wait for the full response before
        displaying it to the user (cleaner UX for Teams).

        Args:
            user_message: User's message/question
            system_prompt: System prompt to guide the AI
            conversation_history: Optional list of previous messages
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Complete AI response as a single string

        Raises:
            Exception: On API errors
        """
        response = ""
        async for chunk in self.stream_response(
            user_message,
            system_prompt,
            conversation_history,
            temperature,
            max_tokens,
        ):
            response += chunk

        logger.info(f"Complete response received: {len(response)} characters")
        return response

    async def get_chunked_response(
        self,
        user_message: str,
        system_prompt: str,
        chunk_size: int = 200,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[str]:
        """
        Get response in larger chunks (useful for sending periodic updates).

        Instead of streaming every token, this buffers tokens and yields
        chunks of approximately chunk_size characters.

        Args:
            user_message: User's message/question
            system_prompt: System prompt to guide the AI
            chunk_size: Approximate size of chunks to yield (default: 200 chars)
            conversation_history: Optional list of previous messages

        Yields:
            Larger chunks of the response
        """
        buffer = ""
        async for chunk in self.stream_response(user_message, system_prompt, conversation_history):
            buffer += chunk
            if len(buffer) >= chunk_size:
                yield buffer
                buffer = ""

        # Yield remaining buffer
        if buffer:
            yield buffer

    def _build_messages(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Build messages array for OpenAI API.

        Args:
            system_prompt: System prompt
            user_message: Current user message
            conversation_history: Optional previous messages

        Returns:
            List of message dictionaries
        """
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            # Limit history to prevent context overflow
            max_history = int(os.getenv("OPENAI_MAX_HISTORY_MESSAGES", "10"))
            messages.extend(conversation_history[-max_history:])

        messages.append({"role": "user", "content": user_message})

        return messages

    def get_last_token_usage(self) -> Optional[TokenUsage]:
        """Get token usage from last request."""
        return self.last_token_usage


# Global service instance (initialized on first import)
_service_instance: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """
    Get or create the global OpenAI service instance.

    Returns:
        OpenAI service instance

    Raises:
        ValueError: If required environment variables are not set
    """
    global _service_instance

    if _service_instance is None:
        config = OpenAIConfig.from_env()
        _service_instance = OpenAIService(config)

    return _service_instance
