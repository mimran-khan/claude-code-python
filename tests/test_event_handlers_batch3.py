"""Tests for remaining hook → event_handlers ports (batch 3)."""

from __future__ import annotations

import asyncio

import pytest

from claude_code.event_handlers.auto_mode_unavailable_notification import (
    wrapped_past_auto_slot,
)
from claude_code.event_handlers.blink import blink_visible
from claude_code.event_handlers.diff_data import (
    GitDiffResult,
    GitDiffStats,
    build_diff_data,
)
from claude_code.event_handlers.diff_in_ide import (
    compute_edits_from_contents,
    ide_rpc_is_file_saved,
    ide_rpc_is_tab_closed,
)
from claude_code.event_handlers.double_press import (
    DOUBLE_PRESS_TIMEOUT_MS,
    DoublePressController,
)
from claude_code.event_handlers.elapsed_time import format_elapsed_time_ms
from claude_code.event_handlers.permission_context import create_resolve_once
from claude_code.event_handlers.teammate_lifecycle_notification import (
    is_in_process_teammate_task,
)
from claude_code.tools.file_edit_tool.edit_utils import get_edits_for_patch
from claude_code.tools.file_edit_tool.types import StructuredPatchHunk


def test_get_edits_for_patch_rebuilds_file_edit() -> None:
    hunk = StructuredPatchHunk(
        old_start=1,
        old_lines=1,
        new_start=1,
        new_lines=1,
        lines=[" old", "-a", "+b"],
    )
    edits = get_edits_for_patch([hunk])
    assert len(edits) == 1
    assert edits[0].old_string == "old\na"
    assert edits[0].new_string == "old\nb"


def test_build_diff_data_flags_large_and_truncated() -> None:
    stats = GitDiffStats(files_changed=1, insertions=2, deletions=2)
    result = GitDiffResult(
        stats=stats,
        per_file_stats={
            "a.py": {"added": 500, "removed": 0, "is_binary": False},
            "b.bin": {"added": 1, "removed": 0, "is_binary": True},
        },
    )
    hunks = {"a.py": [StructuredPatchHunk(0, 0, 0, 0, [])]}
    data = build_diff_data(result, hunks, loading=False)
    by_path = {f.path: f for f in data.files}
    assert by_path["a.py"].is_truncated is True
    assert by_path["b.bin"].is_binary is True


def test_blink_visible_alternates() -> None:
    assert blink_visible(0, interval_ms=600) is True
    assert blink_visible(600, interval_ms=600) is False


def test_format_elapsed_time_ms_with_end_time() -> None:
    s = format_elapsed_time_ms(1000.0, end_time_ms=61_000.0)
    assert "1m" in s


@pytest.mark.asyncio
async def test_create_resolve_once_single_delivery() -> None:
    out: list[int] = []

    def resolve(x: int) -> None:
        out.append(x)

    ro = create_resolve_once(resolve)
    assert ro.claim() is True
    assert ro.claim() is False
    ro.resolve(1)
    ro.resolve(2)
    assert out == [1]


def test_wrapped_past_auto_slot_detection() -> None:
    assert wrapped_past_auto_slot(
        mode="default",
        prev_mode="plan",
        is_auto_mode_available=False,
        has_auto_mode_opt_in=True,
    )
    assert not wrapped_past_auto_slot(
        mode="default",
        prev_mode="default",
        is_auto_mode_available=False,
        has_auto_mode_opt_in=True,
    )


def test_is_in_process_teammate_task() -> None:
    assert is_in_process_teammate_task({"type": "in_process_teammate"})
    assert not is_in_process_teammate_task({"type": "local_agent"})


def test_compute_edits_from_contents_round_trip() -> None:
    edits = compute_edits_from_contents(
        "f.txt",
        "hello\n",
        "hello\nworld\n",
        edit_mode="multiple",
    )
    assert len(edits) >= 1


def test_ide_rpc_is_tab_closed() -> None:
    assert ide_rpc_is_tab_closed([{"type": "text", "text": "TAB_CLOSED"}])
    assert not ide_rpc_is_tab_closed([])


def test_ide_rpc_is_file_saved() -> None:
    data = [{"type": "text", "text": "FILE_SAVED"}, {"type": "text", "text": "x"}]
    assert ide_rpc_is_file_saved(data)


@pytest.mark.asyncio
async def test_double_press_controller_second_press_fires() -> None:
    fired: list[str] = []

    async def on_double() -> None:
        fired.append("x")

    c = DoublePressController(on_double_press=on_double)
    await c.press()
    await asyncio.sleep(0.01)
    await c.press()
    assert fired == ["x"]
    assert DOUBLE_PRESS_TIMEOUT_MS == 800
