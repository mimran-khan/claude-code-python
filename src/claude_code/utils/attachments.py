"""
Attachment utilities.

Types and functions for handling message attachments.

Migrated from: utils/attachments.ts (3998 lines) - Core types and helpers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

AttachmentType = Literal[
    "file",
    "image",
    "directory",
    "memory",
    "todo",
    "task",
    "plan",
    "mcp_resource",
    "hook",
    "agent",
    "diagnostic",
    "selection",
    "command",
]


@dataclass
class BaseAttachment:
    """Base class for all attachment types."""

    type: AttachmentType
    content: str = ""


@dataclass
class FileAttachment(BaseAttachment):
    """File content attachment."""

    type: AttachmentType = "file"
    path: str = ""
    line_start: int | None = None
    line_end: int | None = None
    content: str = ""


@dataclass
class ImageAttachment(BaseAttachment):
    """Image attachment."""

    type: AttachmentType = "image"
    path: str = ""
    media_type: str = "image/png"
    base64_data: str = ""


@dataclass
class DirectoryAttachment(BaseAttachment):
    """Directory listing attachment."""

    type: AttachmentType = "directory"
    path: str = ""
    files: list[str] = field(default_factory=list)


@dataclass
class MemoryAttachment(BaseAttachment):
    """Memory/CLAUDE.md content attachment."""

    type: AttachmentType = "memory"
    source: str = ""  # "global", "project", or file path


@dataclass
class TodoAttachment(BaseAttachment):
    """Todo list attachment."""

    type: AttachmentType = "todo"
    todos: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TaskAttachment(BaseAttachment):
    """Task attachment."""

    type: AttachmentType = "task"
    task_id: str = ""
    task_type: str = ""
    status: str = ""


@dataclass
class PlanAttachment(BaseAttachment):
    """Plan attachment."""

    type: AttachmentType = "plan"
    plan_path: str = ""


@dataclass
class McpResourceAttachment(BaseAttachment):
    """MCP resource attachment."""

    type: AttachmentType = "mcp_resource"
    server_name: str = ""
    uri: str = ""
    mime_type: str | None = None


@dataclass
class HookAttachment(BaseAttachment):
    """Hook result attachment."""

    type: AttachmentType = "hook"
    hook_name: str = ""
    event: str = ""
    result: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookPermissionDecisionAttachment(BaseAttachment):
    """Hook permission decision attachment."""

    type: AttachmentType = "hook"
    decision: str = ""  # "allow", "deny"
    reason: str = ""


@dataclass
class AgentAttachment(BaseAttachment):
    """Agent definition attachment."""

    type: AttachmentType = "agent"
    agent_name: str = ""
    agent_type: str = ""


@dataclass
class DiagnosticAttachment(BaseAttachment):
    """Diagnostic information attachment."""

    type: AttachmentType = "diagnostic"
    diagnostic_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class SelectionAttachment(BaseAttachment):
    """IDE selection attachment."""

    type: AttachmentType = "selection"
    file_path: str = ""
    start_line: int = 0
    end_line: int = 0
    selected_text: str = ""


@dataclass
class CommandAttachment(BaseAttachment):
    """Command attachment."""

    type: AttachmentType = "command"
    command_name: str = ""
    args: list[str] = field(default_factory=list)


# Type alias for any attachment

Attachment = (
    FileAttachment
    | ImageAttachment
    | DirectoryAttachment
    | MemoryAttachment
    | TodoAttachment
    | TaskAttachment
    | PlanAttachment
    | McpResourceAttachment
    | HookAttachment
    | HookPermissionDecisionAttachment
    | AgentAttachment
    | DiagnosticAttachment
    | SelectionAttachment
    | CommandAttachment
)

# Memory section header
MEMORY_HEADER = "# Memory\n\n"


def memory_header() -> str:
    """Get the memory section header."""
    return MEMORY_HEADER


def create_file_attachment(
    path: str,
    content: str,
    line_start: int | None = None,
    line_end: int | None = None,
) -> FileAttachment:
    """Create a file attachment."""
    return FileAttachment(
        path=path,
        content=content,
        line_start=line_start,
        line_end=line_end,
    )


def create_image_attachment(
    path: str,
    base64_data: str,
    media_type: str = "image/png",
) -> ImageAttachment:
    """Create an image attachment."""
    return ImageAttachment(
        path=path,
        base64_data=base64_data,
        media_type=media_type,
    )


def create_directory_attachment(
    path: str,
    files: list[str],
) -> DirectoryAttachment:
    """Create a directory attachment."""
    return DirectoryAttachment(
        path=path,
        files=files,
        content="\n".join(files),
    )


def create_memory_attachment(
    source: str,
    content: str,
) -> MemoryAttachment:
    """Create a memory attachment."""
    return MemoryAttachment(
        source=source,
        content=content,
    )


def attachment_to_content_block(attachment: Attachment) -> dict[str, Any]:
    """
    Convert an attachment to an API content block.

    Returns a text block or image block depending on type.
    """
    if isinstance(attachment, ImageAttachment):
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": attachment.media_type,
                "data": attachment.base64_data,
            },
        }

    # All other types become text blocks
    return {
        "type": "text",
        "text": format_attachment_text(attachment),
    }


def format_attachment_text(attachment: Attachment) -> str:
    """Format an attachment as text for the API."""
    if isinstance(attachment, FileAttachment):
        header = f"File: {attachment.path}"
        if attachment.line_start is not None:
            header += f" (lines {attachment.line_start}-{attachment.line_end or '?'})"
        return f"{header}\n\n{attachment.content}"

    if isinstance(attachment, DirectoryAttachment):
        return f"Directory: {attachment.path}\n\n{attachment.content}"

    if isinstance(attachment, MemoryAttachment):
        return f"Memory ({attachment.source}):\n\n{attachment.content}"

    if isinstance(attachment, TodoAttachment):
        lines = ["Todo List:"]
        for todo in attachment.todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")
            lines.append(f"- [{status}] {content}")
        return "\n".join(lines)

    if isinstance(attachment, TaskAttachment):
        return f"Task {attachment.task_id} ({attachment.task_type}): {attachment.status}"

    if isinstance(attachment, PlanAttachment):
        return f"Plan: {attachment.plan_path}\n\n{attachment.content}"

    if isinstance(attachment, McpResourceAttachment):
        return f"MCP Resource ({attachment.server_name}:{attachment.uri}):\n\n{attachment.content}"

    if isinstance(attachment, SelectionAttachment):
        return f"Selection in {attachment.file_path} (lines {attachment.start_line}-{attachment.end_line}):\n\n{attachment.selected_text}"

    # Default: return content
    return attachment.content
