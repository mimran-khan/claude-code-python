"""
File checkpointing: backups per message and rewind support.

Migrated from: utils/fileHistory.ts (trimmed; VSCode notify / session JSONL hooks are stubs).
"""

from __future__ import annotations

import asyncio
import difflib
import hashlib
import os
import shutil
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from ..bootstrap.state import get_original_cwd, get_session_id
from .config_utils import get_global_config
from .debug import log_for_debugging
from .env_utils import get_claude_config_home_dir, is_env_truthy
from .errors import is_enoent
from .file import path_exists
from .log import log_error

MAX_SNAPSHOTS = 100

MessageId = str
BackupFileName = str | None


@dataclass
class FileHistoryBackup:
    backup_file_name: BackupFileName
    version: int
    backup_time: float


@dataclass
class FileHistorySnapshot:
    message_id: MessageId
    tracked_file_backups: dict[str, FileHistoryBackup]
    timestamp: float


@dataclass
class FileHistoryState:
    snapshots: list[FileHistorySnapshot] = field(default_factory=list)
    tracked_files: set[str] = field(default_factory=set)
    snapshot_sequence: int = 0


def _is_sdk_non_interactive() -> bool:
    return is_env_truthy(os.getenv("CLAUDE_CODE_SDK")) or is_env_truthy(os.getenv("NON_INTERACTIVE"))


def file_history_enabled() -> bool:
    if _is_sdk_non_interactive():
        return is_env_truthy(os.getenv("CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING")) and not is_env_truthy(
            os.getenv("CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING")
        )
    gc = get_global_config()
    checkpoint = getattr(gc, "file_checkpointing_enabled", None)
    if checkpoint is False:
        return False
    return not is_env_truthy(os.getenv("CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING"))


def _backup_file_name(file_path: str, version: int) -> str:
    h = hashlib.sha256(file_path.encode()).hexdigest()[:16]
    return f"{h}@v{version}"


def resolve_backup_path(backup_file_name: str, session_id: str | None = None) -> str:
    sid = session_id or str(get_session_id())
    return os.path.join(get_claude_config_home_dir(), "file-history", sid, backup_file_name)


def maybe_shorten_file_path(file_path: str) -> str:
    if not os.path.isabs(file_path):
        return file_path
    cwd = get_original_cwd()
    if file_path.startswith(cwd):
        return os.path.relpath(file_path, cwd)
    return file_path


def maybe_expand_file_path(file_path: str) -> str:
    if os.path.isabs(file_path):
        return file_path
    return os.path.join(get_original_cwd(), file_path)


async def _create_backup(file_path: str | None, version: int) -> FileHistoryBackup:
    if file_path is None:
        return FileHistoryBackup(backup_file_name=None, version=version, backup_time=_now())
    bname = _backup_file_name(file_path, version)
    dest = resolve_backup_path(bname)
    try:
        await asyncio.to_thread(os.stat, file_path)
    except OSError as e:
        if is_enoent(e):
            return FileHistoryBackup(backup_file_name=None, version=version, backup_time=_now())
        raise
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    await asyncio.to_thread(shutil.copy2, file_path, dest)
    st = await asyncio.to_thread(os.stat, file_path)
    await asyncio.to_thread(os.chmod, dest, st.st_mode)
    return FileHistoryBackup(backup_file_name=bname, version=version, backup_time=_now())


def _now() -> float:
    return time.time()


