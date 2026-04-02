"""
Post-sampling hook runner (placeholder for sampling pipeline integration).

Migrated from: utils/hooks/postSamplingHooks.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class PostSamplingContext:
    prompt: str
    response: dict[str, Any]


PostSamplingHook = Callable[[PostSamplingContext], Awaitable[None]]

_hooks: list[PostSamplingHook] = []


def register_post_sampling_hook(hook: PostSamplingHook) -> None:
    _hooks.append(hook)


async def run_post_sampling_hooks(ctx: PostSamplingContext) -> None:
    for h in _hooks:
        await h(ctx)


def clear_post_sampling_hooks() -> None:
    _hooks.clear()
