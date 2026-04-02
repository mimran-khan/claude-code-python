"""
Query engine type definitions.

Migrated from: QueryEngine.ts (partial - 1296 lines)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from ..types.message import Message


@dataclass
class QueryEngineConfig:
    """Configuration for the query engine."""

    # Model configuration
    model: str | None = None
    model_override: str | None = None

    # System prompt
    system_prompt: str | None = None
    additional_system_prompt: str | None = None

    # Tools
    tools: list[Any] = field(default_factory=list)
    disabled_tools: list[str] = field(default_factory=list)

    # Permissions
    permission_mode: Literal["default", "bypass", "plan", "agent"] = "default"

    # Behavior
    auto_mode: bool = False
    thinking_enabled: bool = False
    verbose_mode: bool = False

    # Session
    session_id: str | None = None
    parent_session_id: str | None = None

    # Callbacks
    on_message: Callable[[Message], None] | None = None
    on_error: Callable[[Exception], None] | None = None


@dataclass
class QueryState:
    """State for a query execution."""

    messages: list[Message] = field(default_factory=list)
    is_running: bool = False
    is_aborted: bool = False
    turn_count: int = 0
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


@dataclass
class QueryResult:
    """Result of a query execution."""

    messages: list[Message]
    final_message: Message | None = None
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    error: str | None = None
    aborted: bool = False


@dataclass
class TokenUsage:
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.input_tokens + self.output_tokens


@dataclass
class CostInfo:
    """Cost information for a query."""

    total_cost_usd: float = 0.0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    cache_read_cost_usd: float = 0.0
    cache_creation_cost_usd: float = 0.0
