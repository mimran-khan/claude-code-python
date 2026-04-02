"""
Native desktop integration shim (replaces @ant/computer-use-swift).

Screenshots and app enumeration use Pillow + pyautogui and platform-specific
helpers. There is no Objective-C runtime bridge in the Python port.

Migrated from: utils/computerUse/swiftLoader.ts
"""

from __future__ import annotations

import base64
import io
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageGrab

from ..debug import log_for_debugging
from .types import DisplayGeometry, InstalledApp, RunningApp, ScreenshotResult

_cached: ComputerUseNativeAPI | None = None


def target_image_size(
    width: int,
    height: int,
    *,
    max_long_side: int = 1568,
    max_pixels: int = 1_199_808,
) -> tuple[int, int]:
    """Scale dimensions down like API_RESIZE_PARAMS / targetImageSize in TS."""
    if width <= 0 or height <= 0:
        return 1, 1
    area = width * height
    scale = min(1.0, max_long_side / max(width, height), (max_pixels / max(area, 1)) ** 0.5)
    nw = max(1, int(width * scale))
    nh = max(1, int(height * scale))
    return nw, nh


def _jpeg_b64(img: Image.Image, quality: int = 75) -> tuple[str, int, int]:
    buf = io.BytesIO()
    rgb = img.convert("RGB")
    rgb.save(buf, format="JPEG", quality=quality, optimize=True)
    raw = buf.getvalue()
    return base64.standard_b64encode(raw).decode("ascii"), rgb.width, rgb.height


@dataclass
class _DisplayAPI:
    def get_size(self, display_id: int | None = None) -> DisplayGeometry:
        _ = display_id
        try:
            import pyautogui

            w, h = pyautogui.size()
            return DisplayGeometry(width=int(w), height=int(h), scaleFactor=1.0)
        except Exception:
            return DisplayGeometry(width=1920, height=1080, scaleFactor=1.0)

    def list_all(self) -> list[DisplayGeometry]:
        return [self.get_size(None)]


@dataclass
class _TccAPI:
    def checkAccessibility(self) -> bool:
        if sys.platform != "darwin":
            return True
        # True-positive stub: real check needs platform APIs; assume granted when GUI present.
        return True

    def checkScreenRecording(self) -> bool:
        if sys.platform != "darwin":
            return True
        return True


@dataclass
class _HotkeyAPI:
    _on_escape: Any = field(default=None, repr=False)

    def registerEscape(self, on_escape: Any) -> bool:
        """No CGEventTap in Python port; accept registration so pump lifecycle matches TS."""
        self._on_escape = on_escape
        return True

    def unregister(self) -> None:
        self._on_escape = None

    def notifyExpectedEscape(self) -> None:
        return None


