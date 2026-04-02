"""
TS-style JSON credential blob types (distinct from ``storage.SecureStorage`` ABC).

Migrated from: utils/secureStorage/types.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

SecureStorageData = dict[str, Any]


@runtime_checkable
class CredentialsJsonStore(Protocol):
    """Single-document OAuth JSON store (TS ``SecureStorage``)."""

    name: str

    def read(self) -> SecureStorageData | None: ...

    async def read_async(self) -> SecureStorageData | None: ...

    def update(self, data: SecureStorageData) -> StorageUpdateResult: ...

    def delete(self) -> bool: ...


@dataclass
class StorageUpdateResult:
    success: bool
    warning: str | None = None
