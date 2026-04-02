"""
Telemetry event logging.

OpenTelemetry event emission.

Migrated from: utils/telemetry/events.ts
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ...bootstrap.state import get_otel_event_logger, get_prompt_id
from ..debug import log_for_debugging
from ..env_utils import is_env_truthy
from .attributes import get_telemetry_attributes

_event_sequence = 0
_has_warned_no_event_logger = False


@dataclass(frozen=True, slots=True)
class OtelEventEnvelope:
    """
    Canonical envelope for claude_code.* OTEL log records.

    Mirrors the attribute bundle built in TS ``logOTelEvent``.
    """

    event_name: str
    sequence: int
    timestamp_iso: str

    @property
    def body(self) -> str:
        return f"claude_code.{self.event_name}"


@dataclass(slots=True)
class OtelEventMetadata:
    """Optional string metadata merged into OTEL log attributes."""

    fields: dict[str, str | None]

    def merged(self, base: dict[str, Any]) -> dict[str, Any]:
        out = dict(base)
        for key, value in self.fields.items():
            if value is not None:
                out[key] = value
        return out


def is_user_prompt_logging_enabled() -> bool:
    return is_env_truthy(os.environ.get("OTEL_LOG_USER_PROMPTS"))


def redact_if_disabled(content: str) -> str:
    return content if is_user_prompt_logging_enabled() else "<REDACTED>"


def _next_sequence() -> int:
    global _event_sequence
    seq = _event_sequence
    _event_sequence += 1
    return seq


def _is_test_env() -> bool:
    if os.environ.get("NODE_ENV") == "test":
        return True
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


async def log_otel_event(
    event_name: str,
    metadata: dict[str, str | None] | None = None,
) -> None:
    global _has_warned_no_event_logger

    event_logger = get_otel_event_logger()
    if event_logger is None:
        if not _has_warned_no_event_logger:
            _has_warned_no_event_logger = True
            log_for_debugging(
                f"[3P telemetry] Event dropped (no event logger initialized): {event_name}",
                level="warn",
            )
        return

    if _is_test_env():
        return

    seq = _next_sequence()
    ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    envelope = OtelEventEnvelope(event_name=event_name, sequence=seq, timestamp_iso=ts)

    attributes: dict[str, Any] = {
        **get_telemetry_attributes(),
        "event.name": envelope.event_name,
        "event.timestamp": envelope.timestamp_iso,
        "event.sequence": envelope.sequence,
    }

    prompt_id = get_prompt_id()
    if prompt_id:
        attributes["prompt.id"] = prompt_id

    workspace_dir = os.environ.get("CLAUDE_CODE_WORKSPACE_HOST_PATHS")
    if workspace_dir:
        attributes["workspace.host_paths"] = workspace_dir.split("|")

    if metadata:
        attributes = OtelEventMetadata(metadata).merged(attributes)

    record: dict[str, Any] = {"body": envelope.body, "attributes": attributes}
    try:
        maybe = event_logger.emit(record)
        if asyncio.iscoroutine(maybe):
            await maybe
    except TypeError:
        event_logger.emit(record)


def schedule_log_otel_event(
    event_name: str,
    metadata: dict[str, str | None] | None = None,
) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(log_otel_event(event_name, metadata))
        return
    loop.create_task(log_otel_event(event_name, metadata))
