"""
Bash Tool prompt and constants.

Migrated from: tools/BashTool/toolName.ts and tools/BashTool/prompt.ts (370 lines)
"""

from __future__ import annotations

BASH_TOOL_NAME = "Shell"

# Default timeout in milliseconds (30 seconds)
DEFAULT_BASH_TIMEOUT_MS = 30_000

# Maximum timeout in milliseconds (10 minutes)
MAX_BASH_TIMEOUT_MS = 600_000


def get_default_timeout_ms() -> int:
    """Get the default timeout for bash commands in milliseconds."""
    return DEFAULT_BASH_TIMEOUT_MS


def get_max_timeout_ms() -> int:
    """Get the maximum timeout for bash commands in milliseconds."""
    return MAX_BASH_TIMEOUT_MS


def get_simple_prompt() -> str:
    """
    Get the prompt description for the Bash tool.

    Returns:
        The tool description string.
    """
    return """Executes a given bash command and returns its output.

The working directory persists between commands, but shell state does not.

IMPORTANT: Avoid using this tool to run `find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk`, or `echo` commands, unless explicitly instructed. Instead, use the appropriate dedicated tool:

- File search: Use Glob (NOT find or ls)
- Content search: Use Grep (NOT grep or rg)
- Read files: Use Read (NOT cat/head/tail)
- Edit files: Use StrReplace (NOT sed/awk)
- Write files: Use Write (NOT echo >/cat <<EOF)
- Communication: Output text directly (NOT echo/printf)

# Instructions

- If your command will create new directories or files, first use this tool to run `ls` to verify the parent directory exists.
- Always quote file paths that contain spaces with double quotes.
- Try to maintain your current working directory by using absolute paths.
- You may specify an optional timeout in milliseconds (up to 600000ms / 10 minutes). Default is 30000ms (30 seconds).
- You can use the `run_in_background` parameter to run the command in the background.

When issuing multiple commands:
- If the commands are independent, make multiple Shell tool calls in parallel.
- If the commands depend on each other, use a single Shell call with '&&' to chain them.
- Use ';' only when you need to run commands sequentially but don't care if earlier commands fail.
- DO NOT use newlines to separate commands.

For git commands:
- Prefer to create a new commit rather than amending an existing commit.
- Before running destructive operations, consider if there is a safer alternative.
- Never skip hooks (--no-verify) unless the user has explicitly asked for it.

# Committing changes with git

Only create commits when requested by the user. If unclear, ask first.

Git Safety Protocol:
- NEVER update the git config
- NEVER run destructive git commands unless explicitly requested
- NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless explicitly requested
- NEVER commit changes unless the user explicitly asks you to
"""
