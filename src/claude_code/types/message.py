"""
Message type definitions.

Types for representing conversation messages.

Migrated from: types/message.ts + utils/messages.ts (partial)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


# Content block types
@dataclass
class TextBlock:
    """A text content block."""

    type: Literal["text"] = "text"
    text: str = ""


@dataclass
class ImageBlock:
    """An image content block."""

    type: Literal["image"] = "image"
    source: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolUseBlock:
    """A tool use content block."""

    type: Literal["tool_use"] = "tool_use"
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResultBlock:
    """A tool result content block."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str = ""
    content: str | list[Any] = ""
    is_error: bool = False


@dataclass
class ThinkingBlock:
    """A thinking content block."""

    type: Literal["thinking"] = "thinking"
    thinking: str = ""


ContentBlock = TextBlock | ImageBlock | ToolUseBlock | ToolResultBlock | ThinkingBlock | dict[str, Any]


# Message origin
MessageOrigin = Literal[
    "user",
    "assistant",
    "tool_result",
    "system",
]


@dataclass
class UserMessage:
    """A message from the user."""

    role: Literal["user"] = "user"
    content: str | list[ContentBlock] = ""
    uuid: str = ""
    timestamp: float = 0.0


@dataclass
class AssistantMessage:
    """A message from the assistant."""

    role: Literal["assistant"] = "assistant"
    content: str | list[ContentBlock] = ""
    uuid: str = ""
    timestamp: float = 0.0
    model: str | None = None
    stop_reason: str | None = None


# System message levels
SystemMessageLevel = Literal["info", "warning", "error", "success"]


@dataclass
class SystemMessage:
    """A system message."""

    type: Literal["system"] = "system"
    level: SystemMessageLevel = "info"
    content: str = ""
    uuid: str = ""
    timestamp: float = 0.0


@dataclass
class SystemInformationalMessage:
    """An informational system message."""

    type: Literal["system_informational"] = "system_informational"
    level: SystemMessageLevel = "info"
    content: str = ""
    title: str | None = None


@dataclass
class SystemAPIErrorMessage:
    """An API error system message."""

    type: Literal["system_api_error"] = "system_api_error"
    error: str = ""
    retry_after: int | None = None


@dataclass
class ProgressMessage:
    """A progress update message."""

    type: Literal["progress"] = "progress"
    tool_use_id: str = ""
    content: str = ""
    progress: float = 0.0


@dataclass
class StreamEvent:
    """A stream event."""

    type: str = ""
    data: Any = None


@dataclass
class RequestStartEvent:
    """Event when a request starts."""

    type: Literal["request_start"] = "request_start"
    request_id: str = ""
    timestamp: float = 0.0


@dataclass
class ToolUseSummaryMessage:
    """Summary of tool uses in a turn."""

    type: Literal["tool_use_summary"] = "tool_use_summary"
    tool_uses: list[dict[str, Any]] = field(default_factory=list)
    total_cost_usd: float = 0.0


@dataclass
class AttachmentMessage:
    """A message with attachments."""

    type: Literal["attachment"] = "attachment"
    attachments: list[dict[str, Any]] = field(default_factory=list)


# Message union type
Message = (
    UserMessage
    | AssistantMessage
    | SystemMessage
    | SystemInformationalMessage
    | SystemAPIErrorMessage
    | ProgressMessage
    | AttachmentMessage
    | ToolUseSummaryMessage
)


# Normalized message types for processing
@dataclass
class NormalizedUserMessage:
    """A normalized user message."""

    role: Literal["user"] = "user"
    content: list[ContentBlock] = field(default_factory=list)


@dataclass
class NormalizedAssistantMessage:
    """A normalized assistant message."""

    role: Literal["assistant"] = "assistant"
    content: list[ContentBlock] = field(default_factory=list)


NormalizedMessage = NormalizedUserMessage | NormalizedAssistantMessage


# Helper functions
def is_user_message(msg: Message) -> bool:
    """Check if a message is from the user."""
    return getattr(msg, "role", None) == "user"


def is_assistant_message(msg: Message) -> bool:
    """Check if a message is from the assistant."""
    return getattr(msg, "role", None) == "assistant"


def is_system_message(msg: Message) -> bool:
    """Check if a message is a system message."""
    return getattr(msg, "type", "").startswith("system")


def extract_text_content(msg: Message) -> str:
    """Extract text content from a message."""
    content = getattr(msg, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, TextBlock):
                texts.append(block.text)
            elif isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return "\n".join(texts)

    return ""


def count_tool_uses(msg: Message) -> int:
    """Count tool use blocks in a message."""
    content = getattr(msg, "content", [])

    if not isinstance(content, list):
        return 0

    count = 0
    for block in content:
        if isinstance(block, ToolUseBlock) or isinstance(block, dict) and block.get("type") == "tool_use":
            count += 1

    return count
