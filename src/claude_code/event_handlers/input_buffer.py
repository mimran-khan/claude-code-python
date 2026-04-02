"""
Debounced undo buffer for prompt text.

Migrated from: hooks/useInputBuffer.ts
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

PastedSnapshot = dict[str, Any]


@dataclass
class BufferEntry:
    text: str
    cursor_offset: int
    pasted_contents: dict[int, PastedSnapshot]
    timestamp: float


@dataclass
class InputBufferState:
    max_buffer_size: int
    debounce_ms: int
    buffer: list[BufferEntry] = field(default_factory=list)
    current_index: int = -1
    last_push_time: float = 0.0
    _debounce_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def clear(self) -> None:
        self.buffer.clear()
        self.current_index = -1
        self.last_push_time = 0.0

    async def push(
        self,
        text: str,
        cursor_offset: int,
        pasted: dict[int, PastedSnapshot] | None = None,
    ) -> None:
        pasted = pasted or {}
        async with self._debounce_lock:
            now = time.time() * 1000
            elapsed = now - self.last_push_time
            if elapsed < self.debounce_ms:
                await asyncio.sleep((self.debounce_ms - elapsed) / 1000)
                now = time.time() * 1000
            self.last_push_time = now
            prev_buf = self.buffer[: self.current_index + 1] if self.current_index >= 0 else list(self.buffer)
            if prev_buf and prev_buf[-1].text == text:
                self.buffer = prev_buf
                return
            entry = BufferEntry(
                text=text,
                cursor_offset=cursor_offset,
                pasted_contents=dict(pasted),
                timestamp=now,
            )
            updated = [*prev_buf, entry]
            if len(updated) > self.max_buffer_size:
                updated = updated[-self.max_buffer_size :]
            self.buffer = updated
            self.current_index = min(len(updated) - 1, self.max_buffer_size - 1)

    def undo(self) -> BufferEntry | None:
        if self.current_index < 0 or not self.buffer:
            return None
        target = max(0, self.current_index - 1)
        entry = self.buffer[target]
        self.current_index = target
        return entry

    @property
    def can_undo(self) -> bool:
        return self.current_index > 0 and len(self.buffer) > 1
