"""
Secure storage interface and factory.

Migrated from: utils/secureStorage/index.ts + fallbackStorage.ts
"""

from __future__ import annotations

import contextlib
import platform
from abc import ABC, abstractmethod


class SecureStorage(ABC):
    """Abstract interface for secure credential storage."""

    @abstractmethod
    def get(self, service: str, account: str) -> str | None:
        """
        Get a credential.

        Args:
            service: Service name
            account: Account name

        Returns:
            Credential value or None
        """
        pass

    @abstractmethod
    def set(self, service: str, account: str, password: str) -> bool:
        """
        Set a credential.

        Args:
            service: Service name
            account: Account name
            password: Credential value

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def delete(self, service: str, account: str) -> bool:
        """
        Delete a credential.

        Args:
            service: Service name
            account: Account name

        Returns:
            True if deleted
        """
        pass


class FallbackStorage(SecureStorage):
    """
    Storage that tries primary, falls back to secondary.
    """

    def __init__(self, primary: SecureStorage, fallback: SecureStorage):
        self._primary = primary
        self._fallback = fallback

    def get(self, service: str, account: str) -> str | None:
        try:
            result = self._primary.get(service, account)
            if result is not None:
                return result
        except Exception:
            pass

        return self._fallback.get(service, account)

    def set(self, service: str, account: str, password: str) -> bool:
        try:
            if self._primary.set(service, account, password):
                return True
        except Exception:
            pass

        return self._fallback.set(service, account, password)

    def delete(self, service: str, account: str) -> bool:
        primary_deleted = False
        fallback_deleted = False

        with contextlib.suppress(Exception):
            primary_deleted = self._primary.delete(service, account)

        with contextlib.suppress(Exception):
            fallback_deleted = self._fallback.delete(service, account)

        return primary_deleted or fallback_deleted


# Global storage instance
_storage: SecureStorage | None = None


def get_secure_storage() -> SecureStorage:
    """
    Get the appropriate secure storage for the current platform.

    Returns:
        SecureStorage implementation
    """
    global _storage

    if _storage is not None:
        return _storage

    if platform.system() == "Darwin":
        from .keychain import KeychainStorage, is_keychain_available
        from .plaintext import PlainTextStorage

        if is_keychain_available():
            _storage = FallbackStorage(KeychainStorage(), PlainTextStorage())
        else:
            _storage = PlainTextStorage()
    else:
        # Linux/Windows: use plaintext for now
        # TODO: Add libsecret support for Linux
        # TODO: Add Windows Credential Manager support
        from .plaintext import PlainTextStorage

        _storage = PlainTextStorage()

    return _storage


def get_credential(service: str, account: str) -> str | None:
    """Get a credential."""
    return get_secure_storage().get(service, account)


def set_credential(service: str, account: str, password: str) -> bool:
    """Set a credential."""
    return get_secure_storage().set(service, account, password)


def delete_credential(service: str, account: str) -> bool:
    """Delete a credential."""
    return get_secure_storage().delete(service, account)
