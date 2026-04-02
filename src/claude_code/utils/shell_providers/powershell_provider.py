"""
PowerShell shell provider.

PowerShell-specific command execution.

Migrated from: utils/shell/powershellProvider.ts + powershellDetection.ts
"""

from __future__ import annotations

import platform
import tempfile

from .provider import CommandBuildResult, ShellProvider, ShellType


class PowerShellProvider(ShellProvider):
    """PowerShell shell provider."""

    def __init__(self, shell_path: str = "pwsh"):
        self._shell_path = shell_path

    @property
    def type(self) -> ShellType:
        return "powershell"

    @property
    def shell_path(self) -> str:
        return self._shell_path

    async def build_exec_command(
        self,
        command: str,
        task_id: str | int,
        sandbox_tmp_dir: str | None = None,
        use_sandbox: bool = False,
    ) -> CommandBuildResult:
        """Build PowerShell command with tracking."""
        # Create temp file for cwd tracking
        cwd_file = tempfile.mktemp(suffix=f".{task_id}.cwd")

        # Build PowerShell command
        # Set error action to stop on first error
        parts = [
            "$ErrorActionPreference = 'Stop'",
            command,
            f'(Get-Location).Path | Out-File -FilePath "{cwd_file}" -Encoding UTF8',
        ]

        command_string = "; ".join(parts)

        return CommandBuildResult(
            command_string=command_string,
            cwd_file_path=cwd_file,
        )

    def get_spawn_args(self, command_string: str) -> list[str]:
        """Get PowerShell spawn arguments."""
        return [
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command_string,
        ]

    async def get_environment_overrides(
        self,
        command: str,
    ) -> dict[str, str]:
        """Get PowerShell environment overrides."""
        return {
            "SHELL": self._shell_path,
        }


def detect_powershell_path() -> str | None:
    """
    Detect the PowerShell executable path.

    Prefers pwsh (PowerShell Core) over powershell (Windows PowerShell).

    Returns:
        Path to PowerShell or None
    """
    import shutil

    # Try PowerShell Core first (cross-platform)
    pwsh = shutil.which("pwsh")
    if pwsh:
        return pwsh

    # On Windows, try Windows PowerShell
    if platform.system() == "Windows":
        powershell = shutil.which("powershell")
        if powershell:
            return powershell

    return None


def is_powershell_available() -> bool:
    """Check if PowerShell is available."""
    return detect_powershell_path() is not None


def create_powershell_provider(
    shell_path: str | None = None,
) -> PowerShellProvider:
    """
    Create a PowerShell provider.

    Args:
        shell_path: Optional path to PowerShell executable

    Returns:
        PowerShellProvider instance
    """
    if shell_path is None:
        shell_path = detect_powershell_path() or "pwsh"

    return PowerShellProvider(shell_path)
