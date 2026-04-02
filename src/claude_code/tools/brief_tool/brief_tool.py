"""Brief Tool implementation for concise message display."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ...core.tool import Tool, ToolCallProgress, ToolResult, ToolUseContext, ValidationResult

BRIEF_TOOL_NAME = "Brief"
LEGACY_BRIEF_TOOL_NAME = "brief"

DESCRIPTION = "Send a brief message to the user with optional attachments"

BRIEF_PROACTIVE_SECTION = """When you have a user-facing message (status update, question, final report), call the Brief tool. This formats your message properly and ensures the user sees it.

- Use status='proactive' when surfacing something the user hasn't asked for (task completion, blocker, unsolicited update)
- Use status='normal' when replying to something the user just said
- Attach relevant files (screenshots, diffs, logs) when they help understanding"""


@dataclass
class BriefAttachment:
    """Attachment metadata."""

    path: str
    size: int
    is_image: bool
    file_uuid: str | None = None


@dataclass
class BriefOutput:
    """Output from brief tool."""

    message: str
    attachments: list[BriefAttachment] = field(default_factory=list)
    sent_at: str | None = None


INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "The message for the user. Supports markdown formatting.",
        },
        "attachments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Optional file paths (absolute or relative to cwd) to attach.",
        },
        "status": {
            "type": "string",
            "enum": ["normal", "proactive"],
            "description": "Use 'proactive' when surfacing something unsolicited, 'normal' when replying.",
        },
    },
    "required": ["message", "status"],
}


class BriefTool(Tool):
    """Tool for sending brief messages with attachments."""

    name = BRIEF_TOOL_NAME
    description = DESCRIPTION
    input_schema = INPUT_SCHEMA
    aliases = [LEGACY_BRIEF_TOOL_NAME]
    is_read_only = True
    is_concurrency_safe = True

    def validate_input(self, input_data: dict[str, Any]) -> ValidationResult:
        """Validate the input."""
        message = input_data.get("message", "")
        if not message:
            return ValidationResult(
                result=False,
                message="Message is required",
                error_code=1,
            )

        status = input_data.get("status", "")
        if status not in ("normal", "proactive"):
            return ValidationResult(
                result=False,
                message="Status must be 'normal' or 'proactive'",
                error_code=2,
            )

        return ValidationResult(result=True)

    async def call(
        self,
        input_data: dict[str, Any],
        context: ToolUseContext,
        progress_callback: ToolCallProgress | None = None,
    ) -> ToolResult[BriefOutput]:
        """Execute the brief message."""
        message = input_data.get("message", "")
        attachment_paths = input_data.get("attachments", [])
        input_data.get("status", "normal")

        # Resolve attachments
        attachments: list[BriefAttachment] = []
        for path in attachment_paths:
            # In full implementation, would validate and resolve paths
            attachments.append(
                BriefAttachment(
                    path=path,
                    size=0,
                    is_image=path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")),
                )
            )

        return ToolResult(
            data=BriefOutput(
                message=message,
                attachments=attachments,
                sent_at=datetime.utcnow().isoformat() + "Z",
            )
        )

    def get_tool_use_summary(self, input_data: dict[str, Any]) -> str:
        """Get a summary of the tool use."""
        message = input_data.get("message", "")
        status = input_data.get("status", "normal")
        attachments = input_data.get("attachments", [])

        # Truncate message
        if len(message) > 30:
            message = message[:27] + "..."

        if attachments:
            return f"Brief({status}: {message} +{len(attachments)} files)"
        return f"Brief({status}: {message})"


def is_brief_enabled() -> bool:
    """Check if brief tool is enabled."""
    # In full implementation, would check feature flags and user opt-in
    return True


def is_brief_entitled() -> bool:
    """Check if user is entitled to use brief tool."""
    # In full implementation, would check feature flags
    return True
