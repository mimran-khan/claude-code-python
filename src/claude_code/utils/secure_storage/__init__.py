"""
Secure storage: legacy per-key API (``storage``) + TS-style JSON blob stores.

Migrated from: utils/secureStorage/*.ts
"""

from __future__ import annotations

import sys

from .fallback_storage import create_fallback_storage
from .keychain_prefetch import prefetch_keychain_reads
from .mac_os_keychain_storage import mac_os_keychain_storage
from .plain_text_storage import plain_text_storage
from .storage import (
    FallbackStorage,
    SecureStorage,
    delete_credential,
    get_credential,
    get_secure_storage,
    set_credential,
)
from .types import CredentialsJsonStore, SecureStorageData, StorageUpdateResult

__all__ = [
    "CredentialsJsonStore",
    "FallbackStorage",
    "SecureStorage",
    "SecureStorageData",
    "StorageUpdateResult",
    "create_fallback_storage",
    "delete_credential",
    "get_credential",
    "get_credentials_json_store",
    "get_secure_storage",
    "mac_os_keychain_storage",
    "plain_text_storage",
    "prefetch_keychain_reads",
    "set_credential",
]


def get_credentials_json_store() -> CredentialsJsonStore:
    """TS ``getSecureStorage()`` equivalent (single JSON credentials document)."""
    if sys.platform == "darwin":
        return create_fallback_storage(mac_os_keychain_storage, plain_text_storage)
    return plain_text_storage
