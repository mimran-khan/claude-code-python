"""API-native context management strategies (clear tool uses / thinking).

Migrated from: services/compact/apiMicrocompact.ts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Tool names aligned with TS defaults (string literals only).
TOOLS_CLEARABLE_RESULTS: tuple[str, ...] = (
    "Bash",
    "Glob",
    "Grep",
    "Read",
    "WebFetch",
    "WebSearch",
)
TOOLS_CLEARABLE_USES: tuple[str, ...] = ("Edit", "Write", "NotebookEdit")


@dataclass
class TriggerInputTokens:
    type: Literal["input_tokens"]
    value: int


@dataclass
class KeepToolUses:
    type: Literal["tool_uses"]
    value: int


@dataclass
class ClearAtLeastInputTokens:
    type: Literal["input_tokens"]
    value: int


@dataclass
class ClearToolUsesStrategy:
    type: Literal["clear_tool_uses_20250919"]
    trigger: TriggerInputTokens | None = None
    keep: KeepToolUses | None = None
    clear_tool_inputs: bool | list[str] | None = None
    exclude_tools: list[str] | None = None
    clear_at_least: ClearAtLeastInputTokens | None = None


@dataclass
class KeepThinkingTurns:
    type: Literal["thinking_turns"]
    value: int


@dataclass
class ClearThinkingStrategy:
    type: Literal["clear_thinking_20251015"]
    keep: KeepThinkingTurns | Literal["all"]


ContextEditStrategy = ClearToolUsesStrategy | ClearThinkingStrategy


@dataclass
class ContextManagementConfig:
    edits: list[ContextEditStrategy]


def get_api_context_management(
    *,
    has_thinking: bool = False,
    is_redact_thinking_active: bool = False,
    clear_all_thinking: bool = False,
) -> ContextManagementConfig | None:
    strategies: list[ContextEditStrategy] = []
    if has_thinking and not is_redact_thinking_active:
        if clear_all_thinking:
            strategies.append(ClearThinkingStrategy(keep=KeepThinkingTurns(type="thinking_turns", value=1)))
        else:
            strategies.append(ClearThinkingStrategy(keep="all"))
    strategies.append(
        ClearToolUsesStrategy(
            type="clear_tool_uses_20250919",
            trigger=TriggerInputTokens(type="input_tokens", value=180_000),
            keep=KeepToolUses(type="tool_uses", value=3),
            exclude_tools=list(TOOLS_CLEARABLE_USES),
        )
    )
    strategies.append(
        ClearToolUsesStrategy(
            type="clear_tool_uses_20250919",
            trigger=TriggerInputTokens(type="input_tokens", value=40_000),
            keep=KeepToolUses(type="tool_uses", value=5),
            clear_tool_inputs=True,
            exclude_tools=list(TOOLS_CLEARABLE_RESULTS),
        )
    )
    return ContextManagementConfig(edits=strategies)
