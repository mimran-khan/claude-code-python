"""
Typed shapes for computer-use (aligned with @ant/computer-use-mcp contracts).

Migrated from implicit TypeScript types in utils/computerUse/*.ts
"""

from __future__ import annotations

from typing import Any, Literal, Protocol, TypedDict

CoordinateMode = Literal["pixels", "normalized"]
MouseButton = Literal["left", "right", "middle"]
KeyPhase = Literal["press", "release", "click"]


class DisplayGeometry(TypedDict):
    width: int
    height: int
    scaleFactor: float


class FrontmostApp(TypedDict):
    bundleId: str
    displayName: str


class InstalledApp(TypedDict, total=False):
    bundleId: str
    displayName: str
    path: str
    iconDataUrl: str


class RunningApp(TypedDict, total=False):
    bundleId: str
    displayName: str
    pid: int


class ScreenshotResult(TypedDict):
    base64: str
    width: int
    height: int


class ResolvePrepareCaptureResult(TypedDict, total=False):
    displayId: int
    jpegBase64: str
    width: int
    height: int


class Logger(Protocol):
    def silly(self, message: str, *args: object) -> None: ...
    def debug(self, message: str, *args: object) -> None: ...
    def info(self, message: str, *args: object) -> None: ...
    def warn(self, message: str, *args: object) -> None: ...
    def error(self, message: str, *args: object) -> None: ...


class ComputerExecutor(Protocol):
    capabilities: dict[str, Any]

    async def prepareForAction(self, allowlist_bundle_ids: list[str], display_id: int | None = None) -> list[str]: ...

    async def previewHideSet(
        self, allowlist_bundle_ids: list[str], display_id: int | None = None
    ) -> list[dict[str, str]]: ...

    async def getDisplaySize(self, display_id: int | None = None) -> DisplayGeometry: ...
    async def listDisplays(self) -> list[DisplayGeometry]: ...
    async def findWindowDisplays(self, bundle_ids: list[str]) -> list[dict[str, Any]]: ...

    async def resolvePrepareCapture(self, opts: dict[str, Any]) -> ResolvePrepareCaptureResult: ...
    async def screenshot(self, opts: dict[str, Any]) -> ScreenshotResult: ...
    async def zoom(
        self,
        region_logical: dict[str, int],
        allowed_bundle_ids: list[str],
        display_id: int | None = None,
    ) -> dict[str, Any]: ...

    async def key(self, key_sequence: str, repeat: int | None = None) -> None: ...
    async def holdKey(self, key_names: list[str], duration_ms: int) -> None: ...
    async def type(self, text: str, opts: dict[str, bool]) -> None: ...

    async def readClipboard(self) -> str: ...
    async def writeClipboard(self, text: str) -> None: ...

    async def moveMouse(self, x: int, y: int) -> None: ...
    async def click(
        self,
        x: int,
        y: int,
        button: MouseButton,
        count: Literal[1, 2, 3],
        modifiers: list[str] | None = None,
    ) -> None: ...
    async def mouseDown(self) -> None: ...
    async def mouseUp(self) -> None: ...
    async def getCursorPosition(self) -> dict[str, int]: ...
    async def drag(self, from_pos: dict[str, int] | None, to: dict[str, int]) -> None: ...
    async def scroll(self, x: int, y: int, dx: int, dy: int) -> None: ...

    async def getFrontmostApp(self) -> FrontmostApp | None: ...
    async def appUnderPoint(self, x: int, y: int) -> dict[str, str] | None: ...
    async def listInstalledApps(self) -> list[InstalledApp]: ...
    async def getAppIcon(self, path: str) -> str | None: ...
    async def listRunningApps(self) -> list[RunningApp]: ...
    async def openApp(self, bundle_id: str) -> None: ...


class ComputerUseHostAdapter(Protocol):
    serverName: str
    logger: Logger
    executor: ComputerExecutor

    async def ensureOsPermissions(self) -> dict[str, Any]: ...
    def isDisabled(self) -> bool: ...
    def getSubGates(self) -> Any: ...
    def getAutoUnhideEnabled(self) -> bool: ...
    def cropRawPatch(self, *args: Any, **kwargs: Any) -> Any: ...
