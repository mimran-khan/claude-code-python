"""
Persistent paste cache on disk (content-addressable by hash).

Migrated from: utils/pasteStore.ts
"""

from __future__ import annotations

import contextlib
import hashlib
import os
from pathlib import Path

from .debug import log_for_debugging
from .env_utils import get_claude_config_home_dir
from .errors import is_enoent

PASTE_STORE_DIR = "paste-cache"


def _paste_store_dir() -> str:
    return str(Path(get_claude_config_home_dir()) / PASTE_STORE_DIR)


def hash_pasted_text(content: str) -> str:
    """SHA-256 hex digest, first 16 chars (sync, for callers before async store)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _paste_path(content_hash: str) -> Path:
    return Path(_paste_store_dir()) / f"{content_hash}.txt"


async def store_pasted_text(content_hash: str, content: str) -> None:
    try:
        d = Path(_paste_store_dir())
        d.mkdir(parents=True, exist_ok=True)
        path = _paste_path(content_hash)
        path.write_text(content, encoding="utf-8")
        with contextlib.suppress(OSError):
            os.chmod(path, 0o600)
        log_for_debugging(f"Stored paste {content_hash} to {path}")
    except OSError as e:
        log_for_debugging(f"Failed to store paste: {e}")


async def retrieve_pasted_text(content_hash: str) -> str | None:
    path = _paste_path(content_hash)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        if not is_enoent(e):
            log_for_debugging(f"Failed to retrieve paste {content_hash}: {e}")
        return None


async def cleanup_old_pastes(cutoff_date) -> None:
    """Remove ``*.txt`` pastes with mtime before ``cutoff_date``."""
    paste_dir = Path(_paste_store_dir())
    try:
        files = list(paste_dir.iterdir())
    except OSError:
        return
    cutoff_ms = cutoff_date.timestamp()
    for p in files:
        if p.suffix != ".txt":
            continue
        try:
            st = p.stat()
            if st.st_mtime < cutoff_ms:
                p.unlink(missing_ok=True)
                log_for_debugging(f"Cleaned up old paste: {p}")
        except OSError:
            pass
