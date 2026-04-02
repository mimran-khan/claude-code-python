"""
Send Message Tool Implementation.

Sends messages between agents/teammates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import SEND_MESSAGE_TOOL_NAME, get_prompt


class SendMessageInput(BaseModel):
    """Input parameters for send message tool."""

    to: str = Field(
        ...,
        description="Recipient: teammate name, or '*' for broadcast to all teammates.",
    )
    message: str = Field(
        ...,
        description="The message content to send.",
    )
    summary: str | None = Field(
        default=None,
        description="A 5-10 word summary shown as a preview in the UI.",
    )


@dataclass
class MessageRouting:
    """Routing information for a message."""

    sender: str = ""
    sender_color: str | None = None
    target: str = ""
    target_color: str | None = None
    summary: str | None = None
    content: str | None = None


@dataclass
class SendMessageSuccess:
    """Successful message send result."""

    type: Literal["success"] = "success"
    recipient: str = ""
    delivered: bool = True
    message: str = ""


@dataclass
class SendMessageError:
    """Failed message send result."""

    type: Literal["error"] = "error"
    recipient: str = ""
    error: str = ""


SendMessageOutput = SendMessageSuccess | SendMessageError


class SendMessageTool(Tool[SendMessageInput, SendMessageOutput]):
    """
    Tool for sending messages between agents.

    Allows agents to communicate with each other by name
    or broadcast to all teammates.
    """

    @property
    def name(self) -> str:
        return SEND_MESSAGE_TOOL_NAME

    @property
    def description(self) -> str:
        return get_prompt()

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient: teammate name, or '*' for broadcast.",
                },
                "message": {
                    "type": "string",
                    "description": "The message content to send.",
                },
                "summary": {
                    "type": "string",
                    "description": "A 5-10 word summary shown as preview.",
                },
            },
            "required": ["to", "message"],
        }

    def is_read_only(self, input_data: SendMessageInput) -> bool:
        return True  # Messaging doesn't modify files

    async def call(
        self,
        input_data: SendMessageInput,
        context: Any,
    ) -> ToolResult[SendMessageOutput]:
        """Execute the send message operation."""
        recipient = input_data.to

        # In a full implementation, this would:
        # 1. Resolve the recipient (by name or broadcast)
        # 2. Queue the message for delivery
        # 3. Return delivery status

        return ToolResult(
            success=False,
            output=SendMessageError(
                recipient=recipient,
                error=("Message sending requires agent runtime integration. This is a placeholder implementation."),
            ),
        )

    def user_facing_name(self, input_data: SendMessageInput | None = None) -> str:
        """Get the user-facing name for this tool."""
        return "Message"

    def get_tool_use_summary(self, input_data: SendMessageInput | None) -> str | None:
        """Get a short summary of this tool use."""
        if input_data:
            if input_data.summary:
                return input_data.summary
            return f"to {input_data.to}"
        return None

    def get_activity_description(self, input_data: SendMessageInput | None) -> str | None:
        """Get a human-readable activity description."""
        if input_data:
            return f"Messaging {input_data.to}"
        return "Sending message"
