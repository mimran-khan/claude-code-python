"""
Prompt suggestion implementation.

Migrated from: services/PromptSuggestion/promptSuggestion.ts
"""

import asyncio
import os
from typing import Any, Literal

from ..analytics import log_event

PromptVariant = Literal["user_intent", "stated_intent"]

# Current abort controller
_current_abort_controller: asyncio.Event | None = None


def get_prompt_variant() -> PromptVariant:
    """Get the current prompt variant."""
    return "user_intent"


def _is_env_truthy(value: str | None) -> bool:
    """Check if environment variable is truthy."""
    if not value:
        return False
    return value.lower() in ("1", "true", "yes")


def _is_env_falsy(value: str | None) -> bool:
    """Check if environment variable is explicitly falsy."""
    if not value:
        return False
    return value.lower() in ("0", "false", "no")


def should_enable_prompt_suggestion() -> bool:
    """Check if prompt suggestion should be enabled.

    Checks environment variables, feature flags, and settings.
    """
    env_override = os.environ.get("CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION")

    if _is_env_falsy(env_override):
        log_event(
            "tengu_prompt_suggestion_init",
            {
                "enabled": False,
                "source": "env",
            },
        )
        return False

    if _is_env_truthy(env_override):
        log_event(
            "tengu_prompt_suggestion_init",
            {
                "enabled": True,
                "source": "env",
            },
        )
        return True

    # Check feature flag (stubbed)
    # In full implementation, would check GrowthBook
    feature_enabled = os.environ.get("PROMPT_SUGGESTION_FEATURE", "").lower() == "true"
    if not feature_enabled:
        log_event(
            "tengu_prompt_suggestion_init",
            {
                "enabled": False,
                "source": "growthbook",
            },
        )
        return False

    # Check if non-interactive session
    if os.environ.get("CLAUDE_NON_INTERACTIVE", "").lower() in ("1", "true"):
        log_event(
            "tengu_prompt_suggestion_init",
            {
                "enabled": False,
                "source": "non_interactive",
            },
        )
        return False

    # Default to enabled
    log_event(
        "tengu_prompt_suggestion_init",
        {
            "enabled": True,
            "source": "setting",
        },
    )
    return True


def abort_prompt_suggestion() -> None:
    """Abort any in-progress prompt suggestion generation."""
    global _current_abort_controller
    if _current_abort_controller:
        _current_abort_controller.set()
        _current_abort_controller = None


async def generate_prompt_suggestions(
    messages: list[Any],
    context: Any,
    limit: int = 3,
) -> list[str]:
    """Generate prompt suggestions based on conversation context.

    Args:
        messages: Current conversation messages
        context: Conversation context
        limit: Maximum number of suggestions to generate

    Returns:
        List of suggested prompts
    """
    global _current_abort_controller

    # Create new abort controller
    _current_abort_controller = asyncio.Event()

    try:
        # In full implementation, would call the model to generate suggestions
        # For now, return empty list
        return []
    finally:
        _current_abort_controller = None


def get_suggestion_prompt(
    messages: list[Any],
    variant: PromptVariant = "user_intent",
) -> str:
    """Build the prompt for generating suggestions.

    Args:
        messages: Conversation history
        variant: Prompt variant to use

    Returns:
        System prompt for suggestion generation
    """
    if variant == "stated_intent":
        return """Based on the conversation, suggest what the user might want to do next.
Focus on their explicitly stated goals and intentions."""

    return """Based on the conversation, suggest what the user might want to do next.
Consider their implicit intent based on the work they're doing."""
