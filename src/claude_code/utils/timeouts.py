"""
Bash / shell timeout constants from environment.

Migrated from: utils/timeouts.ts
"""

from __future__ import annotations

import os
from collections.abc import Mapping

DEFAULT_TIMEOUT_MS = 120_000
MAX_TIMEOUT_MS = 600_000


def get_default_bash_timeout_ms(
    env: Mapping[str, str | None] | None = None,
) -> int:
    e = env if env is not None else os.environ
    raw = e.get("BASH_DEFAULT_TIMEOUT_MS")
    if raw:
        try:
            parsed = int(raw, 10)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return DEFAULT_TIMEOUT_MS


def get_max_bash_timeout_ms(env: Mapping[str, str | None] | None = None) -> int:
    e = env if env is not None else os.environ
    raw = e.get("BASH_MAX_TIMEOUT_MS")
    default = get_default_bash_timeout_ms(e)
    if raw:
        try:
            parsed = int(raw, 10)
            if parsed > 0:
                return max(parsed, default)
        except ValueError:
            pass
    return max(MAX_TIMEOUT_MS, default)
