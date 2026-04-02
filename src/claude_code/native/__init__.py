"""
Native module implementations.

Pure Python ports of native modules that were originally written in Rust.

Migrated from: native-ts/*.ts
"""

from .color_diff import (
    ColorDiff,
    ColorFile,
    Hunk,
    get_syntax_theme,
)
from .file_index import (
    FileIndex,
    SearchResult,
)

__all__ = [
    # File index
    "FileIndex",
    "SearchResult",
    # Color diff
    "ColorDiff",
    "ColorFile",
    "Hunk",
    "get_syntax_theme",
]
