"""
Shell execution utilities.

Functions for executing shell commands.

Migrated from: utils/shell.ts (475 lines)
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field

from .debug import log_for_debugging
from .errors import ShellError
from .log import log_error

DEFAULT_TIMEOUT = 30 * 60  # 30 minutes in seconds


@dataclass
class ExecResult:
    """Result of a shell command execution."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    interrupted: bool = False


@dataclass
class ShellConfig:
    """Shell configuration."""

    shell_path: str = "/bin/bash"
    shell_args: list[str] = field(default_factory=lambda: ["-c"])


def is_executable(path: str) -> bool:
    """Check if a file is executable."""
    try:
        return os.access(path, os.X_OK)
    except Exception:
        return False


async def find_suitable_shell() -> str:
    """
    Find the best available shell to use.

    Prefers zsh, falls back to bash.
    """
    # Check for explicit override
    shell_override = os.getenv("CLAUDE_CODE_SHELL")
    if shell_override:
        if is_executable(shell_override):
            log_for_debugging(f"Using shell override: {shell_override}")
            return shell_override
        log_for_debugging(f"CLAUDE_CODE_SHELL={shell_override} is not valid, falling back")

    # Check user's preferred shell
    env_shell = os.getenv("SHELL")
    prefer_bash = env_shell and "bash" in env_shell

    # Try to find shells
    zsh_path = shutil.which("zsh")
    bash_path = shutil.which("bash")

    # Order based on preference
    if prefer_bash:
        if bash_path and is_executable(bash_path):
            return bash_path
        if zsh_path and is_executable(zsh_path):
            return zsh_path
    else:
        if zsh_path and is_executable(zsh_path):
            return zsh_path
        if bash_path and is_executable(bash_path):
            return bash_path

    # Fallback paths
    for shell in ["/bin/zsh", "/bin/bash", "/usr/bin/zsh", "/usr/bin/bash"]:
        if is_executable(shell):
            return shell

    raise RuntimeError("No suitable shell found")


def get_shell_config() -> ShellConfig:
    """Get the shell configuration."""
    shell_path = os.getenv("SHELL", "/bin/bash")
    return ShellConfig(shell_path=shell_path)


async def exec_command(
    command: str,
    *,
    cwd: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    on_progress: Callable[[str, str, int, int, bool], None] | None = None,
    on_stdout: Callable[[str], None] | None = None,
    env: dict[str, str] | None = None,
) -> ExecResult:
    """
    Execute a shell command asynchronously.

    Args:
        command: The command to execute
        cwd: Working directory
        timeout: Timeout in seconds
        on_progress: Progress callback (last_lines, all_lines, total_lines, total_bytes, is_incomplete)
        on_stdout: Stdout callback for streaming
        env: Additional environment variables

    Returns:
        ExecResult with stdout, stderr, and exit code
    """
    shell_path = await find_suitable_shell()

    # Build environment
    exec_env = dict(os.environ)
    if env:
        exec_env.update(env)

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=exec_env,
            shell=True,
            executable=shell_path,
        )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            stdout = stdout_data.decode("utf-8", errors="replace")
            stderr = stderr_data.decode("utf-8", errors="replace")

            if on_stdout:
                on_stdout(stdout)

            return ExecResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode or 0,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return ExecResult(
                stdout="",
                stderr="Command timed out",
                exit_code=-1,
                timed_out=True,
            )
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            return ExecResult(
                stdout="",
                stderr="Command cancelled",
                exit_code=-1,
                interrupted=True,
            )
    except Exception as e:
        log_error(e)
        return ExecResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
        )


def exec_sync(
    command: str,
    *,
    cwd: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
    check: bool = False,
) -> ExecResult:
    """
    Execute a shell command synchronously.

    Args:
        command: The command to execute
        cwd: Working directory
        timeout: Timeout in seconds
        env: Additional environment variables
        check: Raise exception on non-zero exit

    Returns:
        ExecResult with stdout, stderr, and exit code
    """
    exec_env = dict(os.environ)
    if env:
        exec_env.update(env)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            env=exec_env,
        )

        exec_result = ExecResult(
            stdout=result.stdout.decode("utf-8", errors="replace"),
            stderr=result.stderr.decode("utf-8", errors="replace"),
            exit_code=result.returncode,
        )

        if check and result.returncode != 0:
            raise ShellError(
                stdout=exec_result.stdout,
                stderr=exec_result.stderr,
                code=result.returncode,
                interrupted=False,
            )

        return exec_result
    except subprocess.TimeoutExpired:
        return ExecResult(
            stdout="",
            stderr="Command timed out",
            exit_code=-1,
            timed_out=True,
        )
    except Exception as e:
        log_error(e)
        return ExecResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
        )


async def exec_file(
    executable: str,
    args: list[str],
    *,
    cwd: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> ExecResult:
    """
    Execute a file directly (not through shell).

    Args:
        executable: Path to executable
        args: Command arguments
        cwd: Working directory
        timeout: Timeout in seconds
        env: Additional environment variables

    Returns:
        ExecResult with stdout, stderr, and exit code
    """
    exec_env = dict(os.environ)
    if env:
        exec_env.update(env)

    try:
        process = await asyncio.create_subprocess_exec(
            executable,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=exec_env,
        )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            return ExecResult(
                stdout=stdout_data.decode("utf-8", errors="replace"),
                stderr=stderr_data.decode("utf-8", errors="replace"),
                exit_code=process.returncode or 0,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            return ExecResult(
                stdout="",
                stderr="Command timed out",
                exit_code=-1,
                timed_out=True,
            )
    except Exception as e:
        log_error(e)
        return ExecResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
        )


def which(command: str) -> str | None:
    """Find the path to a command."""
    return shutil.which(command)


def escape_shell_arg(arg: str) -> str:
    """
    Escape a string for use as a shell argument.

    Uses single quotes with escaping for single quotes.
    """
    if not arg:
        return "''"

    # If no special characters, return as-is
    if arg.isalnum() or all(c in "-_./:" for c in arg):
        return arg

    # Escape single quotes and wrap in single quotes
    escaped = arg.replace("'", "'\\''")
    return f"'{escaped}'"


def join_shell_args(args: list[str]) -> str:
    """Join shell arguments with proper escaping."""
    return " ".join(escape_shell_arg(arg) for arg in args)
