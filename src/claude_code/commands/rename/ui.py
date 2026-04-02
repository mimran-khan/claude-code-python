"""
Lazy-loaded /rename UI entry.

Migrated from: commands/rename/index.ts (``load``) and commands/rename/rename.ts (``call``).
"""

from __future__ import annotations

from .rename_impl import call

__all__ = ["call"]
