"""Tests for event_handlers batch 2 (hooks → Python)."""

from __future__ import annotations

import asyncio
import copy

import pytest

from claude_code.event_handlers.agent_progress import (
    create_progress_tracker,
    get_progress_update,
    get_token_count_from_tracker,
    update_progress_from_assistant_message,
)
from claude_code.event_handlers.auto_scroll import AutoScrollState
from claude_code.event_handlers.bridge_connection import BridgeConnectionHandler
from claude_code.event_handlers.bridge_status import bridge_status_snapshot
from claude_code.event_handlers.claude_ai_limits import ClaudeAiLimitsHandler
from claude_code.event_handlers.compact_warning import (
    CompactWarningHandler,
    watch_compact_warning_suppression,
)
from claude_code.event_handlers.connection_status import ide_connection_status
from claude_code.event_handlers.debug_mode import DebugModeHandler
from claude_code.event_handlers.effort_level import EffortLevelHandler
from claude_code.event_handlers.error_recovery import ErrorRecoveryHandler
from claude_code.services.compact.compact_warning_state import (
    clear_compact_warning_suppression,
    suppress_compact_warning,
)
from claude_code.services.limits.tracker import get_current_limits, update_limits
from claude_code.services.limits.types import ClaudeAILimits


def test_agent_progress_tracker_updates() -> None:
    t = create_progress_tracker()
    update_progress_from_assistant_message(
        t,
        usage={"input_tokens": 10, "output_tokens": 3},
        content=[
            {"type": "tool_use", "name": "Read", "input": {"path": "x"}},
        ],
    )
    assert t.tool_use_count == 1
    assert get_token_count_from_tracker(t) == 13
    pu = get_progress_update(t)
    assert pu.last_activity is not None
    assert pu.last_activity.tool_name == "Read"


def test_auto_scroll_sticky_bottom() -> None:
    s = AutoScrollState(viewport_height=10.0, content_height=100.0, sticky=True)
    s._last_max_scroll = s.max_scroll()
    s.notify_content_resized(200.0)
    assert s.sticky is True
    assert s.scroll_top == s.max_scroll()


def test_bridge_status_snapshot() -> None:
    r = bridge_status_snapshot(
        error=None, connected=True, session_active=False, reconnecting=False
    )
    assert r["color"] == "success"


@pytest.mark.asyncio
async def test_claude_ai_limits_handler_subscribe() -> None:
    orig = copy.deepcopy(get_current_limits())
    h = ClaudeAiLimitsHandler()
    await h.initialize()
    before = h.limits.quota_status
    lim2 = ClaudeAILimits(quota_status="allowed_warning" if before == "allowed" else "allowed")
    update_limits(lim2)
    assert h.limits.quota_status == lim2.quota_status
    await h.cleanup()
    update_limits(orig)


def test_compact_warning_handler_refresh() -> None:
    clear_compact_warning_suppression()
    h = CompactWarningHandler()
    assert h.suppressed is False
    suppress_compact_warning()
    assert h.refresh() is True


@pytest.mark.asyncio
async def test_watch_compact_warning_suppression() -> None:
    clear_compact_warning_suppression()
    seen: list[bool] = []
    stop = asyncio.Event()

    async def runner() -> None:
        await watch_compact_warning_suppression(
            lambda b: seen.append(b),
            poll_interval_s=0.01,
            stop=stop,
        )

    task = asyncio.create_task(runner())
    await asyncio.sleep(0.05)
    suppress_compact_warning()
    await asyncio.sleep(0.05)
    stop.set()
    await asyncio.wait_for(task, timeout=2.0)
    assert True in seen


def test_ide_connection_status_dict() -> None:
    clients = [
        {
            "name": "ide",
            "type": "connected",
            "config": {"type": "sse-ide", "ideName": "VSCode"},
        }
    ]
    r = ide_connection_status(clients)
    assert r.status == "connected"
    assert r.ide_name == "VSCode"


def test_debug_mode_handler_refresh() -> None:
    d = DebugModeHandler()
    d.refresh()
    assert isinstance(d.active, bool)


def test_effort_level_handler() -> None:
    e = EffortLevelHandler(model="claude-sonnet-4-20250514", app_state_effort="high")
    assert e.displayed_level in ("low", "medium", "high", "max")


def test_error_recovery_budget() -> None:
    e = ErrorRecoveryHandler()
    assert e.can_retry_max_output_tokens() is True
    assert e.record_max_output_tokens_recovery() is True
    e.reset_recovery_counters()
    assert e.max_output_tokens_recovery_count == 0


@pytest.mark.asyncio
async def test_bridge_connection_handler_fuse() -> None:
    h = BridgeConnectionHandler()
    h.consecutive_failures = 3
    assert await h.init_bridge() is None
