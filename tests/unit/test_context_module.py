"""Unit tests for ``claude_code.context`` (prompt injection, caches, async context builders)."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code import context as context_mod


@pytest.fixture(autouse=True)
def _reset_context_state() -> None:
    context_mod.set_system_prompt_injection(None)
    context_mod.clear_context_caches()
    yield
    context_mod.set_system_prompt_injection(None)
    context_mod.clear_context_caches()


def test_get_set_system_prompt_injection_roundtrip() -> None:
    assert context_mod.get_system_prompt_injection() is None
    context_mod.set_system_prompt_injection("break-cache")
    assert context_mod.get_system_prompt_injection() == "break-cache"


def test_set_system_prompt_injection_clears_lru_caches() -> None:
    # Prime caches with a sentinel by calling cache_clear then relying on injection
    context_mod.get_git_status.cache_clear()
    context_mod.set_system_prompt_injection("v1")
    context_mod.set_system_prompt_injection("v2")
    assert context_mod.get_system_prompt_injection() == "v2"


@pytest.mark.asyncio
async def test_get_git_status_returns_none_under_pytest_env() -> None:
    assert await context_mod.get_git_status() is None


@pytest.mark.asyncio
async def test_get_git_status_builds_snapshot_when_git_available() -> None:
    huge_status = "M file\n" * 1500

    async def fake_exec_git(cmd: list[str]) -> str:
        if "status" in cmd:
            return huge_status
        if "log" in cmd:
            return "abc123 msg"
        if "user.name" in cmd:
            return "tester"
        return ""

    with (
        patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "", "NODE_ENV": ""}, clear=False),
        patch(
            "claude_code.utils.git.get_is_git",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "claude_code.utils.git.get_branch",
            new=AsyncMock(return_value="feature/x"),
        ),
        patch(
            "claude_code.utils.git.get_default_branch_async",
            new=AsyncMock(return_value="main"),
        ),
        patch(
            "claude_code.utils.git.exec_git_command",
            new=AsyncMock(side_effect=fake_exec_git),
        ),
    ):
        context_mod.get_git_status.cache_clear()
        out = await context_mod.get_git_status()

    assert out is not None
    assert "Current branch: feature/x" in out
    assert "Main branch" in out
    assert "truncated" in out.lower()


@pytest.mark.asyncio
async def test_get_git_status_returns_none_when_not_git_repo() -> None:
    with (
        patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "", "NODE_ENV": ""}, clear=False),
        patch(
            "claude_code.utils.git.get_is_git",
            new=AsyncMock(return_value=False),
        ),
    ):
        context_mod.get_git_status.cache_clear()
        assert await context_mod.get_git_status() is None


@pytest.mark.asyncio
async def test_get_system_context_includes_injection_and_skips_git_when_remote() -> None:
    context_mod.set_system_prompt_injection("inj")
    with patch.dict(os.environ, {"CLAUDE_CODE_REMOTE": "1"}, clear=False):
        context_mod.get_system_context.cache_clear()
        ctx = await context_mod.get_system_context()

    assert "gitStatus" not in ctx
    assert ctx.get("cacheBreaker") == "[CACHE_BREAKER: inj]"


@pytest.mark.asyncio
async def test_get_user_context_sets_date_and_respects_claude_md_disable() -> None:
    with patch.dict(os.environ, {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1"}, clear=False):
        context_mod.get_user_context.cache_clear()
        ctx = await context_mod.get_user_context()

    assert "claudeMd" not in ctx
    assert "currentDate" in ctx
    assert ctx["currentDate"].startswith("Today's date is")


# Re-patch submodule imports used inside get_git_status
@pytest.mark.asyncio
async def test_get_git_status_logs_and_returns_none_on_git_failure() -> None:
    with (
        patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "", "NODE_ENV": ""}, clear=False),
        patch(
            "claude_code.utils.git.get_is_git",
            new=AsyncMock(side_effect=RuntimeError("git exploded")),
        ),
        patch("claude_code.context.log_for_diagnostics", MagicMock()),
        patch("claude_code.context.log_error", MagicMock()),
    ):
        context_mod.get_git_status.cache_clear()
        assert await context_mod.get_git_status() is None
