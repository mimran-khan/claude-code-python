"""Compatibility shim; implementation in :mod:`claude_code.utils.plugins.hook_loader`."""

from __future__ import annotations

from .hook_loader import *  # noqa: F403
from .hook_loader import __all__ as _hl_all

__all__ = list(_hl_all)
