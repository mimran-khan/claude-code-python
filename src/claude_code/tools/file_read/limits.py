"""
File Read Tool output limits.

Two caps apply to text reads:

| limit         | default | checks                    | cost          | on overflow     |
|---------------|---------|---------------------------|---------------|-----------------|
| maxSizeBytes  | 256 KB  | TOTAL FILE SIZE (not out) | 1 stat        | throws pre-read |
| maxTokens     | 25000   | actual output tokens      | API roundtrip | throws post-read|

Migrated from: tools/FileReadTool/limits.ts (93 lines)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache

# Default maximum output size in bytes (256 KB)
MAX_OUTPUT_SIZE = 256 * 1024

# Default maximum output tokens
DEFAULT_MAX_OUTPUT_TOKENS = 25000


@dataclass(frozen=True)
class FileReadingLimits:
    """Limits for file reading operations."""

    max_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    max_size_bytes: int = MAX_OUTPUT_SIZE
    include_max_size_in_prompt: bool = False
    targeted_range_nudge: bool = False


def _get_env_max_tokens() -> int | None:
    """
    Get max tokens from environment variable override.

    Returns None when unset/invalid so the caller can fall through
    to the next precedence tier.
    """
    override = os.environ.get("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS")
    if override:
        try:
            parsed = int(override)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return None


@cache
def get_default_file_reading_limits() -> FileReadingLimits:
    """
    Get default limits for Read tool.

    Memoized so the value is fixed at first call — avoids
    the cap changing mid-session.

    Precedence for maxTokens: env var > DEFAULT_MAX_OUTPUT_TOKENS.
    """
    env_max_tokens = _get_env_max_tokens()
    max_tokens = env_max_tokens if env_max_tokens is not None else DEFAULT_MAX_OUTPUT_TOKENS

    return FileReadingLimits(
        max_tokens=max_tokens,
        max_size_bytes=MAX_OUTPUT_SIZE,
    )
