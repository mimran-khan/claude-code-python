"""
CLI computer-use executor (pyautogui + Pillow + native shim).

Migrated from: utils/computerUse/executor.ts
"""

from __future__ import annotations

import asyncio
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from ..debug import log_for_debugging
from .common import CLI_HOST_BUNDLE_ID, get_cli_cu_capabilities, get_terminal_bundle_id
from .drain_run_loop import drain_run_loop
from .esc_hotkey import notify_expected_escape
from .input_loader import ComputerUseInputAPI, require_computer_use_input
from .swift_loader import require_computer_use_swift, target_image_size
from .types import (
    DisplayGeometry,
    FrontmostApp,
    InstalledApp,
    MouseButton,
    ResolvePrepareCaptureResult,
    RunningApp,
    ScreenshotResult,
)

SCREENSHOT_JPEG_QUALITY = 0.75
MOVE_SETTLE_MS = 0.05


def _compute_target_dims(logical_w: int, logical_h: int, scale_factor: float) -> tuple[int, int]:
    phys_w = max(1, int(round(logical_w * scale_factor)))
    phys_h = max(1, int(round(logical_h * scale_factor)))
    return target_image_size(phys_w, phys_h)


def _is_bare_escape(parts: list[str]) -> bool:
    if len(parts) != 1:
        return False
    lower = parts[0].lower()
    return lower in ("escape", "esc")


