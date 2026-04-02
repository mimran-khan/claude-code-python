"""
Query pipeline timing (enable with CLAUDE_CODE_PROFILE_QUERY=1).

Migrated from: utils/queryProfiler.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .debug import log_for_debugging
from .env_utils import is_env_truthy
from .profiler_base import (
    MarkEntry,
    format_ms,
    format_timeline_line,
    get_performance,
    memory_usage_dict,
)


def _enabled() -> bool:
    return is_env_truthy(os.environ.get("CLAUDE_CODE_PROFILE_QUERY"))


_memory_snapshots: dict[str, dict[str, int]] = {}
_query_count = 0
_first_token_time: float | None = None


def start_query_profile() -> None:
    if not _enabled():
        return
    perf = get_performance()
    perf.clearMarks()
    _memory_snapshots.clear()
    global _first_token_time, _query_count
    _first_token_time = None
    _query_count += 1
    query_checkpoint("query_user_input_received")


def query_checkpoint(name: str) -> None:
    if not _enabled():
        return
    perf = get_performance()
    perf.mark(name)
    _memory_snapshots[name] = memory_usage_dict()
    global _first_token_time
    if name == "query_first_chunk_received" and _first_token_time is None:
        marks = perf.getEntriesByType("mark")
        if marks:
            _first_token_time = marks[-1].startTime


def end_query_profile() -> None:
    if not _enabled():
        return
    query_checkpoint("query_profile_end")


def _slow_warning(delta_ms: float, name: str) -> str:
    if name == "query_user_input_received":
        return ""
    if delta_ms > 1000:
        return " ⚠️  VERY SLOW"
    if delta_ms > 100:
        return " ⚠️  SLOW"
    if "git_status" in name and delta_ms > 50:
        return " ⚠️  git status"
    if "tool_schema" in name and delta_ms > 50:
        return " ⚠️  tool schemas"
    if "client_creation" in name and delta_ms > 50:
        return " ⚠️  client creation"
    return ""


@dataclass(frozen=True)
class _Phase:
    label: str
    start_mark: str
    end_mark: str


_PHASES: list[_Phase] = [
    _Phase("Context loading", "query_context_loading_start", "query_context_loading_end"),
    _Phase("Microcompact", "query_microcompact_start", "query_microcompact_end"),
    _Phase("Autocompact", "query_autocompact_start", "query_autocompact_end"),
    _Phase("Query setup", "query_setup_start", "query_setup_end"),
    _Phase("Tool schemas", "query_tool_schema_build_start", "query_tool_schema_build_end"),
    _Phase(
        "Message normalization",
        "query_message_normalization_start",
        "query_message_normalization_end",
    ),
    _Phase("Client creation", "query_client_creation_start", "query_client_creation_end"),
    _Phase("Network TTFB", "query_api_request_sent", "query_first_chunk_received"),
    _Phase("Tool execution", "query_tool_execution_start", "query_tool_execution_end"),
]


def _phase_summary(marks: list[MarkEntry], baseline: float) -> str:
    mark_map = {m.name: m.startTime - baseline for m in marks}
    lines: list[str] = ["", "PHASE BREAKDOWN:"]
    for ph in _PHASES:
        s = mark_map.get(ph.start_mark)
        e = mark_map.get(ph.end_mark)
        if s is not None and e is not None:
            duration = e - s
            bar = "█" * min(int((duration + 9) // 10), 50)
            lines.append(f"  {ph.label:<22} {format_ms(duration).rjust(10)}ms {bar}")
    api_sent = mark_map.get("query_api_request_sent")
    if api_sent is not None:
        lines.append("")
        lines.append(f"  {'Total pre-API overhead':<22} {format_ms(api_sent).rjust(10)}ms")
    return "\n".join(lines)


def _report() -> str:
    if not _enabled():
        return "Query profiling not enabled (set CLAUDE_CODE_PROFILE_QUERY=1)"
    perf = get_performance()
    marks = perf.getEntriesByType("mark")
    if not marks:
        return "No query profiling checkpoints recorded"
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append(f"QUERY PROFILING REPORT - Query #{_query_count}")
    lines.append("=" * 80)
    lines.append("")
    baseline = marks[0].startTime
    prev = baseline
    api_request_sent_rel = 0.0
    first_chunk_rel = 0.0
    for m in marks:
        rel = m.startTime - baseline
        delta = m.startTime - prev
        mem = _memory_snapshots.get(m.name)
        lines.append(
            format_timeline_line(
                rel,
                delta,
                m.name,
                mem,
                10,
                9,
                _slow_warning(delta, m.name),
            )
        )
        if m.name == "query_api_request_sent":
            api_request_sent_rel = rel
        if m.name == "query_first_chunk_received":
            first_chunk_rel = rel
        prev = m.startTime
    lines.append("")
    lines.append("-" * 80)
    last = marks[-1].startTime - baseline
    if first_chunk_rel > 0:
        pre_req = api_request_sent_rel
        net = first_chunk_rel - api_request_sent_rel
        pct_pre = (pre_req / first_chunk_rel * 100) if first_chunk_rel else 0
        pct_net = (net / first_chunk_rel * 100) if first_chunk_rel else 0
        lines.append(f"Total TTFT: {format_ms(first_chunk_rel)}ms")
        lines.append(f"  - Pre-request overhead: {format_ms(pre_req)}ms ({pct_pre:.1f}%)")
        lines.append(f"  - Network latency: {format_ms(net)}ms ({pct_net:.1f}%)")
    else:
        lines.append(f"Total time: {format_ms(last)}ms")
    lines.append(_phase_summary(marks, baseline))
    lines.append("=" * 80)
    return "\n".join(lines)


def log_query_profile_report() -> None:
    if not _enabled():
        return
    log_for_debugging(_report())
