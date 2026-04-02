"""Message compaction for managing context window."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .token_utils import estimate_messages_tokens, message_to_text


@dataclass
class CompactConfig:
    """Configuration for compaction."""

    max_tokens: int = 100_000
    """Hard context ceiling; also default compaction trigger if ``compact_trigger_tokens`` unset."""
    compact_trigger_tokens: int | None = None
    """When ``current_tokens`` reaches this value, compaction may run."""
    target_tokens: int = 80_000
    min_messages_to_keep: int = 4
    summary_model: str | None = None
    summary_max_chars: int = 12_000
    user_instruction_prefix: str | None = None
    """Optional /compact args echoed into the summary block (manual compaction)."""


@dataclass
class CompactResult:
    """Result of compaction."""

    compacted: bool
    messages_before: int
    messages_after: int
    tokens_before: int
    tokens_after: int
    summary: str | None = None
    messages: list[Any] | None = None


def should_compact(
    messages: list[Any],
    config: CompactConfig,
    current_tokens: int,
) -> bool:
    """Check if compaction is needed."""
    trigger = config.compact_trigger_tokens if config.compact_trigger_tokens is not None else config.max_tokens
    if current_tokens < trigger:
        return False

    return not len(messages) <= config.min_messages_to_keep


def _apply_user_compact_prefix(summary: str, prefix: str | None) -> str:
    if not prefix:
        return summary
    note = prefix.strip()
    if not note:
        return summary
    return f"[User compaction instructions]\n{note}\n\n{summary}"


def _build_summary_prefix(older: list[Any], max_chars: int) -> str:
    """Extractive summary: numbered previews of older turns (no LLM call)."""
    lines: list[str] = ["[Compacted earlier turns — summaries of prior messages:]"]
    used = len(lines[0]) + 1
    for i, msg in enumerate(older):
        raw = message_to_text(msg).strip()
        preview = (raw[:800] + "…") if len(raw) > 800 else raw
        line = f"{i + 1}. {preview.replace(chr(10), ' ')}"
        if used + len(line) + 1 > max_chars:
            lines.append(f"... ({len(older) - i} more messages omitted)")
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines)


def _prepend_compact_user_message(summary: str, tail: list[Any]) -> list[Any]:
    """Prepend a synthetic user message; shape follows the first tail message when possible."""
    if not tail:
        return [{"role": "user", "content": summary}]
    first = tail[0]
    if isinstance(first, dict) and "type" in first:
        return [
            {"type": "user", "message": {"role": "user", "content": summary}},
            *tail,
        ]
    return [{"role": "user", "content": summary}, *tail]


async def compact_messages(
    messages: list[Any],
    config: CompactConfig,
    current_tokens: int,
) -> CompactResult:
    """Compact messages: summarize older turns, keep recent tail."""
    measured = estimate_messages_tokens(messages)
    tokens_before = current_tokens if current_tokens > 0 else measured

    if not should_compact(messages, config, tokens_before):
        return CompactResult(
            compacted=False,
            messages_before=len(messages),
            messages_after=len(messages),
            tokens_before=tokens_before,
            tokens_after=tokens_before,
            messages=list(messages),
        )

    keep_count = max(1, min(config.min_messages_to_keep, len(messages) - 1))
    older = messages[:-keep_count]
    tail = messages[-keep_count:]

    summary = _apply_user_compact_prefix(
        _build_summary_prefix(older, config.summary_max_chars),
        config.user_instruction_prefix,
    )
    compacted_messages = _prepend_compact_user_message(summary, tail)

    tokens_after = estimate_messages_tokens(compacted_messages)
    final_summary = summary
    if tokens_after > config.target_tokens and len(compacted_messages) > 2:
        # Second pass: shrink summary if still above target
        shorter = _apply_user_compact_prefix(
            _build_summary_prefix(older, max(2000, config.summary_max_chars // 2)),
            config.user_instruction_prefix,
        )
        compacted_messages = _prepend_compact_user_message(shorter, tail)
        tokens_after = estimate_messages_tokens(compacted_messages)
        final_summary = shorter

    return CompactResult(
        compacted=True,
        messages_before=len(messages),
        messages_after=len(compacted_messages),
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        summary=final_summary,
        messages=compacted_messages,
    )
