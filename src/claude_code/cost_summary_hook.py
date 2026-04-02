"""
Print cost summary on process exit (TS useCostSummary analogue).

Migrated from: costHook.ts
"""

from __future__ import annotations

import atexit
import sys
from collections.abc import Callable
from typing import Any


def register_cost_summary_on_exit(
    get_fps_metrics: Callable[[], Any] | None = None,
) -> None:
    def _on_exit() -> None:
        try:
            from .core.cost_tracker import format_total_cost, save_current_session_costs

            sys.stdout.write("\n" + format_total_cost() + "\n")
            save_current_session_costs(get_fps_metrics() if get_fps_metrics else None)
        except Exception:
            pass

    atexit.register(_on_exit)


__all__ = ["register_cost_summary_on_exit"]
