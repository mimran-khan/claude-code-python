"""
SDK type definitions.

Types for SDK/API integration.

Migrated from: entrypoints/agentSdkTypes.ts + sandboxTypes.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class SDKUsage:
    """Token usage from an SDK request."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class SDKConfig:
    """Configuration for SDK requests."""

    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 1.0
    system_prompt: str | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)

    # Session configuration
    session_id: str | None = None
    resume_session: bool = False

    # Permissions
    allowed_tools: list[str] = field(default_factory=list)
    denied_tools: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)

    # Callbacks
    on_message: callable | None = None
    on_tool_use: callable | None = None
    on_error: callable | None = None


ContentBlockType = Literal["text", "tool_use", "tool_result", "image"]


@dataclass
class SDKContentBlock:
    """A content block in an SDK message."""

    type: ContentBlockType
    text: str | None = None
    tool_use_id: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_result: str | None = None
    is_error: bool = False


@dataclass
class SDKMessage:
    """A message in an SDK conversation."""

    role: Literal["user", "assistant"]
    content: list[SDKContentBlock] = field(default_factory=list)

    @staticmethod
    def user(text: str) -> SDKMessage:
        """Create a user message."""
        return SDKMessage(
            role="user",
            content=[SDKContentBlock(type="text", text=text)],
        )

    @staticmethod
    def assistant(text: str) -> SDKMessage:
        """Create an assistant message."""
        return SDKMessage(
            role="assistant",
            content=[SDKContentBlock(type="text", text=text)],
        )


@dataclass
class SDKResponse:
    """Response from an SDK request."""

    message: SDKMessage
    usage: SDKUsage = field(default_factory=SDKUsage)
    stop_reason: str | None = None
    session_id: str | None = None

    @property
    def text(self) -> str:
        """Get the text content of the response."""
        texts = []
        for block in self.message.content:
            if block.type == "text" and block.text:
                texts.append(block.text)
        return "".join(texts)

    @property
    def tool_calls(self) -> list[SDKContentBlock]:
        """Get tool use blocks."""
        return [block for block in self.message.content if block.type == "tool_use"]


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    enabled: bool = False
    network_access: bool = False
    file_system_access: bool = True
    max_execution_time: int = 300  # seconds
    max_memory: int = 512  # MB
    allowed_paths: list[str] = field(default_factory=list)


@dataclass
class SDKError:
    """Error from SDK operations."""

    code: str
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result
