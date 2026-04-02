"""
Shared constants for permission decision telemetry (partial TS port).

Migrated from: hooks/toolPermission/permissionLogging.ts (tool classification only).
"""

from __future__ import annotations

CODE_EDITING_TOOLS = frozenset({"Edit", "Write", "NotebookEdit"})


def is_code_editing_tool(tool_name: str) -> bool:
    return tool_name in CODE_EDITING_TOOLS
