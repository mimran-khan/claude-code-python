"""Ensure ``src/`` is on ``sys.path`` so examples run without a pip install."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_src_on_path() -> Path:
    """
    Return the claude-code-python project root (parent of ``examples/``).

    Inserts ``<root>/src`` at the front of ``sys.path`` if needed.
    """
    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    src_str = str(src)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
    return root
