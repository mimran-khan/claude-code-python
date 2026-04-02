"""
Double-press Ctrl+C / Ctrl+D to exit (global interrupt path).

Migrated from: hooks/useExitOnCtrlCD.ts and hooks/useExitOnCtrlCDWithKeybindings.ts
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .double_press import DoublePressController


@dataclass
class ExitState:
    pending: bool = False
    key_name: str | None = None


@dataclass
class ExitOnCtrlCdController:
    exit_fn: Callable[[], None] | Callable[[], Awaitable[None]]
    on_interrupt: Callable[[], bool] | None = None
    state: ExitState = field(default_factory=ExitState)
    _ctrl_c: DoublePressController | None = field(default=None, repr=False)
    _ctrl_d: DoublePressController | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._ctrl_c = DoublePressController(
            on_double_press=self.exit_fn,
            set_pending=self._set_pending_c,
        )
        self._ctrl_d = DoublePressController(
            on_double_press=self.exit_fn,
            set_pending=self._set_pending_d,
        )

    def _set_pending_c(self, pending: bool) -> None:
        self.state.pending = pending
        self.state.key_name = "Ctrl-C" if pending else None

    def _set_pending_d(self, pending: bool) -> None:
        self.state.pending = pending
        self.state.key_name = "Ctrl-D" if pending else None

    async def handle_interrupt(self) -> None:
        if self.on_interrupt is not None and self.on_interrupt():
            return
        assert self._ctrl_c is not None
        await self._ctrl_c.press()

    async def handle_exit(self) -> None:
        assert self._ctrl_d is not None
        await self._ctrl_d.press()
