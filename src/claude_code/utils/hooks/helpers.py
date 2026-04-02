"""
Hook helper functions.

Utilities for hook execution.

Migrated from: utils/hooks/hookHelpers.ts
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class HookResponse:
    """Structured response from a hook."""

    ok: bool
    reason: str | None = None


def add_arguments_to_prompt(prompt: str, json_input: str) -> str:
    """
    Add hook input JSON to prompt.

    Replaces $ARGUMENTS placeholder or indexed arguments like $ARGUMENTS[0], $0, etc.

    Args:
        prompt: Prompt template
        json_input: JSON string of input arguments

    Returns:
        Prompt with arguments substituted
    """
    # Parse the JSON input
    try:
        args = json.loads(json_input)
    except json.JSONDecodeError:
        args = json_input

    result = prompt

    # Replace $ARGUMENTS with full JSON
    if "$ARGUMENTS" in result and "[" not in result.split("$ARGUMENTS")[1][:5]:
        result = result.replace("$ARGUMENTS", json_input)

    # Replace indexed arguments $ARGUMENTS[n] or $n
    if isinstance(args, list):
        for i, arg in enumerate(args):
            arg_str = json.dumps(arg) if not isinstance(arg, str) else arg
            result = result.replace(f"$ARGUMENTS[{i}]", arg_str)
            result = result.replace(f"${i}", arg_str)
    elif isinstance(args, dict):
        for key, value in args.items():
            value_str = json.dumps(value) if not isinstance(value, str) else value
            result = result.replace(f"$ARGUMENTS[{key}]", value_str)
            result = result.replace(f"${key}", value_str)

    return result


def validate_hook_response(response: Any) -> HookResponse | None:
    """
    Validate and parse a hook response.

    Args:
        response: Response to validate

    Returns:
        HookResponse or None if invalid
    """
    if isinstance(response, dict):
        ok = response.get("ok")
        if isinstance(ok, bool):
            return HookResponse(
                ok=ok,
                reason=response.get("reason"),
            )

    if isinstance(response, str):
        try:
            data = json.loads(response)
            return validate_hook_response(data)
        except json.JSONDecodeError:
            pass

    return None


def substitute_arguments(template: str, args: str) -> str:
    """
    Substitute argument placeholders in a template.

    Supports:
    - $ARGUMENTS - full JSON
    - $ARGUMENTS[n] - indexed access
    - $0, $1, etc. - shorthand indexed

    Args:
        template: Template string
        args: JSON arguments string

    Returns:
        Substituted string
    """
    return add_arguments_to_prompt(template, args)


def extract_hook_output(stdout: str, stderr: str) -> str:
    """
    Extract meaningful output from hook execution.

    Args:
        stdout: Standard output
        stderr: Standard error

    Returns:
        Combined output
    """
    parts = []

    if stdout.strip():
        parts.append(stdout.strip())

    if stderr.strip():
        parts.append(f"[stderr] {stderr.strip()}")

    return "\n".join(parts)
