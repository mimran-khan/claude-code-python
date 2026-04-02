"""Migrated from tools/FileReadTool/limits.ts."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ...utils.file import MAX_OUTPUT_SIZE

DEFAULT_MAX_OUTPUT_TOKENS = 25_000


def _env_max_tokens() -> int | None:
    raw = os.environ.get("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS")
    if not raw:
        return None
    try:
        v = int(raw, 10)
        return v if v > 0 else None
    except ValueError:
        return None


@dataclass
class FileReadingLimits:
    max_tokens: int
    max_size_bytes: int
    include_max_size_in_prompt: bool | None = None
    targeted_range_nudge: bool | None = None


def get_default_file_reading_limits() -> FileReadingLimits:
    """
    Default read limits.

    TODO: Merge GrowthBook override `tengu_amber_wren` (TS getDefaultFileReadingLimits).
    """
    env_tok = _env_max_tokens()
    max_tokens = env_tok if env_tok is not None else DEFAULT_MAX_OUTPUT_TOKENS
    return FileReadingLimits(
        max_tokens=max_tokens,
        max_size_bytes=int(MAX_OUTPUT_SIZE),
        include_max_size_in_prompt=None,
        targeted_range_nudge=None,
    )
