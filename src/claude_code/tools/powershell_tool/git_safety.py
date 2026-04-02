"""Git safety checks for PowerShell (mirrors Bash git guidance).

Migrated from: tools/PowerShellTool/gitSafety.ts (subset).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GitSafetyNote:
    level: str
    text: str


_FORCE = re.compile(r"(git\s+push\s+.*--force|git\s+reset\s+--hard)", re.I)
_NO_VERIFY = re.compile(r"--no-verify", re.I)


def git_safety_notes(command: str) -> GitSafetyNote | None:
    if _NO_VERIFY.search(command):
        return GitSafetyNote(level="warn", text="Avoid --no-verify unless the user asked.")
    if _FORCE.search(command):
        return GitSafetyNote(level="warn", text="Destructive git operation — prefer safer alternatives.")
    return None
