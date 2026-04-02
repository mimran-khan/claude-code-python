"""
User input processing utilities.

Migrated from: utils/processUserInput/*.ts
"""

from .process_input import (
    ProcessUserInputBaseResult,
    ProcessUserInputContext,
    process_user_input,
)
from .process_text import (
    IdeSelectionDict,
    MentionDict,
    PastedContentBlock,
    ProcessTextPromptResult,
    TextPromptContext,
    extract_mentions,
    parse_input_blocks,
    process_text_prompt,
)

__all__ = [
    "IdeSelectionDict",
    "MentionDict",
    "PastedContentBlock",
    "ProcessTextPromptResult",
    "ProcessUserInputContext",
    "ProcessUserInputBaseResult",
    "TextPromptContext",
    "process_user_input",
    "process_text_prompt",
    "extract_mentions",
    "parse_input_blocks",
]
