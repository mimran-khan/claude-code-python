"""
Primary JSON blob store with secondary fallback.

Migrated from: utils/secureStorage/fallbackStorage.ts
"""

from __future__ import annotations

from .types import CredentialsJsonStore, SecureStorageData, StorageUpdateResult


def create_fallback_storage(
    primary: CredentialsJsonStore,
    secondary: CredentialsJsonStore,
) -> CredentialsJsonStore:
    class _Fallback:
        name = f"{primary.name}-with-{secondary.name}-fallback"

        def read(self) -> SecureStorageData | None:
            result = primary.read()
            if result is not None:
                return result
            sec = secondary.read()
            return sec if sec is not None else {}

        async def read_async(self) -> SecureStorageData | None:
            result = await primary.read_async()
            if result is not None:
                return result
            sec = await secondary.read_async()
            return sec if sec is not None else {}

        def update(self, data: SecureStorageData) -> StorageUpdateResult:
            primary_before = primary.read()
            result = primary.update(data)
            if result.success:
                if primary_before is None:
                    secondary.delete()
                return result
            fb = secondary.update(data)
            if fb.success:
                if primary_before is not None:
                    primary.delete()
                return StorageUpdateResult(success=True, warning=fb.warning)
            return StorageUpdateResult(success=False)

        def delete(self) -> bool:
            return primary.delete() or secondary.delete()

    return _Fallback()
