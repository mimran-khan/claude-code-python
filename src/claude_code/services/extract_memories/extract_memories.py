"""
Extract durable memories from the session transcript (forked-agent pattern).

Migrated from: services/extractMemories/extractMemories.ts (tool gate + structure; full fork wiring is CLI-specific).
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypedDict

from claude_code.utils.debug import log_for_debugging

from .prompts import (
    BASH_TOOL_NAME,
    FILE_EDIT_TOOL_NAME,
    FILE_READ_TOOL_NAME,
    FILE_WRITE_TOOL_NAME,
    GLOB_TOOL_NAME,
    GREP_TOOL_NAME,
)

REPL_TOOL_NAME = "REPL"

ToolBehavior = Literal["allow", "deny"]


def _is_under_memory_dir(file_path: str, memory_dir: str) -> bool:
    try:
        fp = os.path.realpath(file_path)
        root = os.path.realpath(memory_dir)
        return fp == root or fp.startswith(root + os.sep)
    except OSError:
        return False


class CanUseToolResult(TypedDict, total=False):
    behavior: ToolBehavior
    message: str
    updatedInput: dict[str, Any]


def _deny_auto_mem_tool(tool_name: str, reason: str) -> CanUseToolResult:
    log_for_debugging(f"[autoMem] denied {tool_name}: {reason}")
    return {"behavior": "deny", "message": reason}


def create_auto_mem_can_use_tool(
    memory_dir: str,
    *,
    is_read_only_bash: Callable[[dict[str, Any]], bool] | None = None,
) -> Callable[[str, dict[str, Any]], Awaitable[CanUseToolResult]]:
    """
    Returns an async gate allowing Read/Grep/Glob, read-only Bash, and Edit/Write under ``memory_dir``.
    Pass ``is_read_only_bash`` when integrating with a real Bash tool (mirrors ``BashTool.isReadOnly``).
    """

    async def can_use_tool(tool_name: str, input_payload: dict[str, Any]) -> CanUseToolResult:
        if tool_name == REPL_TOOL_NAME:
            return {"behavior": "allow", "updatedInput": input_payload}

        if tool_name in (FILE_READ_TOOL_NAME, GREP_TOOL_NAME, GLOB_TOOL_NAME):
            return {"behavior": "allow", "updatedInput": input_payload}

        if tool_name == BASH_TOOL_NAME:
            if is_read_only_bash is not None and is_read_only_bash(input_payload):
                return {"behavior": "allow", "updatedInput": input_payload}
            return _deny_auto_mem_tool(
                tool_name,
                "Only read-only shell commands are permitted in this context "
                "(ls, find, grep, cat, stat, wc, head, tail, and similar)",
            )

        if tool_name in (FILE_EDIT_TOOL_NAME, FILE_WRITE_TOOL_NAME):
            fp = input_payload.get("file_path")
            if isinstance(fp, str) and _is_under_memory_dir(fp, memory_dir):
                return {"behavior": "allow", "updatedInput": input_payload}

        return _deny_auto_mem_tool(
            tool_name,
            f"only {FILE_READ_TOOL_NAME}, {GREP_TOOL_NAME}, {GLOB_TOOL_NAME}, read-only {BASH_TOOL_NAME}, "
            f"and {FILE_EDIT_TOOL_NAME}/{FILE_WRITE_TOOL_NAME} within {memory_dir} are allowed",
        )

    return can_use_tool


_extract_runner: Callable[..., Awaitable[None]] | None = None


def init_extract_memories() -> None:
    """Reset hook runner state (call per test / session). Mirrors ``initExtractMemories``."""

    global _extract_runner
    _extract_runner = None


async def execute_extract_memories(*_args: Any, **_kwargs: Any) -> None:
    """No-op until the host registers a forked extraction implementation."""
    if _extract_runner is not None:
        await _extract_runner(*_args, **_kwargs)
    elif os.environ.get("USER_TYPE") == "ant":
        log_for_debugging("[extractMemories] execute_extract_memories — no runner registered")


def register_extract_memories_runner(fn: Callable[..., Awaitable[None]] | None) -> None:
    global _extract_runner
    _extract_runner = fn
