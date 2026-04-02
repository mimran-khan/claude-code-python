"""Migrated from tools/FileReadTool/prompt.ts (renderPromptTemplate)."""

from __future__ import annotations

from .constants import (
    LINE_FORMAT_INSTRUCTION,
    MAX_LINES_TO_READ,
    OFFSET_INSTRUCTION_DEFAULT,
    OFFSET_INSTRUCTION_TARGETED,
)


def render_prompt_template(
    line_format: str,
    max_size_instruction: str,
    offset_instruction: str,
) -> str:
    return f"""Reads a file from the local filesystem. You can access any file directly by using this tool.
Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

Usage:
- The file_path parameter must be an absolute path, not a relative path
- By default, it reads up to {MAX_LINES_TO_READ} lines starting from the beginning of the file{max_size_instruction}
{offset_instruction}
{line_format}
- This tool allows Claude Code to read images (eg PNG, JPG, etc). When reading an image file the contents are presented visually as Claude Code is a multimodal LLM.
- TODO: PDF support paragraph when isPDFSupported() is wired (tools/FileReadTool/prompt.ts)
- This tool can read Jupyter notebooks (.ipynb files) and returns all cells with their outputs, combining code, text, and visualizations.
- This tool can only read files, not directories. To read a directory, use ListDir or a shell tool.
- You will regularly be asked to read screenshots. If the user provides a path to a screenshot, ALWAYS use this tool to view the file at the path.
- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents."""


def build_read_tool_prompt(
    *,
    include_max_size_in_prompt: bool,
    max_size_bytes: int,
    targeted_range_nudge: bool,
) -> str:
    from ...utils.format import format_file_size

    max_size_instruction = ""
    if include_max_size_in_prompt:
        max_size_instruction = (
            f". Files larger than {format_file_size(max_size_bytes)} will return an error; "
            "use offset and limit for larger files"
        )
    offset_instruction = OFFSET_INSTRUCTION_TARGETED if targeted_range_nudge else OFFSET_INSTRUCTION_DEFAULT
    return render_prompt_template(
        LINE_FORMAT_INSTRUCTION,
        max_size_instruction,
        offset_instruction,
    )
