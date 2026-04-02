"""
Plaintext storage fallback.

File-based credential storage (not secure, but works everywhere).

Migrated from: utils/secureStorage/plainTextStorage.ts
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..config_utils import get_claude_config_dir
from .storage import SecureStorage


class PlainTextStorage(SecureStorage):
    """
    Plaintext file-based storage.

    WARNING: This is not secure. Credentials are stored in plain text.
    Use only as a fallback when secure storage is unavailable.
    """

    def __init__(self, storage_path: str | None = None):
        if storage_path:
            self._path = Path(storage_path)
        else:
            self._path = Path(get_claude_config_dir()) / "credentials.json"

    def _load(self) -> dict[str, dict[str, str]]:
        """Load credentials from file."""
        if not self._path.exists():
            return {}

        try:
            with open(self._path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self, data: dict[str, dict[str, str]]) -> bool:
        """Save credentials to file."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)

            # Write with restricted permissions
            with open(self._path, "w") as f:
                json.dump(data, f, indent=2)

            # Set file permissions to user-only
            os.chmod(self._path, 0o600)

            return True
        except OSError:
            return False

    def get(self, service: str, account: str) -> str | None:
        """Get a credential."""
        data = self._load()
        service_data = data.get(service, {})
        return service_data.get(account)

    def set(self, service: str, account: str, password: str) -> bool:
        """Set a credential."""
        data = self._load()

        if service not in data:
            data[service] = {}

        data[service][account] = password
        return self._save(data)

    def delete(self, service: str, account: str) -> bool:
        """Delete a credential."""
        data = self._load()

        if service not in data:
            return True  # Already doesn't exist

        if account in data[service]:
            del data[service][account]

            # Clean up empty service
            if not data[service]:
                del data[service]

            return self._save(data)

        return True  # Already doesn't exist
