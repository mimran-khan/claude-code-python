"""
Native installer orchestration (subset of ``utils/nativeInstaller/installer.ts``).

Full npm/GCS install parity is deferred; PATH / symlink checks and PID locks match
the TypeScript behavior where dependencies exist in this port.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ...config.config import get_global_config
from ..debug import log_for_debugging
from ..env_utils import is_env_truthy
from ..errors import is_enoent
from .download import get_latest_version
from .pid_lock import (
    acquire_process_lifetime_lock,
    cleanup_stale_locks,
    is_pid_based_locking_enabled,
)

VERSION_RETENTION_COUNT = 2


@dataclass
class SetupMessage:
    message: str
    user_action_required: bool
    type: Literal["path", "alias", "info", "error"]


@dataclass
class InstallLatestResult:
    latest_version: str | None
    was_updated: bool
    lock_failed: bool = False
    lock_holder_pid: int | None = None


def _xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))


def _xdg_cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))


def _xdg_state_home() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))


def _user_bin_dir() -> Path:
    return Path.home() / ".local" / "bin"


def get_installer_platform_string() -> str:
    """Triplet like ``linux-x64`` / ``macos-arm64`` (mirrors TS ``getPlatform`` in installer)."""
    mapping = {"darwin": "macos", "win32": "win32", "linux": "linux"}
    sysname = mapping.get(sys.platform, "linux")
    machine = __import__("platform").machine().lower()
    arch = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(machine)
    if not arch:
        raise RuntimeError(f"Unsupported architecture: {machine}")
    if sysname == "linux" and os.environ.get("CLAUDE_CODE_FORCE_MUSL"):
        return f"linux-{arch}-musl"
    return f"{sysname}-{arch}"


def get_binary_name(platform_str: str) -> str:
    return "claude.exe" if platform_str.startswith("win32") else "claude"


def get_base_directories() -> dict[str, Path]:
    plat = get_installer_platform_string()
    exe_name = get_binary_name(plat)
    return {
        "versions": _xdg_data_home() / "claude" / "versions",
        "staging": _xdg_cache_home() / "claude" / "staging",
        "locks": _xdg_state_home() / "claude" / "locks",
        "executable": _user_bin_dir() / exe_name,
    }


async def _is_possible_claude_binary(file_path: Path) -> bool:
    def _check() -> bool:
        try:
            st = file_path.stat()
            if not file_path.is_file() or st.st_size == 0:
                return False
            return os.access(file_path, os.X_OK)
        except OSError:
            return False

    return await asyncio.to_thread(_check)


def _installation_type() -> str:
    """Rough analogue of ``getCurrentInstallationType`` — extend when doctor migrates."""
    if os.environ.get("CLAUDE_CODE_DEV_BUILD"):
        return "development"
    cfg = get_global_config()
    if cfg.install_method == "native":
        return "native"
    return "unknown"


async def check_install(force: bool = False) -> list[SetupMessage]:
    if is_env_truthy(os.environ.get("DISABLE_INSTALLATION_CHECKS")):
        return []
    if _installation_type() == "development":
        return []
    cfg = get_global_config()
    should_check = force or _installation_type() == "native" or cfg.install_method == "native"
    if not should_check:
        return []

    dirs = get_base_directories()
    messages: list[SetupMessage] = []
    local_bin = dirs["executable"].parent
    resolved_local = local_bin.resolve()
    plat = get_installer_platform_string()
    is_windows = plat.startswith("win32")
    path_sep = os.pathsep

    if not local_bin.exists():
        messages.append(
            SetupMessage(
                message=f"installMethod is native, but directory {local_bin} does not exist",
                user_action_required=True,
                type="error",
            )
        )

    exe = dirs["executable"]
    if is_windows:
        if not await _is_possible_claude_binary(exe):
            messages.append(
                SetupMessage(
                    message=(f"installMethod is native, but claude command is missing or invalid at {exe}"),
                    user_action_required=True,
                    type="error",
                )
            )
    else:
        try:
            target = await asyncio.to_thread(Path(exe).readlink)
            abs_target = (exe.parent / target).resolve()
            if not await _is_possible_claude_binary(abs_target):
                messages.append(
                    SetupMessage(
                        message=f"Claude symlink points to missing or invalid binary: {target}",
                        user_action_required=True,
                        type="error",
                    )
                )
        except OSError as e:
            if is_enoent(e):
                messages.append(
                    SetupMessage(
                        message=f"installMethod is native, but claude command not found at {exe}",
                        user_action_required=True,
                        type="error",
                    )
                )
            elif not await _is_possible_claude_binary(exe):
                messages.append(
                    SetupMessage(
                        message=f"{exe} exists but is not a valid Claude binary",
                        user_action_required=True,
                        type="error",
                    )
                )

    path_entries = os.environ.get("PATH", "").split(path_sep)
    in_path = False
    for entry in path_entries:
        try:
            resolved_entry = Path(entry).expanduser().resolve()
            if is_windows:
                in_path = resolved_entry.as_posix().lower() == resolved_local.as_posix().lower()
            else:
                in_path = resolved_entry == resolved_local
            if in_path:
                break
        except OSError:
            continue

    if not in_path:
        if is_windows:
            win_path = str(local_bin).replace("/", "\\")
            messages.append(
                SetupMessage(
                    message=(
                        f"Native installation exists but {win_path} is not in your PATH. "
                        "Add it via System Properties → Environment Variables → User PATH."
                    ),
                    user_action_required=True,
                    type="path",
                )
            )
        else:
            shell_hint = "~/.zshrc"
            messages.append(
                SetupMessage(
                    message=(
                        "Native installation exists but ~/.local/bin is not in your PATH. "
                        f"Run: echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> {shell_hint} "
                        f"&& source {shell_hint}"
                    ),
                    user_action_required=True,
                    type="path",
                )
            )

    return messages


_inflight_install: asyncio.Task[InstallLatestResult] | None = None


async def install_latest(channel_or_version: str, force_reinstall: bool = False) -> InstallLatestResult:
    global _inflight_install

    async def _impl() -> InstallLatestResult:
        try:
            ver = await get_latest_version(channel_or_version)
        except Exception as e:
            log_for_debugging(f"install_latest: version resolution failed: {e}")
            return InstallLatestResult(latest_version=None, was_updated=False)
        log_for_debugging(
            f"install_latest: resolved {ver} (full binary install not implemented in Python port)",
        )
        return InstallLatestResult(latest_version=ver, was_updated=False)

    if force_reinstall:
        return await _impl()
    if _inflight_install and not _inflight_install.done():
        log_for_debugging("install_latest: joining in-flight call")
        return await _inflight_install
    _inflight_install = asyncio.get_running_loop().create_task(_impl())

    def _clear(_t: asyncio.Task[InstallLatestResult]) -> None:
        global _inflight_install
        _inflight_install = None

    _inflight_install.add_done_callback(_clear)
    return await _inflight_install


async def lock_current_version() -> None:
    dirs = get_base_directories()
    versions_dir = dirs["versions"]
    exec_path = Path(sys.executable).resolve()
    try:
        exec_str = str(exec_path)
    except OSError:
        return
    if str(versions_dir) not in exec_str:
        return
    await dirs["locks"].mkdir(parents=True, exist_ok=True)
    lock_path = dirs["locks"] / f"{exec_path.name}.lock"
    if is_pid_based_locking_enabled():
        await acquire_process_lifetime_lock(str(exec_path), str(lock_path))


async def cleanup_old_versions() -> None:
    cleanup_stale_locks(str(get_base_directories()["locks"]))
    log_for_debugging("cleanup_old_versions: stale PID locks cleared; version GC not ported")


async def remove_installed_symlink() -> None:
    log_for_debugging("remove_installed_symlink: no-op in Python port")


async def cleanup_shell_aliases() -> list[SetupMessage]:
    return []


async def cleanup_npm_installations() -> dict[str, object]:
    return {"removed": [], "errors": []}
