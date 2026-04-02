"""
Batch exporter for first-party internal analytics events.

Migrated from: services/analytics/firstPartyEventLoggingExporter.ts (subset).

Full TypeScript version includes disk-backed retry and OTEL integration; this
module provides HTTP batch POST via httpx for the Python port.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


def _default_spool_path() -> Path:
    override = os.environ.get("CLAUDE_ANALYTICS_SPOOL_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cache" / "claude-code-python" / "analytics_spool.jsonl"


@dataclass
class FirstPartyEventLoggingExporter:
    """POST JSON batches to ``/api/event_logging/batch``."""

    max_batch_size: int = 200
    timeout_s: float = 10.0
    skip_auth: bool = False
    path: str = "/api/event_logging/batch"
    base_url: str | None = None
    is_killed: Callable[[], bool] = field(default=lambda: False)
    spool_path: Path | None = None

    def __post_init__(self) -> None:
        if self.base_url is None:
            anth = os.environ.get("ANTHROPIC_BASE_URL", "")
            self.base_url = (
                "https://api-staging.anthropic.com"
                if anth == "https://api-staging.anthropic.com"
                else "https://api.anthropic.com"
            )

    @property
    def endpoint(self) -> str:
        base = self.base_url or "https://api.anthropic.com"
        return f"{base.rstrip('/')}{self.path}"

    def _persist_failed_batch(self, events: list[dict[str, Any]]) -> None:
        path = self.spool_path or _default_spool_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                for row in events:
                    f.write(json.dumps(row, default=str) + "\n")
            logger.info("first_party_export_spooled", path=str(path), count=len(events))
        except OSError as e:
            logger.warning("first_party_spool_failed", error=str(e))

    def export_batch(self, events: list[dict[str, Any]]) -> bool:
        """Send up to ``max_batch_size`` events. Returns True on HTTP success."""
        if self.is_killed() or not events:
            return True
        chunk = events[: self.max_batch_size]
        payload = {"events": chunk}
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if not self.skip_auth:
            from ...utils.http import get_auth_headers

            auth = get_auth_headers()
            if auth.error:
                logger.debug("first_party_export_skip_auth", error=auth.error)
            else:
                headers.update(auth.headers)
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                r = client.post(self.endpoint, json=payload, headers=headers)
                ok = r.is_success
                if not ok:
                    self._persist_failed_batch(chunk)
                return ok
        except Exception as e:
            logger.warning("first_party_export_failed", error=str(e))
            self._persist_failed_batch(chunk)
            return False
