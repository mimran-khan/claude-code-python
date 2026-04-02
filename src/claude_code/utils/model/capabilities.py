"""
Model capabilities.

Track model feature support.

Migrated from: utils/model/modelCapabilities.ts
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelCapabilities:
    """Capabilities of a model."""

    tool_use: bool = True
    vision: bool = True
    thinking: bool = False
    computer_use: bool = False
    pdf: bool = True
    streaming: bool = True
    max_context_window: int = 200_000
    max_output_tokens: int = 8192


# Default capabilities by model family
DEFAULT_CAPABILITIES = {
    "opus": ModelCapabilities(
        tool_use=True,
        vision=True,
        thinking=True,
        computer_use=True,
        pdf=True,
        streaming=True,
        max_context_window=200_000,
        max_output_tokens=8192,
    ),
    "sonnet": ModelCapabilities(
        tool_use=True,
        vision=True,
        thinking=True,
        computer_use=True,
        pdf=True,
        streaming=True,
        max_context_window=200_000,
        max_output_tokens=8192,
    ),
    "haiku": ModelCapabilities(
        tool_use=True,
        vision=True,
        thinking=False,
        computer_use=False,
        pdf=True,
        streaming=True,
        max_context_window=200_000,
        max_output_tokens=8192,
    ),
}


def get_model_capabilities(model: str) -> ModelCapabilities:
    """
    Get capabilities for a model.

    Args:
        model: The model name

    Returns:
        ModelCapabilities instance
    """
    model_lower = model.lower()

    if "opus" in model_lower:
        return DEFAULT_CAPABILITIES["opus"]

    if "sonnet" in model_lower:
        return DEFAULT_CAPABILITIES["sonnet"]

    if "haiku" in model_lower:
        return DEFAULT_CAPABILITIES["haiku"]

    # Default to sonnet capabilities
    return DEFAULT_CAPABILITIES["sonnet"]


def supports_tool_use(model: str) -> bool:
    """Check if model supports tool use."""
    return get_model_capabilities(model).tool_use


def supports_vision(model: str) -> bool:
    """Check if model supports vision."""
    return get_model_capabilities(model).vision


def supports_thinking(model: str) -> bool:
    """Check if model supports extended thinking."""
    return get_model_capabilities(model).thinking


def supports_computer_use(model: str) -> bool:
    """Check if model supports computer use."""
    return get_model_capabilities(model).computer_use


def get_max_context_window(model: str) -> int:
    """Get the maximum context window size."""
    return get_model_capabilities(model).max_context_window


def get_max_output_tokens(model: str) -> int:
    """Get the maximum output tokens."""
    return get_model_capabilities(model).max_output_tokens
