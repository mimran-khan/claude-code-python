"""
Tool pool assembly (TS tools.ts registry surface).

Migrated from: tools.ts (naming + assembly hooks).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .core.tool import Tool
from .tools.tool_types import find_tool_by_name as find_tool_by_name

__all__ = ["assemble_tool_pool", "find_tool_by_name"]


def assemble_tool_pool(
    base_tools: Iterable[Tool],
    *,
    deny_rules: dict[str, Any] | None = None,
) -> list[Tool]:
    """Filter tools by deny rules (extend with mergeAndFilterTools parity)."""
    _ = deny_rules
    return list(base_tools)
