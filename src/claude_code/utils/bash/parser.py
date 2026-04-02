"""
Bash command parser.

Tree-sitter based bash command parsing.

Migrated from: utils/bash/parser.ts (231 lines) - Stub implementation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MAX_COMMAND_LENGTH = 10000

# Node types for parsing
DECLARATION_COMMANDS = {"export", "declare", "typeset", "readonly", "local", "unset", "unsetenv"}
ARGUMENT_TYPES = {"word", "string", "raw_string", "number"}
SUBSTITUTION_TYPES = {"command_substitution", "process_substitution"}
COMMAND_TYPES = {"command", "declaration_command"}


@dataclass
class ParsedCommandData:
    """Result of parsing a bash command."""

    original_command: str
    command_node: dict[str, Any] | None = None
    env_vars: list[str] = field(default_factory=list)
    root_node: dict[str, Any] | None = None


# Sentinel for aborted parse
class ParseAborted:
    """Sentinel for parse that was aborted (timeout, panic, etc.)."""

    pass


PARSE_ABORTED = ParseAborted()


async def parse_command(command: str) -> ParsedCommandData | None:
    """
    Parse a bash command using tree-sitter.

    Note: This is a stub implementation. Full tree-sitter integration
    would require the tree-sitter-bash library.

    Args:
        command: The bash command to parse

    Returns:
        ParsedCommandData or None if parsing failed
    """
    if not command or len(command) > MAX_COMMAND_LENGTH:
        return None

    # Stub: Return basic parsed data without tree-sitter
    return ParsedCommandData(
        original_command=command,
        env_vars=_extract_env_vars_simple(command),
    )


async def parse_command_raw(
    command: str,
) -> dict[str, Any] | None | ParseAborted:
    """
    Raw parse - skips findCommandNode/extractEnvVars.

    Returns:
        - dict: parse succeeded (AST root node)
        - None: module not loaded / feature off / empty / over-length
        - PARSE_ABORTED: module loaded but parse failed
    """
    if not command or len(command) > MAX_COMMAND_LENGTH:
        return None

    # Stub: Tree-sitter not implemented
    return None


def _extract_env_vars_simple(command: str) -> list[str]:
    """
    Simple extraction of environment variable assignments from command start.

    This is a simplified fallback when tree-sitter is not available.
    """
    env_vars = []

    # Split on whitespace and look for VAR=value patterns at start
    import re

    env_pattern = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")

    parts = command.split()
    for part in parts:
        match = env_pattern.match(part)
        if match:
            env_vars.append(part)
        else:
            # First non-env-var is the command name
            break

    return env_vars


def extract_command_arguments(command_node: dict[str, Any]) -> list[str]:
    """
    Extract arguments from a command AST node.

    Args:
        command_node: The parsed command node

    Returns:
        List of argument strings
    """
    if not command_node:
        return []

    node_type = command_node.get("type", "")
    children = command_node.get("children", [])

    # Declaration commands
    if node_type == "declaration_command":
        first_child = children[0] if children else None
        if first_child and first_child.get("text", "") in DECLARATION_COMMANDS:
            return [first_child["text"]]
        return []

    # Regular commands
    args = []
    found_command_name = False

    for child in children:
        child_type = child.get("type", "")

        # Skip env vars
        if child_type == "variable_assignment":
            continue

        if child_type == "command_name" or child_type in ARGUMENT_TYPES:
            if not found_command_name:
                found_command_name = True
            args.append(child.get("text", ""))

    return args
