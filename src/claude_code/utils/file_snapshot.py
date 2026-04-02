"""
Opaque file snapshot handle (``utils/fileSnapshot.ts`` not in snapshot).
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class FileSnapshot:
    path: str
    content_hash: str
    captured_at: float


def capture_snapshot(path: str, content_hash: str) -> FileSnapshot:
    return FileSnapshot(path=path, content_hash=content_hash, captured_at=time.time())
