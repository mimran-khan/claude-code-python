"""
Resolve paths to absolute, normalized form.

Migrated from: utils/loadAbsolutePath.ts (source not present in workspace; standard behavior).
"""

from __future__ import annotations

import os
from pathlib import Path


def load_absolute_path(path: str, *, base: str | None = None) -> str:
    """
    Resolve *path* to an absolute path with symlinks resolved where supported.

    If *base* is set, relative paths are resolved against *base*; otherwise the
    process current working directory is used.
    """
    p = Path(path)
    if not p.is_absolute():
        root = Path(base) if base else Path.cwd()
        p = root / p
    return os.path.realpath(str(p))


def load_absolute_path_optional(path: str | None, *, base: str | None = None) -> str | None:
    """Same as load_absolute_path but returns None for None/empty input."""
    if not path:
        return None
    return load_absolute_path(path, base=base)
