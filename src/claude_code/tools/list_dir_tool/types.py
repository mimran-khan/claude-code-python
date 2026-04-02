"""Directory listing types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DirEntry:
    name: str
    path: str
    is_directory: bool
    size_bytes: int | None = None


@dataclass
class ListDirOutput:
    directory: str
    entries: list[DirEntry]
