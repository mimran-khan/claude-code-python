"""Synthetic structured output tool (package name mirrors TS SyntheticOutputTool)."""

from __future__ import annotations

from ..synthetic_output.synthetic_output_tool import (
    SYNTHETIC_OUTPUT_TOOL_NAME,
    CreateSyntheticOutputToolResult,
    SyntheticOutputTool,
    SyntheticStructuredResult,
    create_synthetic_output_tool,
    is_synthetic_output_tool_enabled,
)

__all__ = [
    "SYNTHETIC_OUTPUT_TOOL_NAME",
    "CreateSyntheticOutputToolResult",
    "SyntheticOutputTool",
    "SyntheticStructuredResult",
    "create_synthetic_output_tool",
    "is_synthetic_output_tool_enabled",
]
