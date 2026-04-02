"""Remote managed settings API types. Migrated from: services/remoteManagedSettings/types.ts"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RemoteManagedSettingsFetchResult:
    success: bool
    settings: dict[str, Any] | None = None
    checksum: str | None = None
    error: str | None = None
    skip_retry: bool = False


def parse_remote_settings_response(data: Any) -> tuple[dict[str, Any], str] | None:
    if not isinstance(data, dict):
        return None
    uuid = data.get("uuid")
    checksum = data.get("checksum")
    settings = data.get("settings")
    if not isinstance(uuid, str) or not isinstance(checksum, str):
        return None
    if not isinstance(settings, dict):
        return None
    return settings, checksum
