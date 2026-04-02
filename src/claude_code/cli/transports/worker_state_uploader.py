"""
Coalescing uploader for PUT /worker (session state + metadata).

Migrated from: cli/transports/WorkerStateUploader.ts
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class WorkerStateUploaderConfig:
    send: Callable[[dict[str, Any]], Awaitable[bool]]
    base_delay_ms: float
    max_delay_ms: float
    jitter_ms: float


def coalesce_patches(
    base: dict[str, Any],
    overlay: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key in ("external_metadata", "internal_metadata"):
            b = merged.get(key)
            if b is not None and isinstance(b, dict) and isinstance(value, dict):
                merged[key] = {**b, **value}
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged


class WorkerStateUploader:
    def __init__(self, config: WorkerStateUploaderConfig) -> None:
        self._config = config
        self._inflight: asyncio.Task[None] | None = None
        self._pending: dict[str, Any] | None = None
        self._closed = False

    def enqueue(self, patch: dict[str, Any]) -> None:
        if self._closed:
            return
        if self._pending is None:
            self._pending = dict(patch)
        else:
            self._pending = coalesce_patches(self._pending, patch)
        asyncio.create_task(self._drain())

    def close(self) -> None:
        self._closed = True
        self._pending = None

    async def _drain(self) -> None:
        if self._inflight or self._closed:
            return
        if not self._pending:
            return
        payload = self._pending
        self._pending = None

        async def _run() -> None:
            await self._send_with_retry(payload)

        self._inflight = asyncio.create_task(_run())
        try:
            await self._inflight
        finally:
            self._inflight = None
            if self._pending and not self._closed:
                asyncio.create_task(self._drain())

    async def _send_with_retry(self, payload: dict[str, Any]) -> None:
        current = payload
        failures = 0
        while not self._closed:
            ok = await self._config.send(current)
            if ok:
                return
            failures += 1
            delay = self._retry_delay(failures)
            await asyncio.sleep(delay / 1000.0)
            if self._pending and not self._closed:
                current = coalesce_patches(current, self._pending)
                self._pending = None

    def _retry_delay(self, failures: int) -> float:
        exponential = min(
            self._config.base_delay_ms * (2 ** (failures - 1)),
            self._config.max_delay_ms,
        )
        jitter = random.random() * self._config.jitter_ms
        return exponential + jitter
