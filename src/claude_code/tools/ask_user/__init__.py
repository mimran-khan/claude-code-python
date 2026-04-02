"""
Ask User Question Tool.

Ask the user multiple choice questions.
"""

from .prompt import (
    ASK_USER_QUESTION_TOOL_NAME,
    ASK_USER_QUESTION_TOOL_PROMPT,
    DESCRIPTION,
)


def __getattr__(name: str):
    """Lazy import for AskUserQuestionTool."""
    if name == "AskUserQuestionTool":
        from .tool import AskUserQuestionTool

        return AskUserQuestionTool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ASK_USER_QUESTION_TOOL_NAME",
    "DESCRIPTION",
    "ASK_USER_QUESTION_TOOL_PROMPT",
    "AskUserQuestionTool",
]
