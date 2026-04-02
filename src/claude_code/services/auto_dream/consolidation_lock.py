"""
Lock file whose mtime is lastConsolidatedAt; body holds holder PID.

Migrated from: services/autoDream/consolidationLock.ts
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from claude_code.memdir.paths import get_memory_dir
from claude_code.utils.debug import log_for_debugging

LOCK_FILE = ".consolidate-lock"
HOLDER_STALE_MS = 60 * 60 * 1000


def _is_process_running(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _lock_path(memory_root: str | None = None) -> Path:
    root = memory_root or get_memory_dir()
    return Path(root) / LOCK_FILE


def read_last_consolidated_at_sync(memory_root: str | None = None) -> float:
    path = _lock_path(memory_root)
    try:
        return path.stat().st_mtime * 1000.0
    except OSError:
        return 0.0


async def read_last_consolidated_at(memory_root: str | None = None) -> float:
    import asyncio

    return await asyncio.to_thread(read_last_consolidated_at_sync, memory_root)


async def try_acquire_consolidation_lock(memory_root: str | None = None) -> float | None:
    import asyncio

    return await asyncio.to_thread(_try_acquire_consolidation_lock_sync, memory_root)


def _try_acquire_consolidation_lock_sync(memory_root: str | None = None) -> float | None:
    path = _lock_path(memory_root)
    mtime_ms: float | None = None
    holder_pid: int | None = None
    try:
        st = path.stat()
        mtime_ms = st.st_mtime * 1000.0
        raw = path.read_text(encoding="utf-8").strip()
        parsed = int(raw, 10)
        holder_pid = parsed if parsed > 0 else None
    except OSError:
        pass
    except ValueError:
        holder_pid = None

    now = __import__("time").time() * 1000.0
    if mtime_ms is not None and now - mtime_ms < HOLDER_STALE_MS:
        if holder_pid is not None and _is_process_running(holder_pid):
            log_for_debugging(
                f"[autoDream] lock held by live PID {holder_pid} (mtime {round((now - mtime_ms) / 1000)}s ago)"
            )
            return None

    mem_dir = path.parent
    mem_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(str(os.getpid()), encoding="utf-8")
    try:
        verify = path.read_text(encoding="utf-8").strip()
        if int(verify, 10) != os.getpid():
            return None
    except (OSError, ValueError):
        return None
    return mtime_ms if mtime_ms is not None else 0.0


async def rollback_consolidation_lock(prior_mtime: float, memory_root: str | None = None) -> None:
    import asyncio

    await asyncio.to_thread(_rollback_consolidation_lock_sync, prior_mtime, memory_root)


def _rollback_consolidation_lock_sync(prior_mtime: float, memory_root: str | None = None) -> None:
    path = _lock_path(memory_root)
    try:
        if prior_mtime == 0:
            path.unlink(missing_ok=True)
            return
        path.write_text("", encoding="utf-8")
        t = prior_mtime / 1000.0
        os.utime(path, (t, t))
    except OSError as e:
        log_for_debugging(f"[autoDream] rollback failed: {e} — next trigger delayed to minHours")


@dataclass
class SessionCandidate:
    session_id: str
    mtime: float


async def list_sessions_touched_since(
    since_ms: float,
    transcript_dir: str,
    *,
    list_candidates: Callable[[str, bool], Awaitable[list[SessionCandidate]]] | None = None,
) -> list[str]:
    if list_candidates is not None:
        candidates = await list_candidates(transcript_dir, True)
    else:
        candidates = await _default_list_candidates(transcript_dir)
    return [c.session_id for c in candidates if c.mtime > since_ms]


async def _default_list_candidates(transcript_dir: str) -> list[SessionCandidate]:
    def scan() -> list[SessionCandidate]:
        root = Path(transcript_dir)
        if not root.is_dir():
            return []
        out: list[SessionCandidate] = []
        for f in root.glob("*.jsonl"):
            if f.name.startswith("agent-"):
                continue
            try:
                st = f.stat()
                out.append(SessionCandidate(session_id=f.stem, mtime=st.st_mtime * 1000.0))
            except OSError:
                continue
        return out

    import asyncio

    return await asyncio.to_thread(scan)


async def record_consolidation(memory_root: str | None = None) -> None:
    path = _lock_path(memory_root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as e:
        log_for_debugging(f"[autoDream] recordConsolidation write failed: {e}")
