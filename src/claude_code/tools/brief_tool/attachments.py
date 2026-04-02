"""
Attachment path validation for Brief / user-message flows.

Migrated from: tools/BriefTool/attachments.ts (subset — bridge upload hooks in ``upload.py``).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

_IMAGE_EXT = re.compile(r"\.(png|jpe?g|gif|webp|bmp|svg)$", re.I)


@dataclass
class ResolvedAttachment:
    path: str
    size: int
    is_image: bool
    file_uuid: str | None = None


def validate_attachment_paths(raw_paths: list[str], *, cwd: str | None = None) -> tuple[bool, str | None]:
    base = Path(cwd or os.getcwd())
    for raw in raw_paths:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = (base / p).resolve()
        try:
            if not p.is_file():
                return False, f'Attachment "{raw}" is not a regular file.'
        except OSError as e:
            return False, f'Attachment "{raw}" is not accessible: {e}'
    return True, None


def resolve_attachments_local(raw_paths: list[str], *, cwd: str | None = None) -> list[ResolvedAttachment]:
    base = Path(cwd or os.getcwd())
    out: list[ResolvedAttachment] = []
    for raw in raw_paths:
        p = Path(raw).expanduser()
        if not p.is_absolute():
            p = (base / p).resolve()
        st = p.stat()
        out.append(
            ResolvedAttachment(
                path=str(p),
                size=st.st_size,
                is_image=bool(_IMAGE_EXT.search(p.name)),
            ),
        )
    return out


__all__ = ["ResolvedAttachment", "resolve_attachments_local", "validate_attachment_paths"]
