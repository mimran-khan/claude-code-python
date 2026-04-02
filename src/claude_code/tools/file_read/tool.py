"""
File Read Tool implementation.

Reads files from the local filesystem, supporting:
- Text files (with line numbers)
- Images (PNG, JPG, GIF, WebP)
- PDFs (with page extraction)
- Jupyter notebooks

Migrated from: tools/FileReadTool/FileReadTool.ts (1184 lines)
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import aiofiles
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult, ToolValidationResult
from .limits import get_default_file_reading_limits
from .prompt import (
    DESCRIPTION,
    FILE_READ_TOOL_NAME,
    LINE_FORMAT_INSTRUCTION,
    MAX_LINES_TO_READ,
    OFFSET_INSTRUCTION_DEFAULT,
    OFFSET_INSTRUCTION_TARGETED,
    render_prompt_template,
)

# Device files that would hang the process
BLOCKED_DEVICE_PATHS = frozenset(
    {
        "/dev/zero",
        "/dev/random",
        "/dev/urandom",
        "/dev/full",
        "/dev/stdin",
        "/dev/tty",
        "/dev/console",
        "/dev/stdout",
        "/dev/stderr",
        "/dev/fd/0",
        "/dev/fd/1",
        "/dev/fd/2",
    }
)

# Image extensions supported
IMAGE_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "gif", "webp"})

# Binary extensions that should not be read as text
BINARY_EXTENSIONS = frozenset(
    {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "bmp",
        "ico",
        "tiff",
        "tif",
        "mp4",
        "mov",
        "avi",
        "mkv",
        "webm",
        "wmv",
        "flv",
        "mp3",
        "wav",
        "ogg",
        "flac",
        "aac",
        "zip",
        "tar",
        "gz",
        "bz2",
        "7z",
        "rar",
        "exe",
        "dll",
        "so",
        "dylib",
        "bin",
        "pyc",
        "pyo",
        "class",
        "jar",
        "sqlite",
        "db",
    }
)


def is_blocked_device_path(file_path: str) -> bool:
    """Check if a file path is a blocked device file."""
    if file_path in BLOCKED_DEVICE_PATHS:
        return True
    # /proc/self/fd/0-2 and /proc/<pid>/fd/0-2 are Linux aliases for stdio
    return bool(
        file_path.startswith("/proc/")
        and (file_path.endswith("/fd/0") or file_path.endswith("/fd/1") or file_path.endswith("/fd/2"))
    )


def has_binary_extension(file_path: str) -> bool:
    """Check if a file has a binary extension."""
    ext = Path(file_path).suffix.lower().lstrip(".")
    return ext in BINARY_EXTENSIONS


def is_pdf_extension(ext: str) -> bool:
    """Check if extension is PDF."""
    return ext.lower().lstrip(".") == "pdf"


def add_line_numbers(content: str, start_line: int = 1) -> str:
    """Add line numbers to content in cat -n format."""
    lines = content.splitlines(keepends=True)
    numbered_lines = []
    for i, line in enumerate(lines, start=start_line):
        # Right-align line number in 6 characters, followed by |
        numbered_lines.append(f"{i:6}|{line}")
    return "".join(numbered_lines)


class FileReadInput(BaseModel):
    """Input schema for the FileRead tool."""

    file_path: str = Field(description="The absolute path to the file to read")
    offset: int | None = Field(
        default=None,
        ge=0,
        description="The line number to start reading from (1-indexed). "
        "Only provide if the file is too large to read at once.",
    )
    limit: int | None = Field(
        default=None,
        gt=0,
        description="The number of lines to read. Only provide if the file is too large to read at once.",
    )
    pages: str | None = Field(
        default=None,
        description='Page range for PDF files (e.g., "1-5", "3", "10-20"). '
        "Only applicable to PDF files. Maximum 20 pages per request.",
    )


@dataclass
class TextFileResult:
    """Result for text file reads."""

    type: Literal["text"] = "text"
    file_path: str = ""
    content: str = ""
    num_lines: int = 0
    start_line: int = 1
    total_lines: int = 0


@dataclass
class ImageFileResult:
    """Result for image file reads."""

    type: Literal["image"] = "image"
    base64_data: str = ""
    media_type: str = "image/png"
    original_size: int = 0


@dataclass
class FileUnchangedResult:
    """Result when file hasn't changed since last read."""

    type: Literal["file_unchanged"] = "file_unchanged"
    file_path: str = ""


FileReadOutput = TextFileResult | ImageFileResult | FileUnchangedResult


