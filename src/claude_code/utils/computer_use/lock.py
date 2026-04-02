"""
File-based computer-use session lock.

Migrated from: utils/computerUse/computerUseLock.ts
"""

from __future__ import annotations

import atexit
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import aiofiles

from ...bootstrap.state import get_session_id
from ..debug import log_for_debugging
from ..env_utils import get_claude_config_home_dir
from ..errors import get_errno_code

LOCK_FILENAME = "computer-use.lock"

_atexit_registered = False
_session_holds_lock = False


@dataclass(frozen=True)
class ComputerUseLockRecord:
    session_id: str
    pid: int
    acquired_at: int


AcquireResult = tuple[Literal["acquired"], Literal["fresh"] | Literal["reentrant"]] | tuple[Literal["blocked"], str]
CheckResult = Literal["free"] | Literal["held_by_self"] | tuple[Literal["blocked"], str]


def _lock_path() -> Path:
    return Path(get_claude_config_home_dir()) / LOCK_FILENAME


def _is_computer_use_lock(value: object) -> ComputerUseLockRecord | None:
    if not isinstance(value, dict):
        return None
    sid = value.get("sessionId")
    pid = value.get("pid")
    acquired = value.get("acquiredAt", 0)
    if isinstance(sid, str) and isinstance(pid, int):
        return ComputerUseLockRecord(session_id=sid, pid=pid, acquired_at=int(acquired))
    return None


async def _read_lock() -> ComputerUseLockRecord | None:
    path = _lock_path()
    if not path.is_file():
        return None
    try:
        async with aiofiles.open(path, encoding="utf-8") as f:
            raw = await f.read()
        return _is_computer_use_lock(json.loads(raw))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _read_lock_sync() -> ComputerUseLockRecord | None:
    path = _lock_path()
    if not path.is_file():
        return None
    try:
        return _is_computer_use_lock(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _is_process_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


async def _try_create_exclusive(record: ComputerUseLockRecord) -> bool:
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {
            "sessionId": record.session_id,
            "pid": record.pid,
            "acquiredAt": record.acquired_at,
        },
        separators=(",", ":"),
    )
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        return True
    except OSError as e:
        if get_errno_code(e) == "EEXIST":
            return False
        raise


def _ensure_atexit() -> None:
    global _atexit_registered
    if _atexit_registered:
        return
    _atexit_registered = True
    atexit.register(_sync_release_computer_use_lock_at_exit)


def _sync_release_computer_use_lock_at_exit() -> None:
    if not _session_holds_lock:
        return
    sid = str(get_session_id())
    existing = _read_lock_sync()
    if existing and existing.session_id == sid:
        try:
            _lock_path().unlink(missing_ok=True)
            log_for_debugging("Released computer-use lock (atexit)")
        except OSError:
            pass


async def check_computer_use_lock() -> CheckResult:
    existing = await _read_lock()
    if existing is None:
        return "free"
    if existing.session_id == str(get_session_id()):
        return "held_by_self"
    if _is_process_running(existing.pid):
        return ("blocked", existing.session_id)
    log_for_debugging(
        f"Recovering stale computer-use lock from session {existing.session_id} (PID {existing.pid})",
    )
    try:
        _lock_path().unlink(missing_ok=True)
    except OSError:
        pass
    return "free"


def is_lock_held_locally() -> bool:
    return _session_holds_lock


async def try_acquire_computer_use_lock() -> AcquireResult:
    global _session_holds_lock
    session_id = str(get_session_id())
    record = ComputerUseLockRecord(
        session_id=session_id,
        pid=os.getpid(),
        acquired_at=int(time.time() * 1000),
    )
    Path(get_claude_config_home_dir()).mkdir(parents=True, exist_ok=True)

    if await _try_create_exclusive(record):
        _session_holds_lock = True
        _ensure_atexit()
        return ("acquired", "fresh")

    existing = await _read_lock()
    if existing is None:
        try:
            _lock_path().unlink(missing_ok=True)
        except OSError:
            pass
        if await _try_create_exclusive(record):
            _session_holds_lock = True
            _ensure_atexit()
            return ("acquired", "fresh")
        other = await _read_lock()
        return ("blocked", other.session_id if other else "unknown")

    if existing.session_id == session_id:
        _session_holds_lock = True
        _ensure_atexit()
        return ("acquired", "reentrant")

    if _is_process_running(existing.pid):
        return ("blocked", existing.session_id)

    log_for_debugging(
        f"Recovering stale computer-use lock from session {existing.session_id} (PID {existing.pid})",
    )
    try:
        _lock_path().unlink(missing_ok=True)
    except OSError:
        pass
    if await _try_create_exclusive(record):
        _session_holds_lock = True
        _ensure_atexit()
        return ("acquired", "fresh")
    other = await _read_lock()
    return ("blocked", other.session_id if other else "unknown")


async def release_computer_use_lock() -> bool:
    global _session_holds_lock
    existing = await _read_lock()
    if existing is None or existing.session_id != str(get_session_id()):
        return False
    try:
        _lock_path().unlink()
        log_for_debugging("Released computer-use lock")
        _session_holds_lock = False
        return True
    except OSError:
        return False
