"""
Git-related behaviour driven by user settings (kept out of ``git.py``).

Migrated from: utils/gitSettings.ts
"""

from __future__ import annotations

import os

from .env_utils import is_env_defined_falsy, is_env_truthy
from .settings.settings import get_merged_settings


def should_include_git_instructions() -> bool:
    """Whether to inject git status / instructions into context."""

    env_val = os.environ.get("CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS")
    if is_env_truthy(env_val):
        return False
    if is_env_defined_falsy(env_val):
        return True
    merged = get_merged_settings()
    raw = merged.get("includeGitInstructions")
    if raw is not None:
        return bool(raw)
    return True


__all__ = ["should_include_git_instructions"]
