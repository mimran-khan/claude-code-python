"""
Haiku-backed command prefix extraction (shared across shell tools).

Migrated from: utils/shell/prefix.ts
"""

from __future__ import annotations

import asyncio
import inspect
import os
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

import structlog

from claude_code.services.analytics.events import log_event
from claude_code.services.analytics.growthbook import get_feature_value_cached
from claude_code.services.api.claude import query_model
from claude_code.services.api.errors import starts_with_api_error_prefix

_LOG = structlog.get_logger(__name__)

DANGEROUS_SHELL_PREFIXES = frozenset(
    {
        "sh",
        "bash",
        "zsh",
        "fish",
        "csh",
        "tcsh",
        "ksh",
        "dash",
        "cmd",
        "cmd.exe",
        "powershell",
        "powershell.exe",
        "pwsh",
        "pwsh.exe",
        "bash.exe",
    },
)


@dataclass
class CommandPrefixResult:
    command_prefix: str | None


@dataclass
class CommandSubcommandPrefixResult(CommandPrefixResult):
    subcommand_prefixes: dict[str, CommandPrefixResult]


@dataclass
class PrefixExtractorConfig:
    tool_name: str
    policy_spec: str
    event_name: str
    query_source: str
    pre_check: Callable[[str], CommandPrefixResult | None] | None = None


def _assistant_text(message: dict[str, object]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text")
                if isinstance(t, str):
                    return t
        return "none"
    return "none"


class _AsyncLruCache:
    """LRU cache for async prefix resolution (keyed by command string)."""

    def __init__(self, max_size: int = 200) -> None:
        self._max = max_size
        self._tasks: OrderedDict[str, asyncio.Task[CommandPrefixResult | None]] = OrderedDict()

    async def get_or_create(
        self,
        key: str,
        factory: Callable[[], Awaitable[CommandPrefixResult | None]],
    ) -> CommandPrefixResult | None:
        if key in self._tasks:
            self._tasks.move_to_end(key)
            return await self._tasks[key]

        async def _run() -> CommandPrefixResult | None:
            try:
                return await factory()
            except asyncio.CancelledError:
                self._tasks.pop(key, None)
                raise
            except Exception:
                self._tasks.pop(key, None)
                raise

        task = asyncio.create_task(_run())
        self._tasks[key] = task
        while len(self._tasks) > self._max:
            old_key, old_task = self._tasks.popitem(last=False)
            if not old_task.done():
                old_task.cancel()
        return await task


async def _get_command_prefix_impl(
    command: str,
    tool_name: str,
    policy_spec: str,
    event_name: str,
    query_source: str,
    pre_check: Callable[[str], CommandPrefixResult | None] | None,
) -> CommandPrefixResult | None:
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("NODE_ENV") == "test":
        return None

    if pre_check:
        pc = pre_check(command)
        if pc is not None:
            return pc

    start = time.monotonic()
    use_system_prompt_spec = bool(get_feature_value_cached("tengu_cork_m4q", False))

    if use_system_prompt_spec:
        system = f"Your task is to process {tool_name} commands that an AI coding agent wants to run.\n\n{policy_spec}"
        user = f"Command: {command}"
    else:
        system = (
            f"Your task is to process {tool_name} commands that an AI coding agent wants to run.\n\n"
            "This policy spec defines how to determine the prefix of a "
            f"{tool_name} command:"
        )
        user = f"{policy_spec}\n\nCommand: {command}"

    try:
        result = await query_model(
            [{"role": "user", "content": user}],
            model=os.environ.get("CLAUDE_CODE_PREFIX_MODEL", "claude-3-5-haiku-20241022"),
            system=system,
        )
    except Exception as exc:
        _LOG.warning(
            "command_prefix_model_query_failed",
            tool_name=tool_name,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise

    duration_ms = int((time.monotonic() - start) * 1000)
    prefix = _assistant_text(result.message).strip()

    if starts_with_api_error_prefix(prefix):
        log_event(event_name, {"success": False, "error": "API error", "durationMs": duration_ms})
        return None
    if prefix == "command_injection_detected":
        log_event(
            event_name,
            {"success": False, "error": "command_injection_detected", "durationMs": duration_ms},
        )
        return CommandPrefixResult(command_prefix=None)
    if prefix == "git" or prefix.lower() in DANGEROUS_SHELL_PREFIXES:
        log_event(
            event_name,
            {"success": False, "error": "dangerous_shell_prefix", "durationMs": duration_ms},
        )
        return CommandPrefixResult(command_prefix=None)
    if prefix == "none":
        log_event(event_name, {"success": False, "error": 'prefix "none"', "durationMs": duration_ms})
        return CommandPrefixResult(command_prefix=None)
    if not command.startswith(prefix):
        log_event(
            event_name,
            {
                "success": False,
                "error": "command did not start with prefix",
                "durationMs": duration_ms,
            },
        )
        return CommandPrefixResult(command_prefix=None)
    log_event(event_name, {"success": True, "durationMs": duration_ms})
    return CommandPrefixResult(command_prefix=prefix)


class _PrefixFn(Protocol):
    async def __call__(
        self,
        command: str,
        abort_signal: object | None,
        is_non_interactive_session: bool,
    ) -> CommandPrefixResult | None: ...


def create_command_prefix_extractor(config: PrefixExtractorConfig) -> _PrefixFn:
    cache = _AsyncLruCache(200)

    async def memoized(
        command: str,
        abort_signal: object | None = None,
        is_non_interactive_session: bool = False,
    ) -> CommandPrefixResult | None:
        del abort_signal, is_non_interactive_session

        async def factory() -> CommandPrefixResult | None:
            return await _get_command_prefix_impl(
                command,
                config.tool_name,
                config.policy_spec,
                config.event_name,
                config.query_source,
                config.pre_check,
            )

        return await cache.get_or_create(command, factory)

    return memoized


def create_subcommand_prefix_extractor(
    get_prefix: _PrefixFn,
    split_command: Callable[[str], list[str] | Awaitable[list[str]]],
) -> _PrefixFn:
    cache = _AsyncLruCache(200)

    async def memoized(
        command: str,
        abort_signal: object | None = None,
        is_non_interactive_session: bool = False,
    ) -> CommandSubcommandPrefixResult | None:
        del abort_signal
        sc = split_command(command)
        if inspect.isawaitable(sc):
            subcommands = await sc  # type: ignore[misc]
        else:
            subcommands = sc  # type: ignore[assignment]

        async def factory() -> CommandSubcommandPrefixResult | None:
            full = await get_prefix(command, None, is_non_interactive_session)
            if not full:
                return None
            pairs: list[tuple[str, CommandPrefixResult | None]] = []
            for sub in subcommands:
                pr = await get_prefix(sub, None, is_non_interactive_session)
                pairs.append((sub, pr))
            sub_map: dict[str, CommandPrefixResult] = {}
            for sub, pr in pairs:
                if pr:
                    sub_map[sub] = pr
            return CommandSubcommandPrefixResult(
                command_prefix=full.command_prefix,
                subcommand_prefixes=sub_map,
            )

        out = await cache.get_or_create(command, factory)
        return out  # type: ignore[return-value]

    return memoized


__all__ = [
    "CommandPrefixResult",
    "CommandSubcommandPrefixResult",
    "PrefixExtractorConfig",
    "create_command_prefix_extractor",
    "create_subcommand_prefix_extractor",
]
