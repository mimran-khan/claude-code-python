"""
Session hooks.

Hooks that are registered per-session.

Migrated from: utils/hooks/sessionHooks.ts
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class SessionHook:
    """A session-scoped hook."""

    session_id: str
    event: str
    matcher: str
    callback: Callable[[list[Any]], bool]
    message: str
    timeout: int = 5000
    hook_id: str = ""


class SessionHookRegistry:
    """Registry for session hooks."""

    def __init__(self):
        self._hooks: dict[str, list[SessionHook]] = {}

    def add(self, hook: SessionHook) -> str:
        """
        Add a session hook.

        Args:
            hook: Hook to add

        Returns:
            Hook ID
        """
        import uuid

        if not hook.hook_id:
            hook.hook_id = str(uuid.uuid4())

        if hook.session_id not in self._hooks:
            self._hooks[hook.session_id] = []

        self._hooks[hook.session_id].append(hook)
        return hook.hook_id

    def remove(self, session_id: str, hook_id: str) -> bool:
        """
        Remove a session hook.

        Args:
            session_id: Session ID
            hook_id: Hook ID to remove

        Returns:
            True if removed
        """
        if session_id not in self._hooks:
            return False

        hooks = self._hooks[session_id]
        for i, hook in enumerate(hooks):
            if hook.hook_id == hook_id:
                hooks.pop(i)
                return True

        return False

    def get(self, session_id: str, event: str | None = None) -> list[SessionHook]:
        """
        Get hooks for a session.

        Args:
            session_id: Session ID
            event: Optional event filter

        Returns:
            List of matching hooks
        """
        hooks = self._hooks.get(session_id, [])

        if event:
            hooks = [h for h in hooks if h.event == event]

        return hooks

    def clear(self, session_id: str) -> int:
        """
        Clear all hooks for a session.

        Args:
            session_id: Session ID

        Returns:
            Number of hooks removed
        """
        if session_id in self._hooks:
            count = len(self._hooks[session_id])
            del self._hooks[session_id]
            return count
        return 0


# Global registry
_registry = SessionHookRegistry()


def add_session_hook(
    session_id: str,
    event: str,
    matcher: str,
    callback: Callable[[list[Any]], bool],
    message: str,
    timeout: int = 5000,
) -> str:
    """
    Add a session hook.

    Args:
        session_id: Session ID
        event: Hook event type
        matcher: Pattern to match
        callback: Callback function
        message: Message if callback returns False
        timeout: Timeout in ms

    Returns:
        Hook ID
    """
    hook = SessionHook(
        session_id=session_id,
        event=event,
        matcher=matcher,
        callback=callback,
        message=message,
        timeout=timeout,
    )
    return _registry.add(hook)


def remove_session_hook(session_id: str, hook_id: str) -> bool:
    """Remove a session hook."""
    return _registry.remove(session_id, hook_id)


def get_session_hooks(
    session_id: str,
    event: str | None = None,
) -> list[SessionHook]:
    """Get hooks for a session."""
    return _registry.get(session_id, event)


def clear_session_hooks(session_id: str) -> int:
    """Clear all hooks for a session."""
    return _registry.clear(session_id)
