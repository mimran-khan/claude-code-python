"""Compatibility shim; implementation in :mod:`claude_code.utils.plugins.orphaned_filter`."""

from __future__ import annotations

from .orphaned_filter import *  # noqa: F403
from .orphaned_filter import __all__ as _orph_all

__all__ = list(_orph_all)
