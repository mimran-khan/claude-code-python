"""
Session tracing (interaction, LLM, tool, hook spans).

Migrated from: utils/telemetry/sessionTracing.ts
"""

from __future__ import annotations

import asyncio
import os
import weakref
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar, cast, runtime_checkable

from ...services.analytics.growthbook import get_feature_value_cached
from ...types.message import AssistantMessage, UserMessage
from ..env_utils import is_env_defined_falsy, is_env_truthy
from .attributes import get_telemetry_attributes
from .beta_session_tracing import (
    LLMRequestNewContext,
    add_beta_interaction_attributes,
    add_beta_llm_request_attributes,
    add_beta_llm_response_attributes,
    add_beta_tool_input_attributes,
    add_beta_tool_result_attributes,
    is_beta_tracing_enabled,
    truncate_content,
)
from .perfetto_tracing import (
    end_interaction_perfetto_span,
    end_llm_request_perfetto_span,
    end_tool_perfetto_span,
    end_user_input_perfetto_span,
    is_perfetto_tracing_enabled,
    start_interaction_perfetto_span,
    start_llm_request_perfetto_span,
    start_tool_perfetto_span,
    start_user_input_perfetto_span,
)

try:
    from opentelemetry import context as otel_context
    from opentelemetry import trace as otel_trace

    _HAS_OTEL = True
except ImportError:
    otel_context = None
    otel_trace = None
    _HAS_OTEL = False


@runtime_checkable
class SpanLike(Protocol):
    def get_span_context(self) -> Any: ...

    def set_attribute(self, key: str, value: Any) -> None: ...

    def set_attributes(self, attrs: dict[str, Any]) -> None: ...

    def add_event(self, name: str, attrs: dict[str, Any] | None = None) -> None: ...

    def end(self) -> None: ...

    def record_exception(self, exc: BaseException) -> None: ...


@dataclass
class _NoopSpanContext:
    span_id: str = "0000000000000000"
    trace_id: str = "00000000000000000000000000000000"
    is_valid: bool = True


@dataclass
class NoopSpan:
    _name: str = "noop"
    _attrs: dict[str, Any] = field(default_factory=dict)

    def get_span_context(self) -> _NoopSpanContext:
        return _NoopSpanContext()

    def set_attribute(self, key: str, value: Any) -> None:
        self._attrs[key] = value

    def set_attributes(self, attrs: dict[str, Any]) -> None:
        self._attrs.update(attrs)

    def add_event(self, name: str, attrs: dict[str, Any] | None = None) -> None:
        return

    def end(self) -> None:
        return

    def record_exception(self, exc: BaseException) -> None:
        return


SpanT = TypeVar("SpanT", bound=SpanLike)

SpanType = str


@dataclass
class TrackedSpanContext:
    span: SpanLike
    start_time: float
    attributes: dict[str, Any]
    ended: bool = False
    perfetto_span_id: str | None = None


_interaction_ctx: ContextVar[TrackedSpanContext | None] = ContextVar(
    "telemetry_interaction",
    default=None,
)
_tool_ctx: ContextVar[TrackedSpanContext | None] = ContextVar("telemetry_tool", default=None)
_active_spans: dict[str, weakref.ref[TrackedSpanContext]] = {}
_strong_spans: dict[str, TrackedSpanContext] = {}
_interaction_sequence = 0
_cleanup_interval_started = False
_SPAN_TTL_MS = 30 * 60 * 1000


def _now_ms() -> float:
    import time

    return float(time.time() * 1000)


def get_span_id(span: SpanLike) -> str:
    ctx = span.get_span_context()
    sid = getattr(ctx, "span_id", None)
    if sid is not None:
        return format(sid, "016x") if isinstance(sid, int) else str(sid)
    return str(id(span))


def _ensure_cleanup_interval() -> None:
    global _cleanup_interval_started
    if _cleanup_interval_started:
        return
    _cleanup_interval_started = True
    import threading

    def _run() -> None:
        import time as _t

        cutoff = _t.time() * 1000 - _SPAN_TTL_MS
        for span_id, wref in list(_active_spans.items()):
            ctx = wref()
            if ctx is None:
                _active_spans.pop(span_id, None)
                _strong_spans.pop(span_id, None)
            elif ctx.start_time < cutoff:
                if not ctx.ended:
                    ctx.span.end()
                _active_spans.pop(span_id, None)
                _strong_spans.pop(span_id, None)

    def _loop() -> None:
        _run()
        t = threading.Timer(60.0, _loop)
        t.daemon = True
        t.start()

    threading.Timer(60.0, _loop).start()


