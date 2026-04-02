"""
BigQuery / internal metrics HTTP exporter (OTEL metrics → JSON API).

Migrated from: utils/telemetry/bigqueryExporter.ts
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx
import structlog

from ..debug import log_for_debugging
from ..log import log_error

_log = structlog.get_logger("claude_code.telemetry.bigquery")

try:
    from opentelemetry.sdk.metrics.export import AggregationTemporality
except ImportError:

    class AggregationTemporality:  # type: ignore[no-redef]
        DELTA = 1


ExportResultCallback = Callable[[Any], None]


class BigQueryMetricsExporter:
    """Push metrics to Anthropic internal metrics endpoint (mirrors TS exporter)."""

    def __init__(self, *, timeout: float = 5.0) -> None:
        default_endpoint = "https://api.anthropic.com/api/claude_code/metrics"
        ant_metrics = os.environ.get("ANT_CLAUDE_CODE_METRICS_ENDPOINT")
        if os.environ.get("USER_TYPE") == "ant" and ant_metrics:
            base = os.environ["ANT_CLAUDE_CODE_METRICS_ENDPOINT"].rstrip("/")
            self._endpoint = base + "/api/claude_code/metrics"
        else:
            self._endpoint = default_endpoint
        self._timeout = timeout
        self._pending: list[threading.Thread] = []
        self._shutdown = False
        self._lock = threading.Lock()

    def export(self, metrics: Any, result_callback: ExportResultCallback) -> None:
        if self._shutdown:
            result_callback(type("R", (), {"code": 1})())
            return

        def _run() -> None:
            try:
                self._do_export_sync(metrics, result_callback)
            except Exception as e:
                log_for_debugging(f"BigQuery metrics export failed: {e}")
                log_error(e if isinstance(e, Exception) else RuntimeError(str(e)))
                result_callback(type("R", (), {"code": 1})())

        t = threading.Thread(target=_run, daemon=True)
        with self._lock:
            self._pending.append(t)
        t.start()

    def _do_export_sync(self, metrics: Any, result_callback: ExportResultCallback) -> None:
        if not self._check_trust_or_non_interactive():
            log_for_debugging("BigQuery metrics export: trust not established, skipping")
            result_callback(type("R", (), {"code": 0})())
            return
        if not self._metrics_org_enabled_sync():
            log_for_debugging("Metrics export disabled by organization setting")
            result_callback(type("R", (), {"code": 0})())
            return

        payload = self._transform_metrics_for_internal(metrics)
        headers = self._build_headers()
        if headers is None:
            result_callback(type("R", (), {"code": 1})())
            return

        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(self._endpoint, content=json.dumps(payload), headers=headers)
            r.raise_for_status()
        log_for_debugging("BigQuery metrics exported successfully")
        log_for_debugging(f"BigQuery API Response: {r.text[:2000]}")
        result_callback(type("R", (), {"code": 0})())

    def _check_trust_or_non_interactive(self) -> bool:
        try:
            from ...bootstrap.state import get_is_non_interactive_session

            if get_is_non_interactive_session():
                return True
        except Exception:
            pass
        try:
            from ..config_utils import get_global_config

            cfg = get_global_config()
            return bool(getattr(cfg, "has_trust_dialog_accepted", False))
        except Exception:
            return True

    def _metrics_org_enabled_sync(self) -> bool:
        try:
            from ...services.api.metrics_opt_out import check_metrics_enabled_api

            st = asyncio.run(check_metrics_enabled_api())
            return bool(st.enabled)
        except RuntimeError:
            return True
        except Exception:
            return True

    def _build_headers(self) -> dict[str, str] | None:
        try:
            from ..http import get_auth_headers
            from ..user_agent import get_claude_code_user_agent  # type: ignore[import-untyped]

            auth = get_auth_headers()
            if getattr(auth, "error", None):
                log_for_debugging(f"Metrics export failed: {auth.error}")
                return None
            return {
                "Content-Type": "application/json",
                "User-Agent": get_claude_code_user_agent(),
                **auth.headers,
            }
        except Exception:
            return {"Content-Type": "application/json"}

    def _transform_metrics_for_internal(self, resource_metrics: Any) -> dict[str, Any]:
        resource = getattr(resource_metrics, "resource", resource_metrics)
        attrs = getattr(resource, "attributes", {}) or {}
        delta = getattr(AggregationTemporality, "DELTA", 1)
        resource_attributes: dict[str, str] = {
            "service.name": str(attrs.get("service.name", "claude-code")),
            "service.version": str(attrs.get("service.version", "unknown")),
            "os.type": str(attrs.get("os.type", "unknown")),
            "os.version": str(attrs.get("os.version", "unknown")),
            "host.arch": str(attrs.get("host.arch", "unknown")),
            "aggregation.temporality": ("delta" if self.select_aggregation_temporality() == delta else "cumulative"),
        }
        if attrs.get("wsl.version"):
            resource_attributes["wsl.version"] = str(attrs["wsl.version"])
        self._apply_user_resource_attributes(resource_attributes)

        scope_metrics = getattr(resource_metrics, "scope_metrics", []) or []
        metrics_out: list[dict[str, Any]] = []
        for sm in scope_metrics:
            for m in getattr(sm, "metrics", []) or []:
                desc = getattr(m, "descriptor", m)
                metrics_out.append(
                    {
                        "name": getattr(desc, "name", ""),
                        "description": getattr(desc, "description", None),
                        "unit": getattr(desc, "unit", None),
                        "data_points": self._extract_data_points(m),
                    },
                )
        return {"resource_attributes": resource_attributes, "metrics": metrics_out}

    def _apply_user_resource_attributes(self, resource_attributes: dict[str, str]) -> None:
        """Set user.customer_type and subscription (TS ``transformMetricsForInternal``)."""
        try:
            from claude_code.auth.helpers import get_subscription_type
            from claude_code.commands.cost.cost_impl import is_claude_ai_subscriber

            if is_claude_ai_subscriber():
                resource_attributes["user.customer_type"] = "claude_ai"
                st = get_subscription_type()
                if st:
                    resource_attributes["user.subscription_type"] = str(st)
            else:
                resource_attributes["user.customer_type"] = "api"
        except Exception:
            resource_attributes.setdefault("user.customer_type", "api")

    def _extract_data_points(self, metric_data: Any) -> list[dict[str, Any]]:
        points = getattr(metric_data, "data_points", []) or []
        out: list[dict[str, Any]] = []
        for p in points:
            val = getattr(p, "value", None)
            if not isinstance(val, (int, float)):
                continue
            attrs = getattr(p, "attributes", None)
            hr = (
                getattr(p, "end_time", None)
                or getattr(p, "start_time", None)
                or (
                    int(time.time()),
                    0,
                )
            )
            out.append(
                {
                    "attributes": self._convert_attributes(attrs),
                    "value": float(val),
                    "timestamp": self._hr_time_to_iso(hr),
                },
            )
        return out

    def _convert_attributes(self, attributes: Mapping[str, Any] | None) -> dict[str, str]:
        result: dict[str, str] = {}
        if not attributes:
            return result
        for key, value in attributes.items():
            if value is not None:
                result[str(key)] = str(value)
        return result

    def _hr_time_to_iso(self, hr_time: tuple[int, int]) -> str:
        if not isinstance(hr_time, tuple) or len(hr_time) < 2:
            from datetime import UTC, datetime

            return datetime.now(UTC).isoformat().replace("+00:00", "Z")
        seconds, nanoseconds = int(hr_time[0]), int(hr_time[1])
        from datetime import UTC, datetime, timedelta

        base = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
            seconds=seconds,
            microseconds=nanoseconds // 1000,
        )
        return base.isoformat().replace("+00:00", "Z")

    def shutdown(self) -> None:
        self._shutdown = True
        self.force_flush()

    def force_flush(self) -> None:
        for t in list(self._pending):
            t.join(timeout=self._timeout)
        log_for_debugging("BigQuery metrics exporter flush complete")

    def select_aggregation_temporality(self) -> Any:
        return getattr(AggregationTemporality, "DELTA", 1)
