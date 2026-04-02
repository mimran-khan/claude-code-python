"""
Generate one-line summaries of completed tool batches via Haiku.

Migrated from: services/toolUseSummary/toolUseSummaryGenerator.ts
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ...utils.log import log_error
from ..api.claude import query_model

TOOL_USE_SUMMARY_SYSTEM_PROMPT = """Write a short summary label describing what these tool calls accomplished. It appears as a single-line row in a mobile app and truncates around 30 characters, so think git-commit-subject, not sentence.

Keep the verb in past tense and the most distinctive noun. Drop articles, connectors, and long location context first.

Examples:
- Searched in auth/
- Fixed NPE in UserService
- Created signup endpoint
- Read config.json
- Ran failing tests"""


@dataclass
class ToolInfo:
    name: str
    input: Any
    output: Any


@dataclass
class GenerateToolUseSummaryParams:
    tools: list[ToolInfo]
    is_non_interactive_session: bool
    last_assistant_text: str | None = None
    model: str | None = None


def truncate_json_for_prompt(value: Any, max_length: int) -> str:
    try:
        s = json.dumps(value, default=str)
    except (TypeError, ValueError):
        return "[unable to serialize]"
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."


async def generate_tool_use_summary(params: GenerateToolUseSummaryParams) -> str | None:
    if not params.tools:
        return None
    try:
        parts: list[str] = []
        for tool in params.tools:
            inp = truncate_json_for_prompt(tool.input, 300)
            out = truncate_json_for_prompt(tool.output, 300)
            parts.append(f"Tool: {tool.name}\nInput: {inp}\nOutput: {out}")
        tool_summaries = "\n\n".join(parts)
        prefix = ""
        if params.last_assistant_text:
            prefix = f"User's intent (from assistant's last message): {params.last_assistant_text[:200]}\n\n"
        user_prompt = f"{prefix}Tools completed:\n\n{tool_summaries}\n\nLabel:"
        model = params.model or "claude-3-5-haiku-20241022"
        result = await query_model(
            messages=[{"role": "user", "content": user_prompt}],
            model=model,
            system=TOOL_USE_SUMMARY_SYSTEM_PROMPT,
            max_tokens=256,
            temperature=0.3,
        )
        content = result.message.get("content", [])
        texts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(str(block.get("text", "")))
        summary = "".join(texts).strip()
        return summary or None
    except Exception as err:
        log_error(err if isinstance(err, Exception) else RuntimeError(str(err)))
        return None
