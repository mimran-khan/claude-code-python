"""
IDE diff tab flow for file edits (RPC result guards + edit recompute).

Migrated from: hooks/useDiffInIDE.ts
"""

from __future__ import annotations

import logging
from typing import Literal

from claude_code.tools.file_edit_tool.edit_utils import get_edits_for_patch
from claude_code.tools.file_edit_tool.types import FileEditRecord
from claude_code.utils.diff import get_patch_from_contents

log = logging.getLogger(__name__)

EditMode = Literal["single", "multiple"]


def compute_edits_from_contents(
    file_path: str,
    old_content: str,
    new_content: str,
    *,
    edit_mode: EditMode,
) -> list[FileEditRecord]:
    """Recompute FileEdit list after user changes buffer in IDE (TS: computeEditsFromContents)."""
    single_hunk = edit_mode == "single"
    patch = get_patch_from_contents(
        file_path,
        old_content,
        new_content,
        single_hunk=single_hunk,
    )
    if not patch:
        return []
    if single_hunk and len(patch) > 1:
        log.error("Unexpected number of hunks: %s. Expected 1 hunk.", len(patch))
    return get_edits_for_patch(patch)


def ide_rpc_is_tab_closed(data: object) -> bool:
    return (
        isinstance(data, list)
        and len(data) > 0
        and isinstance(data[0], dict)
        and data[0].get("type") == "text"
        and data[0].get("text") == "TAB_CLOSED"
    )


def ide_rpc_is_diff_rejected(data: object) -> bool:
    return (
        isinstance(data, list)
        and len(data) > 0
        and isinstance(data[0], dict)
        and data[0].get("type") == "text"
        and data[0].get("text") == "DIFF_REJECTED"
    )


def ide_rpc_is_file_saved(data: object) -> bool:
    return (
        isinstance(data, list)
        and len(data) >= 2
        and isinstance(data[0], dict)
        and data[0].get("type") == "text"
        and data[0].get("text") == "FILE_SAVED"
        and isinstance(data[1], dict)
        and isinstance(data[1].get("text"), str)
    )


def ide_rpc_saved_new_content(data: object) -> str | None:
    if ide_rpc_is_file_saved(data) and isinstance(data, list):
        t = data[1].get("text")
        return str(t) if t is not None else None
    return None
