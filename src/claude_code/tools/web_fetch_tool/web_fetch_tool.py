"""
Web Fetch Tool implementation.

Migrated from: tools/WebFetchTool/WebFetchTool.ts
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from ..base import Tool, ToolResult, ToolUseContext
from .preapproved_hosts import is_preapproved_host

WEB_FETCH_TOOL_NAME = "WebFetch"

WEB_FETCH_DESCRIPTION = """- Fetches content from a specified URL and processes it with the given prompt
- Takes a URL and a prompt as input
- Fetches the URL content, converts HTML to markdown when applicable
- Use this tool when you need to retrieve and analyze web content

Usage notes:
  - The URL must be a fully-formed valid URL
  - The prompt should describe what information you want to extract from the page
  - This tool is read-only and does not modify any files
"""

WEB_FETCH_PROMPT_PREFIX = """IMPORTANT: WebFetch WILL FAIL for authenticated or private URLs. Before using this tool, check if the URL points to an authenticated service (e.g. Google Docs, Confluence, Jira, GitHub). If so, look for a specialized MCP tool that provides authenticated access.
"""


@dataclass
class WebFetchInput:
    """Input matching TypeScript WebFetch strictObject schema."""

    url: str
    prompt: str


@dataclass
class WebFetchExecuteOutput:
    """Output matching TypeScript WebFetch tool output."""

    bytes: int
    code: int
    codeText: str
    result: str
    durationMs: int
    url: str


class WebFetchTool(Tool[dict[str, Any], dict[str, Any]]):
    """Fetch a URL and return markdown-oriented content plus prompt context."""

    @property
    def name(self) -> str:
        return WEB_FETCH_TOOL_NAME

    @property
    def search_hint(self) -> str | None:
        return "fetch and extract content from a URL"

    async def description(self) -> str:
        return WEB_FETCH_DESCRIPTION.strip()

    async def prompt(self) -> str:
        return f"{WEB_FETCH_PROMPT_PREFIX}{WEB_FETCH_DESCRIPTION.strip()}"

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch content from"},
                "prompt": {
                    "type": "string",
                    "description": "What to extract or summarize from the fetched content",
                },
            },
            "required": ["url", "prompt"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "bytes": {"type": "integer"},
                "code": {"type": "integer"},
                "codeText": {"type": "string"},
                "result": {"type": "string"},
                "durationMs": {"type": "integer"},
                "url": {"type": "string"},
            },
            "required": ["bytes", "code", "codeText", "result", "durationMs", "url"],
        }

    def user_facing_name(self, input: dict[str, Any] | None = None) -> str:
        return "Fetch"

    def get_tool_use_summary(self, input: dict[str, Any] | None = None) -> str | None:
        if not input:
            return None
        u = input.get("url")
        return str(u) if u else None

    def get_activity_description(self, input: dict[str, Any] | None = None) -> str:
        s = self.get_tool_use_summary(input)
        return f"Fetching {s}" if s else "Fetching web page"

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        return await fetch_url_with_prompt(input, context)


def _html_to_markdown(html: str) -> str:
    import re

    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>", r"[\2](\1)", html, flags=re.IGNORECASE)
    html = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", html, flags=re.IGNORECASE)
    html = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", html, flags=re.IGNORECASE)
    html = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", html, flags=re.IGNORECASE)
    html = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", html, flags=re.IGNORECASE)
    html = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", "", html)
    for a, b in (
        ("&nbsp;", " "),
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
    ):
        html = html.replace(a, b)
    html = re.sub(r"\n\s*\n", "\n\n", html)
    return html.strip()


async def fetch_url(
    input: dict[str, Any],
    context: ToolUseContext,
) -> ToolResult:
    """Backward-compatible fetch: if only url is provided, uses empty prompt."""
    data = dict(input)
    if "prompt" not in data:
        data["prompt"] = "Summarize the main content of this page."
    return await fetch_url_with_prompt(data, context)


async def fetch_url_with_prompt(
    input: dict[str, Any],
    context: ToolUseContext,
) -> ToolResult:
    _ = context
    url = str(input.get("url", "")).strip()
    prompt = str(input.get("prompt", "")).strip()

    if not url or not prompt:
        return ToolResult(
            success=False,
            error='Both "url" and "prompt" are required.',
            error_code=1,
        )

    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("invalid url")
    except Exception:
        return ToolResult(
            success=False,
            error=f'Error: Invalid URL "{url}". The URL provided could not be parsed.',
            error_code=1,
        )

    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1", "::1"}:
        return ToolResult(success=False, error="Cannot fetch from localhost", error_code=1)

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
    except httpx.TimeoutException:
        return ToolResult(success=False, error="Request timed out", error_code=1)
    except httpx.HTTPError as e:
        return ToolResult(success=False, error=str(e), error_code=1)

    code = response.status_code
    code_text = getattr(response, "reason_phrase", None) or ""
    if not code_text:
        code_text = "OK" if code == 200 else "Error"

    content_type = response.headers.get("content-type", "")
    if any(t in content_type for t in ("image/", "audio/", "video/", "application/octet-stream")):
        return ToolResult(success=False, error="Binary content not supported in this migration path", error_code=1)

    body = response.text
    if "text/html" in content_type:
        body = _html_to_markdown(body)

    preapproved = is_preapproved_host(host, parsed.path or "/")
    if preapproved and "text/markdown" in content_type and len(body) < 100_000:
        result = body
    else:
        excerpt = body if len(body) <= 24_000 else body[:24_000] + "\n\n[Truncated…]"
        result = (
            f"## Extracted content\n{excerpt}\n\n---\n## Requested focus\n{prompt}\n\n"
            "_Note: Wire an LLM call to mirror full TS `applyPromptToMarkdown`._"
        )

    out = WebFetchExecuteOutput(
        bytes=len(result.encode("utf-8")),
        code=code,
        codeText=code_text,
        result=result,
        durationMs=int((time.monotonic() - start) * 1000),
        url=str(response.url),
    )
    ok = 200 <= code < 400
    return ToolResult(
        success=ok,
        output=asdict(out),
        error=None if ok else code_text,
    )
