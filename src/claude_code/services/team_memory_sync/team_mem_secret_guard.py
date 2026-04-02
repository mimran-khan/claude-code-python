"""
Block writes of secrets into team memory paths.

Migrated from: services/teamMemorySync/teamMemSecretGuard.ts
"""

from __future__ import annotations

from ...memdir.paths import is_team_mem_path
from .secret_scanner import scan_for_secrets


def check_team_mem_secrets(file_path: str, content: str) -> str | None:
    if not is_team_mem_path(file_path):
        return None
    matches = scan_for_secrets(content)
    if not matches:
        return None
    labels = ", ".join(m.label for m in matches)
    return (
        f"Content contains potential secrets ({labels}) and cannot be written to team memory. "
        "Team memory is shared with all repository collaborators. "
        "Remove the sensitive content and try again."
    )
