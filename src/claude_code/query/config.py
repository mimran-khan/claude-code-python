"""
Query configuration.

Migrated from: query/config.ts
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryConfig:
    """Configuration for a query execution."""

    # Model settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 16384
    temperature: float = 0.7

    # Token budget
    token_budget: int | None = None

    # Tools
    tools: list[Any] = field(default_factory=list)
    tool_choice: str | None = None  # "auto", "none", "required", or tool name

    # System prompt
    system_prompt: str | None = None
    system_prompt_suffix: str | None = None

    # Metadata
    agent_id: str | None = None
    parent_agent_id: str | None = None

    # Callbacks
    on_message: Callable[[Any], None] | None = None
    on_tool_use: Callable[[Any], None] | None = None
    on_error: Callable[[Exception], None] | None = None

    # Limits
    max_turns: int = 100
    max_tool_uses_per_turn: int = 50

    # Features
    enable_thinking: bool = False
    enable_speculation: bool = False

    # Context
    context: dict[str, Any] = field(default_factory=dict)


def get_default_query_config() -> QueryConfig:
    """Get default query configuration."""
    return QueryConfig()


def build_query_config() -> QueryConfig:
    """Build query configuration for a run (alias for default until TS parity)."""
    return QueryConfig()
