"""
API Types.

Type definitions for API requests and responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    pass

# Stop reasons
StopReason = Literal[
    "end_turn",
    "max_tokens",
    "stop_sequence",
    "tool_use",
    "refusal",
]


@dataclass
class TextBlock:
    """Text content block."""

    type: Literal["text"] = "text"
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        return {"type": self.type, "text": self.text}


@dataclass
class ToolUseBlock:
    """Tool use content block."""

    type: Literal["tool_use"] = "tool_use"
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "input": self.input,
        }


@dataclass
class ToolResultBlock:
    """Tool result content block."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str = ""
    content: str | list = ""  # list[TextBlock | ImageBlock]
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        result: dict[str, Any] = {
            "type": self.type,
            "tool_use_id": self.tool_use_id,
        }
        if isinstance(self.content, str):
            result["content"] = self.content
        else:
            result["content"] = [block.to_dict() for block in self.content]
        if self.is_error:
            result["is_error"] = self.is_error
        return result


@dataclass
class ImageBlock:
    """Image content block."""

    type: Literal["image"] = "image"
    source: ImageSource = field(default_factory=lambda: ImageSource())

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        return {"type": self.type, "source": self.source.to_dict()}


@dataclass
class ImageSource:
    """Image source details."""

    type: Literal["base64", "url"] = "base64"
    media_type: str = "image/png"
    data: str = ""
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        if self.type == "base64":
            return {
                "type": self.type,
                "media_type": self.media_type,
                "data": self.data,
            }
        return {"type": self.type, "url": self.url}


@dataclass
class DocumentBlock:
    """Document content block (PDF, etc.)."""

    type: Literal["document"] = "document"
    source: DocumentSource = field(default_factory=lambda: DocumentSource())

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        return {"type": self.type, "source": self.source.to_dict()}


@dataclass
class DocumentSource:
    """Document source details."""

    type: Literal["base64", "url"] = "base64"
    media_type: str = "application/pdf"
    data: str = ""
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        if self.type == "base64":
            return {
                "type": self.type,
                "media_type": self.media_type,
                "data": self.data,
            }
        return {"type": self.type, "url": self.url}


# Union type for all content blocks
ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock | ImageBlock | DocumentBlock


@dataclass
class Usage:
    """Token usage information."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, int]:
        """Convert to dict."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
        }


@dataclass
class ApiConfig:
    """API configuration."""

    api_key: str = ""
    base_url: str = "https://api.anthropic.com"
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 16384
    temperature: float = 1.0
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: list[str] = field(default_factory=list)
    system: str = ""
    betas: list[str] = field(default_factory=list)
    timeout_ms: int = 600000

    @classmethod
    def from_env(cls) -> ApiConfig:
        """Create config from environment variables."""
        import os

        return cls(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        )


@dataclass
class ApiResponse:
    """API response."""

    id: str = ""
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: list[ContentBlock] = field(default_factory=list)
    model: str = ""
    stop_reason: StopReason | None = None
    stop_sequence: str | None = None
    usage: Usage = field(default_factory=Usage)

    def get_text(self) -> str:
        """Extract all text content from the response."""
        texts = []
        for block in self.content:
            if isinstance(block, TextBlock):
                texts.append(block.text)
        return "".join(texts)

    def get_tool_uses(self) -> list[ToolUseBlock]:
        """Extract all tool use blocks from the response."""
        return [block for block in self.content if isinstance(block, ToolUseBlock)]

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        return {
            "id": self.id,
            "type": self.type,
            "role": self.role,
            "content": [block.to_dict() if hasattr(block, "to_dict") else block for block in self.content],
            "model": self.model,
            "stop_reason": self.stop_reason,
            "stop_sequence": self.stop_sequence,
            "usage": self.usage.to_dict(),
        }


@dataclass
class MessageParam:
    """Message parameter for API request."""

    role: Literal["user", "assistant"]
    content: str | list[ContentBlock]

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        if isinstance(self.content, str):
            return {"role": self.role, "content": self.content}
        return {
            "role": self.role,
            "content": [block.to_dict() if hasattr(block, "to_dict") else block for block in self.content],
        }


@dataclass
class ToolDefinition:
    """Tool definition for API request."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    cache_control: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        result: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }
        if self.cache_control:
            result["cache_control"] = self.cache_control
        return result


@dataclass
class ToolChoice:
    """Tool choice configuration."""

    type: Literal["auto", "any", "tool"] = "auto"
    name: str | None = None
    disable_parallel_tool_use: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to API-compatible dict."""
        if self.type == "tool" and self.name:
            result: dict[str, Any] = {"type": self.type, "name": self.name}
        else:
            result = {"type": self.type}
        if self.disable_parallel_tool_use:
            result["disable_parallel_tool_use"] = self.disable_parallel_tool_use
        return result
