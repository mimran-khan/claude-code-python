"""
Orchestrate uploads of modified output files (BYOC).

Migrated from: utils/filePersistence/filePersistence.ts
"""

from __future__ import annotations

import os
import time
from typing import Any

from claude_code.services.api.files_api import (
    FilesApiConfig,
    UploadFailure,
    UploadSuccess,
    upload_session_files,
)

from ..cwd import get_cwd
from ..log import log_error
from .constants import DEFAULT_UPLOAD_CONCURRENCY, FILE_COUNT_LIMIT, OUTPUTS_SUBDIR
from .outputs_scanner import find_modified_files, get_environment_kind, log_debug
from .types import FailedPersistence, FilesPersistedEventData, PersistedFile, TurnStartTime


def _session_ingress_token() -> str | None:
    try:
        from claude_code.cli.transports.session_ingress_headers import (
            get_session_ingress_auth_token,
        )

        return get_session_ingress_auth_token()
    except ImportError:
        return os.getenv("CLAUDE_CODE_SESSION_INGRESS_TOKEN")


def is_file_persistence_enabled() -> bool:
    if not os.getenv("CLAUDE_CODE_ENABLE_FILE_PERSISTENCE"):
        return False
    return (
        get_environment_kind() == "byoc"
        and bool(_session_ingress_token())
        and bool(os.getenv("CLAUDE_CODE_REMOTE_SESSION_ID"))
    )


async def run_file_persistence(
    turn_start_time: TurnStartTime,
    signal: Any | None = None,
) -> FilesPersistedEventData | None:
    if get_environment_kind() != "byoc":
        return None
    token = _session_ingress_token()
    if not token:
        return None
    session_id = os.getenv("CLAUDE_CODE_REMOTE_SESSION_ID")
    if not session_id:
        log_error(
            RuntimeError(
                "File persistence enabled but CLAUDE_CODE_REMOTE_SESSION_ID is not set",
            )
        )
        return None
    config = FilesApiConfig(oauth_token=token, session_id=session_id)
    outputs_dir = os.path.join(get_cwd(), session_id, OUTPUTS_SUBDIR)
    if signal is not None and getattr(signal, "aborted", False):
        log_debug("Persistence aborted before processing")
        return None
    start = time.time() * 1000
    modified_files = await find_modified_files(turn_start_time, outputs_dir)
    if not modified_files:
        log_debug("No modified files to persist")
        return None
    if len(modified_files) > FILE_COUNT_LIMIT:
        return FilesPersistedEventData(
            files=[],
            failed=[
                FailedPersistence(
                    filename=outputs_dir,
                    error=f"Too many files modified ({len(modified_files)}). Maximum: {FILE_COUNT_LIMIT}.",
                )
            ],
        )
    specs: list[dict[str, str]] = []
    for path in modified_files:
        rel = os.path.relpath(path, outputs_dir)
        if rel.startswith(".."):
            log_debug(f"Skipping file outside outputs directory: {rel}")
            continue
        specs.append({"path": path, "relativePath": rel})
    results = await upload_session_files(specs, config, DEFAULT_UPLOAD_CONCURRENCY)
    files: list[PersistedFile] = []
    failed: list[FailedPersistence] = []
    for r in results:
        if isinstance(r, UploadSuccess):
            files.append(PersistedFile(filename=r.path, file_id=r.file_id))
        elif isinstance(r, UploadFailure):
            failed.append(FailedPersistence(filename=r.path, error=r.error or "upload failed"))
    _ = start
    if not files and not failed:
        return None
    return FilesPersistedEventData(files=files, failed=failed)


async def execute_file_persistence(
    turn_start_time: TurnStartTime,
    signal: Any,
    on_result: Any,
) -> None:
    try:
        result = await run_file_persistence(turn_start_time, signal)
        if result:
            on_result(result)
    except Exception as exc:
        log_error(exc)
