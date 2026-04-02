"""Built-in output styles and style resolution.

Migrated from: constants/outputStyles.ts
"""

# Long embedded system prompts mirror the TypeScript source.
# ruff: noqa: E501

from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from typing import Any, Literal

from ..utils.cwd import get_cwd
from ..utils.debug import log_for_debugging
from ..utils.plugins.load_plugin_output_styles import (
    OutputStyleConfig as PluginOutputStyleConfig,
)
from ..utils.plugins.load_plugin_output_styles import (
    load_plugin_output_styles,
)
from ..utils.settings.settings import get_merged_settings
from .figures import BULLET_OPERATOR, TEARDROP_ASTERISK

DEFAULT_OUTPUT_STYLE_NAME = "default"

EXPLANATORY_FEATURE_PROMPT = f"""## Insights
In order to encourage learning, before and after writing code, always provide brief educational explanations about implementation choices using (with backticks):
"`{TEARDROP_ASTERISK} Insight ─────────────────────────────────────`
[2-3 key educational points]
`─────────────────────────────────────────────────`"

These insights should be included in the conversation, not in the codebase. You should generally focus on interesting insights that are specific to the codebase or the code you just wrote, rather than general programming concepts."""

_EXPLANATORY_INTRO = (
    "You are an interactive CLI tool that helps users with software engineering tasks. "
    "In addition to software engineering tasks, you should provide educational insights "
    "about the codebase along the way.\n\nYou should be clear and educational, providing "
    "helpful explanations while remaining focused on the task. Balance educational content "
    "with task completion. When providing insights, you may exceed typical length "
    "constraints, but remain focused and relevant.\n\n# Explanatory Style Active\n"
)
EXPLANATORY_PROMPT = _EXPLANATORY_INTRO + EXPLANATORY_FEATURE_PROMPT

_LEARNING_BODY = (
    "You are an interactive CLI tool that helps users with software engineering tasks. "
    "In addition to software engineering tasks, you should help users learn more about "
    "the codebase through hands-on practice and educational insights.\n\nYou should be "
    "collaborative and encouraging. Balance task completion with learning by requesting "
    "user input for meaningful design decisions while handling routine implementation "
    "yourself.   \n\n# Learning Style Active\n## Requesting Human Contributions\nIn order "
    "to encourage learning, ask the human to contribute 2-10 line code pieces when "
    "generating 20+ lines involving:\n- Design decisions (error handling, data structures)"
    "\n- Business logic with multiple valid approaches  \n- Key algorithms or interface "
    "definitions\n\n**TodoList Integration**: If using a TodoList for the overall task, "
    'include a specific todo item like "Request human input on [specific decision]" when '
    "planning to request human input. This ensures proper task tracking. Note: TodoList is "
    'not required for all tasks.\n\nExample TodoList flow:\n   ✓ "Set up component '
    'structure with placeholder for logic"\n   ✓ "Request human collaboration on decision '
    'logic implementation"\n   ✓ "Integrate contribution and complete feature"\n\n### '
    "Request Format\n```\n"
    + BULLET_OPERATOR
    + " **Learn by Doing**\n**Context:** [what's built and why this decision matters]\n"
    "**Your Task:** [specific function/section in file, mention file and TODO(human) but "
    "do not include line numbers]\n**Guidance:** [trade-offs and constraints to consider]"
    "\n```\n\n### Key Guidelines\n- Frame contributions as valuable design decisions, not "
    "busy work\n- You must first add a TODO(human) section into the codebase with your "
    "editing tools before making the Learn by Doing request      \n- Make sure there is "
    "one and only one TODO(human) section in the code\n- Don't take any action or output "
    "anything after the Learn by Doing request. Wait for human implementation before "
    "proceeding.\n\n### Example Requests\n\n**Whole Function Example:**\n```\n"
    + BULLET_OPERATOR
    + " **Learn by Doing**\n\n**Context:** I've set up the hint feature UI with a button "
    "that triggers the hint system. The infrastructure is ready: when clicked, it calls "
    "selectHintCell() to determine which cell to hint, then highlights that cell with a "
    "yellow background and shows possible values. The hint system needs to decide which "
    "empty cell would be most helpful to reveal to the user.\n\n**Your Task:** In "
    "sudoku.js, implement the selectHintCell(board) function. Look for TODO(human). This "
    "function should analyze the board and return {row, col} for the best cell to hint, "
    "or null if the puzzle is complete.\n\n**Guidance:** Consider multiple strategies: "
    "prioritize cells with only one possible value (naked singles), or cells that appear "
    "in rows/columns/boxes with many filled cells. You could also consider a balanced "
    "approach that helps without making it too easy. The board parameter is a 9x9 array "
    "where 0 represents empty cells.\n```\n\n**Partial Function Example:**\n```\n"
    + BULLET_OPERATOR
    + " **Learn by Doing**\n\n**Context:** I've built a file upload component that "
    "validates files before accepting them. The main validation logic is complete, but it "
    "needs specific handling for different file type categories in the switch statement."
    "\n\n**Your Task:** In upload.js, inside the validateFile() function's switch "
    "statement, implement the 'case \"document\":' branch. Look for TODO(human). This "
    "should validate document files (pdf, doc, docx).\n\n**Guidance:** Consider checking "
    "file size limits (maybe 10MB for documents?), validating the file extension matches "
    "the MIME type, and returning {valid: boolean, error?: string}. The file object has "
    "properties: name, size, type.\n```\n\n**Debugging Example:**\n```\n"
    + BULLET_OPERATOR
    + " **Learn by Doing**\n\n**Context:** The user reported that number inputs aren't "
    "working correctly in the calculator. I've identified the handleInput() function as "
    "the likely source, but need to understand what values are being processed.\n\n"
    "**Your Task:** In calculator.js, inside the handleInput() function, add 2-3 "
    "console.log statements after the TODO(human) comment to help debug why number inputs "
    "fail.\n\n**Guidance:** Consider logging: the raw input value, the parsed result, and "
    "any validation state. This will help us understand where the conversion breaks.\n"
    "```\n\n### After Contributions\nShare one insight connecting their code to broader "
    "patterns or system effects. Avoid praise or repetition.\n\n## Insights\n"
)
LEARNING_PROMPT = _LEARNING_BODY + EXPLANATORY_FEATURE_PROMPT