async def _read_clipboard_darwin() -> str:
    proc = await asyncio.create_subprocess_exec(
        "pbpaste",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        msg = f"pbpaste exited with code {proc.returncode}"
        raise RuntimeError(msg)
    return out.decode("utf-8", errors="replace")


async def _write_clipboard_darwin(text: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "pbcopy",
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate(input=text.encode("utf-8"))
    if proc.returncode != 0:
        msg = f"pbcopy exited with code {proc.returncode}"
        raise RuntimeError(msg)


async def _read_clipboard_cross_platform() -> str:
    if sys.platform == "darwin":
        return await _read_clipboard_darwin()
    if sys.platform == "win32":
        proc = await asyncio.create_subprocess_exec(
            "powershell",
            "-NoProfile",
            "-STA",
            "-Command",
            "Get-Clipboard -Raw",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, _ = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError("clipboard read failed")
        return out.decode("utf-8", errors="replace")
    proc = await asyncio.create_subprocess_exec(
        "xclip",
        "-selection",
        "clipboard",
        "-o",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError("xclip read failed")
    return out.decode("utf-8", errors="replace")


async def _write_clipboard_cross_platform(text: str) -> None:
    if sys.platform == "darwin":
        await _write_clipboard_darwin(text)
        return
    if sys.platform == "win32":
        proc = await asyncio.create_subprocess_exec(
            "clip",
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate(input=text.encode("utf-16le"))
        if proc.returncode != 0:
            raise RuntimeError("clipboard write failed")
        return
    proc = await asyncio.create_subprocess_exec(
        "xclip",
        "-selection",
        "clipboard",
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate(input=text.encode("utf-8"))
    if proc.returncode != 0:
        raise RuntimeError("xclip write failed")


async def _move_and_settle(inp: ComputerUseInputAPI, x: int, y: int) -> None:
    await inp.moveMouse(x, y, False)
    await asyncio.sleep(MOVE_SETTLE_MS)


async def _release_pressed(inp: ComputerUseInputAPI, pressed: list[str]) -> None:
    while pressed:
        k = pressed.pop()
        try:
            await inp.key(k, "release")
        except Exception:
            pass


async def _with_modifiers(
    inp: ComputerUseInputAPI,
    mods: list[str],
    fn: Any,
) -> Any:
    pressed: list[str] = []
    try:
        for m in mods:
            await inp.key(m, "press")
            pressed.append(m)
        return await fn()
    finally:
        await _release_pressed(inp, pressed)


async def _type_via_clipboard(inp: ComputerUseInputAPI, text: str) -> None:
    saved: str | None = None
    try:
        saved = await _read_clipboard_cross_platform()
    except Exception:
        log_for_debugging(
            "[computer-use] clipboard read before paste failed; proceeding without restore",
        )
    try:
        await _write_clipboard_cross_platform(text)
        if (await _read_clipboard_cross_platform()) != text:
            raise RuntimeError("Clipboard write did not round-trip.")
        await inp.keys(["command", "v"] if sys.platform == "darwin" else ["ctrl", "v"])
        await asyncio.sleep(0.1)
    finally:
        if isinstance(saved, str):
            try:
                await _write_clipboard_cross_platform(saved)
            except Exception:
                log_for_debugging("[computer-use] clipboard restore after paste failed")


async def _animated_move(
    inp: ComputerUseInputAPI,
    target_x: int,
    target_y: int,
    mouse_animation_enabled: bool,
) -> None:
    if not mouse_animation_enabled:
        await _move_and_settle(inp, target_x, target_y)
        return
    start = await inp.mouseLocation()
    sx, sy = start["x"], start["y"]
    delta_x = target_x - sx
    delta_y = target_y - sy
    distance = math.hypot(delta_x, delta_y)
    if distance < 1:
        return
    duration_sec = min(distance / 2000.0, 0.5)
    if duration_sec < 0.03:
        await _move_and_settle(inp, target_x, target_y)
        return
    frame_rate = 60
    frame_interval_ms = 1000.0 / frame_rate
    total_frames = int(duration_sec * frame_rate)
    for frame in range(1, total_frames + 1):
        t = frame / total_frames
        eased = 1 - (1 - t) ** 3
        await inp.moveMouse(
            int(round(sx + delta_x * eased)),
            int(round(sy + delta_y * eased)),
            False,
        )
        if frame < total_frames:
            await asyncio.sleep(frame_interval_ms / 1000.0)
    await asyncio.sleep(MOVE_SETTLE_MS)


@dataclass
class CliExecutorOptions:
    get_mouse_animation_enabled: Callable[[], bool]
    get_hide_before_action_enabled: Callable[[], bool]


def create_cli_executor(opts: CliExecutorOptions) -> Any:
    """
    Build the executor used by the computer-use MCP host adapter.

    Unlike the TS CLI (darwin + NAPI only), this port uses pyautogui on
    macOS, Windows, and Linux where a graphical session is available.
    """
    cu = require_computer_use_swift()
    terminal_bundle_id = get_terminal_bundle_id()
    surrogate_host = terminal_bundle_id or CLI_HOST_BUNDLE_ID

    def without_terminal(allowed: list[str]) -> list[str]:
        if terminal_bundle_id is None:
            return list(allowed)
        return [i for i in allowed if i != terminal_bundle_id]

    log_for_debugging(
        f"[computer-use] surrogate host={surrogate_host!r} terminal={terminal_bundle_id!r}",
    )

    caps = {**get_cli_cu_capabilities(), "hostBundleId": CLI_HOST_BUNDLE_ID}

    class _Executor:
        capabilities = caps

        async def prepareForAction(
            self,
            allowlist_bundle_ids: list[str],
            display_id: int | None = None,
        ) -> list[str]:
            if not opts.get_hide_before_action_enabled():
                return []
            try:

                async def _prep() -> list[str]:
                    r = await asyncio.to_thread(
                        cu.apps.prepareDisplay,
                        allowlist_bundle_ids,
                        surrogate_host,
                        display_id,
                    )
                    if isinstance(r, dict):
                        return list(r.get("hidden", []))
                    return []

                return await drain_run_loop(_prep)
            except Exception as e:
                log_for_debugging(
                    f"[computer-use] prepareForAction failed; continuing: {e}",
                    level="warn",
                )
                return []

        async def previewHideSet(
            self,
            allowlist_bundle_ids: list[str],
            display_id: int | None = None,
        ) -> list[dict[str, str]]:
            return await asyncio.to_thread(
                cu.apps.previewHideSet,
                [*allowlist_bundle_ids, surrogate_host],
                display_id,
            )

        async def getDisplaySize(self, display_id: int | None = None) -> DisplayGeometry:
            return await asyncio.to_thread(cu.display.get_size, display_id)

        async def listDisplays(self) -> list[DisplayGeometry]:
            return await asyncio.to_thread(cu.display.list_all)

        async def findWindowDisplays(self, bundle_ids: list[str]) -> list[dict[str, Any]]:
            return await asyncio.to_thread(cu.apps.findWindowDisplays, bundle_ids)

        async def resolvePrepareCapture(self, opts2: dict[str, Any]) -> ResolvePrepareCaptureResult:
            d = await asyncio.to_thread(cu.display.get_size, opts2.get("preferredDisplayId"))
            tw, th = _compute_target_dims(d["width"], d["height"], d["scaleFactor"])

            def _call() -> dict[str, Any]:
                return cu.resolve_prepare_capture(
                    without_terminal(list(opts2["allowedBundleIds"])),
                    surrogate_host,
                    SCREENSHOT_JPEG_QUALITY,
                    tw,
                    th,
                    opts2.get("preferredDisplayId"),
                    opts2["autoResolve"],
                    opts2.get("doHide"),
                )

            raw = await drain_run_loop(lambda: asyncio.to_thread(_call))
            return raw  # type: ignore[return-value]

        async def screenshot(self, opts2: dict[str, Any]) -> ScreenshotResult:
            d = await asyncio.to_thread(cu.display.get_size, opts2.get("displayId"))
            tw, th = _compute_target_dims(d["width"], d["height"], d["scaleFactor"])

            def _cap() -> ScreenshotResult:
                return cu.screenshot.captureExcluding(
                    without_terminal(list(opts2["allowedBundleIds"])),
                    SCREENSHOT_JPEG_QUALITY,
                    tw,
                    th,
                    opts2.get("displayId"),
                )

            return await drain_run_loop(lambda: asyncio.to_thread(_cap))

        async def zoom(
            self,
            region_logical: dict[str, int],
            allowed_bundle_ids: list[str],
            display_id: int | None = None,
        ) -> dict[str, Any]:
            d = await asyncio.to_thread(cu.display.get_size, display_id)
            tw, th = _compute_target_dims(region_logical["w"], region_logical["h"], d["scaleFactor"])

            def _z() -> dict[str, Any]:
                return cu.screenshot.captureRegion(
                    without_terminal(allowed_bundle_ids),
                    region_logical["x"],
                    region_logical["y"],
                    region_logical["w"],
                    region_logical["h"],
                    tw,
                    th,
                    SCREENSHOT_JPEG_QUALITY,
                    display_id,
                )

            return await drain_run_loop(lambda: asyncio.to_thread(_z))

        async def key(self, key_sequence: str, repeat: int | None = None) -> None:
            inp = require_computer_use_input()
            parts = [p for p in key_sequence.split("+") if p]
            is_esc = _is_bare_escape(parts)
            n = repeat or 1

            async def _once() -> None:
                for i in range(n):
                    if i > 0:
                        await asyncio.sleep(0.008)
                    if is_esc:
                        notify_expected_escape()
                    await inp.keys(parts)

            await drain_run_loop(_once)

        async def holdKey(self, key_names: list[str], duration_ms: int) -> None:
            inp = require_computer_use_input()
            pressed: list[str] = []
            orphaned = False

            async def _press_phase() -> None:
                nonlocal orphaned
                for k in key_names:
                    if orphaned:
                        return
                    if _is_bare_escape([k]):
                        notify_expected_escape()
                    await inp.key(k, "press")
                    pressed.append(k)

            try:
                await drain_run_loop(_press_phase)
                await asyncio.sleep(duration_ms / 1000.0)
            finally:
                orphaned = True

                async def _release_all() -> None:
                    await _release_pressed(inp, pressed)

                await drain_run_loop(_release_all)

        async def type(self, text: str, opts2: dict[str, bool]) -> None:
            inp = require_computer_use_input()
            if opts2.get("viaClipboard"):
                await drain_run_loop(lambda: _type_via_clipboard(inp, text))
                return
            await inp.typeText(text)

        async def readClipboard(self) -> str:
            return await _read_clipboard_cross_platform()

        async def writeClipboard(self, text: str) -> None:
            await _write_clipboard_cross_platform(text)

        async def moveMouse(self, x: int, y: int) -> None:
            await _move_and_settle(require_computer_use_input(), x, y)

        async def click(
            self,
            x: int,
            y: int,
            button: MouseButton,
            count: Literal[1, 2, 3],
            modifiers: list[str] | None = None,
        ) -> None:
            inp = require_computer_use_input()
            await _move_and_settle(inp, x, y)
            if modifiers:
                await drain_run_loop(
                    lambda: _with_modifiers(
                        inp,
                        modifiers,
                        lambda: inp.mouseButton(button, "click", count),
                    ),
                )
            else:
                await inp.mouseButton(button, "click", count)

        async def mouseDown(self) -> None:
            await require_computer_use_input().mouseButton("left", "press")

        async def mouseUp(self) -> None:
            await require_computer_use_input().mouseButton("left", "release")

        async def getCursorPosition(self) -> dict[str, int]:
            return await require_computer_use_input().mouseLocation()

        async def drag(self, from_pos: dict[str, int] | None, to: dict[str, int]) -> None:
            inp = require_computer_use_input()
            if from_pos is not None:
                await _move_and_settle(inp, from_pos["x"], from_pos["y"])
            await inp.mouseButton("left", "press")
            await asyncio.sleep(MOVE_SETTLE_MS)
            try:
                await _animated_move(
                    inp,
                    to["x"],
                    to["y"],
                    opts.get_mouse_animation_enabled(),
                )
            finally:
                await inp.mouseButton("left", "release")

        async def scroll(self, x: int, y: int, dx: int, dy: int) -> None:
            inp = require_computer_use_input()
            await _move_and_settle(inp, x, y)
            if dy != 0:
                await inp.mouseScroll(dy, "vertical")
            if dx != 0:
                await inp.mouseScroll(dx, "horizontal")

        async def getFrontmostApp(self) -> FrontmostApp | None:
            info = require_computer_use_input().getFrontmostAppInfo()
            if not info or not info.get("bundleId"):
                return None
            return FrontmostApp(bundleId=info["bundleId"], displayName=info.get("appName", ""))

        async def appUnderPoint(self, x: int, y: int) -> dict[str, str] | None:
            return await asyncio.to_thread(cu.apps.appUnderPoint, x, y)

        async def listInstalledApps(self) -> list[InstalledApp]:
            return await drain_run_loop(lambda: asyncio.to_thread(cu.apps.listInstalled))

        async def getAppIcon(self, path: str) -> str | None:
            return await asyncio.to_thread(cu.apps.iconDataUrl, path)

        async def listRunningApps(self) -> list[RunningApp]:
            return await asyncio.to_thread(cu.apps.listRunning)

        async def openApp(self, bundle_id: str) -> None:
            await asyncio.to_thread(cu.apps.open, bundle_id)

    return _Executor()


async def unhide_computer_use_apps(bundle_ids: list[str]) -> None:
    if not bundle_ids:
        return
    cu = require_computer_use_swift()
    await asyncio.to_thread(cu.apps.unhide, list(bundle_ids))
