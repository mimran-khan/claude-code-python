"""Dataclasses mirroring tools/FileEditTool/types.ts (Zod schemas)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StructuredPatchHunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: list[str] = field(default_factory=list)


@dataclass
class GitDiffInfo:
    filename: str
    status: str  # "modified" | "added"
    additions: int
    deletions: int
    changes: int
    patch: str
    repository: str | None = None


@dataclass
class FileEditInputModel:
    """Logical input; tool uses dict[str, Any] at boundary for JSON schema."""

    file_path: str
    old_string: str
    new_string: str
    replace_all: bool = False


@dataclass
class FileEditRecord:
    """Single edit without file_path (EditInput in TS)."""

    old_string: str
    new_string: str
    replace_all: bool = False


@dataclass
class FileEditOutputModel:
    file_path: str
    old_string: str
    new_string: str
    original_file: str
    structured_patch: list[StructuredPatchHunk]
    user_modified: bool
    replace_all: bool
    git_diff: GitDiffInfo | None = None
