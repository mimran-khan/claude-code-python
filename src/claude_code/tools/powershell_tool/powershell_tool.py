"""
PowerShell Tool implementation.

Execute PowerShell commands on Windows.

Migrated from: tools/PowerShellTool/*.ts
"""

from __future__ import annotations

import asyncio
import platform
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext

POWERSHELL_TOOL_NAME = "PowerShell"


POWERSHELL_DESCRIPTION = """Execute a PowerShell command.

Only available on Windows systems.
Use this for Windows-specific automation.
"""


class PowerShellTool(Tool[dict[str, Any], dict[str, Any]]):
    """Tool for PowerShell commands."""

    @property
    def name(self) -> str:
        return POWERSHELL_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "run powershell, windows command"

    async def description(self) -> str:
        return POWERSHELL_DESCRIPTION

    async def prompt(self) -> str:
        return "Execute PowerShell commands."

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The PowerShell command to execute",
                },
            },
            "required": ["command"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"},
            },
        }

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        """Execute PowerShell command."""
        if platform.system() != "Windows":
            return ToolResult(
                success=False,
                error="PowerShell is only available on Windows",
                error_code=1,
            )

        command = input.get("command", "")

        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-NoProfile",
                "-Command",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            return ToolResult(
                success=proc.returncode == 0,
                output={
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                    "exit_code": proc.returncode,
                },
                error_code=proc.returncode if proc.returncode != 0 else None,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                error_code=1,
            )
