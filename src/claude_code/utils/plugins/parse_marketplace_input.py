"""Compatibility shim; implementation in :mod:`claude_code.utils.plugins.marketplace_parser`."""

from __future__ import annotations

from .marketplace_parser import *  # noqa: F403
from .marketplace_parser import __all__ as _mp_all

__all__ = list(_mp_all)
