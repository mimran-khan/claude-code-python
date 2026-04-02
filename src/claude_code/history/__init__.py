"""
History Module.

Manages command and prompt history.
"""

from .history import (
    History,
    HistoryEntry,
    PastedContent,
    format_image_ref,
    format_pasted_text_ref,
    get_pasted_text_ref_num_lines,
    parse_references,
)

__all__ = [
    "History",
    "HistoryEntry",
    "PastedContent",
    "format_pasted_text_ref",
    "format_image_ref",
    "parse_references",
    "get_pasted_text_ref_num_lines",
]
