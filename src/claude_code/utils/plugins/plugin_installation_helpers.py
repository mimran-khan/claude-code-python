"""Path validation within plugin roots. Migrated from pluginInstallationHelpers.ts."""

from __future__ import annotations

import os


def validate_path_within_base(base: str, relative_path: str) -> str | None:
    base_abs = os.path.abspath(base)
    target = os.path.abspath(os.path.join(base_abs, relative_path))
    try:
        common = os.path.commonpath([base_abs, target])
    except ValueError:
        return None
    if common != base_abs:
        return None
    return target


__all__ = ["validate_path_within_base"]
