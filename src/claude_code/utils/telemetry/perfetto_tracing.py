"""
Chrome Trace Event (Perfetto) file generation.

Migrated from: utils/telemetry/perfettoTracing.ts
"""

from __future__ import annotations

import asyncio
import atexit
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ...bootstrap.state import get_session_id
from ..debug import log_for_debugging
from ..env_utils import get_claude_config_home_dir, is_env_defined_falsy, is_env_truthy
from ..hash import djb2_hash
from ..teammate import get_agent_id, get_agent_name, get_parent_session_id

TraceEventPhase = Literal["B", "E", "X", "i", "C", "b", "n", "e", "M"]


@dataclass
class TraceEvent:
    name: str
    cat: str
    ph: TraceEventPhase
    ts: int
    pid: int
    tid: int
    dur: int | None = None
    args: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    scope: str | None = None


@dataclass
class AgentInfo:
    agent_id: str
    agent_name: str
    parent_agent_id: str | None
    process_id: int
    thread_id: int


@dataclass
class PendingSpan:
    name: str
    category: str
    start_time: int
    agent_info: AgentInfo
    args: dict[str, Any]


_is_enabled = False
_trace_path: str | None = None
_metadata_events: list[dict[str, Any]] = []
_events: list[dict[str, Any]] = []
MAX_EVENTS = 100_000
_pending_spans: dict[str, PendingSpan] = {}
_agent_registry: dict[str, AgentInfo] = {}
_total_agent_count = 0
_start_time_ms = 0
_span_id_counter = 0
_trace_written = False
_process_id_counter = 1
_agent_id_to_process_id: dict[str, int] = {}
_write_interval_id: Any = None
_stale_span_cleanup_id: Any = None

STALE_SPAN_TTL_MS = 30 * 60 * 1000
STALE_SPAN_CLEANUP_INTERVAL_MS = 60 * 1000


def _string_to_numeric_hash(s: str) -> int:
    return abs(djb2_hash(s)) or 1


def _get_process_id_for_agent(agent_id: str) -> int:
    existing = _agent_id_to_process_id.get(agent_id)
    if existing is not None:
        return existing
    global _process_id_counter
    _process_id_counter += 1
    _agent_id_to_process_id[agent_id] = _process_id_counter
    return _process_id_counter


def _get_current_agent_info() -> AgentInfo:
    agent_id = get_agent_id() or str(get_session_id())
    agent_name = get_agent_name() or "main"
    parent_session_id = get_parent_session_id()

    existing = _agent_registry.get(agent_id)
    if existing:
        return existing

    sid = str(get_session_id())
    info = AgentInfo(
        agent_id=agent_id,
        agent_name=agent_name,
        parent_agent_id=parent_session_id,
        process_id=1 if agent_id == sid else _get_process_id_for_agent(agent_id),
        thread_id=_string_to_numeric_hash(agent_name),
    )
    _agent_registry[agent_id] = info
    global _total_agent_count
    _total_agent_count += 1
    return info


def get_timestamp() -> int:
    return int((__import__("time").time() * 1000 - _start_time_ms) * 1000)


def _generate_span_id() -> str:
    global _span_id_counter
    _span_id_counter += 1
    return f"span_{_span_id_counter}"


def _event_to_dict(ev: TraceEvent) -> dict[str, Any]:
    d: dict[str, Any] = {
        "name": ev.name,
        "cat": ev.cat,
        "ph": ev.ph,
        "ts": ev.ts,
        "pid": ev.pid,
        "tid": ev.tid,
    }
    if ev.dur is not None:
        d["dur"] = ev.dur
    if ev.args:
        d["args"] = ev.args
    if ev.id is not None:
        d["id"] = ev.id
    if ev.scope is not None:
        d["scope"] = ev.scope
    return d


def evict_stale_spans() -> None:
    now = get_timestamp()
    ttl_us = STALE_SPAN_TTL_MS * 1000
    stale: list[str] = []
    for span_id, span in _pending_spans.items():
        if now - span.start_time > ttl_us:
            _events.append(
                _event_to_dict(
                    TraceEvent(
                        name=span.name,
                        cat=span.category,
                        ph="E",
                        ts=now,
                        pid=span.agent_info.process_id,
                        tid=span.agent_info.thread_id,
                        args={
                            **span.args,
                            "evicted": True,
                            "duration_ms": (now - span.start_time) / 1000,
                        },
                    ),
                ),
            )
            stale.append(span_id)
    for s in stale:
        del _pending_spans[s]


