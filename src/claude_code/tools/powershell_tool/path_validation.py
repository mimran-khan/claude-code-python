"""Path validation helpers for PowerShell invocations.

Migrated from: tools/PowerShellTool/pathValidation.ts (placeholder subset).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PathCheckResult:
    ok: bool
    normalized: str | None = None
    error: str | None = None


def validate_working_path(path_str: str, allowed_roots: list[str]) -> PathCheckResult:
    try:
        p = Path(path_str).resolve()
    except (OSError, ValueError) as e:
        return PathCheckResult(False, error=str(e))
    for root in allowed_roots:
        try:
            if p.is_relative_to(Path(root).resolve()):
                return PathCheckResult(True, normalized=str(p))
        except (OSError, ValueError):
            continue
    return PathCheckResult(False, error="Path outside allowed working directories.")