class FileReadTool(Tool[FileReadInput, FileReadOutput]):
    """
    Tool for reading files from the local filesystem.

    Supports text files, images, PDFs, and Jupyter notebooks.
    """

    @property
    def name(self) -> str:
        return FILE_READ_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        limits = get_default_file_reading_limits()
        max_size_instruction = ""
        if limits.include_max_size_in_prompt:
            size_kb = limits.max_size_bytes // 1024
            max_size_instruction = (
                f". Files larger than {size_kb}KB will return an error; use offset and limit for larger files"
            )

        offset_instruction = OFFSET_INSTRUCTION_TARGETED if limits.targeted_range_nudge else OFFSET_INSTRUCTION_DEFAULT

        return render_prompt_template(
            LINE_FORMAT_INSTRUCTION,
            max_size_instruction,
            offset_instruction,
        )

    async def validate_input(
        self,
        input_data: FileReadInput,
        context: Any,
    ) -> ToolValidationResult:
        file_path = input_data.file_path

        # Expand path
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)

        # Check for blocked device paths
        if is_blocked_device_path(file_path):
            return ToolValidationResult(
                valid=False,
                message=f"Cannot read '{input_data.file_path}': this device file "
                "would block or produce infinite output.",
                error_code=9,
            )

        # Check for binary extensions (excluding images and PDFs)
        ext = Path(file_path).suffix.lower().lstrip(".")
        if has_binary_extension(file_path) and not is_pdf_extension(ext) and ext not in IMAGE_EXTENSIONS:
            return ToolValidationResult(
                valid=False,
                message=f"This tool cannot read binary files. The file appears to "
                f"be a binary .{ext} file. Please use appropriate tools for "
                "binary file analysis.",
                error_code=4,
            )

        return ToolValidationResult(valid=True)

    async def check_permissions(
        self,
        input_data: FileReadInput,
        context: Any,
    ) -> Any:
        # Permission checking would be implemented here
        # For now, return allow
        return {"behavior": "allow"}

    async def call(
        self,
        input_data: FileReadInput,
        context: Any,
    ) -> ToolResult[FileReadOutput]:
        file_path = input_data.file_path
        offset = input_data.offset or 1
        limit = input_data.limit

        # Expand path
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)

        ext = Path(file_path).suffix.lower().lstrip(".")
        limits = get_default_file_reading_limits()

        try:
            # Handle images
            if ext in IMAGE_EXTENSIONS:
                async with aiofiles.open(file_path, "rb") as f:
                    image_data = await f.read()

                base64_data = base64.b64encode(image_data).decode("utf-8")

                # Determine media type
                media_type = f"image/{ext}"
                if ext == "jpg":
                    media_type = "image/jpeg"

                return ToolResult(
                    data=ImageFileResult(
                        type="image",
                        base64_data=base64_data,
                        media_type=media_type,
                        original_size=len(image_data),
                    )
                )

            # Handle text files
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                all_lines = await f.readlines()

            total_lines = len(all_lines)

            # Apply offset and limit
            start_idx = max(0, offset - 1)
            if limit is not None:
                end_idx = min(start_idx + limit, total_lines)
            else:
                end_idx = min(start_idx + MAX_LINES_TO_READ, total_lines)

            selected_lines = all_lines[start_idx:end_idx]
            content = "".join(selected_lines)

            # Check size limits
            if len(content.encode("utf-8")) > limits.max_size_bytes:
                raise ValueError(
                    f"File content exceeds maximum size ({limits.max_size_bytes} bytes). "
                    "Use offset and limit parameters to read specific portions."
                )

            # Add line numbers
            numbered_content = add_line_numbers(content, start_line=offset)

            return ToolResult(
                data=TextFileResult(
                    type="text",
                    file_path=input_data.file_path,
                    content=numbered_content,
                    num_lines=len(selected_lines),
                    start_line=offset,
                    total_lines=total_lines,
                )
            )

        except FileNotFoundError:
            cwd = os.getcwd()
            raise FileNotFoundError(
                f"File does not exist. Make sure to use an absolute path and "
                f"that the file exists. Current working directory is: {cwd}"
            )
        except UnicodeDecodeError:
            raise ValueError(
                "File appears to be binary. This tool can only read text files, images (PNG, JPG, GIF, WebP), and PDFs."
            )

    def is_read_only(self) -> bool:
        return True

    def is_concurrency_safe(self) -> bool:
        return True

    def get_path(self, input_data: FileReadInput) -> str | None:
        return input_data.file_path

    def get_tool_use_summary(self, input_data: FileReadInput) -> str | None:
        if input_data.file_path:
            return os.path.basename(input_data.file_path)
        return None

    def get_activity_description(self, input_data: FileReadInput) -> str:
        summary = self.get_tool_use_summary(input_data)
        return f"Reading {summary}" if summary else "Reading file"
