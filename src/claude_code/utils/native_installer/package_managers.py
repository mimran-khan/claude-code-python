"""
Package manager heuristics (``utils/nativeInstaller/packageManagers.ts``).
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from typing import Literal

from ..debug import log_for_debugging
from ..platform import get_platform

PackageManager = Literal[
    "homebrew",
    "winget",
    "pacman",
    "deb",
    "rpm",
    "apk",
    "mise",
    "asdf",
    "unknown",
]


def _exec_path() -> str:
    return sys.executable or (sys.argv[0] if sys.argv else "")


async def get_os_release() -> dict[str, object] | None:
    def _read() -> dict[str, object] | None:
        try:
            content = Path("/etc/os-release").read_text(encoding="utf-8")
        except OSError:
            return None
        id_match = re.search(r'^ID=["\']?(\S+?)["\']?\s*$', content, re.MULTILINE)
        id_like_match = re.search(r'^ID_LIKE=["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        id_val = id_match.group(1) if id_match else ""
        likes = id_like_match.group(1).split() if id_like_match else []
        return {"id": id_val, "idLike": likes}

    return await asyncio.to_thread(_read)


def _is_distro_family(os_release: dict[str, object], families: list[str]) -> bool:
    oid = str(os_release.get("id", ""))
    id_like = os_release.get("idLike")
    likes = id_like if isinstance(id_like, list) else []
    if oid in families:
        return True
    return any(str(x) in families for x in likes)


def detect_mise() -> bool:
    p = _exec_path()
    if re.search(r"[/\\]mise[/\\]installs[/\\]", p, re.IGNORECASE):
        log_for_debugging(f"Detected mise installation: {p}")
        return True
    return False


def detect_asdf() -> bool:
    p = _exec_path()
    if re.search(r"[/\\]\.?asdf[/\\]installs[/\\]", p, re.IGNORECASE):
        log_for_debugging(f"Detected asdf installation: {p}")
        return True
    return False


def detect_homebrew() -> bool:
    plat = get_platform()
    if plat not in ("macos", "linux", "wsl"):
        return False
    p = _exec_path()
    if "/Caskroom/" in p:
        log_for_debugging(f"Detected Homebrew cask installation: {p}")
        return True
    return False


def detect_winget() -> bool:
    if get_platform() != "windows":
        return False
    p = _exec_path()
    if re.search(r"Microsoft[/\\]WinGet[/\\](Packages|Links)", p, re.IGNORECASE):
        log_for_debugging(f"Detected winget installation: {p}")
        return True
    return False


async def _run_cmd(argv: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        return 124, "", "timeout"
    code = proc.returncode if proc.returncode is not None else 1
    return code, out_b.decode(errors="replace"), err_b.decode(errors="replace")


async def detect_pacman() -> bool:
    if get_platform() != "linux":
        return False
    rel = await get_os_release()
    if rel and not _is_distro_family(rel, ["arch"]):
        return False
    code, out, _ = await _run_cmd(["pacman", "-Qo", _exec_path()])
    if code == 0 and out.strip():
        log_for_debugging(f"Detected pacman installation: {out.strip()}")
        return True
    return False


async def detect_deb() -> bool:
    if get_platform() != "linux":
        return False
    rel = await get_os_release()
    if rel and not _is_distro_family(rel, ["debian"]):
        return False
    code, out, _ = await _run_cmd(["dpkg", "-S", _exec_path()])
    if code == 0 and out.strip():
        log_for_debugging(f"Detected deb installation: {out.strip()}")
        return True
    return False


async def detect_rpm() -> bool:
    if get_platform() != "linux":
        return False
    rel = await get_os_release()
    if rel and not _is_distro_family(rel, ["fedora", "rhel", "suse"]):
        return False
    code, out, _ = await _run_cmd(["rpm", "-qf", _exec_path()])
    if code == 0 and out.strip():
        log_for_debugging(f"Detected rpm installation: {out.strip()}")
        return True
    return False


async def detect_apk() -> bool:
    if get_platform() != "linux":
        return False
    rel = await get_os_release()
    if rel and not _is_distro_family(rel, ["alpine"]):
        return False
    code, out, _ = await _run_cmd(["apk", "info", "--who-owns", _exec_path()])
    if code == 0 and out.strip():
        log_for_debugging(f"Detected apk installation: {out.strip()}")
        return True
    return False


async def get_package_manager() -> PackageManager:
    if detect_homebrew():
        return "homebrew"
    if detect_winget():
        return "winget"
    if detect_mise():
        return "mise"
    if detect_asdf():
        return "asdf"
    if await detect_pacman():
        return "pacman"
    if await detect_apk():
        return "apk"
    if await detect_deb():
        return "deb"
    if await detect_rpm():
        return "rpm"
    return "unknown"
