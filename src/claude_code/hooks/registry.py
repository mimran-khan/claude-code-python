"""
Hook registry.

Registration and management of hooks.

Migrated from: utils/hooks/AsyncHookRegistry.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from .types import HookEvent

# Hook callback type
HookCallback = Callable[[dict[str, Any], str | None], Awaitable[dict[str, Any]]]


@dataclass
class RegisteredHook:
    """A registered hook."""

    event: HookEvent
    callback: HookCallback
    name: str = ""
    matcher: str | None = None
    plugin_name: str | None = None
    timeout: float = 30.0
    internal: bool = False


class HookRegistry:
    """Registry for managing hooks."""

    def __init__(self):
        self._hooks: dict[HookEvent, list[RegisteredHook]] = {}

    def register(
        self,
        event: HookEvent,
        callback: HookCallback,
        name: str = "",
        matcher: str | None = None,
        plugin_name: str | None = None,
        timeout: float = 30.0,
        internal: bool = False,
    ) -> str:
        """
        Register a hook.

        Args:
            event: The hook event
            callback: The callback function
            name: Optional hook name
            matcher: Optional matcher pattern
            plugin_name: Optional plugin name
            timeout: Timeout in seconds
            internal: Whether this is an internal hook

        Returns:
            Hook ID
        """
        import uuid

        hook_id = name or str(uuid.uuid4())

        hook = RegisteredHook(
            event=event,
            callback=callback,
            name=hook_id,
            matcher=matcher,
            plugin_name=plugin_name,
            timeout=timeout,
            internal=internal,
        )

        if event not in self._hooks:
            self._hooks[event] = []

        self._hooks[event].append(hook)
        return hook_id

    def unregister(self, event: HookEvent, name: str) -> bool:
        """
        Unregister a hook.

        Args:
            event: The hook event
            name: The hook name

        Returns:
            True if unregistered
        """
        if event not in self._hooks:
            return False

        original_len = len(self._hooks[event])
        self._hooks[event] = [h for h in self._hooks[event] if h.name != name]

        return len(self._hooks[event]) < original_len

    def get_hooks(self, event: HookEvent) -> list[RegisteredHook]:
        """Get all hooks for an event."""
        return self._hooks.get(event, [])

    def get_matching_hooks(
        self,
        event: HookEvent,
        tool_name: str | None = None,
    ) -> list[RegisteredHook]:
        """
        Get hooks that match the event and tool.

        Args:
            event: The hook event
            tool_name: Optional tool name to match

        Returns:
            List of matching hooks
        """
        hooks = self.get_hooks(event)

        if tool_name is None:
            return hooks

        matching = []
        for hook in hooks:
            if hook.matcher is None or hook.matcher in tool_name:
                matching.append(hook)

        return matching

    def clear(self, event: HookEvent | None = None) -> None:
        """Clear hooks for an event or all hooks."""
        if event:
            self._hooks[event] = []
        else:
            self._hooks = {}


# Global registry instance
_registry = HookRegistry()


def register_hook(
    event: HookEvent,
    callback: HookCallback,
    **kwargs,
) -> str:
    """Register a hook with the global registry."""
    return _registry.register(event, callback, **kwargs)


def unregister_hook(event: HookEvent, name: str) -> bool:
    """Unregister a hook from the global registry."""
    return _registry.unregister(event, name)


def get_hooks_for_event(
    event: HookEvent,
    tool_name: str | None = None,
) -> list[RegisteredHook]:
    """Get hooks for an event from the global registry."""
    return _registry.get_matching_hooks(event, tool_name)


def clear_hooks(event: HookEvent | None = None) -> None:
    """Clear hooks from the global registry."""
    _registry.clear(event)
