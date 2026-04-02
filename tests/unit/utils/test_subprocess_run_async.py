"""Unit tests for ``claude_code.utils.subprocess`` and ``subprocess_env``."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import claude_code.utils.subprocess_env as subprocess_env_mod
from claude_code.utils.subprocess import AsyncSubprocessResult, run_async
from claude_code.utils.subprocess_env import register_upstream_proxy_env_fn, subprocess_env


@pytest.fixture(autouse=True)
def _reset_upstream_proxy() -> None:
    yield
    subprocess_env_mod._get_upstream_proxy_env = None  # type: ignore[assignment]


def test_subprocess_env_passes_through_without_scrub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    env = subprocess_env()
    assert env.get("ANTHROPIC_API_KEY") == "secret"


def test_subprocess_env_scrub_strips_github_action_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "1")
    base = {
        "ANTHROPIC_API_KEY": "k",
        "INPUT_ANTHROPIC_API_KEY": "ik",
        "PATH": "/usr/bin",
        "REGULAR": "ok",
    }
    env = subprocess_env(base)
    assert "ANTHROPIC_API_KEY" not in env
    assert "INPUT_ANTHROPIC_API_KEY" not in env
    assert env["PATH"] == "/usr/bin"
    assert env["REGULAR"] == "ok"


def test_subprocess_env_merges_upstream_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", raising=False)

    def proxy() -> dict[str, str]:
        return {"HTTP_PROXY": "http://p"}

    register_upstream_proxy_env_fn(proxy)
    env = subprocess_env({"FOO": "bar"})
    assert env["HTTP_PROXY"] == "http://p"
    assert env["FOO"] == "bar"


@pytest.mark.asyncio
async def test_run_async_raises_on_empty_argv() -> None:
    with pytest.raises(ValueError, match="at least the executable"):
        await run_async([])


@pytest.mark.asyncio
async def test_run_async_success_decodes_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", raising=False)
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"out", b"err"))
    proc.returncode = 0
    with patch("claude_code.utils.subprocess.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        res = await run_async(["echo", "hi"])
    assert isinstance(res, AsyncSubprocessResult)
    assert res.returncode == 0
    assert res.stdout == "out"
    assert res.stderr == "err"


@pytest.mark.asyncio
async def test_run_async_merges_custom_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", raising=False)
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"", b""))
    proc.returncode = 0
    mock_exec = AsyncMock(return_value=proc)
    with patch("claude_code.utils.subprocess.asyncio.create_subprocess_exec", new=mock_exec):
        await run_async(["true"], env={"ZZ": "1"})
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["env"]["ZZ"] == "1"


@pytest.mark.asyncio
async def test_run_async_timeout_returns_minus_nine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", raising=False)
    proc = MagicMock()
    proc.communicate = AsyncMock(side_effect=TimeoutError)
    proc.kill = MagicMock()
    proc.wait = AsyncMock(return_value=0)
    with patch("claude_code.utils.subprocess.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        res = await run_async(["sleep", "9"], timeout=0.01)
    assert res.returncode == -9
    assert "timed out" in res.stderr


@pytest.mark.asyncio
async def test_run_async_wait_second_timeout_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", raising=False)
    proc = MagicMock()
    proc.communicate = AsyncMock(side_effect=TimeoutError)
    proc.kill = MagicMock()

    async def bad_wait() -> None:
        raise TimeoutError

    proc.wait = AsyncMock(side_effect=bad_wait)
    with patch("claude_code.utils.subprocess.asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        res = await run_async(["x"], timeout=0.01)
    assert res.returncode == -9
