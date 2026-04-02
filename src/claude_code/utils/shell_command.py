"""
Shell command handle types (``utils/ShellCommand.ts``).

Runtime wiring: :mod:`claude_code.utils.shell_exec` and bash tool implementations.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass
class ExecResult:
    """Aligned with TS ``ExecResult`` (snake_case field names)."""

    stdout: str = ""
    stderr: str = ""
    code: int = 0
    interrupted: bool = False
    background_task_id: str | None = None
    backgrounded_by_user: bool | None = None
    assistant_auto_backgrounded: bool | None = None
    output_file_path: str | None = None
    output_file_size: int | None = None
    output_task_id: str | None = None
    pre_spawn_error: str | None = None


ShellCommandStatus = Literal["running", "backgrounded", "completed", "killed"]


class ShellCommand(Protocol):
    """Structural type matching the TS ``ShellCommand`` object."""

    background: Callable[[str], bool]
    result: Awaitable[ExecResult] | Any
    kill: Callable[[], None]
    status: ShellCommandStatus
    cleanup: Callable[[], None]
    on_timeout: Callable[..., Any] | None
    task_output: Any


__all__ = ["ExecResult", "ShellCommand", "ShellCommandStatus"]
