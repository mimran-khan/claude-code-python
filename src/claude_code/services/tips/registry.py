"""Tip registry for storing and retrieving tips."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TipContext:
    """Context for tip evaluation."""

    bash_tools: list[str] | None = None
    current_model: str | None = None
    has_file_history: bool = False
    platform: str | None = None


@dataclass
class Tip:
    """A tip to show to users."""

    id: str
    message: str
    category: str = "general"
    priority: int = 0
    min_sessions: int = 0
    max_shows: int = 3
    condition: Callable[[TipContext], bool] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Global tip registry
_tips: dict[str, Tip] = {}


def register_tip(tip: Tip) -> None:
    """Register a tip."""
    _tips[tip.id] = tip


def get_tip_by_id(tip_id: str) -> Tip | None:
    """Get a tip by ID."""
    return _tips.get(tip_id)


def get_all_tips() -> list[Tip]:
    """Get all registered tips."""
    return list(_tips.values())


def clear_tips() -> None:
    """Clear all tips (for testing)."""
    _tips.clear()


# Register default tips
def _register_default_tips() -> None:
    """Register built-in tips."""
    tips = [
        Tip(
            id="keyboard_shortcuts",
            message="Press Ctrl+K to see available keyboard shortcuts",
            category="productivity",
            priority=1,
        ),
        Tip(
            id="slash_commands",
            message="Type / to see available commands like /help, /clear, /model",
            category="productivity",
            priority=2,
        ),
        Tip(
            id="file_history",
            message="Enable file history to track changes: /config set fileHistory true",
            category="features",
            condition=lambda ctx: not ctx.has_file_history,
        ),
        Tip(
            id="todo_tracking",
            message="Use the TodoWrite tool to track tasks across sessions",
            category="productivity",
        ),
        Tip(
            id="parallel_tools",
            message="Multiple independent tool calls run in parallel for faster results",
            category="performance",
        ),
    ]

    for tip in tips:
        register_tip(tip)


_register_default_tips()
