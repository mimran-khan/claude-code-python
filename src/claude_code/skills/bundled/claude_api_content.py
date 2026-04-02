"""
Lazy documentation bundle for /claude-api.

Migrated from: skills/bundled/claudeApiContent.ts (full 247KB bundle not vendored).

Populate SKILL_FILES with language-specific markdown when shipping full docs.
"""

from __future__ import annotations

SKILL_MODEL_VARS: dict[str, str] = {
    "ANTHROPIC_VERSION": "2023-06-01",
}

SKILL_PROMPT = """# Claude API skill

Help the user integrate the Anthropic API or official SDKs for their stack.

## Reading Guide

## When to Use WebFetch

Prefer bundled `<doc>` references below; use WebFetch for the latest parameter names or
pricing when the user asks for up-to-the-minute API details.

## Common Pitfalls

- Mixing Messages API shape with legacy completions fields.
- Omitting required `anthropic-version` header on direct HTTP calls.
- Not handling rate limits and retries.
"""

# Empty: detectLanguage will fall back to including no inline docs unless populated.
SKILL_FILES: dict[str, str] = {}
