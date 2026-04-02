"""
Ask User Question Tool Implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from .prompt import ASK_USER_QUESTION_TOOL_NAME, DESCRIPTION


class QuestionOption(BaseModel):
    """An option for a question."""

    id: str = Field(..., description="Unique identifier for this option.")
    label: str = Field(..., description="Display text for this option.")
    preview: str | None = Field(default=None, description="Optional preview content.")


class Question(BaseModel):
    """A single question."""

    id: str = Field(..., description="Unique identifier for this question.")
    prompt: str = Field(..., description="The question text to display.")
    options: list[QuestionOption] = Field(
        ...,
        description="Array of answer options.",
        min_length=2,
    )
    allow_multiple: bool = Field(
        default=False,
        alias="allowMultiple",
        description="If true, user can select multiple options.",
    )


class AskUserInput(BaseModel):
    """Input parameters for ask user tool."""

    title: str | None = Field(
        default=None,
        description="Optional title for the questions form.",
    )
    questions: list[Question] = Field(
        ...,
        description="Array of questions to present.",
        min_length=1,
    )


@dataclass
class SelectedOption:
    """A selected option from a question."""

    question_id: str
    option_ids: list[str] = field(default_factory=list)
    other_text: str | None = None


@dataclass
class AskUserSuccess:
    """Successful ask user result."""

    type: Literal["success"] = "success"
    selections: list[SelectedOption] = field(default_factory=list)


@dataclass
class AskUserPending:
    """Pending ask user result (waiting for response)."""

    type: Literal["pending"] = "pending"
    message: str = "Waiting for user response"


AskUserOutput = AskUserSuccess | AskUserPending


class AskUserQuestionTool(Tool[AskUserInput, AskUserOutput]):
    """
    Tool for asking the user questions.
    """

    @property
    def name(self) -> str:
        return ASK_USER_QUESTION_TOOL_NAME

    @property
    def description(self) -> str:
        return DESCRIPTION

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Optional title for the form.",
                },
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "prompt": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "label": {"type": "string"},
                                    },
                                    "required": ["id", "label"],
                                },
                                "minItems": 2,
                            },
                            "allowMultiple": {
                                "type": "boolean",
                                "default": False,
                            },
                        },
                        "required": ["id", "prompt", "options"],
                    },
                    "minItems": 1,
                },
            },
            "required": ["questions"],
        }

    def is_read_only(self, input_data: AskUserInput) -> bool:
        return True

    async def call(
        self,
        input_data: AskUserInput,
        context: Any,
    ) -> ToolResult[AskUserOutput]:
        """Execute the ask user operation."""
        # In a full implementation, this would present the question
        # to the user and wait for their response
        return ToolResult(
            success=False,
            output=AskUserPending(
                message="Waiting for user response",
            ),
        )

    def user_facing_name(self, input_data: AskUserInput | None = None) -> str:
        return "Question"
