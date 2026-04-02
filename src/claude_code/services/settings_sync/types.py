"""User settings sync types. Migrated from: services/settingsSync/types.ts"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class UserSyncData:
    user_id: str
    version: int
    last_modified: str
    checksum: str
    content: dict[str, Any]


@dataclass
class SettingsSyncFetchResult:
    success: bool
    data: UserSyncData | None = None
    is_empty: bool = False
    error: str | None = None
    skip_retry: bool = False


@dataclass
class SettingsSyncUploadResult:
    success: bool
    checksum: str | None = None
    last_modified: str | None = None
    error: str | None = None


SYNC_KEYS_USER_SETTINGS = "~/.claude/settings.json"
SYNC_KEYS_USER_MEMORY = "~/.claude/CLAUDE.md"


def project_settings_key(project_id: str) -> str:
    return f"projects/{project_id}/.claude/settings.local.json"


def project_memory_key(project_id: str) -> str:
    return f"projects/{project_id}/CLAUDE.local.md"


def parse_user_sync_data(payload: Any) -> UserSyncData | None:
    if not isinstance(payload, dict):
        return None
    try:
        content = payload.get("content")
        if not isinstance(content, dict) or "entries" not in content:
            return None
        entries = content.get("entries")
        if not isinstance(entries, dict):
            return None
        return UserSyncData(
            user_id=str(payload["userId"]),
            version=int(payload["version"]),
            last_modified=str(payload["lastModified"]),
            checksum=str(payload["checksum"]),
            content={"entries": {str(k): str(v) for k, v in entries.items()}},
        )
    except (KeyError, TypeError, ValueError):
        return None
