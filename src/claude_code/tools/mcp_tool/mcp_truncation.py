"""
Output truncation helpers for MCP tool results.

Migrated from: tools/MCPTool/MCPTool.ts (isResultTruncated via isOutputLineTruncated)
"""

from __future__ import annotations

MCP_GLOBAL_RESULT_SOFT_LIMIT: int = 100_000


def is_mcp_result_truncated(output: str, *, max_line_chars: int = 16_384) -> bool:
    """
    Return True if any line in the string exceeds the UI truncation threshold.

    TS uses terminal line truncation; we approximate with per-line length check.
    """
    if not output:
        return False
    for line in output.splitlines():
        if len(line) > max_line_chars:
            return True
    return len(output) > MCP_GLOBAL_RESULT_SOFT_LIMIT
