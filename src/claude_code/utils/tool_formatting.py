"""
Tool / CLI output formatting helpers.

TS `toolFormatting.ts` not present in tree; re-exports terminal preview helpers.
"""

from .terminal_render import (
    ctrl_o_to_expand,
    is_output_line_truncated,
    render_truncated_content,
)

__all__ = [
    "ctrl_o_to_expand",
    "is_output_line_truncated",
    "render_truncated_content",
]
