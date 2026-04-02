#!/usr/bin/env python3
"""
Run a built-in tool directly (outside the full query loop).

Demonstrates ``ToolUseContext``, validation, and structured ``ToolResult`` handling
using the bundled Glob tool.

Run:
  python examples/tool_usage.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from _path_setup import ensure_src_on_path

ensure_src_on_path()

from claude_code.tools.base import ToolUseContext
from claude_code.tools.glob_tool.glob_tool import GlobTool


async def main() -> int:
    tool = GlobTool()
    context = ToolUseContext(tool_use_id="example-glob-1")

    # Search Python files in the current working directory (repo root if run from there).
    tool_input = {
        "pattern": "*.py",
        "path": os.getcwd(),
    }

    try:
        validation = await tool.validate_input(tool_input, context)
        if not validation.get("result", False):
            print(f"Validation failed: {validation.get('message', validation)}", file=sys.stderr)
            return 1

        result = await tool.execute(tool_input, context)

        if not result.success:
            print(f"Tool error: {result.error} (code={result.error_code})", file=sys.stderr)
            return 1

        output = result.output
        print("Glob tool: success")
        if output is not None:
            # GlobOutputModel: filenames, num_files, truncated, duration_ms
            filenames = getattr(output, "filenames", []) or []
            num = getattr(output, "num_files", None)
            truncated = getattr(output, "truncated", None)
            print(f"  num_files: {num}")
            print(f"  truncated: {truncated}")
            if filenames:
                print("  sample paths:")
                for p in filenames[:10]:
                    print(f"    - {p}")
                if len(filenames) > 10:
                    print(f"    ... and {len(filenames) - 10} more")

    except OSError as exc:
        print(f"Filesystem error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
