"""
Plaintext credentials file (~/.claude/.credentials.json).

Migrated from: utils/secureStorage/plainTextStorage.ts
"""

from __future__ import annotations

import json
import os

import aiofiles

from ..env_utils import get_claude_config_home_dir
from .types import SecureStorageData, StorageUpdateResult


def _storage_path() -> tuple[str, str]:
    storage_dir = get_claude_config_home_dir()
    return storage_dir, os.path.join(storage_dir, ".credentials.json")


class PlainTextJsonStore:
    name = "plaintext"

    def read(self) -> SecureStorageData | None:
        _, path = _storage_path()
        try:
            with open(path, encoding="utf-8") as f:
                return json.loads(f.read())
        except (OSError, json.JSONDecodeError):
            return None

    async def read_async(self) -> SecureStorageData | None:
        _, path = _storage_path()
        try:
            async with aiofiles.open(path, encoding="utf-8") as f:
                return json.loads(await f.read())
        except (OSError, json.JSONDecodeError):
            return None

    def update(self, data: SecureStorageData) -> StorageUpdateResult:
        storage_dir, path = _storage_path()
        try:
            os.makedirs(storage_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.chmod(path, 0o600)
            return StorageUpdateResult(
                success=True,
                warning="Warning: Storing credentials in plaintext.",
            )
        except OSError:
            return StorageUpdateResult(success=False)

    def delete(self) -> bool:
        _, path = _storage_path()
        try:
            os.unlink(path)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            return False


plain_text_storage = PlainTextJsonStore()