def build_trace_document() -> str:
    doc = {
        "traceEvents": [*_metadata_events, *_events],
        "metadata": {
            "session_id": str(get_session_id()),
            "trace_start_time": __import__("datetime")
            .datetime.utcfromtimestamp(
                _start_time_ms / 1000,
            )
            .isoformat()
            + "Z",
            "agent_count": _total_agent_count,
            "total_event_count": len(_metadata_events) + len(_events),
        },
    }
    return json.dumps(doc)


def evict_oldest_events() -> None:
    if len(_events) < MAX_EVENTS:
        return
    dropped_n = MAX_EVENTS // 2
    dropped = _events[:dropped_n]
    del _events[:dropped_n]
    last_ts = dropped[-1]["ts"] if dropped else 0
    _events.insert(
        0,
        {
            "name": "trace_truncated",
            "cat": "__metadata",
            "ph": "i",
            "ts": last_ts,
            "pid": 1,
            "tid": 0,
            "args": {"dropped_events": len(dropped)},
        },
    )
    log_for_debugging(
        f"[Perfetto] Evicted {len(dropped)} oldest events (cap {MAX_EVENTS})",
    )


def initialize_perfetto_tracing() -> None:
    global _is_enabled, _trace_path, _start_time_ms, _write_interval_id, _stale_span_cleanup_id

    env_value = os.environ.get("CLAUDE_CODE_PERFETTO_TRACE")
    log_for_debugging(f"[Perfetto] initialize_perfetto_tracing called, env value: {env_value}")

    if not env_value or is_env_defined_falsy(env_value):
        log_for_debugging("[Perfetto] Tracing disabled (env var not set or disabled)")
        return

    _is_enabled = True
    _start_time_ms = int(__import__("time").time() * 1000)

    if is_env_truthy(env_value):
        traces_dir = Path(get_claude_config_home_dir()) / "traces"
        _trace_path = str(traces_dir / f"trace-{get_session_id()}.json")
    else:
        _trace_path = env_value

    log_for_debugging(
        f"[Perfetto] Tracing enabled, will write to: {_trace_path}, isEnabled={_is_enabled}",
    )

    import threading

    interval_sec = int(os.environ.get("CLAUDE_CODE_PERFETTO_WRITE_INTERVAL_S") or "0")
    if interval_sec > 0:

        def _periodic_tick() -> None:
            periodic_write_sync()
            if _is_enabled and not _trace_written:
                t = threading.Timer(float(interval_sec), _periodic_tick)
                t.daemon = True
                t.start()
                global _write_interval_id
                _write_interval_id = t

        _write_interval_id = threading.Timer(float(interval_sec), _periodic_tick)
        _write_interval_id.daemon = True
        _write_interval_id.start()

    def _cleanup_tick() -> None:
        evict_stale_spans()
        evict_oldest_events()
        if _is_enabled:
            t = threading.Timer(STALE_SPAN_CLEANUP_INTERVAL_MS / 1000.0, _cleanup_tick)
            t.daemon = True
            t.start()
            global _stale_span_cleanup_id
            _stale_span_cleanup_id = t

    _stale_span_cleanup_id = threading.Timer(
        STALE_SPAN_CLEANUP_INTERVAL_MS / 1000.0,
        _cleanup_tick,
    )
    _stale_span_cleanup_id.daemon = True
    _stale_span_cleanup_id.start()

    atexit.register(write_perfetto_trace_sync)
    main_agent = _get_current_agent_info()
    _emit_process_metadata(main_agent)


def _emit_process_metadata(agent_info: AgentInfo) -> None:
    if not _is_enabled:
        return
    _metadata_events.append(
        {
            "name": "process_name",
            "cat": "__metadata",
            "ph": "M",
            "ts": 0,
            "pid": agent_info.process_id,
            "tid": 0,
            "args": {"name": agent_info.agent_name},
        },
    )
    _metadata_events.append(
        {
            "name": "thread_name",
            "cat": "__metadata",
            "ph": "M",
            "ts": 0,
            "pid": agent_info.process_id,
            "tid": agent_info.thread_id,
            "args": {"name": agent_info.agent_name},
        },
    )
    if agent_info.parent_agent_id:
        _metadata_events.append(
            {
                "name": "parent_agent",
                "cat": "__metadata",
                "ph": "M",
                "ts": 0,
                "pid": agent_info.process_id,
                "tid": 0,
                "args": {"parent_agent_id": agent_info.parent_agent_id},
            },
        )


