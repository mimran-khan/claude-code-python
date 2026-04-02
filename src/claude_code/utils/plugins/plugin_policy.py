"""Compatibility shim — implementation in :mod:`claude_code.utils.plugins.policy`."""

from __future__ import annotations

from .policy import *  # noqa: F403
from .policy import __all__ as _policy_all

__all__ = list(_policy_all)
