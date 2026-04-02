"""
Poll GitHub PR review status for the current branch.

Migrated from: hooks/usePrStatus.ts
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

POLL_INTERVAL_S = 60.0
SLOW_GH_THRESHOLD_S = 4.0
IDLE_STOP_S = 60 * 60.0

PrReviewState = str | None


@dataclass
class PrFetchResult:
    number: int | None
    url: str | None
    review_state: PrReviewState


@dataclass
class PrStatusMutableState:
    number: int | None = None
    url: str | None = None
    review_state: PrReviewState = None
    last_updated: float = 0.0


INITIAL_PR_STATUS = PrStatusMutableState()


def should_update_pr_status(prev: PrStatusMutableState, result: PrFetchResult | None) -> bool:
    if result is None:
        return False
    return prev.number != result.number or prev.review_state != result.review_state


def apply_pr_fetch(
    prev: PrStatusMutableState,
    result: PrFetchResult | None,
) -> PrStatusMutableState:
    if result is None:
        return prev
    if not should_update_pr_status(prev, result):
        return prev
    return PrStatusMutableState(
        number=result.number,
        url=result.url,
        review_state=result.review_state,
        last_updated=time.time(),
    )


async def run_pr_status_poll_loop(
    *,
    is_loading: bool,
    enabled: bool,
    get_last_interaction_time: Callable[[], float],
    fetch_pr_status: Callable[[], Awaitable[PrFetchResult | None]],
    state: PrStatusMutableState,
    last_fetch_monotonic: list[float],
    disabled_flag: list[bool],
    cancel_event: asyncio.Event,
) -> None:
    """
    One scheduling cycle: sleep until next poll, fetch, update state, reschedule.

    Call from a task; pass ``cancel_event`` to stop. ``last_fetch_monotonic`` is
    a one-element box for cross-await timing (like useRef).
    """
    _ = is_loading  # TS restarts loop when loading changes; caller should cancel+restart
    if not enabled or disabled_flag[0]:
        return

    now = time.monotonic()
    elapsed = now - last_fetch_monotonic[0]
    wait = max(0.0, POLL_INTERVAL_S - elapsed)
    try:
        await asyncio.wait_for(cancel_event.wait(), timeout=wait)
        return
    except TimeoutError:
        pass

    last_seen_interaction = -1.0
    last_activity = time.monotonic()

    while not cancel_event.is_set():
        interaction = get_last_interaction_time()
        if last_seen_interaction != interaction:
            last_seen_interaction = interaction
            last_activity = time.monotonic()
        elif time.monotonic() - last_activity >= IDLE_STOP_S:
            return

        start = time.monotonic()
        result = await fetch_pr_status()
        if cancel_event.is_set():
            return
        last_fetch_monotonic[0] = time.monotonic()

        updated = apply_pr_fetch(state, result)
        state.number = updated.number
        state.url = updated.url
        state.review_state = updated.review_state
        state.last_updated = updated.last_updated

        if time.monotonic() - start > SLOW_GH_THRESHOLD_S:
            disabled_flag[0] = True
            return

        try:
            await asyncio.wait_for(cancel_event.wait(), timeout=POLL_INTERVAL_S)
            return
        except TimeoutError:
            continue
