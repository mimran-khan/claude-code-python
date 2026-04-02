"""Compatibility shim; implementation in :mod:`claude_code.utils.plugins.lsp_integration`."""

from __future__ import annotations

from .lsp_integration import *  # noqa: F403
from .lsp_integration import __all__ as _lsp_all

__all__ = list(_lsp_all)
