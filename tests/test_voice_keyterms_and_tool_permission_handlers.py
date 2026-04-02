"""Tests for voice_keyterms and tool_permission_handlers (hook-adjacent ports)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from claude_code.event_handlers.tool_permission_handlers import (
    PERMISSION_DIALOG_GRACE_PERIOD_MS,
    permission_prompt_within_grace_period,
    run_coordinator_automated_permission_checks,
    run_swarm_worker_classifier_gate,
)
from claude_code.event_handlers.voice_keyterms import (
    GLOBAL_VOICE_KEYTERMS,
    get_voice_keyterms,
    split_identifier,
)


def test_split_identifier_camel_and_kebab() -> None:
    assert split_identifier("featVoiceKeyterms") == ["feat", "Voice", "Keyterms"]
    assert split_identifier("my-branch-name") == ["branch", "name"]
    assert split_identifier("ab") == []


def test_global_voice_keyterms_contains_mcp() -> None:
    assert "MCP" in GLOBAL_VOICE_KEYTERMS


@pytest.mark.asyncio
async def test_get_voice_keyterms_respects_cap_and_recent_files() -> None:
    huge = {f"src/file{n}.ts" for n in range(100)}
    with (
        patch(
            "claude_code.services.voice_keyterms.get_project_root",
            return_value="",
        ),
        patch(
            "claude_code.services.voice_keyterms.get_branch",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        terms = await get_voice_keyterms(huge)
    assert len(terms) <= 50


def test_permission_prompt_within_grace_period() -> None:
    start = 1_000_000.0
    assert permission_prompt_within_grace_period(start, now_ms=start + 50) is True
    assert (
        permission_prompt_within_grace_period(
            start, now_ms=start + PERMISSION_DIALOG_GRACE_PERIOD_MS + 1
        )
        is False
    )


@pytest.mark.asyncio
async def test_run_coordinator_returns_hook_first() -> None:
    sentinel = object()

    async def run_hooks(_m, _s, _u):
        return sentinel

    async def try_classifier(_p, _u):
        raise AssertionError("classifier should not run when hooks resolve")

    out = await run_coordinator_automated_permission_checks(
        permission_mode="default",
        suggestions=None,
        updated_input=None,
        run_hooks=run_hooks,
        try_classifier=try_classifier,
        pending_classifier_check=None,
        bash_classifier_enabled=True,
    )
    assert out is sentinel


@pytest.mark.asyncio
async def test_run_coordinator_falls_through_to_classifier() -> None:
    class _D:
        pass

    d = _D()

    async def run_hooks(_m, _s, _u):
        return None

    async def try_classifier(_p, _u):
        return d

    out = await run_coordinator_automated_permission_checks(
        permission_mode=None,
        suggestions=[],
        updated_input={},
        run_hooks=run_hooks,
        try_classifier=try_classifier,
        pending_classifier_check={"x": 1},
        bash_classifier_enabled=True,
    )
    assert out is d


@pytest.mark.asyncio
async def test_run_coordinator_swallows_hook_exception() -> None:
    async def run_hooks(_m, _s, _u):
        raise RuntimeError("boom")

    out = await run_coordinator_automated_permission_checks(
        permission_mode=None,
        suggestions=None,
        updated_input=None,
        run_hooks=run_hooks,
        try_classifier=None,
        pending_classifier_check=None,
        bash_classifier_enabled=False,
    )
    assert out is None


@pytest.mark.asyncio
async def test_run_swarm_worker_classifier_gate_disabled() -> None:
    async def never(_a, _b):
        raise AssertionError

    out = await run_swarm_worker_classifier_gate(
        bash_classifier_enabled=False,
        try_classifier=never,
        pending_classifier_check=None,
        updated_input={},
    )
    assert out is None
