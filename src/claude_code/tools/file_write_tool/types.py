"""Output schema from tools/FileWriteTool/FileWriteTool.ts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..file_edit_tool.types import GitDiffInfo, StructuredPatchHunk


@dataclass
class FileWriteOutputModel:
    type: Literal["create", "update"]
    file_path: str
    content: str
    structured_patch: list[StructuredPatchHunk] = field(default_factory=list)
    original_file: str | None = None
    git_diff: GitDiffInfo | None = None
