"""
Shell provider interface.

Abstract interface for shell providers.

Migrated from: utils/shell/shellProvider.ts
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

# Shell types
ShellType = Literal["bash", "powershell"]
SHELL_TYPES: tuple[ShellType, ...] = ("bash", "powershell")
DEFAULT_HOOK_SHELL: ShellType = "bash"


@dataclass
class CommandBuildResult:
    """Result of building a shell command."""

    command_string: str
    cwd_file_path: str


class ShellProvider(ABC):
    """Abstract shell provider interface."""

    @property
    @abstractmethod
    def type(self) -> ShellType:
        """Shell type."""
        pass

    @property
    @abstractmethod
    def shell_path(self) -> str:
        """Path to shell executable."""
        pass

    @property
    def detached(self) -> bool:
        """Whether to run detached."""
        return False

    @abstractmethod
    async def build_exec_command(
        self,
        command: str,
        task_id: str | int,
        sandbox_tmp_dir: str | None = None,
        use_sandbox: bool = False,
    ) -> CommandBuildResult:
        """
        Build the full command string including shell-specific setup.

        Args:
            command: Command to execute
            task_id: Task identifier
            sandbox_tmp_dir: Optional sandbox directory
            use_sandbox: Whether to use sandbox

        Returns:
            CommandBuildResult with command and cwd file path
        """
        pass

    @abstractmethod
    def get_spawn_args(self, command_string: str) -> list[str]:
        """
        Get arguments for subprocess spawn.

        Args:
            command_string: Command to run

        Returns:
            List of arguments
        """
        pass

    @abstractmethod
    async def get_environment_overrides(
        self,
        command: str,
    ) -> dict[str, str]:
        """
        Get environment variable overrides for this shell.

        Args:
            command: Command being run

        Returns:
            Environment variable overrides
        """
        pass


def get_shell_provider(shell_type: ShellType) -> ShellProvider:
    """
    Get a shell provider by type.

    Args:
        shell_type: Type of shell

    Returns:
        ShellProvider instance
    """
    if shell_type == "bash":
        from .bash_provider import create_bash_provider

        return create_bash_provider()

    if shell_type == "powershell":
        from .powershell_provider import create_powershell_provider

        return create_powershell_provider()

    raise ValueError(f"Unknown shell type: {shell_type}")
