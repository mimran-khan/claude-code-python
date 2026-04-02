"""
PowerShell shell provider.

Migrated from: utils/shell/powershellProvider.ts
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from .shell_provider import ExecBuildResult, ExecCommandOpts, ShellProvider, ShellType


def build_powershell_args(cmd: str) -> list[str]:
    """``-NoProfile``, ``-NonInteractive``, ``-Command``, and the script body."""
    return ["-NoProfile", "-NonInteractive", "-Command", cmd]


def _encode_powershell_command(ps_command: str) -> str:
    """UTF-16LE base64 for ``-EncodedCommand`` (shell-quoting safe)."""
    return base64.b64encode(ps_command.encode("utf-16-le")).decode("ascii")


def _posix_single_quote_for_sh(path: str) -> str:
    """Single-quote for embedding in ``/bin/sh -c '...'``."""
    return "'" + path.replace("'", "'\\''") + "'"


class PowerShellProvider(ShellProvider):
    """PowerShell :class:`ShellProvider` implementation."""

    def __init__(self, shell_path: str) -> None:
        self._shell_path = shell_path
        self._current_sandbox_tmp_dir: str | None = None

    @property
    def type(self) -> ShellType:
        return "powershell"

    @property
    def shell_path(self) -> str:
        return self._shell_path

    @property
    def detached(self) -> bool:
        return False

    async def build_exec_command(
        self,
        command: str,
        opts: ExecCommandOpts,
    ) -> ExecBuildResult:
        self._current_sandbox_tmp_dir = opts.sandbox_tmp_dir if opts.use_sandbox else None

        tmp_root = Path(os.environ.get("TMPDIR", "") or __import__("tempfile").gettempdir())
        if opts.use_sandbox and opts.sandbox_tmp_dir:
            cwd_file_path = str(
                Path(opts.sandbox_tmp_dir) / f"claude-pwd-ps-{opts.id}",
            )
        else:
            cwd_file_path = str(tmp_root / f"claude-pwd-ps-{opts.id}")

        escaped_cwd = cwd_file_path.replace("'", "''")
        cwd_tracking = (
            "\n; $_ec = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } "
            "elseif ($?) { 0 } else { 1 }\n"
            f"; (Get-Location).Path | Out-File -FilePath '{escaped_cwd}' "
            "-Encoding utf8 -NoNewline\n; exit $_ec"
        )
        ps_command = command + cwd_tracking

        if opts.use_sandbox:
            qpath = _posix_single_quote_for_sh(self._shell_path)
            enc = _encode_powershell_command(ps_command)
            command_string = f"{qpath} -NoProfile -NonInteractive -EncodedCommand {enc}"
        else:
            command_string = ps_command

        return ExecBuildResult(command_string=command_string, cwd_file_path=cwd_file_path)

    def get_spawn_args(self, command_string: str) -> list[str]:
        return build_powershell_args(command_string)

    async def get_environment_overrides(self, command: str) -> dict[str, str]:
        del command  # unused; parity with bash provider signature
        env: dict[str, str] = {}
        try:
            from claude_code.utils.session_environment import get_session_env_vars
        except ImportError:
            session_items: list[tuple[str, str]] = []
        else:
            session_items = list(get_session_env_vars())

        for key, value in session_items:
            env[key] = value

        if self._current_sandbox_tmp_dir:
            env["TMPDIR"] = self._current_sandbox_tmp_dir
            env["CLAUDE_CODE_TMPDIR"] = self._current_sandbox_tmp_dir
        return env


def create_powershell_provider(shell_path: str) -> ShellProvider:
    """Factory matching TS ``createPowerShellProvider``."""
    return PowerShellProvider(shell_path)


__all__ = [
    "PowerShellProvider",
    "build_powershell_args",
    "create_powershell_provider",
]
