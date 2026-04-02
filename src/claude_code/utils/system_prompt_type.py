"""
Branded system prompt list type (compile-time aid in TS; lightweight in Python).

Migrated from: utils/systemPromptType.ts
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NewType

SystemPrompt = NewType("SystemPrompt", tuple[str, ...])


def as_system_prompt(value: Sequence[str]) -> SystemPrompt:
    """Narrow a string sequence to ``SystemPrompt``."""

    return SystemPrompt(tuple(value))


__all__ = ["SystemPrompt", "as_system_prompt"]
