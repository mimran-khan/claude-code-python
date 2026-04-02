"""
Main model query loop facade.

The TypeScript `query.ts` orchestrates streaming, tools, and compaction; the Python
equivalent is `core.query_engine.QueryEngine` plus `query.*` helpers.
"""

from __future__ import annotations

from .core.query_engine import QueryEngine, QueryEngineConfig

__all__ = ["QueryEngine", "QueryEngineConfig"]
