"""
Memoized and volatile system prompt sections.

Migrated from: constants/systemPromptSections.ts
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ..bootstrap.state import (
    clear_beta_header_latches,
    clear_system_prompt_section_state,
    get_system_prompt_section_cache,
    set_system_prompt_section_cache_entry,
)

ComputeFn = Callable[[], str | None | Awaitable[str | None]]


@dataclass(frozen=True)
class SystemPromptSection:
    """A named block of system prompt text, optionally cacheable per session."""

    name: str
    compute: ComputeFn
    cache_break: bool = False


def system_prompt_section(name: str, compute: ComputeFn) -> SystemPromptSection:
    """Memoized section: computed once, cached until /clear or /compact."""
    return SystemPromptSection(name=name, compute=compute, cache_break=False)


def dangerous_uncached_system_prompt_section(
    name: str,
    compute: ComputeFn,
    _reason: str,
) -> SystemPromptSection:
    """
    Volatile section: recomputes every turn; may break prompt cache.

    Requires a reason string documenting why cache-breaking is necessary.
    """
    return SystemPromptSection(name=name, compute=compute, cache_break=True)


async def _invoke_compute(fn: ComputeFn) -> str | None:
    result = fn()
    if inspect.isawaitable(result):
        return await result  # type: ignore[no-any-return]
    return result  # type: ignore[no-any-return]


async def resolve_system_prompt_sections(
    sections: list[SystemPromptSection],
) -> list[str | None]:
    """Resolve all sections, using the global cache when allowed."""
    cache = get_system_prompt_section_cache()
    out: list[str | None] = []
    for section in sections:
        if not section.cache_break and section.name in cache:
            out.append(cache.get(section.name))
            continue
        value = await _invoke_compute(section.compute)
        set_system_prompt_section_cache_entry(section.name, value)
        out.append(value)
    return out


def clear_system_prompt_sections() -> None:
    """Clear section cache and beta header latches (e.g. /clear, /compact)."""
    clear_system_prompt_section_state()
    clear_beta_header_latches()
