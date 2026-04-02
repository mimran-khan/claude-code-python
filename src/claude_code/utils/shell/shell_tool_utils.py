"""
Shell tool name constants and feature gates.

Migrated from: utils/shell/shellToolUtils.ts
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from claude_code.tools.bash_tool.constants import BASH_TOOL_NAME
from claude_code.tools.powershell_tool.tool_name import POWERSHELL_TOOL_NAME
from claude_code.utils.env_utils import is_env_defined_falsy, is_env_truthy
from claude_code.utils.platform import get_platform

if TYPE_CHECKING:
    from .shell_provider import ShellProvider

SHELL_TOOL_NAMES: list[str] = [BASH_TOOL_NAME, POWERSHELL_TOOL_NAME]


async def run_shell_provider_command(
    provider: ShellProvider,
    command: str,
    *,
    task_id: int | str = 0,
    sandbox_tmp_dir: str | None = None,
    use_sandbox: bool = False,
    cwd: str | None = None,
) -> asyncio.subprocess.Process:
    """
    Spawn ``provider.shell_path`` with :func:`asyncio.create_subprocess_exec`.

    Builds argv via :meth:`ShellProvider.build_exec_command` and
    :meth:`ShellProvider.get_spawn_args`; merges environment overrides.
    """
    from .shell_provider import ExecCommandOpts

    built = await provider.build_exec_command(
        command,
        ExecCommandOpts(id=task_id, sandbox_tmp_dir=sandbox_tmp_dir, use_sandbox=use_sandbox),
    )
    argv = [provider.shell_path, *provider.get_spawn_args(built.command_string)]
    env = os.environ.copy()
    env.update(await provider.get_environment_overrides(command))
    return await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        env=env,
    )


def is_powershell_tool_enabled() -> bool:
    """
    Runtime gate for PowerShell tool. Windows-only.

    Ant defaults on (opt-out via env=0); external defaults off (opt-in via env=1).
    """
    if get_platform() != "windows":
        return False
    if os.environ.get("USER_TYPE") == "ant":
        return not is_env_defined_falsy(os.environ.get("CLAUDE_CODE_USE_POWERSHELL_TOOL"))
    return is_env_truthy(os.environ.get("CLAUDE_CODE_USE_POWERSHELL_TOOL"))


__all__ = [
    "BASH_TOOL_NAME",
    "POWERSHELL_TOOL_NAME",
    "SHELL_TOOL_NAMES",
    "is_powershell_tool_enabled",
    "run_shell_provider_command",
]
