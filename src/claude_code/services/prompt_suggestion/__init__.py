"""
Prompt suggestion service.

Provides intelligent prompt suggestions and speculation for user input.

Migrated from: services/PromptSuggestion/*.ts
"""

from .speculation import (
    get_speculation_result,
    is_speculation_enabled,
    start_speculation,
    stop_speculation,
)
from .suggestion import (
    PromptVariant,
    abort_prompt_suggestion,
    generate_prompt_suggestions,
    get_prompt_variant,
    should_enable_prompt_suggestion,
)

__all__ = [
    # Suggestion
    "PromptVariant",
    "get_prompt_variant",
    "should_enable_prompt_suggestion",
    "abort_prompt_suggestion",
    "generate_prompt_suggestions",
    # Speculation
    "is_speculation_enabled",
    "start_speculation",
    "stop_speculation",
    "get_speculation_result",
]
