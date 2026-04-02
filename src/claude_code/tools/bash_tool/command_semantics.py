"""
Bash exit-code semantics (grep, find, diff, test, etc.).

Migrated from: tools/BashTool/commandSemantics.ts
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

from ...utils.bash.commands import split_command


class CommandResultView(TypedDict, total=False):
    is_error: bool
    message: str | None


CommandSemantic = Callable[[int, str, str], CommandResultView]


def _default_semantic(exit_code: int, _stdout: str, _stderr: str) -> CommandResultView:
    return {
        "is_error": exit_code != 0,
        "message": None if exit_code == 0 else f"Command failed with exit code {exit_code}",
    }


def _grep_like(exit_code: int, _stdout: str, _stderr: str) -> CommandResultView:
    return {
        "is_error": exit_code >= 2,
        "message": "No matches found" if exit_code == 1 else None,
    }


def _find_semantic(exit_code: int, _stdout: str, _stderr: str) -> CommandResultView:
    return {
        "is_error": exit_code >= 2,
        "message": "Some directories were inaccessible" if exit_code == 1 else None,
    }


def _diff_semantic(exit_code: int, _stdout: str, _stderr: str) -> CommandResultView:
    return {
        "is_error": exit_code >= 2,
        "message": "Files differ" if exit_code == 1 else None,
    }


def _test_semantic(exit_code: int, _stdout: str, _stderr: str) -> CommandResultView:
    return {
        "is_error": exit_code >= 2,
        "message": "Condition is false" if exit_code == 1 else None,
    }


_COMMAND_SEMANTICS: dict[str, CommandSemantic] = {
    "grep": _grep_like,
    "rg": _grep_like,
    "find": _find_semantic,
    "diff": _diff_semantic,
    "test": _test_semantic,
    "[": _test_semantic,
}


def _extract_base_command(command: str) -> str:
    return (command.strip().split() or [""])[0]


def _heuristic_base_command(command: str) -> str:
    try:
        segments = split_command(command)
    except Exception:
        segments = [command]
    last = segments[-1] if segments else command
    return _extract_base_command(last)


def get_command_semantic(command: str) -> CommandSemantic:
    base = _heuristic_base_command(command)
    return _COMMAND_SEMANTICS.get(base, _default_semantic)


def interpret_command_result(
    command: str,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> CommandResultView:
    semantic = get_command_semantic(command)
    return semantic(exit_code, stdout, stderr)


__all__ = ["interpret_command_result", "get_command_semantic", "CommandResultView"]
