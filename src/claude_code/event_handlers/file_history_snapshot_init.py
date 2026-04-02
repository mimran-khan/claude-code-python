"""
One-shot restore of file-history snapshots from session log.

Migrated from: hooks/useFileHistorySnapshotInit.ts
"""

from __future__ import annotations

from collections.abc import Callable

from ..utils.file_history import (
    FileHistorySnapshot,
    FileHistoryState,
    file_history_enabled,
    file_history_restore_state_from_log,
)


def run_file_history_snapshot_init_once(
    initialized_flag: list[bool],
    initial_file_history_snapshots: list[FileHistorySnapshot] | None,
    _file_history_state: FileHistoryState,
    on_update_state: Callable[[FileHistoryState], None],
) -> None:
    """
    Restore snapshots once when file history is enabled.

    ``initialized_flag`` must be a single-element list so callers can share mutability
    across async boundaries without a class (mirrors ``useRef``).
    """
    if not file_history_enabled() or initialized_flag[0]:
        return
    initialized_flag[0] = True
    if initial_file_history_snapshots:
        file_history_restore_state_from_log(initial_file_history_snapshots, on_update_state)
