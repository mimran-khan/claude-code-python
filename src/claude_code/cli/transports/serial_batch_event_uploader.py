"""
Serial ordered event uploader with batching, retry, and backpressure.

Migrated from: cli/transports/SerialBatchEventUploader.ts
"""

from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class RetryableError(Exception):
    """Raise from send() to retry; optional retry_after_ms overrides backoff."""

    def __init__(self, message: str, retry_after_ms: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_ms = retry_after_ms


@dataclass
class SerialBatchEventUploaderConfig(Generic[T]):
    max_batch_size: int
    max_queue_size: int
    send: Callable[[list[T]], Awaitable[None]]
    base_delay_ms: float
    max_delay_ms: float
    jitter_ms: float
    max_batch_bytes: int | None = None
    max_consecutive_failures: int | None = None
    on_batch_dropped: Callable[[int, int], None] | None = None


class SerialBatchEventUploader(Generic[T]):
    def __init__(self, config: SerialBatchEventUploaderConfig[T]) -> None:
        self._config = config
        self._pending: list[T] = []
        self._pending_at_close = 0
        self._draining = False
        self._closed = False
        self._dropped_batches = 0
        self._lock = asyncio.Lock()
        self._backpressure: list[asyncio.Event] = []
        self._flush_waiters: list[asyncio.Event] = []
        self._sleep_task: asyncio.Task[None] | None = None

    @property
    def dropped_batch_count(self) -> int:
        return self._dropped_batches

    @property
    def pending_count(self) -> int:
        return self._pending_at_close if self._closed else len(self._pending)

    async def enqueue(self, events: T | list[T]) -> None:
        if self._closed:
            return
        items: list[T] = events if isinstance(events, list) else [events]
        if not items:
            return
        async with self._lock:
            while len(self._pending) + len(items) > self._config.max_queue_size and not self._closed:
                ev = asyncio.Event()
                self._backpressure.append(ev)
                await ev.wait()
            if self._closed:
                return
            self._pending.extend(items)
        asyncio.create_task(self._drain())

    async def flush(self) -> None:
        ev = asyncio.Event()
        async with self._lock:
            if not self._pending and not self._draining:
                return
            self._flush_waiters.append(ev)
        asyncio.create_task(self._drain())
        await ev.wait()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._pending_at_close = len(self._pending)
        self._pending.clear()
        for ev in self._backpressure:
            ev.set()
        self._backpressure.clear()
        for ev in self._flush_waiters:
            ev.set()
        self._flush_waiters.clear()

    async def _drain(self) -> None:
        async with self._lock:
            if self._draining or self._closed:
                return
            self._draining = True
        failures = 0
        try:
            while True:
                async with self._lock:
                    if not self._pending or self._closed:
                        break
                    batch = self._take_batch_unlocked()
                if not batch:
                    continue
                try:
                    await self._config.send(batch)
                    failures = 0
                except Exception as err:
                    failures += 1
                    max_f = self._config.max_consecutive_failures
                    if max_f is not None and failures >= max_f:
                        self._dropped_batches += 1
                        if self._config.on_batch_dropped:
                            self._config.on_batch_dropped(len(batch), failures)
                        failures = 0
                        self._release_backpressure()
                        continue
                    async with self._lock:
                        self._pending = batch + self._pending
                    retry_after = err.retry_after_ms if isinstance(err, RetryableError) else None
                    delay = self._retry_delay(failures, retry_after)
                    await asyncio.sleep(delay / 1000.0)
                    continue
                self._release_backpressure()
        finally:
            async with self._lock:
                self._draining = False
                waiters: list[asyncio.Event] = []
                if not self._pending:
                    waiters = list(self._flush_waiters)
                    self._flush_waiters.clear()
            for w in waiters:
                w.set()

    def _take_batch_unlocked(self) -> list[T]:
        cfg = self._config
        if cfg.max_batch_bytes is None:
            n = min(cfg.max_batch_size, len(self._pending))
            batch = self._pending[:n]
            del self._pending[:n]
            return batch
        total_bytes = 0
        count = 0
        while count < len(self._pending) and count < cfg.max_batch_size:
            try:
                item_bytes = len(json.dumps(self._pending[count], ensure_ascii=False).encode("utf-8"))
            except (TypeError, ValueError):
                del self._pending[count]
                continue
            if count > 0 and total_bytes + item_bytes > cfg.max_batch_bytes:
                break
            total_bytes += item_bytes
            count += 1
        batch = self._pending[:count]
        del self._pending[:count]
        return batch

    def _retry_delay(self, failures: int, retry_after_ms: int | None) -> float:
        jitter = random.random() * self._config.jitter_ms
        if retry_after_ms is not None:
            clamped = max(
                self._config.base_delay_ms,
                min(float(retry_after_ms), self._config.max_delay_ms),
            )
            return clamped + jitter
        exponential = min(
            self._config.base_delay_ms * (2 ** (failures - 1)),
            self._config.max_delay_ms,
        )
        return exponential + jitter

    def _release_backpressure(self) -> None:
        for ev in self._backpressure:
            ev.set()
        self._backpressure.clear()
