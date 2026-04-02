"""
OpenTelemetry bootstrap and provider wiring.

Migrated from: utils/telemetry/instrumentation.ts (subset + extension points).

Full OTLP exporter matrix from the TypeScript build can be enabled by installing
``opentelemetry-sdk`` and related exporter packages; this module provides env
mirroring, feature flags, and hooks used by the rest of the Python CLI.
"""

from __future__ import annotations

import contextlib
import os
from typing import Any

from ..debug import get_has_formatted_output, log_for_debugging
from ..env_utils import is_env_truthy
from .beta_session_tracing import is_beta_tracing_enabled
from .bigquery_exporter import BigQueryMetricsExporter
from .perfetto_tracing import initialize_perfetto_tracing
from .session_tracing import end_interaction_span

DEFAULT_METRICS_EXPORT_INTERVAL_MS = 60000
DEFAULT_LOGS_EXPORT_INTERVAL_MS = 5000
DEFAULT_TRACES_EXPORT_INTERVAL_MS = 5000


class TelemetryTimeoutError(Exception):
    pass


def bootstrap_telemetry() -> None:
    """Copy ANT_* OTEL env vars for internal builds (mirrors TS)."""
    if os.environ.get("USER_TYPE") == "ant":
        mappings = (
            ("ANT_OTEL_METRICS_EXPORTER", "OTEL_METRICS_EXPORTER"),
            ("ANT_OTEL_LOGS_EXPORTER", "OTEL_LOGS_EXPORTER"),
            ("ANT_OTEL_TRACES_EXPORTER", "OTEL_TRACES_EXPORTER"),
            ("ANT_OTEL_EXPORTER_OTLP_PROTOCOL", "OTEL_EXPORTER_OTLP_PROTOCOL"),
            ("ANT_OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT"),
            ("ANT_OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_HEADERS"),
        )
        for src, dst in mappings:
            v = os.environ.get(src)
            if v:
                os.environ[dst] = v
    if not os.environ.get("OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE"):
        os.environ["OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE"] = "delta"


def parse_exporter_types(value: str | None) -> list[str]:
    return [t.strip() for t in (value or "").split(",") if t.strip() and t.strip() != "none"]


def is_telemetry_enabled() -> bool:
    return is_env_truthy(os.environ.get("CLAUDE_CODE_ENABLE_TELEMETRY"))


def _is_1p_api_customer() -> bool:
    """
    First-party Anthropic API (API key) customer, excluding Claude.ai subscription
    billing and non-1P providers. Mirrors TS ``is1PApiCustomer`` intent.
    """
    provider = (os.environ.get("CLAUDE_CODE_API_PROVIDER") or os.environ.get("ANTHROPIC_API_PROVIDER") or "").lower()
    if provider in ("bedrock", "vertex", "foundry", "aws"):
        return False
    try:
        from claude_code.commands.cost.cost_impl import is_claude_ai_subscriber

        if is_claude_ai_subscriber():
            return False
    except ImportError:
        pass
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def is_big_query_metrics_enabled() -> bool:
    """
    BigQuery / internal metrics: API customers, Claude for Enterprise / Teams,
    or ``CLAUDE_CODE_BIGQUERY_METRICS=1``. Mirrors TS ``isBigQueryMetricsEnabled``.
    """
    if is_env_truthy(os.environ.get("CLAUDE_CODE_BIGQUERY_METRICS")):
        return True
    try:
        from claude_code.auth.helpers import get_subscription_type
        from claude_code.commands.cost.cost_impl import is_claude_ai_subscriber

        subscription_type = get_subscription_type()
        is_c4e_or_team = is_claude_ai_subscriber() and subscription_type in (
            "enterprise",
            "team",
        )
        return _is_1p_api_customer() or is_c4e_or_team
    except ImportError:
        return False


def _strip_console_exporters_when_formatted_output() -> None:
    if not get_has_formatted_output():
        return
    for key in ("OTEL_METRICS_EXPORTER", "OTEL_LOGS_EXPORTER", "OTEL_TRACES_EXPORTER"):
        v = os.environ.get(key)
        if v and "console" in v:
            parts = [p.strip() for p in v.split(",") if p.strip() and p.strip() != "console"]
            os.environ[key] = ",".join(parts)


def initialize_telemetry() -> Any:
    """
    Initialize Perfetto, optional OpenTelemetry SDK, and register cleanup.

    Returns a metrics ``Meter`` when the OTEL SDK is available, else ``None``.
    """
    bootstrap_telemetry()
    _strip_console_exporters_when_formatted_output()

    initialize_perfetto_tracing()

    log_for_debugging(
        f"[3P telemetry] isTelemetryEnabled={is_telemetry_enabled()} "
        f"(CLAUDE_CODE_ENABLE_TELEMETRY={os.environ.get('CLAUDE_CODE_ENABLE_TELEMETRY')})",
    )

    meter = None
    try:
        from opentelemetry import metrics as otel_metrics
        from opentelemetry.metrics import set_meter_provider
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource

        readers: list[Any] = []
        if is_big_query_metrics_enabled():
            exporter = BigQueryMetricsExporter()
            readers.append(
                PeriodicExportingMetricReader(
                    exporter,
                    export_interval_millis=5 * 60 * 1000,
                ),
            )
        if not readers:
            return None

        resource = Resource.create(
            {
                "service.name": "claude-code",
                "service.version": os.environ.get("CLAUDE_CODE_VERSION", "0.0.0"),
            },
        )
        provider = MeterProvider(resource=resource, metric_readers=readers)
        set_meter_provider(provider)
        meter = otel_metrics.get_meter("com.anthropic.claude_code", "1.0.0")
    except Exception as e:
        log_for_debugging(f"[3P telemetry] MeterProvider not started: {e}")

    if is_beta_tracing_enabled():
        log_for_debugging(
            "[3P telemetry] Beta tracing enabled (separate OTLP path — see TS parity)",
        )

    import atexit

    def _shutdown() -> None:
        with contextlib.suppress(Exception):
            end_interaction_span()

    atexit.register(_shutdown)
    return meter


async def flush_telemetry() -> None:
    """Best-effort flush of OTEL providers."""
    try:
        from opentelemetry import metrics as otel_metrics

        p = otel_metrics.get_meter_provider()
        if hasattr(p, "force_flush"):
            p.force_flush()
    except Exception as e:
        log_for_debugging(f"Telemetry flush failed: {e}", level="warn")
