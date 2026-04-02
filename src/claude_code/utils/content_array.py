"""
Insert blocks into API message content arrays relative to ``tool_result`` blocks.

Migrated from: ``utils/contentArray.ts``
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import Any


def _is_tool_result_block(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    return item.get("type") == "tool_result"


def insert_block_after_tool_results(content: MutableSequence[Any], block: object) -> None:
    """
    Insert ``block`` after the last ``tool_result`` entry, or before the last
    block when none exist. Mutates ``content`` in place.

    If the inserted block becomes the final element, appends a minimal text
    continuation (some APIs require prompts not to end on non-text content).
    """
    last_tool = -1
    for i, item in enumerate(content):
        if _is_tool_result_block(item):
            last_tool = i

    if last_tool >= 0:
        insert_pos = last_tool + 1
        content.insert(insert_pos, block)
        if insert_pos == len(content) - 1:
            content.append({"type": "text", "text": "."})
    else:
        insert_index = max(0, len(content) - 1)
        content.insert(insert_index, block)