def is_enhanced_telemetry_enabled() -> bool:
    env = os.environ.get("CLAUDE_CODE_ENHANCED_TELEMETRY_BETA") or os.environ.get(
        "ENABLE_ENHANCED_TELEMETRY_BETA",
    )
    if is_env_truthy(env):
        return True
    if is_env_defined_falsy(env):
        return False
    return os.environ.get("USER_TYPE") == "ant" or bool(
        get_feature_value_cached("enhanced_telemetry_beta", False),
    )


def is_any_tracing_enabled() -> bool:
    return is_enhanced_telemetry_enabled() or is_beta_tracing_enabled()


def _get_tracer() -> Any:
    if _HAS_OTEL and otel_trace is not None:
        return otel_trace.get_tracer("com.anthropic.claude_code.tracing", "1.0.0")
    return None


def _dummy_span() -> SpanLike:
    if _HAS_OTEL and otel_trace is not None:
        span = otel_trace.get_current_span()
        if span is not None and getattr(span, "is_recording", lambda: False)():
            return cast(SpanLike, span)
        tr = _get_tracer()
        if tr is not None:
            return cast(SpanLike, tr.start_span("dummy"))
    return NoopSpan()


def create_span_attributes(
    span_type: SpanType,
    custom: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = dict(get_telemetry_attributes())
    return {**base, "span.type": span_type, **(custom or {})}


def start_interaction_span(user_prompt: str) -> SpanLike:
    _ensure_cleanup_interval()
    perfetto_id = start_interaction_perfetto_span(user_prompt) if is_perfetto_tracing_enabled() else None
    if not is_any_tracing_enabled():
        if perfetto_id:
            span = _dummy_span()
            ctx = TrackedSpanContext(
                span=span,
                start_time=_now_ms(),
                attributes={},
                perfetto_span_id=perfetto_id,
            )
            _active_spans[get_span_id(span)] = weakref.ref(ctx)
            _interaction_ctx.set(ctx)
            return span
        return _dummy_span()

    tracer = _get_tracer()
    if tracer is None:
        interaction_span: SpanLike = NoopSpan()
    else:
        log_prompt = user_prompt if is_env_truthy(os.environ.get("OTEL_LOG_USER_PROMPTS")) else "<REDACTED>"
        global _interaction_sequence
        _interaction_sequence += 1
        attrs = create_span_attributes(
            "interaction",
            {
                "user_prompt": log_prompt,
                "user_prompt_length": len(user_prompt),
                "interaction.sequence": _interaction_sequence,
            },
        )
        interaction_span = cast(
            SpanLike,
            tracer.start_span("claude_code.interaction", attributes=attrs),
        )
        add_beta_interaction_attributes(interaction_span, user_prompt)

    ctx = TrackedSpanContext(
        span=interaction_span,
        start_time=_now_ms(),
        attributes=create_span_attributes("interaction"),
        perfetto_span_id=perfetto_id,
    )
    _active_spans[get_span_id(interaction_span)] = weakref.ref(ctx)
    _interaction_ctx.set(ctx)
    return interaction_span


def end_interaction_span() -> None:
    ctx = _interaction_ctx.get()
    if not ctx or ctx.ended:
        return
    if ctx.perfetto_span_id:
        end_interaction_perfetto_span(ctx.perfetto_span_id)
    if not is_any_tracing_enabled():
        ctx.ended = True
        _active_spans.pop(get_span_id(ctx.span), None)
        _interaction_ctx.set(None)
        return
    duration = _now_ms() - ctx.start_time
    ctx.span.set_attributes({"interaction.duration_ms": duration})
    ctx.span.end()
    ctx.ended = True
    _active_spans.pop(get_span_id(ctx.span), None)
    _interaction_ctx.set(None)


def start_llm_request_span(
    model: str,
    new_context: LLMRequestNewContext | None = None,
    messages_for_api: list[UserMessage | AssistantMessage] | None = None,
    fast_mode: bool | None = None,
) -> SpanLike:
    perfetto_id = (
        start_llm_request_perfetto_span(
            model=model,
            query_source=new_context.query_source if new_context else None,
        )
        if is_perfetto_tracing_enabled()
        else None
    )
    if not is_any_tracing_enabled():
        if perfetto_id:
            span = _dummy_span()
            tctx = TrackedSpanContext(
                span=span,
                start_time=_now_ms(),
                attributes={"model": model},
                perfetto_span_id=perfetto_id,
            )
            sid = get_span_id(span)
            _active_spans[sid] = weakref.ref(tctx)
            _strong_spans[sid] = tctx
            return span
        return _dummy_span()

    tracer = _get_tracer()
    attrs: dict[str, Any] = {"model": model, "span.type": "llm_request"}
    if tracer is None:
        span = NoopSpan()
    else:
        parent = _interaction_ctx.get()
        attrs = create_span_attributes(
            "llm_request",
            {
                "model": model,
                "llm_request.context": "interaction" if parent else "standalone",
                "speed": "fast" if fast_mode else "normal",
            },
        )
        parent_ctx = otel_context.get_current() if otel_context else None
        if parent and _HAS_OTEL and otel_context is not None and otel_trace is not None:
            tok = otel_context.attach(otel_trace.set_span_in_context(parent.span, parent_ctx))
            try:
                span = cast(
                    SpanLike,
                    tracer.start_span("claude_code.llm_request", attributes=attrs),
                )
            finally:
                otel_context.detach(tok)
        else:
            span = cast(SpanLike, tracer.start_span("claude_code.llm_request", attributes=attrs))
        if new_context and new_context.query_source:
            span.set_attribute("query_source", new_context.query_source)
        add_beta_llm_request_attributes(span, new_context, messages_for_api)

    tctx = TrackedSpanContext(
        span=span,
        start_time=_now_ms(),
        attributes=attrs,
        perfetto_span_id=perfetto_id,
    )
    sid = get_span_id(span)
    _active_spans[sid] = weakref.ref(tctx)
    _strong_spans[sid] = tctx
    return span


def end_llm_request_span(
    span: SpanLike | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    metadata = metadata or {}
    llm_ctx: TrackedSpanContext | None = None
    if span is not None:
        wref = _active_spans.get(get_span_id(span))
        llm_ctx = wref() if wref else None
        if llm_ctx is None:
            llm_ctx = _strong_spans.get(get_span_id(span))
    else:
        for _sid, wref in reversed(list(_active_spans.items())):
            c = wref()
            if not c:
                continue
            is_llm = c.attributes.get("span.type") == "llm_request"
            if is_llm or c.attributes.get("model") is not None:
                llm_ctx = c
                break
    if not llm_ctx:
        return
    duration = int(_now_ms() - llm_ctx.start_time)
    if llm_ctx.perfetto_span_id:
        end_llm_request_perfetto_span(
            llm_ctx.perfetto_span_id,
            {
                "ttftMs": metadata.get("ttftMs"),
                "ttltMs": duration,
                "promptTokens": metadata.get("inputTokens"),
                "outputTokens": metadata.get("outputTokens"),
                "cacheReadTokens": metadata.get("cacheReadTokens"),
                "cacheCreationTokens": metadata.get("cacheCreationTokens"),
                "success": metadata.get("success"),
                "error": metadata.get("error"),
                "requestSetupMs": metadata.get("requestSetupMs"),
                "attemptStartTimes": metadata.get("attemptStartTimes"),
            },
        )
    if not is_any_tracing_enabled():
        sid = get_span_id(llm_ctx.span)
        _active_spans.pop(sid, None)
        _strong_spans.pop(sid, None)
        return
    end_attrs: dict[str, Any] = {"duration_ms": duration}
    if metadata:
        for k, py_key in (
            ("inputTokens", "input_tokens"),
            ("outputTokens", "output_tokens"),
            ("cacheReadTokens", "cache_read_tokens"),
            ("cacheCreationTokens", "cache_creation_tokens"),
            ("success", "success"),
            ("statusCode", "status_code"),
            ("error", "error"),
            ("attempt", "attempt"),
            ("hasToolCall", "response.has_tool_call"),
            ("ttftMs", "ttft_ms"),
        ):
            if metadata.get(k) is not None:
                end_attrs[py_key] = metadata[k]
        add_beta_llm_response_attributes(
            end_attrs,
            {
                "modelOutput": metadata.get("modelOutput"),
                "thinkingOutput": metadata.get("thinkingOutput"),
            },
        )
    llm_ctx.span.set_attributes(end_attrs)
    llm_ctx.span.end()
    sid = get_span_id(llm_ctx.span)
    _active_spans.pop(sid, None)
    _strong_spans.pop(sid, None)


def start_tool_span(
    tool_name: str,
    tool_attributes: dict[str, Any] | None = None,
    tool_input: str | None = None,
) -> SpanLike:
    perfetto_id = None
    if is_perfetto_tracing_enabled():
        perfetto_id = start_tool_perfetto_span(tool_name, tool_attributes)
    if not is_any_tracing_enabled():
        if perfetto_id:
            span = _dummy_span()
            tctx = TrackedSpanContext(
                span=span,
                start_time=_now_ms(),
                attributes={"span.type": "tool", "tool_name": tool_name},
                perfetto_span_id=perfetto_id,
            )
            _active_spans[get_span_id(span)] = weakref.ref(tctx)
            _tool_ctx.set(tctx)
            return span
        return _dummy_span()

    tracer = _get_tracer()
    attrs = create_span_attributes("tool", {"tool_name": tool_name, **(tool_attributes or {})})
    if tracer is None:
        span = NoopSpan()
    else:
        parent = _interaction_ctx.get()
        parent_ctx = otel_context.get_current() if otel_context else None
        if parent and _HAS_OTEL and otel_context is not None and otel_trace is not None:
            tok = otel_context.attach(otel_trace.set_span_in_context(parent.span, parent_ctx))
            try:
                span = cast(SpanLike, tracer.start_span("claude_code.tool", attributes=attrs))
            finally:
                otel_context.detach(tok)
        else:
            span = cast(SpanLike, tracer.start_span("claude_code.tool", attributes=attrs))
        if tool_input:
            add_beta_tool_input_attributes(span, tool_name, tool_input)

    tctx = TrackedSpanContext(
        span=span,
        start_time=_now_ms(),
        attributes=attrs,
        perfetto_span_id=perfetto_id,
    )
    _active_spans[get_span_id(span)] = weakref.ref(tctx)
    _tool_ctx.set(tctx)
    return span


def start_tool_blocked_on_user_span() -> SpanLike:
    perfetto_id = start_user_input_perfetto_span("tool_permission") if is_perfetto_tracing_enabled() else None
    if not is_any_tracing_enabled():
        if perfetto_id:
            span = _dummy_span()
            tctx = TrackedSpanContext(
                span=span,
                start_time=_now_ms(),
                attributes={"span.type": "tool.blocked_on_user"},
                perfetto_span_id=perfetto_id,
            )
            sid = get_span_id(span)
            _active_spans[sid] = weakref.ref(tctx)
            _strong_spans[sid] = tctx
            return span
        return _dummy_span()

    tracer = _get_tracer()
    attrs = create_span_attributes("tool.blocked_on_user")
    if tracer is None:
        span = NoopSpan()
    else:
        parent = _tool_ctx.get()
        parent_ctx = otel_context.get_current() if otel_context else None
        if parent and _HAS_OTEL and otel_context is not None and otel_trace is not None:
            tok = otel_context.attach(otel_trace.set_span_in_context(parent.span, parent_ctx))
            try:
                span = cast(
                    SpanLike,
                    tracer.start_span("claude_code.tool.blocked_on_user", attributes=attrs),
                )
            finally:
                otel_context.detach(tok)
        else:
            span = cast(
                SpanLike,
                tracer.start_span("claude_code.tool.blocked_on_user", attributes=attrs),
            )

    tctx = TrackedSpanContext(
        span=span,
        start_time=_now_ms(),
        attributes=attrs,
        perfetto_span_id=perfetto_id,
    )
    sid = get_span_id(span)
    _active_spans[sid] = weakref.ref(tctx)
    _strong_spans[sid] = tctx
    return span


def end_tool_blocked_on_user_span(decision: str | None = None, source: str | None = None) -> None:
    blocked: TrackedSpanContext | None = None
    for _sid, wref in reversed(list(_active_spans.items())):
        c = wref()
        if c and c.attributes.get("span.type") == "tool.blocked_on_user":
            blocked = c
            break
    if not blocked:
        return
    if blocked.perfetto_span_id:
        end_user_input_perfetto_span(
            blocked.perfetto_span_id,
            {"decision": decision, "source": source},
        )
    if not is_any_tracing_enabled():
        sid = get_span_id(blocked.span)
        _active_spans.pop(sid, None)
        _strong_spans.pop(sid, None)
        return
    duration = int(_now_ms() - blocked.start_time)
    attrs: dict[str, Any] = {"duration_ms": duration}
    if decision:
        attrs["decision"] = decision
    if source:
        attrs["source"] = source
    blocked.span.set_attributes(attrs)
    blocked.span.end()
    sid = get_span_id(blocked.span)
    _active_spans.pop(sid, None)
    _strong_spans.pop(sid, None)


def start_tool_execution_span() -> SpanLike:
    if not is_any_tracing_enabled():
        return _dummy_span()
    tracer = _get_tracer()
    if tracer is None:
        return NoopSpan()
    parent = _tool_ctx.get()
    attrs = create_span_attributes("tool.execution")
    parent_ctx = otel_context.get_current() if otel_context else None
    if parent and _HAS_OTEL and otel_context is not None and otel_trace is not None:
        tok = otel_context.attach(otel_trace.set_span_in_context(parent.span, parent_ctx))
        try:
            span = cast(SpanLike, tracer.start_span("claude_code.tool.execution", attributes=attrs))
        finally:
            otel_context.detach(tok)
    else:
        span = cast(SpanLike, tracer.start_span("claude_code.tool.execution", attributes=attrs))
    tctx = TrackedSpanContext(span=span, start_time=_now_ms(), attributes=attrs)
    sid = get_span_id(span)
    _active_spans[sid] = weakref.ref(tctx)
    _strong_spans[sid] = tctx
    return span


def end_tool_execution_span(metadata: dict[str, Any] | None = None) -> None:
    if not is_any_tracing_enabled():
        return
    metadata = metadata or {}
    exec_ctx: TrackedSpanContext | None = None
    for _sid, wref in reversed(list(_active_spans.items())):
        c = wref()
        if c and c.attributes.get("span.type") == "tool.execution":
            exec_ctx = c
            break
    if not exec_ctx:
        return
    duration = int(_now_ms() - exec_ctx.start_time)
    attrs: dict[str, Any] = {"duration_ms": duration}
    if "success" in metadata:
        attrs["success"] = metadata["success"]
    if "error" in metadata:
        attrs["error"] = metadata["error"]
    exec_ctx.span.set_attributes(attrs)
    exec_ctx.span.end()
    sid = get_span_id(exec_ctx.span)
    _active_spans.pop(sid, None)
    _strong_spans.pop(sid, None)


def end_tool_span(tool_result: str | None = None, result_tokens: int | None = None) -> None:
    ctx = _tool_ctx.get()
    if not ctx:
        return
    if ctx.perfetto_span_id:
        end_tool_perfetto_span(
            ctx.perfetto_span_id,
            {"success": True, "resultTokens": result_tokens},
        )
    if not is_any_tracing_enabled():
        _active_spans.pop(get_span_id(ctx.span), None)
        _tool_ctx.set(None)
        return
    duration = int(_now_ms() - ctx.start_time)
    end_attrs: dict[str, Any] = {"duration_ms": duration}
    if tool_result:
        tool_name = ctx.attributes.get("tool_name", "unknown")
        add_beta_tool_result_attributes(end_attrs, str(tool_name), tool_result)
    if result_tokens is not None:
        end_attrs["result_tokens"] = result_tokens
    ctx.span.set_attributes(end_attrs)
    ctx.span.end()
    _active_spans.pop(get_span_id(ctx.span), None)
    _tool_ctx.set(None)


def is_tool_content_logging_enabled() -> bool:
    return is_env_truthy(os.environ.get("OTEL_LOG_TOOL_CONTENT"))


def add_tool_content_event(event_name: str, attributes: dict[str, Any]) -> None:
    if not is_any_tracing_enabled() or not is_tool_content_logging_enabled():
        return
    current = _tool_ctx.get()
    if not current:
        return
    processed: dict[str, Any] = {}
    for key, value in attributes.items():
        if isinstance(value, str):
            content, truncated = truncate_content(value)
            processed[key] = content
            if truncated:
                processed[f"{key}_truncated"] = True
                processed[f"{key}_original_length"] = len(value)
        else:
            processed[key] = value
    current.span.add_event(event_name, processed)


def get_current_span() -> SpanLike | None:
    if not is_any_tracing_enabled():
        return None
    t = _tool_ctx.get()
    if t:
        return t.span
    i = _interaction_ctx.get()
    return i.span if i else None


async def execute_in_span(
    span_name: str,
    fn: Callable[[SpanLike], Any],
    attributes: dict[str, Any] | None = None,
) -> Any:
    if not is_any_tracing_enabled():
        return await fn(_dummy_span())
    tracer = _get_tracer()
    if tracer is None:
        return await fn(NoopSpan())
    parent = _tool_ctx.get() or _interaction_ctx.get()
    final_attrs = create_span_attributes("tool", attributes or {})
    parent_ctx = otel_context.get_current() if otel_context else None
    if parent and _HAS_OTEL and otel_context is not None and otel_trace is not None:
        tok = otel_context.attach(otel_trace.set_span_in_context(parent.span, parent_ctx))
        try:
            span = cast(SpanLike, tracer.start_span(span_name, attributes=final_attrs))
        finally:
            otel_context.detach(tok)
    else:
        span = cast(SpanLike, tracer.start_span(span_name, attributes=final_attrs))
    sid = get_span_id(span)
    tctx = TrackedSpanContext(span=span, start_time=_now_ms(), attributes=final_attrs)
    _active_spans[sid] = weakref.ref(tctx)
    _strong_spans[sid] = tctx
    try:
        return await fn(span)
    except (Exception, asyncio.CancelledError) as exc:
        span.record_exception(exc)
        raise
    finally:
        span.end()
        _active_spans.pop(sid, None)
        _strong_spans.pop(sid, None)


def start_hook_span(
    hook_event: str,
    hook_name: str,
    num_hooks: int,
    hook_definitions: str,
) -> SpanLike:
    if not is_beta_tracing_enabled():
        return _dummy_span()
    tracer = _get_tracer()
    if tracer is None:
        return NoopSpan()
    parent = _tool_ctx.get() or _interaction_ctx.get()
    attrs = create_span_attributes(
        "hook",
        {
            "hook_event": hook_event,
            "hook_name": hook_name,
            "num_hooks": num_hooks,
            "hook_definitions": hook_definitions,
        },
    )
    parent_ctx = otel_context.get_current() if otel_context else None
    if parent and _HAS_OTEL and otel_context is not None and otel_trace is not None:
        tok = otel_context.attach(otel_trace.set_span_in_context(parent.span, parent_ctx))
        try:
            span = cast(SpanLike, tracer.start_span("claude_code.hook", attributes=attrs))
        finally:
            otel_context.detach(tok)
    else:
        span = cast(SpanLike, tracer.start_span("claude_code.hook", attributes=attrs))
    tctx = TrackedSpanContext(span=span, start_time=_now_ms(), attributes=attrs)
    sid = get_span_id(span)
    _active_spans[sid] = weakref.ref(tctx)
    _strong_spans[sid] = tctx
    return span


def end_hook_span(span: SpanLike, metadata: dict[str, Any] | None = None) -> None:
    if not is_beta_tracing_enabled():
        return
    metadata = metadata or {}
    sid = get_span_id(span)
    wref = _active_spans.get(sid)
    tctx = (wref() if wref else None) or _strong_spans.get(sid)
    if not tctx:
        return
    duration = int(_now_ms() - tctx.start_time)
    end_attrs: dict[str, Any] = {"duration_ms": duration}
    for k, pk in (
        ("numSuccess", "num_success"),
        ("numBlocking", "num_blocking"),
        ("numNonBlockingError", "num_non_blocking_error"),
        ("numCancelled", "num_cancelled"),
    ):
        if k in metadata:
            end_attrs[pk] = metadata[k]
    tctx.span.set_attributes(end_attrs)
    tctx.span.end()
    _active_spans.pop(sid, None)
    _strong_spans.pop(sid, None)
