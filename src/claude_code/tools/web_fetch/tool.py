"""
Web Fetch Tool Implementation.

Fetches content from URLs and processes it.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import DESCRIPTION, WEB_FETCH_TOOL_NAME


class WebFetchInput(BaseModel):
    """Input parameters for web fetch tool."""

    url: str = Field(
        ...,
        description="The URL to fetch content from.",
    )
    prompt: str = Field(
        default="Summarize this page.",
        description="What to extract or analyze from the page content.",
    )


@dataclass
class WebFetchSuccess:
    """Successful web fetch result."""

    type: Literal["success"] = "success"
    url: str = ""
    content: str = ""
    cached: bool = False


@dataclass
class WebFetchRedirect:
    """Redirect response."""

    type: Literal["redirect"] = "redirect"
    original_url: str = ""
    redirect_url: str = ""
    message: str = ""


@dataclass
class WebFetchError:
    """Failed web fetch result."""

    type: Literal["error"] = "error"
    url: str = ""
    error: str = ""


WebFetchOutput = WebFetchSuccess | WebFetchRedirect | WebFetchError


# Simple cache for fetched content
_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 15 * 60  # 15 minutes


def _get_cache_key(url: str) -> str:
    """Generate cache key for a URL."""
    return hashlib.sha256(url.encode()).hexdigest()


def _get_cached(url: str) -> str | None:
    """Get cached content if available and not expired."""
    key = _get_cache_key(url)
    if key in _cache:
        content, timestamp = _cache[key]
        if time.time() - timestamp < _CACHE_TTL:
            return content
        # Expired, remove
        del _cache[key]
    return None


def _set_cached(url: str, content: str) -> None:
    """Cache content for a URL."""
    key = _get_cache_key(url)
    _cache[key] = (content, time.time())

    # Clean old entries
    now = time.time()
    expired = [k for k, (_, ts) in _cache.items() if now - ts >= _CACHE_TTL]
    for k in expired:
        del _cache[k]


# Pre-approved domains that have less restrictive content handling
PREAPPROVED_DOMAINS = frozenset(
    {
        "docs.anthropic.com",
        "anthropic.com",
        "github.com",
        "raw.githubusercontent.com",
        "docs.python.org",
        "pypi.org",
        "npmjs.com",
        "docs.rs",
        "crates.io",
        "developer.mozilla.org",
        "stackoverflow.com",
        "docs.github.com",
    }
)


def is_preapproved_domain(url: str) -> bool:
    """Check if URL is from a pre-approved domain."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        # Check exact match or subdomain match
        return any(host == domain or host.endswith(f".{domain}") for domain in PREAPPROVED_DOMAINS)
    except Exception:
        return False


class WebFetchTool(Tool[WebFetchInput, WebFetchOutput]):
    """
    Tool for fetching and processing web content.

    Fetches URLs, converts HTML to markdown, and processes
    the content using a secondary model.
    """

    @property
    def name(self) -> str:
        return WEB_FETCH_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch content from.",
                },
                "prompt": {
                    "type": "string",
                    "description": "What to extract or analyze from the page content.",
                    "default": "Summarize this page.",
                },
            },
            "required": ["url"],
        }

    def is_read_only(self, input_data: WebFetchInput) -> bool:
        return True

    async def call(
        self,
        input_data: WebFetchInput,
        context: Any,
    ) -> ToolResult[WebFetchOutput]:
        """Execute the web fetch operation."""
        url = input_data.url

        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                url = f"https://{url}"
                parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                return ToolResult(
                    success=False,
                    output=WebFetchError(
                        url=url,
                        error=f"Invalid URL scheme: {parsed.scheme}. Only http and https are supported.",
                    ),
                )

            # Upgrade HTTP to HTTPS
            if parsed.scheme == "http":
                url = url.replace("http://", "https://", 1)

        except Exception as e:
            return ToolResult(
                success=False,
                output=WebFetchError(
                    url=url,
                    error=f"Invalid URL: {e}",
                ),
            )

        # Check cache
        cached_content = _get_cached(url)
        if cached_content is not None:
            return ToolResult(
                success=True,
                output=WebFetchSuccess(
                    url=url,
                    content=cached_content,
                    cached=True,
                ),
            )

        # Fetch content
        try:
            import httpx

            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                response = await client.get(url)

                # Check for cross-domain redirect
                final_url = str(response.url)
                if final_url != url:
                    original_host = urlparse(url).netloc
                    final_host = urlparse(final_url).netloc
                    if original_host != final_host:
                        return ToolResult(
                            success=True,
                            output=WebFetchRedirect(
                                original_url=url,
                                redirect_url=final_url,
                                message=(
                                    f"The URL redirected to a different host. "
                                    f"Please make a new request with: {final_url}"
                                ),
                            ),
                        )

                response.raise_for_status()
                content = response.text

        except ImportError:
            return ToolResult(
                success=False,
                output=WebFetchError(
                    url=url,
                    error="httpx not installed. Run: pip install httpx",
                ),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=WebFetchError(
                    url=url,
                    error=f"Failed to fetch URL: {e}",
                ),
            )

        # Convert HTML to markdown (simplified)
        markdown_content = _html_to_markdown(content)

        # Cache the result
        _set_cached(url, markdown_content)

        # For now, return the content directly
        # In full implementation, this would call a secondary model
        return ToolResult(
            success=True,
            output=WebFetchSuccess(
                url=url,
                content=markdown_content[:50000],  # Limit size
                cached=False,
            ),
        )

    def user_facing_name(self, input_data: WebFetchInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        return "Fetch"

    def get_tool_use_summary(self, input_data: WebFetchInput | None) -> str | None:
        """Get a short summary of this tool use."""
        if input_data and input_data.url:
            try:
                parsed = urlparse(input_data.url)
                return parsed.netloc or input_data.url[:50]
            except Exception:
                return input_data.url[:50]
        return None

    def get_activity_description(self, input_data: WebFetchInput | None) -> str | None:
        """Get a human-readable activity description."""
        if input_data and input_data.url:
            return f"Fetching {input_data.url[:50]}"
        return "Fetching URL"


def _html_to_markdown(html: str) -> str:
    """Simple HTML to text/markdown conversion.

    In a full implementation, this would use a proper library
    like html2text or markdownify.
    """
    import re

    # Remove script and style elements
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # Replace common elements
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<p[^>]*>", "\n\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</p>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n\n# \1\n\n", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(
        r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        r"[\2](\1)",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<pre[^>]*>(.*?)</pre>", r"\n```\n\1\n```\n", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", html, flags=re.DOTALL | re.IGNORECASE)

    # Remove remaining tags
    html = re.sub(r"<[^>]+>", "", html)

    # Decode HTML entities
    html = html.replace("&nbsp;", " ")
    html = html.replace("&lt;", "<")
    html = html.replace("&gt;", ">")
    html = html.replace("&amp;", "&")
    html = html.replace("&quot;", '"')
    html = html.replace("&#39;", "'")

    # Clean up whitespace
    html = re.sub(r"\n\s*\n\s*\n", "\n\n", html)
    html = html.strip()

    return html
