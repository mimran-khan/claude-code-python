"""
Subprocess helpers: scrubbed child env (``subprocess_env``) and async execution.

TS uses ``subprocessEnv.ts``; this module adds an asyncio wrapper with timeouts.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Mapping
from dataclasses import dataclass

from .subprocess_env import (
    register_upstream_proxy_env_fn,
    subprocess_env,
)

__all__ = [
    "register_upstream_proxy_env_fn",
    "subprocess_env",
    "AsyncSubprocessResult",
    "run_async",
]


@dataclass(frozen=True)
class AsyncSubprocessResult:
    """Completed process outcome from :func:`run_async`."""

    returncode: int
    stdout: str
    stderr: str


async def run_async(
    argv: list[str],
    *,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
) -> AsyncSubprocessResult:
    """
    Run ``argv[0]`` with arguments via :func:`asyncio.create_subprocess_exec`.

    Uses :func:`subprocess_env` as the base environment when ``env`` is omitted.
    On timeout, the process is killed and ``returncode`` is set to ``-9``.
    """
    if not argv:
        raise ValueError("argv must contain at least the executable")

    base = subprocess_env()
    if env is not None:
        base.update(env)
    proc = await asyncio.create_subprocess_exec(
        argv[0],
        *argv[1:],
        cwd=cwd,
        env=base,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        if timeout is not None:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        else:
            stdout_b, stderr_b = await proc.communicate()
    except TimeoutError:
        proc.kill()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        return AsyncSubprocessResult(-9, "", "timed out")

    rc = proc.returncode if proc.returncode is not None else -1
    return AsyncSubprocessResult(
        rc,
        stdout_b.decode("utf-8", errors="replace"),
        stderr_b.decode("utf-8", errors="replace"),
    )