@dataclass
class _AppsAPI:
    surrogate_host: str = ""

    def prepareDisplay(
        self,
        _allowlist: list[str],
        _surrogate_host: str,
        _display_id: int | None = None,
    ) -> dict[str, Any]:
        return {"hidden": [], "activated": None}

    def previewHideSet(
        self,
        _bundle_ids: list[str],
        _display_id: int | None = None,
    ) -> list[dict[str, str]]:
        return []

    def findWindowDisplays(self, _bundle_ids: list[str]) -> list[dict[str, Any]]:
        return []

    def appUnderPoint(self, _x: int, _y: int) -> dict[str, str] | None:
        return None

    def listInstalled(self) -> list[InstalledApp]:
        if sys.platform == "darwin":
            return _list_installed_macos()
        if sys.platform == "win32":
            return _list_installed_windows_stub()
        return _list_installed_linux_stub()

    def iconDataUrl(self, _path: str) -> str | None:
        return None

    def listRunning(self) -> list[RunningApp]:
        if sys.platform != "darwin":
            return []
        try:
            script = (
                'tell application "System Events" to get the {name, bundle identifier} '
                "of every application process whose background only is false"
            )
            out = subprocess.run(
                ["osascript", "-e", script],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if out.returncode != 0:
                return []
            return _parse_running_apps(out.stdout)
        except OSError:
            return []

    def open(self, bundle_id: str) -> None:
        if sys.platform == "darwin":
            subprocess.run(["open", "-b", bundle_id], check=False, capture_output=True)
        elif sys.platform == "win32":
            subprocess.run(["cmd", "/c", "start", "", bundle_id], check=False, capture_output=True)

    def unhide(self, _bundle_ids: list[str]) -> None:
        log_for_debugging(f"[computer-use] unhide stub for {_bundle_ids!r}")


@dataclass
class _ScreenshotAPI:
    def captureExcluding(
        self,
        _allowed_bundle_ids: list[str],
        jpeg_quality: float,
        target_w: int,
        target_h: int,
        display_id: int | None = None,
    ) -> ScreenshotResult:
        _ = display_id
        img = ImageGrab.grab(all_screens=True)
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        q = max(1, min(95, int(jpeg_quality * 100) if jpeg_quality <= 1 else int(jpeg_quality)))
        b64, w, h = _jpeg_b64(img, quality=q)
        return ScreenshotResult(base64=b64, width=w, height=h)

    def captureRegion(
        self,
        _allowed_bundle_ids: list[str],
        x: int,
        y: int,
        w: int,
        h: int,
        out_w: int,
        out_h: int,
        jpeg_quality: float,
        display_id: int | None = None,
    ) -> dict[str, Any]:
        _ = display_id
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
        img = img.resize((out_w, out_h), Image.Resampling.LANCZOS)
        q = max(1, min(95, int(jpeg_quality * 100) if jpeg_quality <= 1 else int(jpeg_quality)))
        b64, ow, oh = _jpeg_b64(img, quality=q)
        return {"base64": b64, "width": ow, "height": oh}


@dataclass
class ComputerUseNativeAPI:
    display: _DisplayAPI = field(default_factory=_DisplayAPI)
    apps: _AppsAPI = field(default_factory=_AppsAPI)
    screenshot: _ScreenshotAPI = field(default_factory=_ScreenshotAPI)
    tcc: _TccAPI = field(default_factory=_TccAPI)
    hotkey: _HotkeyAPI = field(default_factory=_HotkeyAPI)

    def _drain_main_run_loop(self) -> None:
        return None

    def resolve_prepare_capture(
        self,
        allowed_bundle_ids: list[str],
        surrogate_host: str,
        jpeg_quality: float,
        target_w: int,
        target_h: int,
        preferred_display_id: int | None,
        auto_resolve: bool,
        do_hide: bool | None,
    ) -> dict[str, Any]:
        _ = surrogate_host, auto_resolve, do_hide
        d = self.display.get_size(preferred_display_id)
        return {
            "displayId": preferred_display_id or 0,
            **self.screenshot.captureExcluding(
                allowed_bundle_ids,
                jpeg_quality,
                target_w,
                target_h,
                preferred_display_id,
            ),
            "logicalWidth": d["width"],
            "logicalHeight": d["height"],
        }


def require_computer_use_swift() -> ComputerUseNativeAPI:
    global _cached
    if _cached is not None:
        return _cached
    _cached = ComputerUseNativeAPI()
    return _cached


def _parse_running_apps(stdout: str) -> list[RunningApp]:
    # osascript may return comma-separated pairs; heuristic parse
    text = stdout.strip()
    if not text:
        return []
    parts = [p.strip() for p in text.split(", ")]
    out: list[RunningApp] = []
    i = 0
    while i + 1 < len(parts):
        name, bid = parts[i], parts[i + 1]
        if bid.startswith("com.") or bid.startswith("org.") or "." in bid:
            out.append({"displayName": name, "bundleId": bid})
            i += 2
        else:
            i += 1
    return out


def _list_installed_macos() -> list[InstalledApp]:
    try:
        proc = subprocess.run(
            [
                "mdfind",
                "kMDItemContentType == 'com.apple.application-bundle'",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return []
        apps: list[InstalledApp] = []
        for line in proc.stdout.splitlines():
            path = line.strip()
            if not path.endswith(".app"):
                continue
            name = path.rsplit("/", 1)[-1].replace(".app", "")
            bid = _bundle_id_for_app_path(path) or ""
            apps.append({"bundleId": bid, "displayName": name or bid or path, "path": path})
            if len(apps) >= 400:
                break
        return apps
    except (OSError, subprocess.TimeoutExpired):
        return []


def _bundle_id_for_app_path(path: str) -> str | None:
    try:
        plist = subprocess.run(
            ["defaults", "read", f"{path}/Contents/Info", "CFBundleIdentifier"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if plist.returncode == 0:
            return plist.stdout.strip()
    except OSError:
        pass
    return None


def _list_installed_windows_stub() -> list[InstalledApp]:
    return []


def _list_installed_linux_stub() -> list[InstalledApp]:
    apps: list[InstalledApp] = []
    for root in ("/usr/share/applications", "/var/lib/snapd/desktop/applications"):
        try:
            for p in Path(root).glob("*.desktop"):
                data = p.read_text(encoding="utf-8", errors="ignore")
                name = ""
                for line in data.splitlines():
                    if line.startswith("Name=") and not name:
                        name = line[5:].strip()
                apps.append(
                    {
                        "bundleId": p.stem,
                        "displayName": name or p.stem,
                        "path": str(p),
                    }
                )
                if len(apps) >= 200:
                    return apps
        except OSError:
            continue
    return apps
