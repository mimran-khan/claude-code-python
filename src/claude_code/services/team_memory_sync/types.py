"""Team memory sync API types. Migrated from: services/teamMemorySync/types.ts"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkippedSecretFile:
    path: str
    rule_id: str
    label: str


@dataclass
class TeamMemorySyncFetchResult:
    success: bool
    data: dict[str, Any] | None = None
    is_empty: bool = False
    not_modified: bool = False
    checksum: str | None = None
    error: str | None = None
    skip_retry: bool = False
    error_type: str | None = None
    http_status: int | None = None


@dataclass
class TeamMemorySyncPushResult:
    success: bool
    files_uploaded: int = 0
    checksum: str | None = None
    conflict: bool = False
    error: str | None = None
    skipped_secrets: list[SkippedSecretFile] = field(default_factory=list)
    error_type: str | None = None
    http_status: int | None = None


@dataclass
class SyncState:
    """Mutable sync state for team memory pull/push."""

    last_known_checksum: str | None = None
    server_version: int | None = None
    entry_checksums: dict[str, str] = field(default_factory=dict)
