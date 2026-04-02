"""Org-level metrics logging opt-out (Anthropic API)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

from ...utils.http import get_auth_headers, get_user_agent

logger = structlog.get_logger(__name__)


@dataclass
class MetricsStatus:
    enabled: bool
    has_error: bool


async def _fetch_metrics_enabled() -> dict[str, bool]:
    auth = get_auth_headers()
    if auth.error:
        raise RuntimeError(auth.error)
    headers = {"Content-Type": "application/json", "User-Agent": get_user_agent(), **auth.headers}
    url = "https://api.anthropic.com/api/claude_code/organizations/metrics_enabled"
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        d = r.json()
    if not isinstance(d, dict):
        return {"metrics_logging_enabled": False}
    return {"metrics_logging_enabled": bool(d.get("metrics_logging_enabled", False))}


async def check_metrics_enabled_api() -> MetricsStatus:
    try:
        data = await _fetch_metrics_enabled()
        enabled = data.get("metrics_logging_enabled", False)
        logger.debug("metrics_opt_out", enabled=enabled)
        return MetricsStatus(enabled=enabled, has_error=False)
    except Exception as e:
        logger.debug("metrics_opt_out_failed", error=str(e))
        return MetricsStatus(enabled=False, has_error=True)
