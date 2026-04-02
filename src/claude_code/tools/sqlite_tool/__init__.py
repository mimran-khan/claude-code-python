"""Sqlite — read-only local database queries."""

from __future__ import annotations

from .constants import SQLITE_TOOL_NAME
from .sqlite_tool import SqliteTool

__all__ = ["SQLITE_TOOL_NAME", "SqliteTool"]
