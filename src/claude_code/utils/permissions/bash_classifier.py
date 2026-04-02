"""
Bash command classifier stub.

Stub for external builds - classifier permissions feature is ANT-ONLY.

Migrated from: utils/permissions/bashClassifier.ts (62 lines)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PROMPT_PREFIX = "prompt:"


@dataclass
class ClassifierResult:
    """Result of a command classification."""

    matches: bool
    confidence: Literal["high", "medium", "low"]
    reason: str
    matched_description: str | None = None


ClassifierBehavior = Literal["deny", "ask", "allow"]


def extract_prompt_description(rule_content: str | None) -> str | None:
    """Extract prompt description from rule content."""
    return None


def create_prompt_rule_content(description: str) -> str:
    """Create prompt rule content from a description."""
    return f"{PROMPT_PREFIX} {description.strip()}"


def is_classifier_permissions_enabled() -> bool:
    """Check if classifier permissions are enabled."""
    return False


def get_bash_prompt_deny_descriptions(context: dict) -> list[str]:
    """Get bash prompt deny descriptions."""
    return []


def get_bash_prompt_ask_descriptions(context: dict) -> list[str]:
    """Get bash prompt ask descriptions."""
    return []


def get_bash_prompt_allow_descriptions(context: dict) -> list[str]:
    """Get bash prompt allow descriptions."""
    return []


async def classify_bash_command(
    command: str,
    cwd: str,
    descriptions: list[str],
    behavior: ClassifierBehavior,
    is_non_interactive_session: bool = False,
) -> ClassifierResult:
    """
    Classify a bash command.

    Stub implementation - always returns not matching.
    """
    return ClassifierResult(
        matches=False,
        confidence="high",
        reason="This feature is disabled",
    )


async def generate_generic_description(
    command: str,
    specific_description: str | None,
) -> str | None:
    """Generate a generic description for a command."""
    return specific_description