async def check_origin_file_changed(
    original_file: str,
    backup_file_name: str,
    original_stats_hint: os.stat_result | None = None,
) -> bool:
    backup_path = resolve_backup_path(backup_file_name)
    ostat = original_stats_hint
    if ostat is None:
        try:
            ostat = await asyncio.to_thread(os.stat, original_file)
        except OSError as e:
            if is_enoent(e):
                ostat = None
            else:
                return True
    try:
        bstat = await asyncio.to_thread(os.stat, backup_path)
    except OSError as e:
        if is_enoent(e):
            bstat = None
        else:
            return True
    if (ostat is None) != (bstat is None):
        return True
    if ostat is None or bstat is None:
        return False
    if ostat.st_mode != bstat.st_mode or ostat.st_size != bstat.st_size:
        return True
    if ostat.st_mtime < bstat.st_mtime:
        return False
    try:
        otxt, btxt = await asyncio.gather(
            asyncio.to_thread(lambda: open(original_file, encoding="utf-8").read()),
            asyncio.to_thread(lambda: open(backup_path, encoding="utf-8").read()),
        )
        return otxt != btxt
    except OSError:
        return True


async def file_history_track_edit(
    update_file_history_state: Callable[[Callable[[FileHistoryState], FileHistoryState]], None],
    file_path: str,
    message_id: MessageId,
) -> None:
    if not file_history_enabled():
        return
    tracking_path = maybe_shorten_file_path(file_path)
    captured: list[FileHistoryState | None] = [None]

    def _capture(prev: FileHistoryState) -> FileHistoryState:
        captured[0] = prev
        return prev

    update_file_history_state(_capture)
    state = captured[0]
    if not state or not state.snapshots:
        return
    most_recent = state.snapshots[-1]
    if tracking_path in most_recent.tracked_file_backups:
        return
    try:
        backup = await _create_backup(file_path, 1)
    except Exception as exc:
        log_error(exc)
        return

    def _commit(prev: FileHistoryState) -> FileHistoryState:
        if not prev.snapshots:
            return prev
        last = prev.snapshots[-1]
        if tracking_path in last.tracked_file_backups:
            return prev
        tf = set(prev.tracked_files)
        tf.add(tracking_path)
        new_backups = {**last.tracked_file_backups, tracking_path: backup}
        new_last = replace(last, tracked_file_backups=new_backups)
        snaps = prev.snapshots[:-1] + [new_last]
        return replace(prev, snapshots=snaps, tracked_files=tf)

    update_file_history_state(_commit)
    log_for_debugging(f"FileHistory: Tracked file modification for {file_path}")


async def file_history_make_snapshot(
    update_file_history_state: Callable[[Callable[[FileHistoryState], FileHistoryState]], None],
    message_id: MessageId,
) -> None:
    if not file_history_enabled():
        return
    captured: list[FileHistoryState | None] = [None]
    update_file_history_state(lambda s: captured.__setitem__(0, s) or s)
    state = captured[0]
    if not state:
        return
    most_recent = state.snapshots[-1] if state.snapshots else None
    tracked_file_backups: dict[str, FileHistoryBackup] = {}
    if most_recent:
        for tp in state.tracked_files:
            fp = maybe_expand_file_path(tp)
            prev_b = most_recent.tracked_file_backups.get(tp)
            ver = (prev_b.version + 1) if prev_b else 1
            try:
                st = await asyncio.to_thread(os.stat, fp)
            except OSError as e:
                if is_enoent(e):
                    tracked_file_backups[tp] = FileHistoryBackup(None, ver, _now())
                    continue
                log_error(e)
                continue
            if (
                prev_b
                and prev_b.backup_file_name
                and not await check_origin_file_changed(fp, prev_b.backup_file_name, st)
            ):
                tracked_file_backups[tp] = prev_b
            else:
                tracked_file_backups[tp] = await _create_backup(fp, ver)

    def _commit(prev: FileHistoryState) -> FileHistoryState:
        last = prev.snapshots[-1] if prev.snapshots else None
        merged = dict(tracked_file_backups)
        if last:
            for tp in prev.tracked_files:
                if tp not in merged and tp in last.tracked_file_backups:
                    merged[tp] = last.tracked_file_backups[tp]
        snap = FileHistorySnapshot(message_id=message_id, tracked_file_backups=merged, timestamp=_now())
        all_snaps = prev.snapshots + [snap]
        if len(all_snaps) > MAX_SNAPSHOTS:
            all_snaps = all_snaps[-MAX_SNAPSHOTS:]
        return replace(
            prev,
            snapshots=all_snaps,
            snapshot_sequence=prev.snapshot_sequence + 1,
        )

    update_file_history_state(_commit)


