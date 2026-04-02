"""
Compact prompts.

Prompts for conversation compaction.

Migrated from: services/compact/prompt.ts
"""

from __future__ import annotations

COMPACT_SYSTEM_PROMPT = """You are a helpful assistant that summarizes conversations.
Your task is to create a concise but comprehensive summary of the conversation that:

1. Preserves all important decisions, requirements, and context
2. Maintains the key technical details and code references
3. Keeps track of files that were read or modified
4. Notes any active tasks or pending work
5. Preserves the user's goals and intentions

The summary should be written in a way that allows the conversation to continue
seamlessly, with all relevant context available."""


COMPACT_USER_MESSAGE_TEMPLATE = """Please summarize the following conversation.
Focus on preserving all important context needed to continue the work.

{custom_instructions}

Conversation to summarize:

{conversation}"""


def get_compact_prompt(custom_instructions: str | None = None) -> str:
    """
    Get the system prompt for compaction.

    Args:
        custom_instructions: Optional custom instructions

    Returns:
        The compaction system prompt
    """
    if custom_instructions:
        return f"{COMPACT_SYSTEM_PROMPT}\n\nAdditional instructions: {custom_instructions}"
    return COMPACT_SYSTEM_PROMPT


def get_compact_user_summary_message(
    conversation_text: str,
    custom_instructions: str | None = None,
) -> str:
    """
    Get the user message for compaction.

    Args:
        conversation_text: The conversation to summarize
        custom_instructions: Optional custom instructions

    Returns:
        The compaction user message
    """
    instructions = ""
    if custom_instructions:
        instructions = f"\n\nCustom instructions: {custom_instructions}"

    return COMPACT_USER_MESSAGE_TEMPLATE.format(
        custom_instructions=instructions,
        conversation=conversation_text,
    )


def get_partial_compact_prompt(
    direction: str,
    custom_instructions: str | None = None,
) -> str:
    """
    Get prompt for partial compaction.

    Args:
        direction: Direction of partial compact ("oldest", "newest")
        custom_instructions: Optional custom instructions

    Returns:
        The partial compaction prompt
    """
    base_prompt = COMPACT_SYSTEM_PROMPT

    if direction == "oldest":
        base_prompt += (
            "\n\nFocus on summarizing the older parts of the conversation while keeping recent messages intact."
        )
    else:
        base_prompt += "\n\nFocus on summarizing recent work while preserving the original context and goals."

    if custom_instructions:
        base_prompt += f"\n\nAdditional instructions: {custom_instructions}"

    return base_prompt
