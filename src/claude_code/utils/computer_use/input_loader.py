"""
Lazy loader for pyautogui-backed input (replaces @ant/computer-use-input).

Migrated from: utils/computerUse/inputLoader.ts
"""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Literal

import pyautogui

from .types import KeyPhase, MouseButton

if TYPE_CHECKING:
    pass

_cached_api: ComputerUseInputAPI | None = None

# Fail-safe: move mouse to corner aborts — disable for automation stability in tests via env.
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01


def _modifier_map(name: str) -> str:
    n = name.lower()
    if n in ("command", "cmd", "super"):
        return "command" if sys.platform == "darwin" else "win"
    if n == "ctrl" or n == "control":
        return "ctrl"
    if n in ("alt", "option"):
        return "alt"
    if n == "shift":
        return "shift"
    return name


class ComputerUseInputAPI:
    """Subset of the Node enigo API used by executor.ts, implemented with pyautogui."""

    @property
    def is_supported(self) -> bool:
        return True

    async def moveMouse(self, x: int, y: int, animated: bool) -> None:
        def _do() -> None:
            if animated:
                pyautogui.moveTo(x, y, duration=0.2)
            else:
                pyautogui.moveTo(x, y)

        await asyncio.to_thread(_do)

    async def mouseButton(
        self,
        button: MouseButton,
        action: KeyPhase | Literal["click"],
        count: int = 1,
    ) -> None:
        btn = {"left": "left", "right": "right", "middle": "middle"}[button]

        def _press() -> None:
            if action == "press":
                pyautogui.mouseDown(button=btn)
            elif action == "release":
                pyautogui.mouseUp(button=btn)
            else:
                pyautogui.click(button=btn, clicks=count)

        await asyncio.to_thread(_press)

    async def mouseScroll(self, amount: int, axis: Literal["vertical", "horizontal"]) -> None:
        def _do() -> None:
            if axis == "vertical":
                pyautogui.scroll(int(amount))
            else:
                if hasattr(pyautogui, "hscroll"):
                    pyautogui.hscroll(int(amount))
                else:
                    pyautogui.scroll(int(amount), x=0, y=0)

        await asyncio.to_thread(_do)

    async def key(self, name: str, phase: KeyPhase) -> None:
        k = _normalize_key(name)

        def _do() -> None:
            if phase == "press":
                pyautogui.keyDown(k)
            else:
                pyautogui.keyUp(k)

        await asyncio.to_thread(_do)

    async def keys(self, parts: list[str]) -> None:
        mapped = [_normalize_key(_modifier_map(p)) for p in parts]

        def _do() -> None:
            pyautogui.hotkey(*mapped)

        await asyncio.to_thread(_do)

    async def typeText(self, text: str) -> None:
        await asyncio.to_thread(pyautogui.typewrite, text, interval=0.01)

    async def mouseLocation(self) -> dict[str, int]:
        p = await asyncio.to_thread(pyautogui.position)
        return {"x": int(p.x), "y": int(p.y)}

    def getFrontmostAppInfo(self) -> dict[str, str] | None:
        if sys.platform != "darwin":
            return None
        try:
            import subprocess

            script = (
                'tell application "System Events" to get {name, bundle identifier} '
                "of first application process whose frontmost is true"
            )
            out = subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode != 0 or not out.stdout.strip():
                return None
            # osascript returns "AppName, com.bundle.id" or multiline
            raw = out.stdout.strip().split(", ")
            if len(raw) >= 2:
                return {"appName": raw[0], "bundleId": raw[-1]}
            return {"appName": raw[0], "bundleId": ""}
        except OSError:
            return None


def _normalize_key(name: str) -> str:
    n = name.lower()
    if n in ("escape", "esc"):
        return "esc"
    if n == "return" or n == "enter":
        return "enter"
    if n == "space":
        return "space"
    return _modifier_map(name)


def require_computer_use_input() -> ComputerUseInputAPI:
    global _cached_api
    if _cached_api is not None:
        return _cached_api
    _cached_api = ComputerUseInputAPI()
    return _cached_api
