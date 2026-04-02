"""Types for FileSearch tool."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FileSearchHit:
    path: str
    score: float | None = None
    snippet: str | None = None


@dataclass
class FileSearchOutput:
    query: str
    hits: list[FileSearchHit]
