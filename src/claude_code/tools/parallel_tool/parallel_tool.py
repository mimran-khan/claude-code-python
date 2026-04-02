"""
Parallel HTTP fetches (batch WebFetch-style operations).

No direct TS `ParallelTool` in the leaked tree; this supports concurrent URL reads.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from ..base import Tool, ToolResult, ToolUseContext

PARALLEL_TOOL_NAME = "Parallel"


@dataclass
class ParallelUrlResult:
    url: str
    ok: bool
    status_code: int
    excerpt: str
    error: str | None = None


@dataclass
class ParallelToolOutput:
    duration_ms: int
    results: list[dict[str, Any]]


class ParallelTool(Tool[dict[str, Any], dict[str, Any]]):
    """Fetch multiple URLs concurrently (read-only, text/HTML)."""

    @property
    def name(self) -> str:
        return PARALLEL_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "parallel web fetches, batch URL retrieval"

    async def description(self) -> str:
        return (
            "Fetch multiple public URLs in parallel and return short text excerpts. "
            "Blocks localhost and private-network targets."
        )

    async def prompt(self) -> str:
        return await self.description()

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 16,
                    "description": "Fully-qualified HTTP(S) URLs",
                },
                "max_chars_per_url": {
                    "type": "integer",
                    "description": "Truncate each body to this many characters",
                    "default": 8000,
                },
            },
            "required": ["urls"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": True}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        _ = context
        urls = input.get("urls") or []
        if not isinstance(urls, list) or not urls:
            return ToolResult(success=False, error="urls must be a non-empty list")
        max_chars = int(input.get("max_chars_per_url") or 8000)
        max_chars = max(500, min(max_chars, 50_000))

        for u in urls:
            if not isinstance(u, str):
                return ToolResult(success=False, error="each url must be a string")
            try:
                p = urlparse(u)
                h = p.hostname or ""
                if h in {"localhost", "127.0.0.1", "::1"} or not p.scheme.startswith("http"):
                    return ToolResult(success=False, error=f"URL not allowed: {u}")
            except Exception:
                return ToolResult(success=False, error=f"Invalid URL: {u}")

        start = time.monotonic()

        async def one(url: str) -> ParallelUrlResult:
            try:
                async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                    r = await client.get(url)
                text = r.text
                if len(text) > max_chars:
                    text = text[:max_chars] + "\n[truncated]"
                return ParallelUrlResult(
                    url=str(r.url),
                    ok=200 <= r.status_code < 400,
                    status_code=r.status_code,
                    excerpt=text,
                    error=None if 200 <= r.status_code < 400 else r.reason_phrase,
                )
            except Exception as e:
                return ParallelUrlResult(
                    url=url,
                    ok=False,
                    status_code=0,
                    excerpt="",
                    error=str(e),
                )

        results = await asyncio.gather(*[one(str(u)) for u in urls])
        out = ParallelToolOutput(
            duration_ms=int((time.monotonic() - start) * 1000),
            results=[asdict(x) for x in results],
        )
        return ToolResult(success=True, output=asdict(out))
