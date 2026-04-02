"""
Cron scheduler session wiring (headless / REPL orchestration).

Migrated from: hooks/useScheduledTasks.ts (lifecycle + fire-time formatting;
scheduler I/O is injected via callables).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class CronSchedulerLike(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ScheduledTasksSession:
    """Started scheduler; call :meth:`stop` on teardown."""

    scheduler: CronSchedulerLike

    def stop(self) -> None:
        self.scheduler.stop()


def format_cron_fire_time(d: datetime) -> str:
    """
    Human-readable fire time similar to ``useScheduledTasks`` (en-US compact).

    Example shape: ``Apr 2 3:45pm``.
    """
    hour12 = d.hour % 12 or 12
    ampm = "am" if d.hour < 12 else "pm"
    month = d.strftime("%b")
    return f"{month} {d.day} {hour12}:{d.strftime('%M')}{ampm}"


def start_scheduled_tasks_session(
    *,
    is_cron_enabled: Callable[[], bool],
    create_scheduler: Callable[[], CronSchedulerLike],
) -> ScheduledTasksSession | None:
    """
    If cron is enabled, start the scheduler and return a handle.

    The TypeScript hook always mounts; the runtime gate lives inside the
    effect. Callers should pass ``is_cron_enabled`` that reads current config.
    """
    if not is_cron_enabled():
        return None
    scheduler = create_scheduler()
    scheduler.start()
    return ScheduledTasksSession(scheduler=scheduler)
