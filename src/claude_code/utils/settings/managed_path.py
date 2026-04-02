"""Managed policy paths. Migrated from: utils/settings/managedPath.ts"""

from __future__ import annotations

import os
from functools import lru_cache

from ..platform import get_platform


@lru_cache(maxsize=1)
def get_managed_file_path() -> str:
    if os.environ.get("USER_TYPE") == "ant" and os.environ.get("CLAUDE_CODE_MANAGED_SETTINGS_PATH"):
        return os.environ["CLAUDE_CODE_MANAGED_SETTINGS_PATH"]
    plat = get_platform()
    if plat == "macos":
        return "/Library/Application Support/ClaudeCode"
    if plat == "windows":
        return r"C:\Program Files\ClaudeCode"
    return "/etc/claude-code"


@lru_cache(maxsize=1)
def get_managed_settings_drop_in_dir() -> str:
    return os.path.join(get_managed_file_path(), "managed-settings.d")
