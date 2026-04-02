"""Bundled claude-in-chrome skill. Migrated from: skills/bundled/claudeInChrome.ts"""

from __future__ import annotations

BASE_CHROME_PROMPT = """# Claude in Chrome

You can automate the user's Chrome session via MCP browser tools when they are available.

Start by listing tab context, then navigate or interact only after the user has granted
site permissions in the extension.

Prefer small, verifiable steps and screenshots when the user asked for visual confirmation.
"""

# Placeholder tool names — replace when `@ant/claude-for-chrome-mcp` constants are vendored.
_BROWSER_TOOL_NAMES = [
    "tabs_context_mcp",
    "navigate",
    "click",
    "fill",
    "screenshot",
]

SKILL_ACTIVATION_MESSAGE = """
Now that this skill is invoked, you have access to Chrome browser automation tools.
Start with `mcp__claude-in-chrome__tabs_context_mcp` to read open tabs.
"""


def _should_auto_enable_claude_in_chrome() -> bool:
    import os

    return os.environ.get("CLAUDE_CODE_CLAUDE_IN_CHROME", "").lower() in ("1", "true", "yes")


def register_claude_in_chrome_skill() -> None:
    from ..bundled_registry import register_bundled_skill
    from ..types import BundledSkillDefinition

    allowed = [f"mcp__claude-in-chrome__{n}" for n in _BROWSER_TOOL_NAMES]

    async def get_prompt_for_command(args: str, ctx: object) -> list[dict[str, str]]:
        del ctx
        prompt = f"{BASE_CHROME_PROMPT}\n{SKILL_ACTIVATION_MESSAGE}"
        if args.strip():
            prompt += f"\n## Task\n\n{args}"
        return [{"type": "text", "text": prompt}]

    register_bundled_skill(
        BundledSkillDefinition(
            name="claude-in-chrome",
            description=(
                "Automates Chrome: click, forms, screenshots, console logs, navigation "
                "in the user's existing browser session."
            ),
            when_to_use=(
                "When the user wants browser automation or web interaction. "
                "Invoke before using mcp__claude-in-chrome__* tools."
            ),
            allowed_tools=allowed,
            user_invocable=True,
            is_enabled=_should_auto_enable_claude_in_chrome,
            get_prompt_for_command=get_prompt_for_command,
        ),
    )
