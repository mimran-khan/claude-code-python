"""
Typed input/output for WebFetch (TS schema parity).

Migrated from: tools/WebFetchTool/WebFetchTool.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WebFetchToolInput:
    """Validated input for WebFetch."""

    url: str
    prompt: str


@dataclass
class WebFetchToolOutput:
    """Output matching TypeScript outputSchema."""

    bytes: int
    code: int
    code_text: str
    result: str
    duration_ms: int
    url: str
