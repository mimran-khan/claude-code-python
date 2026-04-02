"""
Resolve main-loop model name with GrowthBook refresh subscription.

Migrated from: hooks/useMainLoopModel.ts
"""

from __future__ import annotations

from collections.abc import Callable


def resolve_main_loop_model(
    *,
    main_loop_model: str | None,
    main_loop_model_for_session: str | None,
    get_default_main_loop_model: Callable[[], str],
    parse_user_specified_model: Callable[[str], str],
) -> str:
    raw = main_loop_model_for_session or main_loop_model or get_default_main_loop_model()
    return parse_user_specified_model(raw)


def subscribe_growthbook_refresh(on_refresh: Callable[[], None]) -> Callable[[], None]:
    """Inject TS ``onGrowthBookRefresh`` equivalent; returns unsubscribe if supported."""
    _ = on_refresh
    return lambda: None
