"""
Poll CCR for ExitPlanMode approval (/ultraplan).

Migrated from: utils/ultraplan/ccrSession.ts
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from claude_code.tools.exit_plan_mode_tool.constants import EXIT_PLAN_MODE_V2_TOOL_NAME

from ..sleep import sleep as async_sleep
from ..teleport.api import is_transient_network_error
from ..teleport.poll import poll_remote_session_events

logger = logging.getLogger(__name__)

POLL_INTERVAL_MS = 3000
MAX_CONSECUTIVE_FAILURES = 5

PollFailReason = Literal[
    "terminated",
    "timeout_pending",
    "timeout_no_plan",
    "extract_marker_missing",
    "network_or_unknown",
    "stopped",
]

ULTRAPLAN_TELEPORT_SENTINEL = "__ULTRAPLAN_TELEPORT_LOCAL__"


class UltraplanPollError(RuntimeError):
    def __init__(
        self,
        message: str,
        reason: PollFailReason,
        reject_count: int,
        *,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.reason: PollFailReason = reason
        self.reject_count = reject_count
        self.__cause__ = cause


@dataclass
class PollResult:
    plan: str
    reject_count: int
    execution_target: Literal["local", "remote"]


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for b in content:
            if isinstance(b, dict) and "text" in b:
                parts.append(str(b.get("text", "")))
        return "".join(parts)
    return ""


def _extract_teleport_plan(content: Any) -> str | None:
    text = _content_to_text(content)
    marker = f"{ULTRAPLAN_TELEPORT_SENTINEL}\n"
    idx = text.find(marker)
    if idx == -1:
        return None
    return text[idx + len(marker) :].rstrip()


def _extract_approved_plan(content: Any) -> str:
    text = _content_to_text(content)
    for marker in (
        "## Approved Plan (edited by user):\n",
        "## Approved Plan:\n",
    ):
        idx = text.find(marker)
        if idx != -1:
            return text[idx + len(marker) :].rstrip()
    raise RuntimeError(f"ExitPlanMode approved but tool_result has no Approved Plan marker; preview={text[:200]!r}")


ScanKind = Literal[
    "approved",
    "teleport",
    "rejected",
    "pending",
    "terminated",
    "unchanged",
]


@dataclass
class ScanResult:
    kind: ScanKind
    plan: str = ""
    id: str = ""
    subtype: str = ""


class ExitPlanModeScanner:
    def __init__(self) -> None:
        self._exit_plan_calls: list[str] = []
        self._results: dict[str, dict[str, Any]] = {}
        self._rejected_ids: set[str] = set()
        self._terminated: dict[str, str] | None = None
        self._rescan_after_rejection = False
        self.ever_seen_pending = False

    @property
    def reject_count(self) -> int:
        return len(self._rejected_ids)

    @property
    def has_pending_plan(self) -> bool:
        for uid in reversed(self._exit_plan_calls):
            if uid in self._rejected_ids:
                continue
            return uid not in self._results
        return False

    def ingest(self, new_events: list[dict[str, Any]]) -> ScanResult:
        for m in new_events:
            t = m.get("type")
            if t == "assistant":
                msg = m.get("message") or {}
                content = msg.get("content") or []
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") == EXIT_PLAN_MODE_V2_TOOL_NAME:
                        tid = block.get("id")
                        if isinstance(tid, str):
                            self._exit_plan_calls.append(tid)
            elif t == "user":
                msg = m.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_result":
                        continue
                    tuid = block.get("tool_use_id")
                    if isinstance(tuid, str):
                        self._results[tuid] = block
            elif t == "result" and m.get("subtype") != "success":
                self._terminated = {"subtype": str(m.get("subtype", "unknown"))}

        should_scan = bool(new_events) or self._rescan_after_rejection
        self._rescan_after_rejection = False

        found: ScanResult | None = None
        if should_scan:
            for i in range(len(self._exit_plan_calls) - 1, -1, -1):
                uid = self._exit_plan_calls[i]
                if uid in self._rejected_ids:
                    continue
                tr = self._results.get(uid)
                if not tr:
                    found = ScanResult("pending")
                elif tr.get("is_error") is True:
                    tp = _extract_teleport_plan(tr.get("content"))
                    found = ScanResult("teleport", plan=tp or "") if tp is not None else ScanResult("rejected", id=uid)
                else:
                    found = ScanResult("approved", plan=_extract_approved_plan(tr.get("content")))
                break
            if found and found.kind in ("approved", "teleport"):
                return found

        if found and found.kind == "rejected":
            self._rejected_ids.add(found.id)
            self._rescan_after_rejection = True
        if self._terminated:
            return ScanResult("terminated", subtype=self._terminated["subtype"])
        if found and found.kind == "rejected":
            return found
        if found and found.kind == "pending":
            self.ever_seen_pending = True
            return found
        return ScanResult("unchanged")


async def poll_for_approved_exit_plan_mode(
    session_id: str,
    timeout_ms: int,
    on_phase_change: Callable[[str], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> PollResult:
    deadline = time.monotonic() + timeout_ms / 1000.0
    scanner = ExitPlanModeScanner()
    cursor: str | None = None
    failures = 0
    last_phase = "running"

    while time.monotonic() < deadline:
        if should_stop and should_stop():
            raise UltraplanPollError("poll stopped by caller", "stopped", scanner.reject_count)
        try:
            resp = await poll_remote_session_events(session_id, cursor)
            new_events = resp.new_events
            cursor = resp.last_event_id
            session_status = resp.session_status
            failures = 0
        except Exception as e:
            transient = is_transient_network_error(e)
            failures += 1
            if not transient or failures >= MAX_CONSECUTIVE_FAILURES:
                raise UltraplanPollError(
                    str(e),
                    "network_or_unknown",
                    scanner.reject_count,
                    cause=e,
                ) from e
            await async_sleep(POLL_INTERVAL_MS / 1000.0)
            continue

        try:
            result = scanner.ingest(new_events)
        except Exception as e:
            raise UltraplanPollError(
                str(e),
                "extract_marker_missing",
                scanner.reject_count,
                cause=e,
            ) from e

        if result.kind == "approved":
            return PollResult(
                plan=result.plan,
                reject_count=scanner.reject_count,
                execution_target="remote",
            )
        if result.kind == "teleport":
            return PollResult(
                plan=result.plan,
                reject_count=scanner.reject_count,
                execution_target="local",
            )
        if result.kind == "terminated":
            raise UltraplanPollError(
                f"remote session ended ({result.subtype}) before plan approval",
                "terminated",
                scanner.reject_count,
            )

        quiet_idle = session_status in ("idle", "requires_action") and not new_events
        phase = "plan_ready" if scanner.has_pending_plan else ("needs_input" if quiet_idle else "running")
        if phase != last_phase:
            logger.debug("[ultraplan] phase %s → %s", last_phase, phase)
            last_phase = phase
            if on_phase_change:
                on_phase_change(phase)

        await async_sleep(POLL_INTERVAL_MS / 1000.0)

    msg = (
        f"no approval after {timeout_ms // 1000}s"
        if scanner.ever_seen_pending
        else (f"ExitPlanMode never reached after {timeout_ms // 1000}s (remote failed to start?)")
    )
    raise UltraplanPollError(
        msg,
        "timeout_pending" if scanner.ever_seen_pending else "timeout_no_plan",
        scanner.reject_count,
    )
