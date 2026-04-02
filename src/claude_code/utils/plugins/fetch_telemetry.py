"""
Telemetry for plugin/marketplace network fetches.

Migrated from: utils/plugins/fetchTelemetry.ts
"""

from __future__ import annotations

import re
from typing import Final, Literal
from urllib.parse import urlparse

from claude_code.services.analytics.events import log_event

from .official_marketplace import OFFICIAL_MARKETPLACE_NAME

PluginFetchSource = Literal[
    "install_counts",
    "marketplace_clone",
    "marketplace_pull",
    "marketplace_url",
    "plugin_clone",
    "mcpb",
    "marketplace_gcs",
]

PluginFetchOutcome = Literal["success", "failure", "cache_hit"]

KNOWN_PUBLIC_HOSTS: Final[frozenset[str]] = frozenset(
    {
        "github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com",
        "gist.githubusercontent.com",
        "gitlab.com",
        "bitbucket.org",
        "codeberg.org",
        "dev.azure.com",
        "ssh.dev.azure.com",
        "storage.googleapis.com",
        "downloads.claude.ai",
    }
)


def _extract_host(url_or_spec: str) -> str:
    scp_match = re.match(r"^[^@/]+@([^:/]+):", url_or_spec)
    if scp_match:
        normalized = scp_match.group(1).lower()
        return normalized if normalized in KNOWN_PUBLIC_HOSTS else "other"
    try:
        host = urlparse(url_or_spec).hostname or ""
    except ValueError:
        return "unknown"
    if not host:
        return "unknown"
    normalized = host.lower()
    return normalized if normalized in KNOWN_PUBLIC_HOSTS else "other"


def _is_official_repo(url_or_spec: str) -> bool:
    return f"anthropics/{OFFICIAL_MARKETPLACE_NAME}" in url_or_spec


def log_plugin_fetch(
    source: PluginFetchSource,
    url_or_spec: str | None,
    outcome: PluginFetchOutcome,
    duration_ms: float,
    error_kind: str | None = None,
) -> None:
    payload: dict[str, object] = {
        "source": source,
        "host": _extract_host(url_or_spec) if url_or_spec else "unknown",
        "is_official": _is_official_repo(url_or_spec) if url_or_spec else False,
        "outcome": outcome,
        "duration_ms": round(duration_ms),
    }
    if error_kind:
        payload["error_kind"] = error_kind
    log_event("tengu_plugin_remote_fetch", payload)


def classify_fetch_error(error: BaseException | object) -> str:
    msg = str(getattr(error, "message", error))
    if re.search(
        r"ENOTFOUND|ECONNREFUSED|EAI_AGAIN|Could not resolve host|Connection refused",
        msg,
        re.I,
    ):
        return "dns_or_refused"
    if re.search(r"ETIMEDOUT|timed out|timeout", msg, re.I):
        return "timeout"
    if re.search(
        r"ECONNRESET|socket hang up|Connection reset by peer|remote end hung up",
        msg,
        re.I,
    ):
        return "conn_reset"
    if re.search(r"403|401|authentication|permission denied", msg, re.I):
        return "auth"
    if re.search(r"404|not found|repository not found", msg, re.I):
        return "not_found"
    if re.search(r"certificate|SSL|TLS|unable to get local issuer", msg, re.I):
        return "tls"
    if re.search(r"Invalid response format|Invalid marketplace schema", msg, re.I):
        return "invalid_schema"
    return "other"


__all__ = [
    "PluginFetchOutcome",
    "PluginFetchSource",
    "classify_fetch_error",
    "log_plugin_fetch",
]
