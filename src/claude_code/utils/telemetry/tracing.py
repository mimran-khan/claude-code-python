"""
Distributed tracing.

Span creation and management.

Migrated from: utils/telemetry/sessionTracing.ts + betaSessionTracing.ts
"""

from __future__ import annotations

import os
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from ..env_utils import is_env_truthy


@dataclass
class SpanContext:
    """Context for a span."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None


@dataclass
class Span:
    """A tracing span."""

    name: str
    context: SpanContext
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"

    @property
    def duration_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append(
            {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
        )

    def set_status(self, status: str, message: str | None = None) -> None:
        self.status = status
        if message:
            self.attributes["status.message"] = message

    def end(self) -> None:
        self.end_time = time.time()


class Tracer:
    """Tracer for creating spans."""

    def __init__(self, name: str = "claude-code"):
        self.name = name
        self._spans: dict[str, Span] = {}
        self._current_trace_id: str | None = None

    def start_span(
        self,
        name: str,
        parent: Span | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new span."""
        trace_id = parent.context.trace_id if parent else (self._current_trace_id or uuid.uuid4().hex[:32])

        if not self._current_trace_id:
            self._current_trace_id = trace_id

        span = Span(
            name=name,
            context=SpanContext(
                trace_id=trace_id,
                span_id=uuid.uuid4().hex[:16],
                parent_span_id=parent.context.span_id if parent else None,
            ),
            attributes=attributes or {},
        )

        self._spans[span.context.span_id] = span
        return span

    def end_span(self, span: Span) -> None:
        """End a span."""
        span.end()

    def get_span(self, span_id: str) -> Span | None:
        """Get a span by ID."""
        return self._spans.get(span_id)

    def get_all_spans(self) -> list[Span]:
        """Get all spans."""
        return list(self._spans.values())

    def clear(self) -> None:
        """Clear all spans."""
        self._spans.clear()
        self._current_trace_id = None


# Context variable for current span
_current_span: ContextVar[Span | None] = ContextVar("current_span", default=None)

# Global tracer instance
_tracer: Tracer | None = None


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled."""
    return is_env_truthy(os.getenv("CLAUDE_CODE_ENABLE_TRACING"))


def get_tracer() -> Tracer:
    """Get the global tracer."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def create_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Span:
    """
    Create a new span.

    Args:
        name: Span name
        attributes: Optional attributes

    Returns:
        New span
    """
    parent = _current_span.get()
    span = get_tracer().start_span(name, parent, attributes)
    _current_span.set(span)
    return span


def end_span(span: Span) -> None:
    """End a span."""
    get_tracer().end_span(span)

    # Restore parent as current
    if span.context.parent_span_id:
        parent = get_tracer().get_span(span.context.parent_span_id)
        _current_span.set(parent)
    else:
        _current_span.set(None)


def get_current_span() -> Span | None:
    """Get the current span."""
    return _current_span.get()
