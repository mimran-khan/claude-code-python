"""Permission mode checks for Bash tool.

Migrated from: tools/BashTool/modeValidation.ts (subset).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PermissionMode = Literal["default", "plan", "bypassPermissions", "auto", "acceptEdits", "bubble"]


@dataclass
class ModeCheckResult:
    allowed: bool
    reason: str = ""


def check_permission_mode(mode: PermissionMode, *, read_only: bool) -> ModeCheckResult:
    if mode == "plan" and not read_only:
        return ModeCheckResult(False, "Plan mode allows only read-only commands.")
    return ModeCheckResult(True)


def get_auto_allowed_commands() -> frozenset[str]:
    """Commands auto-approved in ``auto`` mode (TS expands this set)."""
    return frozenset({"git status", "git diff", "git log"})


__all__ = [
    "ModeCheckResult",
    "PermissionMode",
    "check_permission_mode",
    "get_auto_allowed_commands",
]
