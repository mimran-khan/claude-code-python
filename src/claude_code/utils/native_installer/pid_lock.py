"""
PID-based version locking (``utils/nativeInstaller/pidLock.ts``).
"""

from __future__ import annotations

import atexit
import contextlib
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..debug import log_for_debugging
from ..env_utils import is_env_defined_falsy, is_env_truthy
from ..errors import is_enoent, to_error
from ..log import log_error


def is_pid_based_locking_enabled() -> bool:
    env_var = os.environ.get("ENABLE_PID_BASED_VERSION_LOCKING")
    if is_env_truthy(env_var):
        return True
    if is_env_defined_falsy(env_var):
        return False
    # GrowthBook gate ``tengu_pid_based_version_locking`` — external builds default off.
    return False


@dataclass
class VersionLockContent:
    pid: int
    version: str
    exec_path: str
    acquired_at: int


@dataclass
class LockInfo:
    version: str
    pid: int
    is_process_running: bool
    exec_path: str
    acquired_at: datetime
    lock_file_path: str


FALLBACK_STALE_MS = 2 * 60 * 60 * 1000


def is_process_running(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def get_process_command(pid: int) -> str | None:
    if pid <= 1:
        return None
    try:
        if sys.platform == "win32":
            return None
        if sys.platform == "darwin":
            r = subprocess.run(
                ["ps", "-p", str(pid), "-o", "args="],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            out = (r.stdout or "").strip()
            return out or None
        cmdline = Path(f"/proc/{pid}/cmdline")
        if not cmdline.is_file():
            return None
        raw = cmdline.read_bytes().replace(b"\x00", b" ").decode(errors="replace").strip()
        return raw or None
    except OSError:
        return None


def _is_claude_process(pid: int, expected_exec_path: str) -> bool:
    if not is_process_running(pid):
        return False
    if pid == os.getpid():
        return True
    command = get_process_command(pid)
    if not command:
        return True
    low_cmd = command.lower()
    low_exec = expected_exec_path.lower()
    return "claude" in low_cmd or low_exec in low_cmd


def read_lock_content(lock_file_path: str) -> VersionLockContent | None:
    p = Path(lock_file_path)
    try:
        content = p.read_text(encoding="utf-8")
    except OSError:
        return None
    if not content.strip():
        return None
    try:
        data: dict[str, Any] = json.loads(content)
    except json.JSONDecodeError:
        return None
    pid = data.get("pid")
    version = data.get("version")
    exec_path = data.get("execPath")
    acquired = data.get("acquiredAt")
    if not isinstance(pid, int) or not isinstance(version, str) or not isinstance(exec_path, str):
        return None
    acq = int(acquired) if isinstance(acquired, (int, float)) else 0
    return VersionLockContent(pid=pid, version=version, exec_path=exec_path, acquired_at=acq)


def is_lock_active(lock_file_path: str) -> bool:
    content = read_lock_content(lock_file_path)
    if not content:
        return False
    if not is_process_running(content.pid):
        return False
    if not _is_claude_process(content.pid, content.exec_path):
        log_for_debugging(
            f"Lock PID {content.pid} running but not Claude-like — treating as stale",
        )
        return False
    try:
        age_ms = (time.time() * 1000) - (Path(lock_file_path).stat().st_mtime * 1000)
        if age_ms > FALLBACK_STALE_MS and not is_process_running(content.pid):
            return False
    except OSError:
        pass
    return True


def _write_lock_file(lock_file_path: str, content: VersionLockContent) -> None:
    p = Path(lock_file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(f".tmp.{os.getpid()}.{int(time.time() * 1000)}")
    payload = {
        "pid": content.pid,
        "version": content.version,
        "execPath": content.exec_path,
        "acquiredAt": content.acquired_at,
    }
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(p)


async def try_acquire_lock(version_path: str, lock_file_path: str) -> Callable[[], None] | None:
    version_name = Path(version_path).name
    if is_lock_active(lock_file_path):
        existing = read_lock_content(lock_file_path)
        held = existing.pid if existing else "?"
        log_for_debugging(f"Cannot acquire lock for {version_name} - held by PID {held}")
        return None
    lock_content = VersionLockContent(
        pid=os.getpid(),
        version=version_name,
        exec_path=sys.executable,
        acquired_at=int(time.time() * 1000),
    )
    try:
        _write_lock_file(lock_file_path, lock_content)
        verify = read_lock_content(lock_file_path)
        if verify is None or verify.pid != os.getpid():
            return None
        log_for_debugging(f"Acquired PID lock for {version_name} (PID {os.getpid()})")

        def release() -> None:
            try:
                current = read_lock_content(lock_file_path)
                if current and current.pid == os.getpid():
                    Path(lock_file_path).unlink(missing_ok=True)
                    log_for_debugging(f"Released PID lock for {version_name}")
            except OSError as e:
                log_for_debugging(f"Failed to release lock for {version_name}: {e}")

        return release
    except OSError as e:
        log_for_debugging(f"Failed to acquire lock for {version_name}: {e}")
        return None


def _register_exit_hooks(release: Callable[[], None]) -> None:
    def cleanup() -> None:
        with contextlib.suppress(Exception):
            release()

    atexit.register(cleanup)


async def acquire_process_lifetime_lock(version_path: str, lock_file_path: str) -> bool:
    release = await try_acquire_lock(version_path, lock_file_path)
    if not release:
        return False
    _register_exit_hooks(release)
    return True


async def with_lock(
    version_path: str,
    lock_file_path: str,
    callback: Callable[[], object | Awaitable[object]],
) -> bool:
    release = await try_acquire_lock(version_path, lock_file_path)
    if not release:
        return False
    try:
        res = callback()
        if hasattr(res, "__await__"):
            await res  # type: ignore[func-returns-value]
        return True
    finally:
        release()


def get_all_lock_info(locks_dir: str) -> list[LockInfo]:
    root = Path(locks_dir)
    out: list[LockInfo] = []
    try:
        for f in root.iterdir():
            if not f.name.endswith(".lock") or not f.is_file():
                continue
            content = read_lock_content(str(f))
            if not content:
                continue
            out.append(
                LockInfo(
                    version=content.version,
                    pid=content.pid,
                    is_process_running=is_process_running(content.pid),
                    exec_path=content.exec_path,
                    acquired_at=datetime.fromtimestamp(content.acquired_at / 1000.0, tz=UTC),
                    lock_file_path=str(f),
                )
            )
    except OSError as e:
        if not is_enoent(e):
            log_error(to_error(e))
    return out


def cleanup_stale_locks(locks_dir: str) -> int:
    root = Path(locks_dir)
    cleaned = 0
    try:
        for entry in root.iterdir():
            if not entry.name.endswith(".lock"):
                continue
            path = str(entry)
            try:
                st = entry.lstat()
                if stat.S_ISDIR(st.st_mode):
                    shutil.rmtree(path, ignore_errors=True)
                    cleaned += 1
                    log_for_debugging(f"Cleaned up legacy directory lock: {entry.name}")
                elif not is_lock_active(path):
                    entry.unlink(missing_ok=True)
                    cleaned += 1
                    log_for_debugging(f"Cleaned up stale lock: {entry.name}")
            except OSError:
                continue
    except OSError as e:
        if not is_enoent(e):
            log_error(to_error(e))
    return cleaned
