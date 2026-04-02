"""Output variants aligned with tools/FileReadTool/FileReadTool.ts discriminated union."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TextFilePayload:
    file_path: str
    content: str
    num_lines: int
    start_line: int
    total_lines: int


@dataclass
class ImageDimensions:
    original_width: int | None = None
    original_height: int | None = None
    display_width: int | None = None
    display_height: int | None = None


@dataclass
class ImageFilePayload:
    base64: str
    media_type: str
    original_size: int
    dimensions: ImageDimensions | None = None


@dataclass
class NotebookFilePayload:
    file_path: str
    cells: list[Any] = field(default_factory=list)


@dataclass
class PdfFilePayload:
    file_path: str
    base64: str
    original_size: int


@dataclass
class FileReadTextResult:
    type: Literal["text"] = "text"
    file: TextFilePayload = field(default_factory=lambda: TextFilePayload("", "", 0, 1, 0))


@dataclass
class FileReadImageResult:
    type: Literal["image"] = "image"
    file: ImageFilePayload = field(default_factory=lambda: ImageFilePayload("", "image/png", 0))


@dataclass
class FileReadNotebookResult:
    type: Literal["notebook"] = "notebook"
    file: NotebookFilePayload = field(default_factory=lambda: NotebookFilePayload(""))


@dataclass
class FileReadPdfResult:
    type: Literal["pdf"] = "pdf"
    file: PdfFilePayload = field(default_factory=lambda: PdfFilePayload("", "", 0))


@dataclass
class FileUnchangedResult:
    type: Literal["file_unchanged"] = "file_unchanged"
    file_path: str = ""
