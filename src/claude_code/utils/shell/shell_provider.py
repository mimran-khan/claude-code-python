"""
Abstract shell provider protocol for Bash and PowerShell.

Migrated from: utils/shell/shellProvider.ts
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

SHELL_TYPES: tuple[str, ...] = ("bash", "powershell")
ShellType = Literal["bash", "powershell"]
DEFAULT_HOOK_SHELL: ShellType = "bash"


@dataclass(frozen=True, slots=True)
class ExecCommandOpts:
    """Options for :meth:`ShellProvider.build_exec_command`."""

    id: int | str
    sandbox_tmp_dir: str | None = None
    use_sandbox: bool = False


@dataclass(frozen=True, slots=True)
class ExecBuildResult:
    """Built shell command and native path to the cwd tracking file."""

    command_string: str
    cwd_file_path: str


class ShellProvider(ABC):
    """
    Shell-specific command wrapping, spawn argv, and environment overrides.

    Implementations build the full command string (snapshot, session env,
    security hardening, eval / encoded command) and supply spawn arguments.
    """

    @property
    @abstractmethod
    def type(self) -> ShellType:
        """``bash`` or ``powershell``."""

    @property
    @abstractmethod
    def shell_path(self) -> str:
        """Executable path passed to :func:`asyncio.create_subprocess_exec`."""

    @property
    @abstractmethod
    def detached(self) -> bool:
        """Whether the process should be spawned detached (Bash: true)."""

    @abstractmethod
    async def build_exec_command(
        self,
        command: str,
        opts: ExecCommandOpts,
    ) -> ExecBuildResult:
        """Build the full command string and cwd file path."""

    @abstractmethod
    def get_spawn_args(self, command_string: str) -> list[str]:
        """Arguments after the shell executable (e.g. ``-c``, ``-l``, script)."""

    @abstractmethod
    async def get_environment_overrides(self, command: str) -> dict[str, str]:
        """Extra env vars for this shell type (merged into the process env)."""


__all__ = [
    "DEFAULT_HOOK_SHELL",
    "ExecBuildResult",
    "ExecCommandOpts",
    "SHELL_TYPES",
    "ShellProvider",
    "ShellType",
]
