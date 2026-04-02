"""
Brief Tool Implementation.

Send messages to the user with attachments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import BRIEF_TOOL_NAME, DESCRIPTION


class BriefInput(BaseModel):
    """Input parameters for brief tool."""

    message: str = Field(
        ...,
        description="The message for the user. Supports markdown formatting.",
    )
    attachments: list[str] | None = Field(
        default=None,
        description="Optional file paths to attach.",
    )
    status: Literal["normal", "proactive"] = Field(
        default="normal",
        description="Message status type.",
    )


@dataclass
class AttachmentInfo:
    """Information about an attached file."""

    path: str
    size: int = 0
    is_image: bool = False
    file_uuid: str | None = None


@dataclass
class BriefSuccess:
    """Successful brief result."""

    type: Literal["success"] = "success"
    message: str = ""
    attachments: list[AttachmentInfo] = field(default_factory=list)
    sent_at: str | None = None


@dataclass
class BriefError:
    """Failed brief result."""

    type: Literal["error"] = "error"
    error: str = ""


BriefOutput = BriefSuccess | BriefError


class BriefTool(Tool[BriefInput, BriefOutput]):
    """
    Tool for sending messages to the user.
    """

    @property
    def name(self) -> str:
        return BRIEF_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message for the user.",
                },
                "attachments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional file paths to attach.",
                },
                "status": {
                    "type": "string",
                    "enum": ["normal", "proactive"],
                    "description": "Message status type.",
                    "default": "normal",
                },
            },
            "required": ["message", "status"],
        }

    def is_read_only(self, input_data: BriefInput) -> bool:
        return True  # Messaging doesn't modify files

    async def call(
        self,
        input_data: BriefInput,
        context: Any,
    ) -> ToolResult[BriefOutput]:
        """Execute the brief operation."""
        # Resolve attachments if provided
        attachments: list[AttachmentInfo] = []
        if input_data.attachments:
            for path in input_data.attachments:
                # In a full implementation, this would:
                # 1. Validate the path exists
                # 2. Get file size and type
                # 3. Generate UUID for uploads
                attachments.append(AttachmentInfo(path=path))

        return ToolResult(
            success=True,
            output=BriefSuccess(
                message=input_data.message,
                attachments=attachments,
                sent_at=datetime.utcnow().isoformat() + "Z",
            ),
        )

    def user_facing_name(self, input_data: BriefInput | None = None) -> str:
        return "Brief"

    def get_tool_use_summary(self, input_data: BriefInput | None) -> str | None:
        if input_data:
            # Return first 50 chars of message
            msg = input_data.message
            if len(msg) > 50:
                return msg[:47] + "..."
            return msg
        return None