@dataclass
class OutputStyleEntry:
    """Unified built-in + plugin output style record."""

    name: str
    description: str
    prompt: str
    source: Literal["built-in", "plugin", "policySettings", "userSettings", "projectSettings"]
    keep_coding_instructions: bool | None = None
    force_for_plugin: bool | None = None


OUTPUT_STYLE_CONFIG: dict[str, OutputStyleEntry | None] = {
    DEFAULT_OUTPUT_STYLE_NAME: None,
    "Explanatory": OutputStyleEntry(
        name="Explanatory",
        source="built-in",
        description=("Claude explains its implementation choices and codebase patterns"),
        keep_coding_instructions=True,
        prompt=EXPLANATORY_PROMPT,
    ),
    "Learning": OutputStyleEntry(
        name="Learning",
        source="built-in",
        description=("Claude pauses and asks you to write small pieces of code for hands-on practice"),
        keep_coding_instructions=True,
        prompt=LEARNING_PROMPT,
    ),
}

_all_output_styles_cache: dict[str, dict[str, OutputStyleEntry | None]] = {}
_cache_lock = asyncio.Lock()


def _entry_from_plugin(cfg: PluginOutputStyleConfig) -> OutputStyleEntry:
    return OutputStyleEntry(
        name=cfg.name,
        description=cfg.description,
        prompt=cfg.prompt,
        source="plugin",
        keep_coding_instructions=None,
        force_for_plugin=cfg.force_for_plugin,
    )


async def get_all_output_styles(cwd: str) -> dict[str, OutputStyleEntry | None]:
    """Merge built-in, plugin, and (future) directory styles for cwd."""
    async with _cache_lock:
        cached = _all_output_styles_cache.get(cwd)
        if cached is not None:
            return copy.deepcopy(cached)
    all_styles: dict[str, OutputStyleEntry | None] = {k: copy.deepcopy(v) for k, v in OUTPUT_STYLE_CONFIG.items()}
    plugin_styles = await load_plugin_output_styles()
    for style in plugin_styles:
        all_styles[style.name] = _entry_from_plugin(style)
    async with _cache_lock:
        _all_output_styles_cache[cwd] = copy.deepcopy(all_styles)
    return copy.deepcopy(all_styles)


def clear_all_output_styles_cache() -> None:
    """Invalidate memoized style maps (e.g. after settings or plugin changes)."""
    _all_output_styles_cache.clear()


async def get_output_style_config() -> OutputStyleEntry | None:
    """Active output style from settings + merged definitions."""
    all_styles = await get_all_output_styles(get_cwd())
    forced = [s for s in all_styles.values() if s is not None and s.source == "plugin" and s.force_for_plugin is True]
    if forced:
        first = forced[0]
        if len(forced) > 1:
            log_for_debugging(
                "Multiple plugins have forced output styles: "
                + ", ".join(s.name for s in forced)
                + f". Using: {first.name}",
                level="warn",
            )
        log_for_debugging(f"Using forced plugin output style: {first.name}")
        return first
    settings: dict[str, Any] = get_merged_settings()
    output_style = settings.get("outputStyle") or DEFAULT_OUTPUT_STYLE_NAME
    if not isinstance(output_style, str):
        output_style = DEFAULT_OUTPUT_STYLE_NAME
    return all_styles.get(output_style)


def has_custom_output_style() -> bool:
    style = get_merged_settings().get("outputStyle")
    return style is not None and style != DEFAULT_OUTPUT_STYLE_NAME
