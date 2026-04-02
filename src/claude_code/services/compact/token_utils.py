"""Token estimation for compaction (tiktoken when available, else char heuristic)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _tiktoken_encoding() -> Any:
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def message_to_text(msg: Any) -> str:
    """Best-effort string extraction for transcript-style message objects."""
    if msg is None:
        return ""
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    t = block.get("type")
                    if t == "text" and isinstance(block.get("text"), str):
                        parts.append(block["text"])
                    elif t == "tool_result":
                        c = block.get("content", "")
                        parts.append(c if isinstance(c, str) else str(c))
                    else:
                        parts.append(str(block))
                elif isinstance(block, str):
                    parts.append(block)
            return "\n".join(parts)
        nested = msg.get("message")
        if nested is not None:
            return message_to_text(nested)
    return str(msg)


def estimate_text_tokens(text: str) -> int:
    """Approximate token count for a string."""
    if not text:
        return 0
    enc = _tiktoken_encoding()
    if enc is not None:
        return len(enc.encode(text))
    return max(1, len(text) // 4)


def estimate_message_tokens(message: Any) -> int:
    """Token estimate for one message."""
    return estimate_text_tokens(message_to_text(message))


def estimate_messages_tokens(messages: list[Any]) -> int:
    """Sum token estimates for a conversation."""
    return sum(estimate_message_tokens(m) for m in messages)
