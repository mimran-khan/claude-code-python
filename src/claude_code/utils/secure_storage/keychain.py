"""
macOS Keychain storage.

Migrated from: utils/secureStorage/macOsKeychainStorage.ts + macOsKeychainHelpers.ts
"""

from __future__ import annotations

import platform
import subprocess

from .storage import SecureStorage


def is_keychain_available() -> bool:
    """Check if macOS Keychain is available."""
    if platform.system() != "Darwin":
        return False

    try:
        result = subprocess.run(
            ["security", "help"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


class KeychainStorage(SecureStorage):
    """
    macOS Keychain-based secure storage.

    Uses the `security` command-line tool.
    """

    def get(self, service: str, account: str) -> str | None:
        """Get a credential from Keychain."""
        try:
            result = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-s",
                    service,
                    "-a",
                    account,
                    "-w",  # Output password only
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return result.stdout.strip()

            return None

        except Exception:
            return None

    def set(self, service: str, account: str, password: str) -> bool:
        """Set a credential in Keychain."""
        try:
            # Delete existing entry first (silently ignore if not exists)
            subprocess.run(
                [
                    "security",
                    "delete-generic-password",
                    "-s",
                    service,
                    "-a",
                    account,
                ],
                capture_output=True,
                timeout=10,
            )

            # Add new entry
            result = subprocess.run(
                [
                    "security",
                    "add-generic-password",
                    "-s",
                    service,
                    "-a",
                    account,
                    "-w",
                    password,
                    "-U",  # Update if exists
                ],
                capture_output=True,
                timeout=10,
            )

            return result.returncode == 0

        except Exception:
            return False

    def delete(self, service: str, account: str) -> bool:
        """Delete a credential from Keychain."""
        try:
            result = subprocess.run(
                [
                    "security",
                    "delete-generic-password",
                    "-s",
                    service,
                    "-a",
                    account,
                ],
                capture_output=True,
                timeout=10,
            )

            # Return true even if not found (idempotent)
            return result.returncode == 0 or result.returncode == 44

        except Exception:
            return False


def keychain_prefetch(services: list[tuple[str, str]]) -> dict[str, str]:
    """
    Prefetch multiple credentials from Keychain.

    Args:
        services: List of (service, account) tuples

    Returns:
        Dict mapping service/account to password
    """
    results = {}
    storage = KeychainStorage()

    for service, account in services:
        password = storage.get(service, account)
        if password:
            results[f"{service}/{account}"] = password

    return results
