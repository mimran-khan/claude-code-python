"""Compatibility shim; implementation in :mod:`claude_code.utils.plugins.installed_manager`."""

from __future__ import annotations

from .installed_manager import *  # noqa: F403
from .installed_manager import __all__ as _im_all

__all__ = list(_im_all)
