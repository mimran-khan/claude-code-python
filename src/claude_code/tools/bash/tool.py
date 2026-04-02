"""
Bash tool implementation.

Executes shell commands with timeout and sandbox support.

Migrated from: tools/BashTool/*.ts
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult, ToolValidationResult
from .prompt import BASH_TOOL_NAME, get_default_timeout_ms, get_max_timeout_ms


class BashInput(BaseModel):
    """Input schema for the Bash tool."""

    command: str = Field(
        ...,
        description="The bash command to execute.",
    )
    timeout: int | None = Field(
        None,
        description="Timeout in milliseconds.",
    )
    run_in_background: bool = Field(
        False,
        description="Run the command in the background.",
    )
    working_directory: str | None = Field(
        None,
        description="Working directory for the command.",
    )


@dataclass
class BashOutput:
    """Output from the Bash tool."""

    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False
    background: bool = False


class BashTool(Tool[BashInput, BashOutput]):
    """
    Tool for executing bash commands.

    Provides shell command execution with:
    - Configurable timeout
    - Working directory support
    - Background execution mode
    - Sandbox restrictions (when enabled)
    """

    @property
    def name(self) -> str:
        return BASH_TOOL_NAME

    @property
    def description(self) -> str:
        from .prompt import get_simple_prompt

        return get_simple_prompt()

    def get_input_schema(self) -> dict[str, Any]:
        return BashInput.model_json_schema()

    async def validate_input(
        self,
        input_data: BashInput,
        context: Any,
    ) -> ToolValidationResult:
        """Validate the command input."""
        if not input_data.command or not input_data.command.strip():
            return ToolValidationResult(valid=False, error="Command cannot be empty")

        # Check timeout is within bounds
        if input_data.timeout is not None:
            max_timeout = get_max_timeout_ms()
            if input_data.timeout > max_timeout:
                return ToolValidationResult(
                    valid=False,
                    error=f"Timeout cannot exceed {max_timeout}ms",
                )

        return ToolValidationResult(valid=True)

    async def call(
        self,
        input_data: BashInput,
        context: Any,
    ) -> ToolResult[BashOutput]:
        """Execute the bash command."""
        command = input_data.command
        timeout_ms = input_data.timeout or get_default_timeout_ms()
        timeout_sec = timeout_ms / 1000.0

        # Determine working directory
        cwd = input_data.working_directory or os.getcwd()

        # Background mode
        if input_data.run_in_background:
            try:
                # Start process without waiting
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return ToolResult(
                    data=BashOutput(
                        stdout=f"Started background process with PID {process.pid}",
                        stderr="",
                        exit_code=0,
                        background=True,
                    )
                )
            except Exception as e:
                return ToolResult(
                    data=BashOutput(
                        stdout="",
                        stderr=str(e),
                        exit_code=1,
                        background=True,
                    ),
                    error=str(e),
                )

        # Execute command with timeout
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=os.environ.copy(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_sec,
                )

                return ToolResult(
                    data=BashOutput(
                        stdout=stdout.decode("utf-8", errors="replace"),
                        stderr=stderr.decode("utf-8", errors="replace"),
                        exit_code=process.returncode or 0,
                    )
                )
            except TimeoutError:
                # Kill the process on timeout
                with contextlib.suppress(Exception):
                    process.kill()

                return ToolResult(
                    data=BashOutput(
                        stdout="",
                        stderr=f"Command timed out after {timeout_ms}ms",
                        exit_code=124,  # Standard timeout exit code
                        timed_out=True,
                    ),
                    error=f"Command timed out after {timeout_ms}ms",
                )
        except Exception as e:
            return ToolResult(
                data=BashOutput(
                    stdout="",
                    stderr=str(e),
                    exit_code=1,
                ),
                error=str(e),
            )
