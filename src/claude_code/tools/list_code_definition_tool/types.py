"""Symbol listing types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeDefinition:
    name: str
    kind: str
    location: str
    detail: str | None = None
    children: list[CodeDefinition] = field(default_factory=list)


@dataclass
class ListCodeDefinitionOutput:
    file_path: str
    symbols: list[CodeDefinition]
    raw: dict[str, Any] | None = None
