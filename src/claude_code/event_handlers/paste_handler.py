"""
Bracketed-paste chunking and image path detection.

Migrated from: hooks/usePasteHandler.ts (core text transforms only).
"""

from __future__ import annotations

import re
from collections.abc import Callable

PASTE_THRESHOLD = 20


def split_paste_lines_for_image_paths(chunk: str) -> list[str]:
    parts = re.split(r" (?=\/|[A-Za-z]:\\)", chunk)
    lines: list[str] = []
    for p in parts:
        lines.extend(p.split("\n"))
    return [ln for ln in lines if ln.strip()]


def should_buffer_as_paste(
    *,
    is_from_paste: bool,
    input_text: str,
    paste_pending: bool,
    has_image_file_path_fn: Callable[[str], bool],
    on_paste_enabled: bool,
) -> bool:
    if not on_paste_enabled:
        return False
    lines = split_paste_lines_for_image_paths(input_text)
    has_img = any(has_image_file_path_fn(ln.strip()) for ln in lines)
    return len(input_text) > PASTE_THRESHOLD or paste_pending or has_img or is_from_paste


def join_paste_chunks(chunks: list[str]) -> str:
    raw = "".join(chunks)
    raw = re.sub(r"\[I$", "", raw)
    return re.sub(r"\[O$", "", raw)
