"""
System Prompt Generation.

Main system prompt generation functions.
"""

from __future__ import annotations

import os
import platform
from typing import Any

from ..utils.cwd import get_cwd

# Boundary marker separating static and dynamic content
SYSTEM_PROMPT_DYNAMIC_BOUNDARY = "__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__"


# Default agent prompt
DEFAULT_AGENT_PROMPT = """You are an agent for Claude Code, Anthropic's official CLI for Claude. Given the user's message, you should use the tools available to complete the task. Complete the task fully—don't gold-plate, but don't leave it half-done. When you complete the task, respond with a concise report covering what was done and any key findings — the caller will relay this to the user, so it only needs the essentials."""


def get_system_prompt(
    tools: list[Any],
    model: str,
    additional_working_directories: list[str] | None = None,
    mcp_clients: list[Any] | None = None,
) -> list[str]:
    """Generate the system prompt.

    Args:
        tools: List of available tools
        model: The model ID
        additional_working_directories: Additional directories
        mcp_clients: MCP server connections

    Returns:
        List of system prompt sections
    """
    from .sections import (
        get_actions_section,
        get_doing_tasks_section,
        get_intro_section,
        get_output_efficiency_section,
        get_system_section,
        get_tone_and_style_section,
        get_using_tools_section,
    )

    enabled_tools = {getattr(t, "name", str(t)) for t in tools}

    env_info = get_env_info(model, additional_working_directories)

    return [
        # Static content
        get_intro_section(),
        get_system_section(),
        get_doing_tasks_section(),
        get_actions_section(),
        get_using_tools_section(enabled_tools),
        get_tone_and_style_section(),
        get_output_efficiency_section(),
        # Dynamic boundary
        SYSTEM_PROMPT_DYNAMIC_BOUNDARY,
        # Dynamic content
        env_info,
    ]


def get_env_info(
    model_id: str,
    additional_working_directories: list[str] | None = None,
) -> str:
    """Generate environment information section.

    Args:
        model_id: The model ID
        additional_working_directories: Additional directories

    Returns:
        Environment info string
    """
    from .sections import prepend_bullets

    cwd = get_cwd()
    is_git = _is_git_repo(cwd)
    uname_sr = _get_uname_sr()
    shell = os.getenv("SHELL", "unknown")

    env_items = [
        f"Primary working directory: {cwd}",
        f"Is a git repository: {is_git}",
    ]

    if additional_working_directories:
        env_items.append("Additional working directories:")
        for dir_path in additional_working_directories:
            env_items.append(f"  - {dir_path}")

    env_items.extend(
        [
            f"Platform: {platform.system().lower()}",
            f"Shell: {os.path.basename(shell)}",
            f"OS Version: {uname_sr}",
            f"You are powered by the model {model_id}.",
        ]
    )

    lines = ["# Environment", "You have been invoked in the following environment:"]
    lines.extend(prepend_bullets(env_items))

    return "\n".join(lines)


def _is_git_repo(path: str) -> bool:
    """Check if a path is in a git repository.

    Args:
        path: Path to check

    Returns:
        True if in a git repo
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _get_uname_sr() -> str:
    """Get OS type and release.

    Returns:
        OS version string
    """
    system = platform.system()
    release = platform.release()

    if system == "Windows":
        return f"{platform.version()} {release}"

    return f"{system} {release}"
