"""
macOS Keychain service name + cache metadata.

Migrated from: utils/secureStorage/macOsKeychainHelpers.ts
"""

from __future__ import annotations

import getpass
import hashlib
import os
from dataclasses import dataclass
from typing import Any

from ...constants.oauth import get_oauth_config
from ..env_utils import get_claude_config_home_dir
from .types import SecureStorageData

CREDENTIALS_SERVICE_SUFFIX = "-credentials"
KEYCHAIN_CACHE_TTL_MS = 30_000


def get_mac_os_keychain_storage_service_name(service_suffix: str = "") -> str:
    config_dir = get_claude_config_home_dir()
    is_default = not os.environ.get("CLAUDE_CONFIG_DIR")
    suffix = "" if is_default else f"-{hashlib.sha256(config_dir.encode()).hexdigest()[:8]}"
    oauth = get_oauth_config()
    return f"Claude Code{oauth.OAUTH_FILE_SUFFIX}{service_suffix}{suffix}"


def get_username() -> str:
    try:
        return os.environ.get("USER") or getpass.getuser()
    except Exception:
        return "claude-code-user"


@dataclass
class KeychainCacheState:
    data: SecureStorageData | None = None
    cached_at: float = 0.0
    generation: int = 0
    read_in_flight: Any = None


keychain_cache_state = KeychainCacheState()


def clear_keychain_cache() -> None:
    keychain_cache_state.generation += 1
    keychain_cache_state.data = None
    keychain_cache_state.cached_at = 0.0
    keychain_cache_state.read_in_flight = None
