"""
Headless / print-mode helpers.

Migrated from: cli/print.ts (exported utilities + runHeadless shell).
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator, Iterable
from typing import Any

PromptValue = str | list[dict[str, Any]]


def _to_blocks(v: PromptValue) -> list[dict[str, Any]]:
    if isinstance(v, str):
        return [{"type": "text", "text": v}]
    return list(v)


def join_prompt_values(values: list[PromptValue]) -> PromptValue:
    if len(values) == 1:
        return values[0]
    if all(isinstance(v, str) for v in values):
        return "\n".join(str(v) for v in values)
    out: list[dict[str, Any]] = []
    for v in values:
        out.extend(_to_blocks(v))
    return out


def can_batch_with(head: dict[str, Any], next_cmd: dict[str, Any] | None) -> bool:
    if next_cmd is None:
        return False
    return (
        next_cmd.get("mode") == "prompt"
        and next_cmd.get("workload") == head.get("workload")
        and next_cmd.get("isMeta") == head.get("isMeta")
    )


async def run_headless(
    input_prompt: str | AsyncIterator[str],
    get_app_state: Any,
    set_app_state: Any,
    commands: Any,
    tools: Any,
    sdk_mcp_configs: dict[str, Any],
    agents: Any,
    options: dict[str, Any] | None = None,
) -> None:
    """
    Main non-interactive entry (TS runHeadless). Wire QueryEngine + MCP here.
    """
    _ = (
        get_app_state,
        set_app_state,
        commands,
        tools,
        sdk_mcp_configs,
        agents,
    )
    options = options or {}
    if options.get("resume_session_at") and not options.get("resume"):
        sys.stderr.write("Error: --resume-session-at requires --resume\n")
        sys.exit(1)
    if options.get("rewind_files") and not options.get("resume"):
        sys.stderr.write("Error: --rewind-files requires --resume\n")
        sys.exit(1)
    if options.get("rewind_files") and input_prompt:
        sys.stderr.write("Error: --rewind-files is a standalone operation and cannot be used with a prompt\n")
        sys.exit(1)

    if isinstance(input_prompt, str):
        sys.stdout.write(input_prompt + "\n")
    else:
        async for chunk in input_prompt:
            sys.stdout.write(str(chunk))
        sys.stdout.write("\n")
    sys.stdout.write("(run_headless) Connect StructuredIOSDK / RemoteIOSDK and QueryEngine for full parity.\n")


def remove_interrupted_message(messages: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip interrupted tail (TS removeInterruptedMessage parity — simplified)."""
    return [m for m in messages if m.get("type") != "interrupted"]
