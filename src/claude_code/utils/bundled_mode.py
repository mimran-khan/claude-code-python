"""
Detect Bun runtime / bundled executable mode.

Migrated from: utils/bundledMode.ts

Python builds are not Bun; these helpers return False unless overridden in tests.
"""

from __future__ import annotations

import os


def is_running_with_bun() -> bool:
    """True when the active runtime is Bun (Node compatibility hook)."""

    return os.environ.get("CLAUDE_CODE_RUNTIME", "").lower() == "bun"


def is_in_bundled_mode() -> bool:
    """True when running as a single-file / embedded bundle (Bun compile)."""

    return os.environ.get("CLAUDE_CODE_BUNDLED", "").lower() in ("1", "true", "yes")


__all__ = ["is_running_with_bun", "is_in_bundled_mode"]
