"""
Prompt templates for the background memory extraction agent.

Migrated from: services/extractMemories/prompts.ts
"""

from __future__ import annotations

from claude_code.memdir.memory_types import (
    MEMORY_FRONTMATTER_EXAMPLE,
    TYPES_SECTION_COMBINED,
    TYPES_SECTION_INDIVIDUAL,
    WHAT_NOT_TO_SAVE_SECTION,
)

BASH_TOOL_NAME = "Bash"
FILE_READ_TOOL_NAME = "Read"
FILE_EDIT_TOOL_NAME = "Edit"
FILE_WRITE_TOOL_NAME = "Write"
GLOB_TOOL_NAME = "Glob"
GREP_TOOL_NAME = "Grep"


def _opener(new_message_count: int, existing_memories: str) -> str:
    manifest = (
        f"\n\n## Existing memory files\n\n{existing_memories}\n\n"
        "Check this list before writing — update an existing file rather than creating a duplicate."
        if existing_memories
        else ""
    )
    return "\n".join(
        [
            f"You are now acting as the memory extraction subagent. Analyze the most recent ~{new_message_count} messages above and use them to update your persistent memory systems.",
            "",
            f"Available tools: {FILE_READ_TOOL_NAME}, {GREP_TOOL_NAME}, {GLOB_TOOL_NAME}, read-only {BASH_TOOL_NAME} (ls/find/cat/stat/wc/head/tail and similar), and {FILE_EDIT_TOOL_NAME}/{FILE_WRITE_TOOL_NAME} for paths inside the memory directory only. {BASH_TOOL_NAME} rm is not permitted. All other tools — MCP, Agent, write-capable {BASH_TOOL_NAME}, etc — will be denied.",
            "",
            f"You have a limited turn budget. {FILE_EDIT_TOOL_NAME} requires a prior {FILE_READ_TOOL_NAME} of the same file, so the efficient strategy is: turn 1 — issue all {FILE_READ_TOOL_NAME} calls in parallel for every file you might update; turn 2 — issue all {FILE_WRITE_TOOL_NAME}/{FILE_EDIT_TOOL_NAME} calls in parallel. Do not interleave reads and writes across multiple turns.",
            "",
            f"You MUST only use content from the last ~{new_message_count} messages to update your persistent memories. Do not waste any turns attempting to investigate or verify that content further — no grepping source files, no reading code to confirm a pattern exists, no git commands."
            + manifest,
        ]
    )


def build_extract_auto_only_prompt(
    new_message_count: int,
    existing_memories: str,
    skip_index: bool = False,
) -> str:
    how_to_save = (
        [
            "## How to save memories",
            "",
            "Write each memory to its own file (e.g., `user_role.md`, `feedback_testing.md`) using this frontmatter format:",
            "",
            *MEMORY_FRONTMATTER_EXAMPLE,
            "",
            "- Organize memory semantically by topic, not chronologically",
            "- Update or remove memories that turn out to be wrong or outdated",
            "- Do not write duplicate memories. First check if there is an existing memory you can update before writing a new one.",
        ]
        if skip_index
        else [
            "## How to save memories",
            "",
            "Saving a memory is a two-step process:",
            "",
            "**Step 1** — write the memory to its own file (e.g., `user_role.md`, `feedback_testing.md`) using this frontmatter format:",
            "",
            *MEMORY_FRONTMATTER_EXAMPLE,
            "",
            "**Step 2** — add a pointer to that file in `MEMORY.md`. `MEMORY.md` is an index, not a memory — each entry should be one line, under ~150 characters: `- [Title](file.md) — one-line hook`. It has no frontmatter. Never write memory content directly into `MEMORY.md`.",
            "",
            "- `MEMORY.md` is always loaded into your system prompt — lines after 200 will be truncated, so keep the index concise",
            "- Organize memory semantically by topic, not chronologically",
            "- Update or remove memories that turn out to be wrong or outdated",
            "- Do not write duplicate memories. First check if there is an existing memory you can update before writing a new one.",
        ]
    )
    return "\n".join(
        [
            _opener(new_message_count, existing_memories),
            "",
            "If the user explicitly asks you to remember something, save it immediately as whichever type fits best. If they ask you to forget something, find and remove the relevant entry.",
            "",
            *TYPES_SECTION_INDIVIDUAL,
            *WHAT_NOT_TO_SAVE_SECTION,
            "",
            *how_to_save,
        ]
    )


def build_extract_combined_prompt(
    new_message_count: int,
    existing_memories: str,
    skip_index: bool = False,
    *,
    team_memory_enabled: bool = False,
) -> str:
    if not team_memory_enabled:
        return build_extract_auto_only_prompt(new_message_count, existing_memories, skip_index)
    how_to_save = (
        [
            "## How to save memories",
            "",
            "Write each memory to its own file in the chosen directory (private or team, per the type's scope guidance) using this frontmatter format:",
            "",
            *MEMORY_FRONTMATTER_EXAMPLE,
            "",
            "- Organize memory semantically by topic, not chronologically",
            "- Update or remove memories that turn out to be wrong or outdated",
            "- Do not write duplicate memories. First check if there is an existing memory you can update before writing a new one.",
        ]
        if skip_index
        else [
            "## How to save memories",
            "",
            "Saving a memory is a two-step process:",
            "",
            "**Step 1** — write the memory to its own file in the chosen directory (private or team, per the type's scope guidance) using this frontmatter format:",
            "",
            *MEMORY_FRONTMATTER_EXAMPLE,
            "",
            "**Step 2** — add a pointer to that file in the same directory's `MEMORY.md`. Each directory (private and team) has its own `MEMORY.md` index — each entry should be one line, under ~150 characters: `- [Title](file.md) — one-line hook`. They have no frontmatter. Never write memory content directly into a `MEMORY.md`.",
            "",
            "- Both `MEMORY.md` indexes are loaded into your system prompt — lines after 200 will be truncated, so keep them concise",
            "- Organize memory semantically by topic, not chronologically",
            "- Update or remove memories that turn out to be wrong or outdated",
            "- Do not write duplicate memories. First check if there is an existing memory you can update before writing a new one.",
        ]
    )
    return "\n".join(
        [
            _opener(new_message_count, existing_memories),
            "",
            "If the user explicitly asks you to remember something, save it immediately as whichever type fits best. If they ask you to forget something, find and remove the relevant entry.",
            "",
            *TYPES_SECTION_COMBINED,
            *WHAT_NOT_TO_SAVE_SECTION,
            "- You MUST avoid saving sensitive data within shared team memories. For example, never save API keys or user credentials.",
            "",
            *how_to_save,
        ]
    )
