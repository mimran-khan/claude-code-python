"""Grep tool constants. Migrated from tools/GrepTool/prompt.ts."""

# Inline tool names to avoid import cycles with agent_tool / bash_tool.
_AGENT = "Agent"
_BASH = "Bash"

GREP_TOOL_NAME = "Grep"


def get_description() -> str:
    return f"""A powerful search tool built on ripgrep

  Usage:
  - ALWAYS use {GREP_TOOL_NAME} for search tasks. NEVER invoke `grep` or `rg` as a {_BASH} command. The {GREP_TOOL_NAME} tool has been optimized for correct permissions and access.
  - Supports full regex syntax (e.g., "log.*Error", "function\\s+\\w+")
  - Filter files with glob parameter (e.g., "*.js", "**/*.tsx") or type parameter (e.g., "js", "py", "rust")
  - Output modes: "content" shows matching lines, "files_with_matches" shows only file paths (default), "count" shows match counts
  - Use {_AGENT} tool for open-ended searches requiring multiple rounds
  - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping
  - Multiline matching: For cross-line patterns, use `multiline: true`
"""