async def file_history_rewind(
    update_file_history_state: Callable[[Callable[[FileHistoryState], FileHistoryState]], None],
    message_id: MessageId,
) -> None:
    if not file_history_enabled():
        return
    captured: list[FileHistoryState | None] = [None]
    update_file_history_state(lambda s: captured.__setitem__(0, s) or s)
    state = captured[0]
    if not state:
        return
    target = next((s for s in reversed(state.snapshots) if s.message_id == message_id), None)
    if not target:
        raise RuntimeError("The selected snapshot was not found")
    for tp in state.tracked_files:
        fp = maybe_expand_file_path(tp)
        tb = target.tracked_file_backups.get(tp)
        bname = tb.backup_file_name if tb else None
        if bname is None:
            try:
                await asyncio.to_thread(os.unlink, fp)
            except OSError as e:
                if not is_enoent(e):
                    log_error(e)
            continue
        src = resolve_backup_path(bname)
        if await check_origin_file_changed(fp, bname):
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            await asyncio.to_thread(shutil.copy2, src, fp)
            st = await asyncio.to_thread(os.stat, src)
            await asyncio.to_thread(os.chmod, fp, st.st_mode)


def file_history_can_restore(state: FileHistoryState, message_id: MessageId) -> bool:
    if not file_history_enabled():
        return False
    return any(s.message_id == message_id for s in state.snapshots)


async def file_history_get_diff_stats(
    state: FileHistoryState,
    message_id: MessageId,
) -> dict[str, Any] | None:
    if not file_history_enabled():
        return None
    target = next((s for s in reversed(state.snapshots) if s.message_id == message_id), None)
    if not target:
        return None
    files_changed: list[str] = []
    ins = dels = 0
    for tp in state.tracked_files:
        fp = maybe_expand_file_path(tp)
        tb = target.tracked_file_backups.get(tp)
        bname = tb.backup_file_name if tb else None
        cur = ""
        try:
            cur = await asyncio.to_thread(lambda: open(fp, encoding="utf-8").read())
        except OSError:
            cur = ""
        old = ""
        if bname:
            try:
                p = resolve_backup_path(bname)
                old = await asyncio.to_thread(lambda: open(p, encoding="utf-8").read())
            except OSError:
                old = ""
        diff = list(difflib.unified_diff(old.splitlines(), cur.splitlines(), lineterm=""))
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
        if added or removed or (bname is None and path_exists(fp)):
            files_changed.append(fp)
            ins += added
            dels += removed
    return {"filesChanged": files_changed, "insertions": ins, "deletions": dels}


def file_history_restore_state_from_log(
    file_history_snapshots: list[FileHistorySnapshot],
    on_update_state: Callable[[FileHistoryState], None],
) -> None:
    if not file_history_enabled():
        return
    tracked: set[str] = set()
    snaps: list[FileHistorySnapshot] = []
    for snap in file_history_snapshots:
        backups: dict[str, FileHistoryBackup] = {}
        for path, backup in snap.tracked_file_backups.items():
            tp = maybe_shorten_file_path(path)
            tracked.add(tp)
            backups[tp] = backup
        snaps.append(replace(snap, tracked_file_backups=backups))
    on_update_state(FileHistoryState(snapshots=snaps, tracked_files=tracked, snapshot_sequence=len(snaps)))


def new_file_history_state() -> FileHistoryState:
    initial_snap = FileHistorySnapshot(
        message_id=str(uuid.uuid4()),
        tracked_file_backups={},
        timestamp=_now(),
    )
    return FileHistoryState(snapshots=[initial_snap], tracked_files=set(), snapshot_sequence=1)
