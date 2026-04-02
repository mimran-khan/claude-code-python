"""Grep output (tools/GrepTool/GrepTool.ts outputSchema)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class GrepOutputModel:
    mode: Literal["content", "files_with_matches", "count"] | None
    num_files: int
    filenames: list[str]
    content: str | None = None
    num_lines: int | None = None
    num_matches: int | None = None
    applied_limit: int | None = None
    applied_offset: int | None = None
    output_truncated: bool = False
    stderr: str | None = None
