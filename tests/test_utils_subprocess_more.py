"""Additional tests for claude_code.utils.subprocess.run_async."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claude_code.utils.subprocess import AsyncSubprocessResult, run_async


@pytest.mark.asyncio
async def test_run_async_rejects_empty_argv() -> None:
    with pytest.raises(ValueError, match="at least the executable"):
        await run_async([])


@pytest.mark.asyncio
@patch("claude_code.utils.subprocess.asyncio.create_subprocess_exec", new_callable=AsyncMock)
async def test_run_async_success_decodes_stdout(mock_cpe) -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"hello\n", b""))
    proc.returncode = 0
    mock_cpe.return_value = proc

    with patch(
        "claude_code.utils.subprocess.subprocess_env",
        return_value={**__import__("os").environ, "TEST": "1"},
    ):
        r = await run_async(["/bin/echo", "hi"], timeout=5.0)

    assert isinstance(r, AsyncSubprocessResult)
    assert r.returncode == 0
    assert r.stdout == "hello\n"
    assert r.stderr == ""
    mock_cpe.assert_called_once()
    _args, kwargs = mock_cpe.call_args
    assert kwargs["env"]["TEST"] == "1"


@pytest.mark.asyncio
@patch("claude_code.utils.subprocess.asyncio.create_subprocess_exec", new_callable=AsyncMock)
async def test_run_async_merges_explicit_env_over_base(mock_cpe) -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock(return_value=(b"", b""))
    proc.returncode = 0
    mock_cpe.return_value = proc

    with patch("claude_code.utils.subprocess.subprocess_env", return_value={"BASE": "1"}):
        await run_async(["/bin/true"], env={"BASE": "2", "OTHER": "x"})

    _args, kwargs = mock_cpe.call_args
    assert kwargs["env"]["BASE"] == "2"
    assert kwargs["env"]["OTHER"] == "x"


@pytest.mark.asyncio
@patch("claude_code.utils.subprocess.asyncio.create_subprocess_exec", new_callable=AsyncMock)
async def test_run_async_timeout_sets_minus_nine(mock_cpe) -> None:
    proc = MagicMock()
    proc.communicate = AsyncMock()
    proc.kill = MagicMock()
    proc.wait = AsyncMock()
    mock_cpe.return_value = proc

    async def fake_wait_for(aw: object, timeout: float | None = None) -> None:
        if asyncio.iscoroutine(aw):
            aw.close()
        raise TimeoutError

    with (
        patch("claude_code.utils.subprocess.asyncio.wait_for", side_effect=fake_wait_for),
        patch("claude_code.utils.subprocess.subprocess_env", return_value={}),
    ):
        r = await run_async(["/bin/sleep", "9"], timeout=0.01)

    assert r.returncode == -9
    assert "timed out" in r.stderr
