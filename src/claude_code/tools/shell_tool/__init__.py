"""
ShellTool — Bash + PowerShell entrypoints (TS: tools/BashTool, tools/PowerShellTool).
"""

from ..bash_tool import (
    BASH_TOOL_NAME,
    DEFAULT_TIMEOUT_MS,
    MAX_TIMEOUT_MS,
    BashTool,
    BashToolOutput,
)
from ..powershell_tool import POWERSHELL_TOOL_NAME, PowerShellTool

ShellTool = BashTool
SHELL_TOOL_NAME = BASH_TOOL_NAME

__all__ = [
    "ShellTool",
    "SHELL_TOOL_NAME",
    "BASH_TOOL_NAME",
    "BashTool",
    "BashToolOutput",
    "DEFAULT_TIMEOUT_MS",
    "MAX_TIMEOUT_MS",
    "POWERSHELL_TOOL_NAME",
    "PowerShellTool",
]
