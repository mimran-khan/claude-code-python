"""
Bash shell provider.

Bash-specific command execution.

Migrated from: utils/shell/bashProvider.ts
"""

from __future__ import annotations

import os
import tempfile

from .provider import CommandBuildResult, ShellProvider, ShellType


class BashProvider(ShellProvider):
    """Bash shell provider."""

    def __init__(self, shell_path: str = "/bin/bash"):
        self._shell_path = shell_path

    @property
    def type(self) -> ShellType:
        return "bash"

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
        """Build bash command with tracking."""
        # Create temp file for cwd tracking
        cwd_file = tempfile.mktemp(suffix=f".{task_id}.cwd")

        # Build command with cwd tracking
        parts = []

        # Disable extglob for safety
        parts.append("shopt -u extglob")

        # Run the actual command
        parts.append(command)

        # Save final cwd
        parts.append(f'echo "$PWD" > "{cwd_file}"')

        command_string = " && ".join(parts)

        return CommandBuildResult(
            command_string=command_string,
            cwd_file_path=cwd_file,
        )

    def get_spawn_args(self, command_string: str) -> list[str]:
        """Get bash spawn arguments."""
        return ["-c", command_string]

    async def get_environment_overrides(
        self,
        command: str,
    ) -> dict[str, str]:
        """Get bash environment overrides."""
        overrides = {
            "SHELL": self._shell_path,
        }

        # Disable history for non-interactive
        overrides["HISTFILE"] = ""

        return overrides


def create_bash_provider(shell_path: str | None = None) -> BashProvider:
    """
    Create a bash provider.

    Args:
        shell_path: Optional path to bash executable

    Returns:
        BashProvider instance
    """
    if shell_path is None:
        # Try to find bash
        for path in ["/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash"]:
            if os.path.exists(path):
                shell_path = path
                break
        else:
            shell_path = "/bin/bash"

    return BashProvider(shell_path)
