"""
Ripgrep utilities.

Provides functions for using ripgrep for fast file searching.

Migrated from: utils/ripgrep.ts (680 lines)
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from .platform import get_platform

MAX_BUFFER_SIZE = 20_000_000  # 20MB


class RipgrepTimeoutError(Exception):
    """Error for ripgrep timeouts."""

    def __init__(self, message: str, partial_results: list[str]):
        super().__init__(message)
        self.partial_results = partial_results


@dataclass
class RipgrepConfig:
    """Ripgrep configuration."""

    mode: str  # 'system' | 'builtin'
    command: str
    args: list[str]


@lru_cache(maxsize=1)
def get_ripgrep_config() -> RipgrepConfig:
    """
    Get the ripgrep configuration.

    Returns:
        RipgrepConfig with the ripgrep command and arguments.
    """
    # Try to find system ripgrep
    rg_path = shutil.which("rg")
    if rg_path:
        return RipgrepConfig(mode="system", command="rg", args=[])

    # Fall back to error
    return RipgrepConfig(mode="not_found", command="rg", args=[])


def ripgrep_command() -> tuple[str, list[str]]:
    """
    Get the ripgrep command and arguments.

    Returns:
        Tuple of (command, args).
    """
    config = get_ripgrep_config()
    return (config.command, config.args)


def _is_eagain_error(stderr: str) -> bool:
    """Check if an error is EAGAIN (resource temporarily unavailable)."""
    return "os error 11" in stderr or "Resource temporarily unavailable" in stderr


async def ripgrep(
    args: list[str],
    target: str,
    *,
    timeout_ms: int | None = None,
) -> list[str]:
    """
    Run ripgrep and return matching lines.

    Args:
        args: Ripgrep arguments.
        target: Target directory or file.
        timeout_ms: Optional timeout in milliseconds.

    Returns:
        List of matching lines.

    Raises:
        RipgrepTimeoutError: If ripgrep times out.
    """
    rg_cmd, rg_args = ripgrep_command()

    # Set default timeout based on platform
    if timeout_ms is None:
        platform = get_platform()
        timeout_ms = 60_000 if platform == "wsl" else 20_000

    timeout_sec = timeout_ms / 1000.0

    full_args = rg_args + args + [target]

    try:
        process = await asyncio.create_subprocess_exec(
            rg_cmd,
            *full_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=MAX_BUFFER_SIZE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_sec,
            )
        except TimeoutError:
            with contextlib.suppress(Exception):
                process.kill()

            raise RipgrepTimeoutError(
                f"Ripgrep search timed out after {timeout_ms}ms",
                [],
            )

        # Exit code 1 is "no matches" - normal
        if process.returncode in (0, 1):
            output = stdout.decode("utf-8", errors="replace")
            lines = [line.rstrip("\r") for line in output.strip().split("\n") if line]
            return lines

        # Check for EAGAIN error
        stderr_text = stderr.decode("utf-8", errors="replace")
        if _is_eagain_error(stderr_text):
            # Retry with single-threaded mode
            return await ripgrep(
                ["-j", "1"] + args,
                target,
                timeout_ms=timeout_ms,
            )

        # Return empty list for other errors
        return []

    except FileNotFoundError:
        raise RuntimeError("ripgrep (rg) not found. Please install ripgrep.")
    except Exception as e:
        if isinstance(e, RipgrepTimeoutError):
            raise
        return []


async def ripgrep_stream(
    args: list[str],
    target: str,
    on_lines: Callable[[list[str]], None],
    *,
    timeout_ms: int | None = None,
) -> None:
    """
    Stream lines from ripgrep as they arrive.

    Args:
        args: Ripgrep arguments.
        target: Target directory or file.
        on_lines: Callback for each batch of lines.
        timeout_ms: Optional timeout in milliseconds.
    """
    rg_cmd, rg_args = ripgrep_command()

    full_args = rg_args + args + [target]

    try:
        process = await asyncio.create_subprocess_exec(
            rg_cmd,
            *full_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        remainder = ""

        while True:
            chunk = await process.stdout.read(65536)  # 64KB chunks
            if not chunk:
                break

            data = remainder + chunk.decode("utf-8", errors="replace")
            lines = data.split("\n")
            remainder = lines.pop() or ""

            if lines:
                on_lines([line.rstrip("\r") for line in lines])

        # Flush remainder
        if remainder:
            on_lines([remainder.rstrip("\r")])

        await process.wait()

    except FileNotFoundError:
        raise RuntimeError("ripgrep (rg) not found. Please install ripgrep.")


async def count_files_rounded_rg(
    dir_path: str,
    *,
    ignore_patterns: list[str] | None = None,
    timeout_ms: int = 10_000,
) -> int | None:
    """
    Count files in a directory using ripgrep, rounded to nearest power of 10.

    Args:
        dir_path: Directory to count files in.
        ignore_patterns: Optional patterns to ignore.
        timeout_ms: Timeout in milliseconds.

    Returns:
        Rounded file count, or None if error.
    """
    # Skip if home directory (avoid macOS TCC dialogs)
    if os.path.abspath(dir_path) == os.path.expanduser("~"):
        return None

    args = ["--files", "--hidden"]

    if ignore_patterns:
        for pattern in ignore_patterns:
            args.extend(["--glob", f"!{pattern}"])

    try:
        lines = await ripgrep(args, dir_path, timeout_ms=timeout_ms)
        count = len(lines)

        if count == 0:
            return 0

        # Round to nearest power of 10
        import math

        magnitude = int(math.floor(math.log10(count)))
        power = 10**magnitude
        return round(count / power) * power

    except Exception:
        return None


def get_ripgrep_status() -> dict[str, str | bool | None]:
    """
    Get ripgrep status and configuration info.

    Returns:
        Dict with mode, path, and working status.
    """
    config = get_ripgrep_config()

    # Test if ripgrep works
    working = None
    try:
        result = subprocess.run(
            [config.command, "--version"],
            capture_output=True,
            timeout=5,
        )
        working = result.returncode == 0 and result.stdout.decode().startswith("ripgrep ")
    except Exception:
        working = False

    return {
        "mode": config.mode,
        "path": config.command,
        "working": working,
    }
