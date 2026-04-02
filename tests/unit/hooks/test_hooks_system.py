"""Unit tests for hook registry, executor, and hook types."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from claude_code.hooks import executor as hook_executor
from claude_code.hooks import registry as hook_registry
from claude_code.hooks.types import (
    AggregatedHookResult,
    HookBlockingError,
    HookResult,
    is_hook_event,
    is_async_hook_output,
    is_sync_hook_output,
)


@pytest.fixture(autouse=True)
def clear_global_hooks() -> None:
    hook_registry.clear_hooks()
    yield
    hook_registry.clear_hooks()


def test_hook_registry_register_and_unregister() -> None:
    reg = hook_registry.HookRegistry()

    async def cb(_data, _tid):
        return {"continue": True}

    hid = reg.register("SessionStart", cb, name="h1")
    assert hid == "h1"
    assert len(reg.get_hooks("SessionStart")) == 1
    assert reg.unregister("SessionStart", "h1") is True
    assert reg.get_hooks("SessionStart") == []


def test_hook_registry_matcher_filters_by_tool_name() -> None:
    reg = hook_registry.HookRegistry()

    async def cb(_d, _t):
        return {"continue": True}

    reg.register("PreToolUse", cb, name="any", matcher=None)
    reg.register("PreToolUse", cb, name="bash_only", matcher="Bash")
    matched = reg.get_matching_hooks("PreToolUse", tool_name="Bash_run")
    assert {h.name for h in matched} == {"any", "bash_only"}
    matched_glob = reg.get_matching_hooks("PreToolUse", tool_name="Read")
    assert {h.name for h in matched_glob} == {"any"}


@pytest.mark.asyncio
async def test_execute_single_hook_success_maps_fields() -> None:
    async def cb(_inp, _tid):
        return {
            "additionalContext": "ctx",
            "updatedInput": {"x": 1},
            "permissionDecision": "allow",
            "stopReason": "user",
            "continue": False,
        }

    hook = hook_registry.RegisteredHook(
        event="PreToolUse",
        callback=cb,
        name="n1",
        timeout=5.0,
    )
    result = await hook_executor.execute_single_hook(hook, {})
    assert result.outcome == "success"
    assert result.additional_context == "ctx"
    assert result.updated_input == {"x": 1}
    assert result.permission_behavior == "allow"
    assert result.stop_reason == "user"
    assert result.prevent_continuation is True


@pytest.mark.asyncio
async def test_execute_single_hook_timeout_returns_non_blocking_error() -> None:
    async def slow_cb(_inp, _tid):
        await asyncio.sleep(10)
        return {"continue": True}

    hook = hook_registry.RegisteredHook(
        event="PreToolUse",
        callback=slow_cb,
        name="slow",
        timeout=0.01,
    )
    result = await hook_executor.execute_single_hook(hook, {})
    assert result.outcome == "non_blocking_error"
    assert result.blocking_error is not None
    assert "timed out" in (result.blocking_error.blocking_error or "")


@pytest.mark.asyncio
async def test_execute_single_hook_exception_non_blocking() -> None:
    async def bad_cb(_inp, _tid):
        raise RuntimeError("boom")

    hook = hook_registry.RegisteredHook(event="PreToolUse", callback=bad_cb, name="bad")
    with patch.object(hook_executor, "_LOG") as mock_log:
        result = await hook_executor.execute_single_hook(hook, {})
    mock_log.warning.assert_called_once()
    assert result.outcome == "non_blocking_error"
    assert result.blocking_error is not None
    assert "boom" in (result.blocking_error.blocking_error or "")


def test_aggregate_hook_results_merges_permission_and_retry() -> None:
    r1 = HookResult(
        permission_behavior="deny",
        hook_permission_decision_reason="r1",
        retry=True,
    )
    r2 = HookResult(
        additional_context="a",
        prevent_continuation=True,
        stop_reason="stop",
    )
    agg = hook_executor.aggregate_hook_results([r1, r2])
    assert isinstance(agg, AggregatedHookResult)
    assert agg.permission_behavior == "deny"
    assert agg.hook_permission_decision_reason == "r1"
    assert agg.retry is True
    assert agg.prevent_continuation is True
    assert agg.stop_reason == "stop"
    assert agg.additional_contexts == ["a"]


@pytest.mark.asyncio
async def test_execute_hooks_empty_returns_empty_aggregate() -> None:
    with patch.object(hook_executor, "get_hooks_for_event", return_value=[]):
        out = await hook_executor.execute_hooks("PreToolUse", {})
    assert isinstance(out, AggregatedHookResult)
    assert out.blocking_errors == []


@pytest.mark.asyncio
async def test_execute_pre_and_post_tool_hooks_delegate() -> None:
    mock_agg = AggregatedHookResult(retry=True)
    with patch.object(hook_executor, "execute_hooks", new=AsyncMock(return_value=mock_agg)) as ex:
        pre = await hook_executor.execute_pre_tool_hooks("t", {}, "id-1")
        post = await hook_executor.execute_post_tool_hooks("t", {}, "out", "id-2")
    assert pre is mock_agg and post is mock_agg
    assert ex.await_count == 2


def test_is_hook_event_and_sync_async_helpers() -> None:
    assert is_hook_event("PreToolUse") is True
    assert is_hook_event("NotAnEvent") is False
    assert is_sync_hook_output({}) is True
    assert is_sync_hook_output({"async": True}) is False
    assert is_async_hook_output({"async": True}) is True
