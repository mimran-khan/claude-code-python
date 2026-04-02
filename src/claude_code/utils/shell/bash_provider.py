"""
Bash shell provider.

Migrated from: utils/shell/bashProvider.ts

Depends on :mod:`claude_code.utils.bash.shell_quoting` for POSIX quoting and NUL redirect rewrite.
Optional snapshot / session / tmux hooks load when those modules exist.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path, PurePosixPath

from claude_code.utils.api import windows_path_to_posix
from claude_code.utils.bash.shell_quote import quote
from claude_code.utils.bash.shell_quoting import (
    quote_shell_command,
    rewrite_windows_null_redirect,
    should_add_stdin_redirect,
)
from claude_code.utils.debug import log_for_debugging
from claude_code.utils.platform import get_platform

from .shell_provider import ExecBuildResult, ExecCommandOpts, ShellProvider, ShellType

_SNAPSHOT_NOT_LOADED = object()


def _format_shell_prefix_command(prefix: str, command: str) -> str:
    """Migrated from utils/bash/shellPrefix.ts (executable + optional args)."""
    space_before_dash = prefix.rfind(" -")
    if space_before_dash > 0:
        exec_path = prefix[:space_before_dash]
        args = prefix[space_before_dash + 1 :]
        return f"{quote([exec_path])} {args} {quote([command])}"
    return f"{quote([prefix])} {quote([command])}"


def _single_quote_for_eval(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"


def _rearrange_pipe_command(command: str) -> str:
    """
    Place stdin redirect after the first pipeline segment.

    When full shell-quote parse parity is unavailable, use the TS fallback:
    ``eval 'cmd' < /dev/null`` (single-quoted payload).
    """
    return _single_quote_for_eval(command) + " < /dev/null"


def _get_disable_extglob_command(shell_path: str) -> str | None:
    if os.environ.get("CLAUDE_CODE_SHELL_PREFIX"):
        return "{ shopt -u extglob || setopt NO_EXTENDED_GLOB; } >/dev/null 2>&1 || true"
    sp = shell_path.lower()
    if "bash" in sp:
        return "shopt -u extglob 2>/dev/null || true"
    if "zsh" in sp:
        return "setopt NO_EXTENDED_GLOB 2>/dev/null || true"
    return None


def _try_session_env_script() -> str | None:
    try:
        from claude_code.utils.session_environment import get_session_environment_script
    except ModuleNotFoundError:
        return None
    return get_session_environment_script()  # type: ignore[no-any-return]


def _try_session_env_vars() -> list[tuple[str, str]]:
    try:
        from claude_code.utils.session_environment import get_session_env_vars
    except ModuleNotFoundError:
        return []
    return list(get_session_env_vars())


async def _try_create_snapshot(shell_path: str) -> str | None:
    try:
        from claude_code.utils.bash.shell_snapshot import create_and_save_snapshot
    except ModuleNotFoundError:
        return None
    try:
        return await create_and_save_snapshot(shell_path)
    except Exception as exc:
        log_for_debugging(f"Failed to create shell snapshot: {exc}")
        return None


class BashProvider(ShellProvider):
    """Bash :class:`ShellProvider` implementation."""

    def __init__(
        self,
        shell_path: str,
        *,
        skip_snapshot: bool = False,
    ) -> None:
        self._shell_path = shell_path
        self._skip_snapshot = skip_snapshot
        self._snapshot_state: object | str | None = _SNAPSHOT_NOT_LOADED
        self._last_snapshot_file_path: str | None = None
        self._current_sandbox_tmp_dir: str | None = None

    @property
    def type(self) -> ShellType:
        return "bash"

    @property
    def shell_path(self) -> str:
        return self._shell_path

    @property
    def detached(self) -> bool:
        return True

    async def _get_snapshot_path(self) -> str | None:
        if self._snapshot_state is _SNAPSHOT_NOT_LOADED:
            if self._skip_snapshot:
                self._snapshot_state = None
            else:
                self._snapshot_state = await _try_create_snapshot(self._shell_path)
        if self._snapshot_state is None:
            return None
        path = self._snapshot_state  # type: ignore[assignment]
        if isinstance(path, str) and path:
            try:
                if Path(path).is_file():
                    return path
            except OSError:
                pass
            log_for_debugging(f"Snapshot file missing, falling back to login shell: {path}")
            return None
        return None

    async def build_exec_command(
        self,
        command: str,
        opts: ExecCommandOpts,
    ) -> ExecBuildResult:
        snapshot_file_path = await self._get_snapshot_path()
        if snapshot_file_path:
            self._last_snapshot_file_path = snapshot_file_path
        else:
            self._last_snapshot_file_path = None

        self._current_sandbox_tmp_dir = opts.sandbox_tmp_dir

        tmpdir = tempfile.gettempdir()
        is_windows = get_platform() == "windows"
        shell_tmpdir = windows_path_to_posix(tmpdir) if is_windows else tmpdir

        if opts.use_sandbox:
            if not opts.sandbox_tmp_dir:
                raise ValueError("use_sandbox requires sandbox_tmp_dir")
            sand = opts.sandbox_tmp_dir.replace("\\", "/")
            shell_cwd_file_path = str(PurePosixPath(sand) / f"cwd-{opts.id}")
            cwd_file_path = str(Path(opts.sandbox_tmp_dir) / f"cwd-{opts.id}")
        else:
            shell_cwd_file_path = str(PurePosixPath(shell_tmpdir) / f"claude-{opts.id}-cwd")
            cwd_file_path = str(Path(tmpdir) / f"claude-{opts.id}-cwd")

        normalized = rewrite_windows_null_redirect(command)
        add_stdin = should_add_stdin_redirect(normalized)
        quoted_command = quote_shell_command(normalized, add_stdin)

        if "|" in normalized and add_stdin:
            quoted_command = _rearrange_pipe_command(normalized)

        command_parts: list[str] = []
        if snapshot_file_path:
            final_path = (
                windows_path_to_posix(snapshot_file_path) if get_platform() == "windows" else snapshot_file_path
            )
            command_parts.append(f"source {quote([final_path])} 2>/dev/null || true")

        sess = _try_session_env_script()
        if sess:
            command_parts.append(sess)

        extglob_off = _get_disable_extglob_command(self._shell_path)
        if extglob_off:
            command_parts.append(extglob_off)

        command_parts.append(f"eval {quoted_command}")
        command_parts.append(f"pwd -P >| {quote([shell_cwd_file_path])}")
        command_string = " && ".join(command_parts)

        prefix = os.environ.get("CLAUDE_CODE_SHELL_PREFIX")
        if prefix:
            command_string = _format_shell_prefix_command(prefix, command_string)

        return ExecBuildResult(command_string=command_string, cwd_file_path=cwd_file_path)

    def get_spawn_args(self, command_string: str) -> list[str]:
        skip_login = self._last_snapshot_file_path is not None
        if skip_login:
            log_for_debugging("Spawning shell without login (-l flag skipped)")
        return ["-c", *([] if skip_login else ["-l"]), command_string]

    async def get_environment_overrides(self, command: str) -> dict[str, str]:
        env: dict[str, str] = {}

        if os.environ.get("USER_TYPE") == "ant":
            try:
                from claude_code.utils.tmux_socket import (
                    ensure_socket_initialized,
                    get_claude_tmux_env,
                    has_tmux_tool_been_used,
                )
            except ModuleNotFoundError:
                pass
            else:
                command_uses_tmux = "tmux" in command
                if has_tmux_tool_been_used() or command_uses_tmux:
                    await ensure_socket_initialized()
                claude_tmux = get_claude_tmux_env()
                if claude_tmux:
                    env["TMUX"] = claude_tmux

        if self._current_sandbox_tmp_dir:
            posix_tmp = (
                windows_path_to_posix(self._current_sandbox_tmp_dir)
                if get_platform() == "windows"
                else self._current_sandbox_tmp_dir
            )
            env["TMPDIR"] = posix_tmp
            env["CLAUDE_CODE_TMPDIR"] = posix_tmp
            env["TMPPREFIX"] = str(PurePosixPath(posix_tmp) / "zsh")

        for key, value in _try_session_env_vars():
            env[key] = value
        return env


async def create_bash_shell_provider(
    shell_path: str,
    *,
    skip_snapshot: bool = False,
) -> ShellProvider:
    """Factory matching TS ``createBashShellProvider``."""
    return BashProvider(shell_path, skip_snapshot=skip_snapshot)


__all__ = ["BashProvider", "create_bash_shell_provider"]