def is_perfetto_tracing_enabled() -> bool:
    return _is_enabled


def register_agent(agent_id: str, agent_name: str, parent_agent_id: str | None = None) -> None:
    if not _is_enabled:
        return
    info = AgentInfo(
        agent_id=agent_id,
        agent_name=agent_name,
        parent_agent_id=parent_agent_id,
        process_id=_get_process_id_for_agent(agent_id),
        thread_id=_string_to_numeric_hash(agent_name),
    )
    _agent_registry[agent_id] = info
    global _total_agent_count
    _total_agent_count += 1
    _emit_process_metadata(info)


def unregister_agent(agent_id: str) -> None:
    if not _is_enabled:
        return
    _agent_registry.pop(agent_id, None)
    _agent_id_to_process_id.pop(agent_id, None)


def start_llm_request_perfetto_span(
    *,
    model: str,
    prompt_tokens: int | None = None,
    message_id: str | None = None,
    is_speculative: bool = False,
    query_source: str | None = None,
) -> str:
    if not _is_enabled:
        return ""
    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    args: dict[str, Any] = {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "message_id": message_id,
        "is_speculative": is_speculative,
        "query_source": query_source,
    }
    _pending_spans[span_id] = PendingSpan(
        name="API Call",
        category="api",
        start_time=get_timestamp(),
        agent_info=agent_info,
        args=args,
    )
    st = _pending_spans[span_id].start_time
    _events.append(
        {
            "name": "API Call",
            "cat": "api",
            "ph": "B",
            "ts": st,
            "pid": agent_info.process_id,
            "tid": agent_info.thread_id,
            "args": args,
        },
    )
    return span_id


