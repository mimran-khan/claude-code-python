"""Compatibility shim; implementation in :mod:`claude_code.utils.plugins.markdown_walker`."""

from __future__ import annotations

from .markdown_walker import *  # noqa: F403
from .markdown_walker import __all__ as _md_all

__all__ = list(_md_all)
