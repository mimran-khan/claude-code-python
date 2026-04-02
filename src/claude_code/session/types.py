"""
Session Types.

Type definitions for session storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    pass

# Message types
MessageRole = Literal["user", "assistant", "system"]


@dataclass
class SerializedMessage:
    """A serialized message for storage."""

    role: MessageRole
    content: str | list[dict[str, Any]]
    uuid: str = ""
    timestamp: float = 0.0

    # Optional metadata
    model: str | None = None
    tool_use_id: str | None = None
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }

        if self.uuid:
            result["uuid"] = self.uuid
        if self.timestamp:
            result["timestamp"] = self.timestamp
        if self.model:
            result["model"] = self.model
        if self.tool_use_id:
            result["tool_use_id"] = self.tool_use_id
        if self.is_error:
            result["is_error"] = self.is_error

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SerializedMessage:
        """Create from dictionary."""
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            uuid=data.get("uuid", ""),
            timestamp=data.get("timestamp", 0.0),
            model=data.get("model"),
            tool_use_id=data.get("tool_use_id"),
            is_error=data.get("is_error", False),
        )


@dataclass
class TranscriptEntry:
    """A transcript entry with metadata."""

    type: Literal["message", "tool_use", "tool_result", "system", "compact_marker"]
    message: SerializedMessage | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "type": self.type,
            "timestamp": self.timestamp,
        }

        if self.message:
            result["message"] = self.message.to_dict()
        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TranscriptEntry:
        """Create from dictionary."""
        message = None
        if "message" in data:
            message = SerializedMessage.from_dict(data["message"])

        return cls(
            type=data.get("type", "message"),
            message=message,
            timestamp=data.get("timestamp", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PersistedSession:
    """A persisted session with metadata."""

    session_id: str
    project_dir: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    title: str = ""

    # Session configuration
    model: str = ""
    system_prompt: str = ""

    # Session state
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    num_turns: int = 0

    # Worktree info (for git)
    worktree_id: str | None = None
    branch: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "session_id": self.session_id,
            "project_dir": self.project_dir,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        if self.title:
            result["title"] = self.title
        if self.model:
            result["model"] = self.model
        if self.system_prompt:
            result["system_prompt"] = self.system_prompt

        result["total_cost_usd"] = self.total_cost_usd
        result["total_input_tokens"] = self.total_input_tokens
        result["total_output_tokens"] = self.total_output_tokens
        result["num_turns"] = self.num_turns

        if self.worktree_id:
            result["worktree_id"] = self.worktree_id
        if self.branch:
            result["branch"] = self.branch

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersistedSession:
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", ""),
            project_dir=data.get("project_dir", ""),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
            title=data.get("title", ""),
            model=data.get("model", ""),
            system_prompt=data.get("system_prompt", ""),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            total_input_tokens=data.get("total_input_tokens", 0),
            total_output_tokens=data.get("total_output_tokens", 0),
            num_turns=data.get("num_turns", 0),
            worktree_id=data.get("worktree_id"),
            branch=data.get("branch"),
        )