def end_llm_request_perfetto_span(
    span_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    if not _is_enabled or not span_id:
        return
    metadata = metadata or {}
    pending = _pending_spans.get(span_id)
    if not pending:
        return
    end_time = get_timestamp()
    duration = end_time - pending.start_time
    prompt_tokens = metadata.get("promptTokens") or pending.args.get("prompt_tokens")
    ttft_ms = metadata.get("ttftMs")
    ttlt_ms = metadata.get("ttltMs")
    output_tokens = metadata.get("outputTokens")
    cache_read_tokens = metadata.get("cacheReadTokens")

    itps = None
    if ttft_ms is not None and prompt_tokens is not None and ttft_ms > 0:
        itps = round((float(prompt_tokens) / (ttft_ms / 1000.0)) * 100) / 100

    sampling_ms = None
    if ttlt_ms is not None and ttft_ms is not None:
        sampling_ms = ttlt_ms - ttft_ms
    otps = None
    if sampling_ms is not None and output_tokens is not None and sampling_ms > 0:
        otps = round((float(output_tokens) / (sampling_ms / 1000.0)) * 100) / 100

    cache_hit_rate = None
    if cache_read_tokens is not None and prompt_tokens is not None and float(prompt_tokens) > 0:
        cache_hit_rate = round((float(cache_read_tokens) / float(prompt_tokens)) * 10000) / 100

    request_setup_ms = metadata.get("requestSetupMs")
    attempt_start_times = metadata.get("attemptStartTimes")

    args: dict[str, Any] = {
        **pending.args,
        "ttft_ms": ttft_ms,
        "ttlt_ms": ttlt_ms,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": metadata.get("cacheCreationTokens"),
        "message_id": metadata.get("messageId") or pending.args.get("message_id"),
        "success": metadata.get("success", True),
        "error": metadata.get("error"),
        "duration_ms": duration / 1000,
        "request_setup_ms": request_setup_ms,
        "itps": itps,
        "otps": otps,
        "cache_hit_rate_pct": cache_hit_rate,
    }

    setup_us = int(request_setup_ms * 1000) if request_setup_ms and request_setup_ms > 0 else 0
    if setup_us > 0:
        setup_end_ts = pending.start_time + setup_us
        _events.extend(
            [
                {
                    "name": "Request Setup",
                    "cat": "api,setup",
                    "ph": "B",
                    "ts": pending.start_time,
                    "pid": pending.agent_info.process_id,
                    "tid": pending.agent_info.thread_id,
                    "args": {
                        "request_setup_ms": request_setup_ms,
                        "attempt_count": len(attempt_start_times or []) or 1,
                    },
                },
                {
                    "name": "Request Setup",
                    "cat": "api,setup",
                    "ph": "E",
                    "ts": setup_end_ts,
                    "pid": pending.agent_info.process_id,
                    "tid": pending.agent_info.thread_id,
                },
            ],
        )
        if attempt_start_times and len(attempt_start_times) > 1:
            base_wall_ms = attempt_start_times[0]
            for i in range(len(attempt_start_times) - 1):
                dt_start = (attempt_start_times[i] - base_wall_ms) * 1000
                dt_end = (attempt_start_times[i + 1] - base_wall_ms) * 1000
                attempt_start_us = pending.start_time + dt_start
                attempt_end_us = pending.start_time + dt_end
                _events.extend(
                    [
                        {
                            "name": f"Attempt {i + 1} (retry)",
                            "cat": "api,retry",
                            "ph": "B",
                            "ts": attempt_start_us,
                            "pid": pending.agent_info.process_id,
                            "tid": pending.agent_info.thread_id,
                            "args": {"attempt": i + 1},
                        },
                        {
                            "name": f"Attempt {i + 1} (retry)",
                            "cat": "api,retry",
                            "ph": "E",
                            "ts": attempt_end_us,
                            "pid": pending.agent_info.process_id,
                            "tid": pending.agent_info.thread_id,
                        },
                    ],
                )

    if ttft_ms is not None:
        first_token_start_ts = pending.start_time + setup_us
        first_token_end_ts = first_token_start_ts + ttft_ms * 1000
        _events.extend(
            [
                {
                    "name": "First Token",
                    "cat": "api,ttft",
                    "ph": "B",
                    "ts": first_token_start_ts,
                    "pid": pending.agent_info.process_id,
                    "tid": pending.agent_info.thread_id,
                    "args": {
                        "ttft_ms": ttft_ms,
                        "prompt_tokens": prompt_tokens,
                        "itps": itps,
                        "cache_hit_rate_pct": cache_hit_rate,
                    },
                },
                {
                    "name": "First Token",
                    "cat": "api,ttft",
                    "ph": "E",
                    "ts": first_token_end_ts,
                    "pid": pending.agent_info.process_id,
                    "tid": pending.agent_info.thread_id,
                },
            ],
        )
        actual_sampling_ms = None
        if ttlt_ms is not None:
            actual_sampling_ms = ttlt_ms - ttft_ms - setup_us / 1000
        if actual_sampling_ms is not None and actual_sampling_ms > 0:
            _events.extend(
                [
                    {
                        "name": "Sampling",
                        "cat": "api,sampling",
                        "ph": "B",
                        "ts": first_token_end_ts,
                        "pid": pending.agent_info.process_id,
                        "tid": pending.agent_info.thread_id,
                        "args": {
                            "sampling_ms": actual_sampling_ms,
                            "output_tokens": output_tokens,
                            "otps": otps,
                        },
                    },
                    {
                        "name": "Sampling",
                        "cat": "api,sampling",
                        "ph": "E",
                        "ts": int(first_token_end_ts + actual_sampling_ms * 1000),
                        "pid": pending.agent_info.process_id,
                        "tid": pending.agent_info.thread_id,
                    },
                ],
            )

    _events.append(
        {
            "name": pending.name,
            "cat": pending.category,
            "ph": "E",
            "ts": end_time,
            "pid": pending.agent_info.process_id,
            "tid": pending.agent_info.thread_id,
            "args": args,
        },
    )
    del _pending_spans[span_id]


def start_tool_perfetto_span(
    tool_name: str,
    args: dict[str, Any] | None = None,
) -> str:
    if not _is_enabled:
        return ""
    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    merged = {"tool_name": tool_name, **(args or {})}
    _pending_spans[span_id] = PendingSpan(
        name=f"Tool: {tool_name}",
        category="tool",
        start_time=get_timestamp(),
        agent_info=agent_info,
        args=merged,
    )
    st = _pending_spans[span_id].start_time
    _events.append(
        {
            "name": f"Tool: {tool_name}",
            "cat": "tool",
            "ph": "B",
            "ts": st,
            "pid": agent_info.process_id,
            "tid": agent_info.thread_id,
            "args": merged,
        },
    )
    return span_id


def end_tool_perfetto_span(
    span_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    if not _is_enabled or not span_id:
        return
    metadata = metadata or {}
    pending = _pending_spans.get(span_id)
    if not pending:
        return
    end_time = get_timestamp()
    duration = end_time - pending.start_time
    args = {
        **pending.args,
        "success": metadata.get("success", True),
        "error": metadata.get("error"),
        "result_tokens": metadata.get("resultTokens"),
        "duration_ms": duration / 1000,
    }
    _events.append(
        {
            "name": pending.name,
            "cat": pending.category,
            "ph": "E",
            "ts": end_time,
            "pid": pending.agent_info.process_id,
            "tid": pending.agent_info.thread_id,
            "args": args,
        },
    )
    del _pending_spans[span_id]


def start_user_input_perfetto_span(context: str | None = None) -> str:
    if not _is_enabled:
        return ""
    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    merged = {"context": context}
    _pending_spans[span_id] = PendingSpan(
        name="Waiting for User Input",
        category="user_input",
        start_time=get_timestamp(),
        agent_info=agent_info,
        args=merged,
    )
    st = _pending_spans[span_id].start_time
    _events.append(
        {
            "name": "Waiting for User Input",
            "cat": "user_input",
            "ph": "B",
            "ts": st,
            "pid": agent_info.process_id,
            "tid": agent_info.thread_id,
            "args": merged,
        },
    )
    return span_id


def end_user_input_perfetto_span(
    span_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    if not _is_enabled or not span_id:
        return
    metadata = metadata or {}
    pending = _pending_spans.get(span_id)
    if not pending:
        return
    end_time = get_timestamp()
    duration = end_time - pending.start_time
    args = {
        **pending.args,
        "decision": metadata.get("decision"),
        "source": metadata.get("source"),
        "duration_ms": duration / 1000,
    }
    _events.append(
        {
            "name": pending.name,
            "cat": pending.category,
            "ph": "E",
            "ts": end_time,
            "pid": pending.agent_info.process_id,
            "tid": pending.agent_info.thread_id,
            "args": args,
        },
    )
    del _pending_spans[span_id]


def emit_perfetto_instant(name: str, category: str, args: dict[str, Any] | None = None) -> None:
    if not _is_enabled:
        return
    agent_info = _get_current_agent_info()
    _events.append(
        {
            "name": name,
            "cat": category,
            "ph": "i",
            "ts": get_timestamp(),
            "pid": agent_info.process_id,
            "tid": agent_info.thread_id,
            "args": args or {},
        },
    )


def emit_perfetto_counter(name: str, values: dict[str, float]) -> None:
    if not _is_enabled:
        return
    agent_info = _get_current_agent_info()
    _events.append(
        {
            "name": name,
            "cat": "counter",
            "ph": "C",
            "ts": get_timestamp(),
            "pid": agent_info.process_id,
            "tid": agent_info.thread_id,
            "args": values,
        },
    )


def start_interaction_perfetto_span(user_prompt: str | None = None) -> str:
    if not _is_enabled:
        return ""
    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    merged = {"user_prompt_length": len(user_prompt) if user_prompt else None}
    _pending_spans[span_id] = PendingSpan(
        name="Interaction",
        category="interaction",
        start_time=get_timestamp(),
        agent_info=agent_info,
        args={k: v for k, v in merged.items() if v is not None},
    )
    st = _pending_spans[span_id].start_time
    _events.append(
        {
            "name": "Interaction",
            "cat": "interaction",
            "ph": "B",
            "ts": st,
            "pid": agent_info.process_id,
            "tid": agent_info.thread_id,
            "args": _pending_spans[span_id].args,
        },
    )
    return span_id


def end_interaction_perfetto_span(span_id: str) -> None:
    if not _is_enabled or not span_id:
        return
    pending = _pending_spans.get(span_id)
    if not pending:
        return
    end_time = get_timestamp()
    duration = end_time - pending.start_time
    _events.append(
        {
            "name": pending.name,
            "cat": pending.category,
            "ph": "E",
            "ts": end_time,
            "pid": pending.agent_info.process_id,
            "tid": pending.agent_info.thread_id,
            "args": {**pending.args, "duration_ms": duration / 1000},
        },
    )
    del _pending_spans[span_id]


def _stop_write_interval() -> None:
    global _stale_span_cleanup_id, _write_interval_id
    stale = _stale_span_cleanup_id
    if stale is not None:
        stale.cancel()
    _stale_span_cleanup_id = None
    interval = _write_interval_id
    if interval is not None:
        interval.cancel()
    _write_interval_id = None


def close_open_spans() -> None:
    for span_id, pending in list(_pending_spans.items()):
        end_time = get_timestamp()
        _events.append(
            {
                "name": pending.name,
                "cat": pending.category,
                "ph": "E",
                "ts": end_time,
                "pid": pending.agent_info.process_id,
                "tid": pending.agent_info.thread_id,
                "args": {
                    **pending.args,
                    "incomplete": True,
                    "duration_ms": (end_time - pending.start_time) / 1000,
                },
            },
        )
        del _pending_spans[span_id]


async def periodic_write() -> None:
    global _trace_written
    if not _is_enabled or not _trace_path or _trace_written:
        return
    try:
        Path(_trace_path).parent.mkdir(parents=True, exist_ok=True)
        Path(_trace_path).write_text(build_trace_document(), encoding="utf-8")
        log_for_debugging(f"[Perfetto] Periodic write: {len(_events)} events to {_trace_path}")
    except OSError as e:
        log_for_debugging(f"[Perfetto] Periodic write failed: {e}", level="error")


def periodic_write_sync() -> None:
    try:
        asyncio.run(periodic_write())
    except RuntimeError:
        if not _is_enabled or not _trace_path or _trace_written:
            return
        try:
            Path(_trace_path).parent.mkdir(parents=True, exist_ok=True)
            Path(_trace_path).write_text(build_trace_document(), encoding="utf-8")
        except OSError as e:
            log_for_debugging(f"[Perfetto] Periodic write failed: {e}", level="error")


async def write_perfetto_trace() -> None:
    global _trace_written
    if not _is_enabled or not _trace_path or _trace_written:
        log_for_debugging(
            f"[Perfetto] Skipping final write: isEnabled={_is_enabled}, "
            f"tracePath={_trace_path}, traceWritten={_trace_written}",
        )
        return
    _stop_write_interval()
    close_open_spans()
    log_for_debugging(f"[Perfetto] write_perfetto_trace called: events={len(_events)}")
    try:
        Path(_trace_path).parent.mkdir(parents=True, exist_ok=True)
        Path(_trace_path).write_text(build_trace_document(), encoding="utf-8")
        _trace_written = True
        log_for_debugging(f"[Perfetto] Trace finalized at: {_trace_path}")
    except OSError as e:
        log_for_debugging(f"[Perfetto] Failed to write final trace: {e}", level="error")


def write_perfetto_trace_sync() -> None:
    global _trace_written
    if not _is_enabled or not _trace_path or _trace_written:
        return
    _stop_write_interval()
    close_open_spans()
    try:
        Path(_trace_path).parent.mkdir(parents=True, exist_ok=True)
        Path(_trace_path).write_text(build_trace_document(), encoding="utf-8")
        _trace_written = True
        log_for_debugging(f"[Perfetto] Trace finalized synchronously at: {_trace_path}")
    except OSError as e:
        log_for_debugging(
            f"[Perfetto] Failed to write final trace synchronously: {e}",
            level="error",
        )


def get_perfetto_events() -> list[dict[str, Any]]:
    return [*_metadata_events, *_events]


def reset_perfetto_tracer() -> None:
    global _is_enabled, _trace_path, _total_agent_count, _start_time_ms, _span_id_counter
    global _trace_written, _process_id_counter
    _stop_write_interval()
    _metadata_events.clear()
    _events.clear()
    _pending_spans.clear()
    _agent_registry.clear()
    _agent_id_to_process_id.clear()
    _total_agent_count = 0
    _process_id_counter = 1
    _span_id_counter = 0
    _is_enabled = False
    _trace_path = None
    _start_time_ms = 0
    _trace_written = False


async def trigger_periodic_write_for_testing() -> None:
    await periodic_write()


def evict_stale_spans_for_testing() -> None:
    evict_stale_spans()


MAX_EVENTS_FOR_TESTING = MAX_EVENTS


def evict_oldest_events_for_testing() -> None:
    evict_oldest_events()
