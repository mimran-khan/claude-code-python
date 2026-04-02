"""Constants for FileEditTool (tools/FileEditTool/constants.ts)."""

FILE_EDIT_TOOL_NAME = "Edit"

CLAUDE_FOLDER_PERMISSION_PATTERN = "/.claude/**"
GLOBAL_CLAUDE_FOLDER_PERMISSION_PATTERN = "~/.claude/**"

FILE_UNEXPECTEDLY_MODIFIED_ERROR = "File has been unexpectedly modified. Read it again before attempting to write it."

# Match TS: 1 GiB cap on editable file size (stat bytes)
MAX_EDIT_FILE_SIZE = 1024 * 1024 * 1024
