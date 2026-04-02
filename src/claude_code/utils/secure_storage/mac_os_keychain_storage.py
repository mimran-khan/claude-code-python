"""
macOS Keychain-backed JSON credential blob (``security`` CLI).

Migrated from: utils/secureStorage/macOsKeychainStorage.ts
"""

from __future__ import annotations

import shutil
import subprocess
import time

from ..slow_operations import json_parse, json_stringify
from .mac_os_keychain_helpers import (
    CREDENTIALS_SERVICE_SUFFIX,
    KEYCHAIN_CACHE_TTL_MS,
    clear_keychain_cache,
    get_mac_os_keychain_storage_service_name,
    get_username,
    keychain_cache_state,
)
from .types import SecureStorageData, StorageUpdateResult


class MacOsKeychainJsonStore:
    name = "keychain"

    def read(self) -> SecureStorageData | None:
        prev_data = keychain_cache_state.data
        prev_at = keychain_cache_state.cached_at
        if prev_data is not None and time.time() * 1000 - prev_at < KEYCHAIN_CACHE_TTL_MS:
            return prev_data
        if shutil.which("security") is None:
            return None
        service = get_mac_os_keychain_storage_service_name(CREDENTIALS_SERVICE_SUFFIX)
        user = get_username()
        try:
            proc = subprocess.run(
                ["security", "find-generic-password", "-a", user, "-w", "-s", service],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                raise RuntimeError(proc.stderr or "keychain miss")
            raw_out = proc.stdout.strip()
            try:
                decoded = bytes.fromhex(raw_out).decode("utf-8")
                data = json_parse(decoded)
            except ValueError:
                data = json_parse(raw_out)
            keychain_cache_state.data = data
            keychain_cache_state.cached_at = time.time() * 1000
            return data
        except Exception:
            if prev_data is not None:
                keychain_cache_state.data = prev_data
                keychain_cache_state.cached_at = time.time() * 1000
                return prev_data
            keychain_cache_state.data = None
            keychain_cache_state.cached_at = time.time() * 1000
            return None

    async def read_async(self) -> SecureStorageData | None:
        return self.read()

    def update(self, data: SecureStorageData) -> StorageUpdateResult:
        clear_keychain_cache()
        if shutil.which("security") is None:
            return StorageUpdateResult(success=False)
        service = get_mac_os_keychain_storage_service_name(CREDENTIALS_SERVICE_SUFFIX)
        user = get_username()
        raw = json_stringify(data)
        hex_value = raw.encode("utf-8").hex()
        cmd = f'add-generic-password -U -a "{user}" -s "{service}" -X "{hex_value}"\n'
        try:
            proc = subprocess.run(
                ["security", "-i"],
                input=cmd,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
            if proc.returncode != 0:
                return StorageUpdateResult(success=False)
            return StorageUpdateResult(success=True)
        except OSError:
            return StorageUpdateResult(success=False)

    def delete(self) -> bool:
        clear_keychain_cache()
        service = get_mac_os_keychain_storage_service_name(CREDENTIALS_SERVICE_SUFFIX)
        user = get_username()
        try:
            subprocess.run(
                ["security", "delete-generic-password", "-a", user, "-s", service],
                check=False,
                capture_output=True,
                timeout=30,
            )
            return True
        except OSError:
            return False


mac_os_keychain_storage = MacOsKeychainJsonStore()
