"""
Output length limits for shell tools.

Migrated from: utils/shell/outputLimits.ts
"""

from __future__ import annotations

import os

from claude_code.utils.debug import log_for_debugging

BASH_MAX_OUTPUT_UPPER_LIMIT = 150_000
BASH_MAX_OUTPUT_DEFAULT = 30_000


def _validate_bounded_int_env_var(
    name: str,
    value: str | None,
    default_value: int,
    upper_limit: int,
) -> int:
    if not value:
        return default_value
    try:
        parsed = int(value, 10)
    except ValueError:
        log_for_debugging(f'{name} Invalid value "{value}" (using default: {default_value})')
        return default_value
    if parsed <= 0:
        log_for_debugging(f'{name} Invalid value "{value}" (using default: {default_value})')
        return default_value
    if parsed > upper_limit:
        log_for_debugging(f"{name} Capped from {parsed} to {upper_limit}")
        return upper_limit
    return parsed


def get_max_output_length() -> int:
    return _validate_bounded_int_env_var(
        "BASH_MAX_OUTPUT_LENGTH",
        os.environ.get("BASH_MAX_OUTPUT_LENGTH"),
        BASH_MAX_OUTPUT_DEFAULT,
        BASH_MAX_OUTPUT_UPPER_LIMIT,
    )


__all__ = [
    "BASH_MAX_OUTPUT_DEFAULT",
    "BASH_MAX_OUTPUT_UPPER_LIMIT",
    "get_max_output_length",
]
