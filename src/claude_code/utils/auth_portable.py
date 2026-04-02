"""
Portable auth helpers (macOS keychain cleanup, API key display normalization).

Migrated from: utils/authPortable.ts
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

from .secure_storage.mac_os_keychain_helpers import (
    CREDENTIALS_SERVICE_SUFFIX,
    get_mac_os_keychain_storage_service_name,
)


async def maybe_remove_api_key_from_mac_os_keychain_throws() -> None:
    """Delete the Claude API key generic password entry (macOS only)."""

    if sys.platform != "darwin":
        return

    service = get_mac_os_keychain_storage_service_name(CREDENTIALS_SERVICE_SUFFIX)
    user = os.environ.get("USER", "")

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["security", "delete-generic-password", "-a", user, "-s", service],
            capture_output=True,
            text=True,
            check=False,
        )

    result = await asyncio.to_thread(_run)
    if result.returncode != 0:
        raise RuntimeError("Failed to delete keychain entry")


def normalize_api_key_for_config(api_key: str) -> str:
    """Return last 20 characters (display / redaction helper)."""

    return api_key[-20:]


__all__ = ["maybe_remove_api_key_from_mac_os_keychain_throws", "normalize_api_key_for_config"]
