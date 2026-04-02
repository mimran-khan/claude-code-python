"""Anthropic official MCP registry URL prefetch.

Migrated from: services/mcp/officialRegistry.ts
"""

from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse

import httpx
import structlog

logger = structlog.get_logger(__name__)

_official_urls: set[str] | None = None


def _normalize_url(url: str) -> str | None:
    try:
        p = urlparse(url)
        clean = p._replace(query="")
        s = urlunparse(clean).rstrip("/")
        return s
    except Exception:
        return None


async def prefetch_official_mcp_urls() -> None:
    global _official_urls
    if os.environ.get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return
    url = "https://api.anthropic.com/mcp-registry/v0/servers?version=latest&visibility=commercial"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            payload = r.json()
    except Exception as exc:
        logger.debug("official_mcp_registry_fetch_failed", error=str(exc))
        return
    if not isinstance(payload, dict):
        return
    servers = payload.get("servers", [])
    if not isinstance(servers, list):
        return
    urls: set[str] = set()
    for entry in servers:
        if not isinstance(entry, dict):
            continue
        srv = entry.get("server", {})
        if not isinstance(srv, dict):
            continue
        remotes = srv.get("remotes", [])
        if not isinstance(remotes, list):
            continue
        for remote in remotes:
            if isinstance(remote, dict):
                u = remote.get("url")
                if isinstance(u, str):
                    n = _normalize_url(u)
                    if n:
                        urls.add(n)
    _official_urls = urls


def is_official_mcp_url(candidate: str) -> bool:
    if _official_urls is None:
        return False
    n = _normalize_url(candidate)
    return n in _official_urls if n else False
