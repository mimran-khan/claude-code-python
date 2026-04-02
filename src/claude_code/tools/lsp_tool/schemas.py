"""
JSON-schema style descriptions for LSP tool operations.

Migrated from: tools/LSPTool/schemas.ts
"""

from __future__ import annotations

from .lsp_tool import INPUT_SCHEMA, LSP_OPERATIONS

LSP_TOOL_INPUT_SCHEMA = INPUT_SCHEMA

__all__ = ["INPUT_SCHEMA", "LSP_OPERATIONS", "LSP_TOOL_INPUT_SCHEMA"]
