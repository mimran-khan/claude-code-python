"""
OpenTelemetry diagnostic logger bridge (structlog + app error path).

Migrated from: utils/telemetry/logger.ts
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

import structlog

from ..debug import log_for_debugging
from ..log import log_error

_log = structlog.get_logger("claude_code.telemetry.diag")


class ClaudeCodeDiagLogger:
    """
    Implements the OpenTelemetry DiagLogger surface (error/warn/info/debug/verbose).

    Used with ``opentelemetry._logs`` / ``opentelemetry.metrics`` diagnostic callbacks.
    """

    def error(self, message: str, *_args: object, **_kwargs: object) -> None:
        log_error(RuntimeError(message))
        log_for_debugging(f"[3P telemetry] OTEL diag error: {message}", level="error")
        _log.error("otel_diag", message=message)

    def warn(self, message: str, *_args: object, **_kwargs: object) -> None:
        log_error(RuntimeError(message))
        log_for_debugging(f"[3P telemetry] OTEL diag warn: {message}", level="warn")
        _log.warning("otel_diag", message=message)

    def info(self, _message: str, *_args: object, **_kwargs: object) -> None:
        return

    def debug(self, _message: str, *_args: object, **_kwargs: object) -> None:
        return

    def verbose(self, _message: str, *_args: object, **_kwargs: object) -> None:
        return


LogLevel = Literal["debug", "info", "warn", "error"]


@dataclass
class TelemetryRecord:
    """In-memory telemetry record (tests / local inspection)."""

    timestamp: str
    level: LogLevel
    message: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            **self.attributes,
        }


class TelemetryLogger:
    """Optional in-memory logger retained for shutdown/tests (see entrypoints/init)."""

    def __init__(
        self,
        name: str = "claude-code",
        min_level: LogLevel = "info",
    ) -> None:
        self.name = name
        self.min_level = min_level
        self._records: list[TelemetryRecord] = []
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def _should_log(self, level: LogLevel) -> bool:
        levels = ["debug", "info", "warn", "error"]
        return levels.index(level) >= levels.index(self.min_level)

    def _log(
        self,
        level: LogLevel,
        message: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        if not self._enabled or not self._should_log(level):
            return
        record = TelemetryRecord(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            level=level,
            message=message,
            attributes=attributes or {},
        )
        self._records.append(record)
        if len(self._records) > 1000:
            self._records = self._records[-1000:]

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("debug", message, kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("info", message, kwargs)

    def warn(self, message: str, **kwargs: Any) -> None:
        self._log("warn", message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("error", message, kwargs)

    def get_records(self, level: LogLevel | None = None) -> list[TelemetryRecord]:
        if level:
            return [r for r in self._records if r.level == level]
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()


_logger: TelemetryLogger | None = None


def get_telemetry_logger() -> TelemetryLogger:
    global _logger
    if _logger is None:
        _logger = TelemetryLogger()
    return _logger


def log_telemetry(level: LogLevel, message: str, **kwargs: Any) -> None:
    logger = get_telemetry_logger()
    if level == "debug":
        logger.debug(message, **kwargs)
    elif level == "info":
        logger.info(message, **kwargs)
    elif level == "warn":
        logger.warn(message, **kwargs)
    elif level == "error":
        logger.error(message, **kwargs)
