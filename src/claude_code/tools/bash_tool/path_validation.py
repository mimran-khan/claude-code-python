"""
Path-related validation for bash file operations.

Migrated from: tools/BashTool/pathValidation.ts

Delegates to :mod:`claude_code.utils.permissions.path_validation` for resolve/check helpers.
"""

from __future__ import annotations

from typing import Literal

from ...utils.permissions.path_validation import (
    expand_tilde,
    format_directory_list,
    is_path_allowed,
    resolve_and_check_path,
)

PathCommand = Literal[
    "cd",
    "ls",
    "find",
    "mkdir",
    "touch",
    "rm",
    "rmdir",
    "mv",
    "cp",
    "cat",
    "head",
    "tail",
    "sort",
    "uniq",
    "wc",
    "cut",
    "paste",
    "column",
    "tr",
    "file",
    "stat",
    "diff",
    "awk",
    "strings",
    "hexdump",
    "od",
    "base64",
    "nl",
    "grep",
    "rg",
    "sed",
    "git",
    "jq",
]

__all__ = [
    "PathCommand",
    "expand_tilde",
    "format_directory_list",
    "is_path_allowed",
    "resolve_and_check_path",
]
