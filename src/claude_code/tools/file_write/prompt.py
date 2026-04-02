"""
File Write Tool prompt and constants.

Migrated from: tools/FileWriteTool/prompt.ts (19 lines)
"""

from ..file_read.prompt import FILE_READ_TOOL_NAME

FILE_WRITE_TOOL_NAME = "Write"
DESCRIPTION = "Write a file to the local filesystem."


def _get_pre_read_instruction() -> str:
    """Get the instruction about reading files first."""
    return (
        f"\n- If this is an existing file, you MUST use the {FILE_READ_TOOL_NAME} "
        "tool first to read the file's contents. This tool will fail if you did "
        "not read the file first."
    )


def get_write_tool_description() -> str:
    """Get the full description for the Write tool."""
    return f"""Writes a file to the local filesystem.

Usage:
- This tool will overwrite the existing file if there is one at the provided path.{_get_pre_read_instruction()}
- Prefer the Edit tool for modifying existing files — it only sends the diff. Only use this tool to create new files or for complete rewrites.
- NEVER create documentation files (*.md) or README files unless explicitly requested by the User.
- Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked."""
