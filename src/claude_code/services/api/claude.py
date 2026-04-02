"""
Claude API query functions.

Core API communication with Claude models.

Migrated from: services/api/claude.ts (3420 lines) - Core functions
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal

from .client import AnthropicClient, get_anthropic_client
from .retry import RetryConfig, with_retry

# Stream event types
StreamEventType = Literal[
    "message_start",
    "content_block_start",
    "content_block_delta",
    "content_block_stop",
    "message_delta",
    "message_stop",
    "ping",
    "error",
]


@dataclass
class StreamEvent:
    """A streaming event from the API."""

    type: StreamEventType
    index: int = 0
    content_block: dict[str, Any] | None = None
    delta: dict[str, Any] | None = None
    message: dict[str, Any] | None = None
    usage: dict[str, int] | None = None
    error: str | None = None


@dataclass
class QueryResult:
    """Result from a query."""

    message: dict[str, Any]
    usage: dict[str, int] = field(default_factory=dict)
    stop_reason: str | None = None
    model: str = ""
    request_id: str | None = None

    @property
    def input_tokens(self) -> int:
        return self.usage.get("input_tokens", 0)

    @property
    def output_tokens(self) -> int:
        return self.usage.get("output_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# Default max output tokens by model family
DEFAULT_MAX_OUTPUT_TOKENS = 8192
CAPPED_DEFAULT_MAX_TOKENS = 16000


def get_max_output_tokens_for_model(model: str) -> int:
    """
    Get maximum output tokens for a model.

    Args:
        model: Model name

    Returns:
        Maximum output tokens
    """
    env_override = os.getenv("ANTHROPIC_MAX_OUTPUT_TOKENS")
    if env_override:
        try:
            return int(env_override)
        except ValueError:
            pass

    model_lower = model.lower()

    # Opus models have higher limits
    if "opus" in model_lower:
        return 32000

    # Sonnet
    if "sonnet" in model_lower:
        return 16000

    # Haiku
    if "haiku" in model_lower:
        return 8192

    return DEFAULT_MAX_OUTPUT_TOKENS


async def query_model(
    messages: list[dict[str, Any]],
    model: str,
    system: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int | None = None,
    temperature: float = 1.0,
    client: AnthropicClient | None = None,
    retry_config: RetryConfig | None = None,
) -> QueryResult:
    """
    Query a Claude model (non-streaming).

    Args:
        messages: Conversation messages
        model: Model name
        system: Optional system prompt
        tools: Optional tool definitions
        max_tokens: Maximum output tokens
        temperature: Sampling temperature
        client: Optional client (created if not provided)
        retry_config: Optional retry configuration

    Returns:
        QueryResult
    """
    if client is None:
        client = await get_anthropic_client()

    if max_tokens is None:
        max_tokens = get_max_output_tokens_for_model(model)

    async def make_request() -> dict[str, Any]:
        return await client.messages_create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system=system,
            tools=tools,
            temperature=temperature,
        )

    if retry_config:
        response = await with_retry(make_request, retry_config)
    else:
        response = await make_request()

    return QueryResult(
        message={
            "role": "assistant",
            "content": response.get("content", []),
        },
        usage=response.get("usage", {}),
        stop_reason=response.get("stop_reason"),
        model=response.get("model", model),
        request_id=response.get("id"),
    )


async def query_model_with_streaming(
    messages: list[dict[str, Any]],
    model: str,
    system: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int | None = None,
    temperature: float = 1.0,
    client: AnthropicClient | None = None,
    on_event: callable | None = None,
) -> AsyncIterator[StreamEvent]:
    """
    Query a Claude model with streaming.

    Args:
        messages: Conversation messages
        model: Model name
        system: Optional system prompt
        tools: Optional tool definitions
        max_tokens: Maximum output tokens
        temperature: Sampling temperature
        client: Optional client
        on_event: Optional callback for events

    Yields:
        StreamEvent objects
    """
    if client is None:
        client = await get_anthropic_client()

    if max_tokens is None:
        max_tokens = get_max_output_tokens_for_model(model)

    try:
        async for event in client.messages_stream(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system=system,
            tools=tools,
            temperature=temperature,
        ):
            stream_event = _parse_stream_event(event)

            if on_event:
                on_event(stream_event)

            yield stream_event

    except Exception as e:
        error_event = StreamEvent(
            type="error",
            error=str(e),
        )
        yield error_event


def _parse_stream_event(event: dict[str, Any]) -> StreamEvent:
    """Parse a raw stream event into StreamEvent."""
    event_type = event.get("type", "unknown")

    if event_type == "message_start":
        return StreamEvent(
            type="message_start",
            message=event.get("message"),
        )

    if event_type == "content_block_start":
        return StreamEvent(
            type="content_block_start",
            index=event.get("index", 0),
            content_block=event.get("content_block"),
        )

    if event_type == "content_block_delta":
        return StreamEvent(
            type="content_block_delta",
            index=event.get("index", 0),
            delta=event.get("delta"),
        )

    if event_type == "content_block_stop":
        return StreamEvent(
            type="content_block_stop",
            index=event.get("index", 0),
        )

    if event_type == "message_delta":
        return StreamEvent(
            type="message_delta",
            delta=event.get("delta"),
            usage=event.get("usage"),
        )

    if event_type == "message_stop":
        return StreamEvent(
            type="message_stop",
        )

    if event_type == "ping":
        return StreamEvent(type="ping")

    if event_type == "error":
        return StreamEvent(
            type="error",
            error=event.get("error", {}).get("message", "Unknown error"),
        )

    return StreamEvent(type="ping")


async def accumulate_stream(
    stream: AsyncIterator[StreamEvent],
) -> QueryResult:
    """
    Accumulate a stream into a complete result.

    Args:
        stream: Stream of events

    Returns:
        Complete QueryResult
    """
    content_blocks: list[dict[str, Any]] = []
    current_block: dict[str, Any] | None = None
    current_text = ""
    usage = {}
    stop_reason = None
    model = ""
    request_id = None

    async for event in stream:
        if event.type == "message_start" and event.message:
            model = event.message.get("model", "")
            request_id = event.message.get("id")

        elif event.type == "content_block_start":
            current_block = event.content_block or {}
            current_text = ""

        elif event.type == "content_block_delta" and event.delta:
            delta_type = event.delta.get("type", "")
            if delta_type == "text_delta":
                current_text += event.delta.get("text", "")
            elif delta_type == "input_json_delta":
                # Tool use input
                if current_block:
                    partial = current_block.get("partial_json", "")
                    current_block["partial_json"] = partial + event.delta.get("partial_json", "")

        elif event.type == "content_block_stop":
            if current_block:
                if current_block.get("type") == "text":
                    current_block["text"] = current_text
                elif current_block.get("type") == "tool_use":
                    # Parse accumulated JSON
                    import json

                    try:
                        partial = current_block.pop("partial_json", "{}")
                        current_block["input"] = json.loads(partial)
                    except json.JSONDecodeError:
                        current_block["input"] = {}

                content_blocks.append(current_block)
                current_block = None

        elif event.type == "message_delta":
            if event.delta:
                stop_reason = event.delta.get("stop_reason")
            if event.usage:
                usage.update(event.usage)

        elif event.type == "error":
            raise RuntimeError(event.error or "Stream error")

    return QueryResult(
        message={
            "role": "assistant",
            "content": content_blocks,
        },
        usage=usage,
        stop_reason=stop_reason,
        model=model,
        request_id=request_id,
    )
