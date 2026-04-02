"""Tests for bash_tool (core.Tool implementation)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import pytest

from claude_code.core.tool import ToolUseContext
from claude_code.tools.bash_tool.bash_tool import (
    MAX_TIMEOUT_MS,
    BashTool,
    _coerce_timeout_ms,
    execute_bash,
)


def test_coerce_timeout_ms_defaults_and_clamps() -> None:
    assert _coerce_timeout_ms(None) == 120_000
    assert _coerce_timeout_ms("not-int") == 120_000
    assert _coerce_timeout_ms(1) == 1
    assert _coerce_timeout_ms(MAX_TIMEOUT_MS + 999_999) == MAX_TIMEOUT_MS


def test_bash_tool_validate_input_rejects_empty_command() -> None:
    tool = BashTool()
    bad = tool.validate_input({"command": "  "})
    assert bad.result is False
    assert "required" in bad.message.lower()
    good = tool.validate_input({"command": "echo hi"})
    assert good.result is True


@pytest.mark.asyncio
async def test_bash_tool_background_returns_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePopen:
        pid = 424242

        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    async def fake_to_thread(
        func: Callable[..., object],
        *args: object,
        **kwargs: object,
    ) -> object:
        return func(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(
        "claude_code.tools.bash_tool.bash_tool.subprocess.Popen",
        FakePopen,
    )
    tool = BashTool()
    ctx = ToolUseContext(options={})
    res = await tool.call(
        {"command": "sleep 9", "run_in_background": True},
        ctx,
        None,
    )
    assert "Background" in res.data.stdout
    assert "424242" in res.data.stdout


@pytest.mark.asyncio
async def test_bash_tool_success_via_mocked_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeProc:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"hello\n", b""

    async def fake_shell(*_a: object, **_kw: object) -> FakeProc:
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_shell", fake_shell)
    tool = BashTool()
    ctx = ToolUseContext(options={"cwd": "/"})
    res = await tool.call({"command": "echo ok"}, ctx, None)
    assert res.data.stdout == "hello\n"
    assert res.data.interrupted is False


@pytest.mark.asyncio
async def test_bash_tool_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    class SlowProc:
        returncode: int | None = None

        def kill(self) -> None:
            self.returncode = -9

        async def wait(self) -> None:
            return None

        async def communicate(self) -> tuple[bytes, bytes]:
            await asyncio.sleep(10)
            return b"", b""

    async def fake_shell(*_a: object, **_kw: object) -> SlowProc:
        return SlowProc()

    monkeypatch.setattr(asyncio, "create_subprocess_shell", fake_shell)
    tool = BashTool()
    ctx = ToolUseContext(options={})
    res = await tool.call({"command": "slow", "timeout": 50}, ctx, None)
    assert res.data.interrupted is True
    assert "timed out" in res.data.stderr.lower()


@pytest.mark.asyncio
async def test_execute_bash_delegates_to_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeProc:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"x", b""

    async def fake_shell(*_a: object, **_kw: object) -> FakeProc:
        return FakeProc()

    monkeypatch.setattr(asyncio, "create_subprocess_shell", fake_shell)
    ctx = ToolUseContext(options={})
    res = await execute_bash({"command": "true"}, ctx)
    assert res.data.stdout == "x"


def test_get_tool_use_summary_prefers_description() -> None:
    tool = BashTool()
    s = tool.get_tool_use_summary({"description": "Run tests", "command": "ignored"})
    assert "Run tests" in s
