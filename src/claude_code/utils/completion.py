"""
Shell input completion context (command / variable / file).

Migrated from: utils/bash/shellCompletion.ts (parse path only).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .bash.shell_quote import try_parse_shell_command

ShellCompletionType = Literal["command", "variable", "file"]

COMMAND_OPERATORS = frozenset({"|", "||", "&&", ";"})


@dataclass
class InputContext:
    prefix: str
    completion_type: ShellCompletionType


def _get_completion_type_from_prefix(prefix: str) -> ShellCompletionType:
    if prefix.startswith("$"):
        return "variable"
    if "/" in prefix or prefix.startswith("~") or prefix.startswith("."):
        return "file"
    return "command"


def _find_last_string_token(tokens: list[object]) -> tuple[str, int] | None:
    for i in range(len(tokens) - 1, -1, -1):
        if isinstance(tokens[i], str):
            return (tokens[i], i)
    return None


def _is_command_operator_token(token: object) -> bool:
    return isinstance(token, str) and token in COMMAND_OPERATORS


def _is_new_command_context(tokens: list[object], idx: int) -> bool:
    if idx == 0:
        return True
    prev = tokens[idx - 1]
    return _is_command_operator_token(prev)


def parse_input_context(input_str: str, cursor_offset: int) -> InputContext:
    before = input_str[:cursor_offset]

    var_match = re.search(r"\$[a-zA-Z_][a-zA-Z0-9_]*$", before)
    if var_match:
        return InputContext(prefix=var_match.group(0), completion_type="variable")

    parsed = try_parse_shell_command(before)
    if not parsed.success:
        parts = before.split()
        prefix = parts[-1] if parts else ""
        is_first = len(parts) == 1 and " " not in before
        ctype: ShellCompletionType = "command" if is_first else _get_completion_type_from_prefix(prefix)
        return InputContext(prefix=prefix, completion_type=ctype)

    last = _find_last_string_token(parsed.tokens)
    if last is None:
        last_tok = parsed.tokens[-1] if parsed.tokens else None
        ctype = "command" if last_tok is not None and _is_command_operator_token(last_tok) else "command"
        return InputContext(prefix="", completion_type=ctype)

    if before.endswith(" "):
        return InputContext(prefix="", completion_type="file")

    token, idx = last
    base = _get_completion_type_from_prefix(token)
    if base in ("variable", "file"):
        return InputContext(prefix=token, completion_type=base)
    ctype = "command" if _is_new_command_context(parsed.tokens, idx) else "file"
    return InputContext(prefix=token, completion_type=ctype)
