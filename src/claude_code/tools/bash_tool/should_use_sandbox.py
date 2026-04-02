"""
Whether a bash invocation should run inside the sandbox adapter.

Migrated from: tools/BashTool/shouldUseSandbox.ts (simplified — no GrowthBook ant config).
"""

from __future__ import annotations

from typing import TypedDict


class SandboxInput(TypedDict, total=False):
    command: str
    dangerously_disable_sandbox: bool


def _sandboxing_enabled() -> bool:
    import os

    return os.environ.get("CLAUDE_CODE_SANDBOX", "").lower() in ("1", "true", "yes")


def _unsandboxed_allowed() -> bool:
    import os

    return os.environ.get("CLAUDE_CODE_ALLOW_UNSANDBOXED", "").lower() in ("1", "true", "yes")


def should_use_sandbox(input_data: SandboxInput | dict[str, object] | None) -> bool:
    if not _sandboxing_enabled():
        return False
    if not input_data:
        return False
    cmd = input_data.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        return False
    return not (input_data.get("dangerously_disable_sandbox") and _unsandboxed_allowed())


__all__ = ["SandboxInput", "should_use_sandbox"]
