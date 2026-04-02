"""Automatic compaction based on context size."""

from typing import Any

from .compact import CompactConfig, CompactResult, compact_messages

DEFAULT_AUTO_COMPACT_THRESHOLD = 0.8  # Compact at 80% of max


def get_auto_compact_threshold(max_tokens: int) -> int:
    """Get the token threshold for auto-compaction."""
    return int(max_tokens * DEFAULT_AUTO_COMPACT_THRESHOLD)


async def auto_compact_if_needed(
    messages: list[Any],
    current_tokens: int,
    max_tokens: int,
    config: CompactConfig | None = None,
) -> CompactResult:
    """Automatically compact if we're approaching the limit."""
    threshold = get_auto_compact_threshold(max_tokens)

    if current_tokens < threshold:
        return CompactResult(
            compacted=False,
            messages_before=len(messages),
            messages_after=len(messages),
            tokens_before=current_tokens,
            tokens_after=current_tokens,
            messages=list(messages),
        )

    cfg = config or CompactConfig(
        max_tokens=max_tokens,
        target_tokens=int(max_tokens * 0.6),
    )
    if cfg.compact_trigger_tokens is None:
        cfg.compact_trigger_tokens = threshold

    return await compact_messages(messages, cfg, current_tokens)
