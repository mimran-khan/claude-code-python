"""
Upload brief attachments to OAuth file API (bridge / web viewer).

Migrated from: tools/BriefTool/upload.ts (stub — requires host HTTP + tokens).
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any

from ...utils.debug import log_for_debugging

_MAX_UPLOAD_BYTES = 30 * 1024 * 1024
_UPLOAD_TIMEOUT_S = 30.0


def guess_mime_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }[ext]
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


async def upload_attachment_best_effort(
    file_path: str,
    *,
    session: Any | None = None,
) -> str | None:
    """
    Return ``file_uuid`` when upload succeeds; otherwise log and return None.
    """
    path = Path(file_path)
    try:
        size = path.stat().st_size
    except OSError as e:
        log_for_debugging(f"[brief:upload] stat failed: {e}")
        return None
    if size > _MAX_UPLOAD_BYTES:
        log_for_debugging("[brief:upload] file too large")
        return None
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not token:
        log_for_debugging("[brief:upload] no oauth token; skip")
        return None
    _ = session
    log_for_debugging("[brief:upload] HTTP upload not wired in Python host; skipped")
    return None


__all__ = ["guess_mime_type", "upload_attachment_best_effort"]
