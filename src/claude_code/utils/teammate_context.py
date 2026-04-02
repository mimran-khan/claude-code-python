"""
In-process teammate execution context (AsyncLocalStorage equivalent).

Migrated from: utils/teammateContext.ts
"""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class TeammateContext:
    """Runtime context for in-process teammates."""

    agent_id: str
    agent_name: str
    team_name: str
    plan_mode_required: bool
    parent_session_id: str
    color: str | None = None
    is_in_process: bool = True


_teammate_ctx: ContextVar[TeammateContext | None] = ContextVar("claude_code_teammate_ctx", default=None)


def get_teammate_context() -> TeammateContext | None:
    return _teammate_ctx.get()


def is_in_process_teammate() -> bool:
    return _teammate_ctx.get() is not None


def run_with_teammate_context(context: TeammateContext, fn: Callable[[], T]) -> T:
    token: Token[TeammateContext | None] = _teammate_ctx.set(context)
    try:
        return fn()
    finally:
        _teammate_ctx.reset(token)


def create_teammate_context(
    *,
    agent_id: str,
    agent_name: str,
    team_name: str,
    plan_mode_required: bool,
    parent_session_id: str,
    color: str | None = None,
) -> TeammateContext:
    return TeammateContext(
        agent_id=agent_id,
        agent_name=agent_name,
        team_name=team_name,
        plan_mode_required=plan_mode_required,
        parent_session_id=parent_session_id,
        color=color,
        is_in_process=True,
    )
