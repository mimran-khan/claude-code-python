"""
Speculative execution for prompt suggestions.

Migrated from: services/PromptSuggestion/speculation.ts
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class SpeculationResult:
    """Result of speculative execution."""

    messages: list[Any]
    completed: bool
    aborted: bool
    time_saved_ms: float


# Global speculation state
_speculation_active = False
_speculation_abort = asyncio.Event()
_speculation_result: SpeculationResult | None = None


def is_speculation_enabled() -> bool:
    """Check if speculative execution is enabled.

    Speculation pre-executes likely next steps to reduce latency.
    """
    # Check environment override
    env_value = os.environ.get("CLAUDE_CODE_ENABLE_SPECULATION", "")
    if env_value.lower() in ("0", "false", "no"):
        return False
    if env_value.lower() in ("1", "true", "yes"):
        return True

    # Check if prompt suggestion is enabled (speculation requires it)
    from .suggestion import should_enable_prompt_suggestion

    return should_enable_prompt_suggestion()


async def start_speculation(
    predicted_prompt: str,
    messages: list[Any],
    context: Any,
) -> SpeculationResult | None:
    """Start speculative execution of a predicted prompt.

    Args:
        predicted_prompt: The prompt we predict the user will submit
        messages: Current conversation messages
        context: Execution context

    Returns:
        SpeculationResult if completed, None if aborted or failed
    """
    global _speculation_active, _speculation_result

    if _speculation_active:
        # Already speculating, don't start another
        return None

    _speculation_active = True
    _speculation_abort.clear()
    _speculation_result = None

    try:
        # In full implementation, would:
        # 1. Fork a subagent to run the predicted prompt
        # 2. Monitor for abort signal
        # 3. Collect results

        # For now, stub implementation
        await asyncio.sleep(0.1)

        if _speculation_abort.is_set():
            return None

        result = SpeculationResult(
            messages=[],
            completed=True,
            aborted=False,
            time_saved_ms=0.0,
        )
        _speculation_result = result
        return result

    finally:
        _speculation_active = False


def stop_speculation() -> None:
    """Stop any in-progress speculation."""
    global _speculation_active
    _speculation_abort.set()
    _speculation_active = False


def get_speculation_result() -> SpeculationResult | None:
    """Get the result of the last speculation, if available."""
    return _speculation_result


def is_speculation_active() -> bool:
    """Check if speculation is currently running."""
    return _speculation_active


def apply_speculation_result(
    result: SpeculationResult,
    actual_prompt: str,
    predicted_prompt: str,
) -> bool:
    """Apply speculation result if the actual prompt matches prediction.

    Args:
        result: The speculation result
        actual_prompt: The actual prompt submitted
        predicted_prompt: The prompt that was predicted

    Returns:
        True if result was applied, False otherwise
    """
    # Simple check: exact match
    if actual_prompt.strip() != predicted_prompt.strip():
        return False

    # In full implementation, would merge speculation messages
    # into the current conversation
    return True
