"""
Bash tool — execute shell commands.

Migrated from: tools/BashTool/BashTool.tsx (orchestration subset).
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, overload

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext, ValidationResult
from .constants import BASH_TOOL_NAME

# Host may later wire: LocalShellTask, sandbox (SandboxManager), bashToolHasPermission, sed fast path.


@dataclass
class BashToolOutput:
    stdout: str
    stderr: str
    interrupted: bool = False
    exit_code: int | None = None
    raw_output_path: str | None = None
    is_image: bool | None = None
    background_task_id: str | None = None
    backgrounded_by_user: bool | None = None
    assistant_auto_backgrounded: bool | None = None
    dangerously_disable_sandbox: bool | None = None
    return_code_interpretation: str | None = None
    no_output_expected: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Structured, JSON-friendly summary for hosts and tests."""
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None or k in ("stdout", "stderr", "interrupted", "exit_code")}


DEFAULT_TIMEOUT_MS = 120_000
MAX_TIMEOUT_MS = 600_000


def _coerce_timeout_ms(raw: Any) -> int:
    if raw is None:
        return DEFAULT_TIMEOUT_MS
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_MS
    return max(1, min(v, MAX_TIMEOUT_MS))


INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "command": {"type": "string", "description": "The command to execute"},
        "timeout": {
            "type": "integer",
            "description": f"Optional timeout in milliseconds (max {MAX_TIMEOUT_MS})",
        },
        "description": {
            "type": "string",
            "description": "Short description of what the command does (active voice)",
        },
        "run_in_background": {
            "type": "boolean",
            "description": "Run in background; host should surface completion later",
        },
        "dangerously_disable_sandbox": {
            "type": "boolean",
            "description": "Override sandbox (requires host policy)",
        },
    },
    "required": ["command"],
}


@overload
async def execute_bash(command: str, context: ToolUseContext | None = None) -> ToolResult[BashToolOutput]: ...


@overload
async def execute_bash(
    input_data: dict[str, Any],
    context: ToolUseContext | None = None,
) -> ToolResult[BashToolOutput]: ...


async def execute_bash(
    command_or_input: str | dict[str, Any],
    context: ToolUseContext | None = None,
) -> ToolResult[BashToolOutput]:
    """Run a shell command. Pass a string for quick tests, or a full input dict + context."""
    tool = BashTool()
    if isinstance(command_or_input, str):
        input_data: dict[str, Any] = {"command": command_or_input}
        ctx = context or ToolUseContext()
    else:
        input_data = command_or_input
        ctx = context if context is not None else ToolUseContext()
    return await tool.call(input_data, ctx, None)


class BashTool(Tool):
    """Run shell commands (subset of TS BashTool)."""

    name = BASH_TOOL_NAME
    description = "Executes a given bash command and returns its output."
    input_schema = INPUT_SCHEMA
    is_read_only = False
    is_concurrency_safe = False
    user_facing_name = BASH_TOOL_NAME

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        cmd = input_data.get("command", "")
        if not isinstance(cmd, str) or not cmd.strip():
            return ValidationResult(result=False, message="command is required", error_code=1)
        return ValidationResult(result=True)

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[BashToolOutput]:
        _ = progress_callback
        command = str(input_data.get("command", "")).strip()
        timeout_ms = _coerce_timeout_ms(input_data.get("timeout"))
        run_bg = bool(input_data.get("run_in_background"))
        # dangerously_disable_sandbox: host may enforce via context.options when wired.

        cwd = os.getcwd()
        opts = context.options or {}
        if isinstance(opts, dict):
            wd = opts.get("working_directory") or opts.get("cwd")
            if isinstance(wd, str) and wd:
                cwd = wd

        if run_bg:

            def _spawn_bg() -> subprocess.Popen:
                return subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    env=os.environ.copy(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                )

            try:
                popen = await asyncio.to_thread(_spawn_bg)
            except Exception as e:
                return ToolResult(
                    data=BashToolOutput(
                        stdout="",
                        stderr=str(e),
                        interrupted=False,
                        exit_code=None,
                    ),
                )
            return ToolResult(
                data=BashToolOutput(
                    stdout=f"Background shell started (PID {popen.pid}). Stdout/stderr are discarded.",
                    stderr="",
                    interrupted=False,
                    exit_code=0,
                    background_task_id=str(popen.pid),
                    backgrounded_by_user=True,
                ),
            )

        timeout_sec = timeout_ms / 1000.0
        proc: asyncio.subprocess.Process | None = None
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=os.environ.copy(),
            )
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
            code = proc.returncode if proc.returncode is not None else 0
            return ToolResult(
                data=BashToolOutput(
                    stdout=stdout_b.decode("utf-8", errors="replace"),
                    stderr=stderr_b.decode("utf-8", errors="replace"),
                    interrupted=False,
                    exit_code=code,
                ),
            )
        except TimeoutError:
            if proc is not None and proc.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    proc.kill()
                with contextlib.suppress(TimeoutError, ProcessLookupError):
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
            return ToolResult(
                data=BashToolOutput(
                    stdout="",
                    stderr=f"Command timed out after {timeout_ms}ms",
                    interrupted=True,
                    exit_code=124,
                ),
            )
        except Exception as e:
            return ToolResult(
                data=BashToolOutput(
                    stdout="",
                    stderr=str(e),
                    interrupted=False,
                    exit_code=None,
                ),
            )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        desc = input_data.get("description")
        if isinstance(desc, str) and desc.strip():
            return desc[:100]
        cmd = input_data.get("command")
        if isinstance(cmd, str):
            return (cmd[:97] + "...") if len(cmd) > 100 else cmd
        return BASH_TOOL_NAME
