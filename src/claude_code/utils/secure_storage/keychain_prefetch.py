"""Warm keychain read at startup. Migrated from: utils/secureStorage/keychainPrefetch.ts"""

from __future__ import annotations


async def prefetch_keychain_reads() -> None:
    import sys

    if sys.platform != "darwin":
        return
    from .mac_os_keychain_storage import mac_os_keychain_storage

    await mac_os_keychain_storage.read_async()
