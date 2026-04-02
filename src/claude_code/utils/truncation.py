"""Width-aware truncation (TS: truncate.ts). Re-exports `truncate` utilities."""

from .truncate import (
    string_width,
    truncate,
    truncate_path_middle,
    truncate_start_to_width,
    truncate_to_width,
    truncate_to_width_no_ellipsis,
    wrap_text,
)

__all__ = [
    "string_width",
    "truncate",
    "truncate_path_middle",
    "truncate_start_to_width",
    "truncate_to_width",
    "truncate_to_width_no_ellipsis",
    "wrap_text",
]
