"""
Anthropic LLM Provider (MOD-LLM-001)

Claude API provider implementation.
Requires ANTHROPIC_API_KEY environment variable.

Usage:
    from llm_anthropic import AnthropicProvider

    provider = AnthropicProvider()
    response = provider.chat([Message(role="user", content="Hello")])
"""

import os
from typing import Optional

from .interfaces import LLMProviderInterface, Message, LLMResponse


class AnthropicProvider(LLMProviderInterface):
    """
    Anthropic Claude API provider.

    Supports Claude models via the Anthropic API.
    Requires anthropic package and ANTHROPIC_API_KEY.
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    AVAILABLE_MODELS = [
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-20250514",
        "claude-3-5-haiku-20241022",
    ]

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Anthropic provider.

        Args:
            api_key: API key (or use ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-sonnet-4-20250514)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self._client = None

    def _get_client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    def chat(self, messages: list[Message], **kwargs) -> LLMResponse:
        """
        Send chat messages and get a response.

        Args:
            messages: List of Message objects
            **kwargs: Additional API parameters (max_tokens, temperature, etc.)

        Returns:
            LLMResponse with content and metadata
        """
        client = self._get_client()

        # Separate system message if present
        system = None
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # Build request
        request = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": chat_messages,
        }
        if system:
            request["system"] = system
        if "temperature" in kwargs:
            request["temperature"] = kwargs["temperature"]

        # Call API
        response = client.messages.create(**request)

        # Extract response
        content = ""
        if response.content:
            content = response.content[0].text

        return LLMResponse(
            content=content,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason or "unknown",
        )

    def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Complete a prompt.

        Wraps prompt in a user message for chat-based models.
        """
        messages = [Message(role="user", content=prompt)]
        return self.chat(messages, **kwargs)

    def get_models(self) -> list[str]:
        """List available Claude models."""
        return self.AVAILABLE_MODELS.copy()

    def is_available(self) -> bool:
        """Check if provider is configured and reachable."""
        if not self.api_key:
            return False
        try:
            client = self._get_client()
            # Try a minimal API call to verify connectivity
            return True
        except Exception:
            return False

    def stream_chat(self, messages: list[Message], **kwargs):
        """
        Stream chat response.

        Yields content chunks as they arrive.
        """
        client = self._get_client()

        # Separate system message
        system = None
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # Build request
        request = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": chat_messages,
        }
        if system:
            request["system"] = system

        # Stream response
        with client.messages.stream(**request) as stream:
            for text in stream.text_stream:
                yield text


# Factory function for module loading
def create_llm_provider(config: dict) -> AnthropicProvider:
    """Create an AnthropicProvider instance from config."""
    api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    model = config.get("model", AnthropicProvider.DEFAULT_MODEL)
    return AnthropicProvider(api_key=api_key, model=model)
