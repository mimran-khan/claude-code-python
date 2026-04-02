"""Permission mode checks for PowerShell tool.

Migrated from: tools/PowerShellTool/modeValidation.ts (subset).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PermissionMode = Literal["default", "plan", "bypassPermissions", "auto", "acceptEdits"]


@dataclass
class ModeCheckResult:
    allowed: bool
    reason: str = ""


def check_mode_allows_powershell(mode: PermissionMode, *, read_only: bool) -> ModeCheckResult:
    if mode == "plan" and not read_only:
        return ModeCheckResult(False, "Plan mode allows only read-only commands.")
    return ModeCheckResult(True)
