"""Output from tools/GlobTool/GlobTool.ts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GlobOutputModel:
    duration_ms: float
    num_files: int
    filenames: list[str]
    truncated: bool
