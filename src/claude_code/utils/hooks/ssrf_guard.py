"""
Basic SSRF guard for hook HTTP targets.

Migrated from: utils/hooks/ssrfGuard.ts (minimal allowlist).
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class SsrfCheckResult:
    allowed: bool
    reason: str | None = None


_BLOCKED_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})


def is_url_hook_safe(url: str, *, allow_private_ips: bool = False) -> SsrfCheckResult:
    try:
        parsed = urlparse(url)
    except Exception as e:
        return SsrfCheckResult(False, str(e))
    if parsed.scheme not in ("http", "https"):
        return SsrfCheckResult(False, "only http(s) URLs are allowed")
    host = (parsed.hostname or "").lower()
    if host in _BLOCKED_HOSTS:
        return SsrfCheckResult(False, "loopback host not allowed")
    if not allow_private_ips:
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return SsrfCheckResult(False, "private IP not allowed")
        except ValueError:
            pass
    return SsrfCheckResult(True, None)
