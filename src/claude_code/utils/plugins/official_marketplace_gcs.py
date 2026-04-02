"""
Fetch the official marketplace zip from the GCS/CDN mirror.

Migrated from: utils/plugins/officialMarketplaceGcs.ts
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import os
import re
import shutil
import time
import zipfile
from typing import Any, Final

import httpx

from claude_code.services.analytics.events import log_event

from ..debug import log_for_debugging
from ..errors import error_message, get_errno_code

GCS_BASE: Final[str] = "https://downloads.claude.ai/claude-code-releases/plugins/claude-plugins-official"
ARC_PREFIX: Final[str] = "marketplaces/claude-plugins-official/"

KNOWN_FS_CODES: Final[set[str]] = {
    "ENOSPC",
    "EACCES",
    "EPERM",
    "EXDEV",
    "EBUSY",
    "ENOENT",
    "ENOTDIR",
    "EROFS",
    "EMFILE",
    "ENAMETOOLONG",
}


def classify_gcs_error(exc: BaseException | object) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        return f"http_{exc.response.status_code}"
    if isinstance(exc, httpx.RequestError):
        return "network"
    code = get_errno_code(exc)
    if code and re.match(r"^E[A-Z]+$", code) and not code.startswith("ERR_"):
        return f"fs_{code}" if code in KNOWN_FS_CODES else "fs_other"
    if isinstance(getattr(exc, "code", None), int):
        return "zip_parse"
    msg = error_message(exc)
    if re.search(r"unzip|invalid zip|central directory", msg, re.I):
        return "zip_parse"
    if re.search(r"empty body", msg, re.I):
        return "empty_latest"
    return "other"


async def fetch_official_marketplace_from_gcs(
    install_location: str,
    marketplaces_cache_dir: str,
) -> str | None:
    cache_dir = os.path.realpath(marketplaces_cache_dir)
    resolved_loc = os.path.realpath(install_location)
    sep = os.sep
    if resolved_loc != cache_dir and not resolved_loc.startswith(cache_dir + sep):
        log_for_debugging(
            f"fetch_official_marketplace_from_gcs: refusing path outside cache dir: {install_location}",
            level="error",
        )
        return None

    start = time.perf_counter()
    outcome = "failed"
    sha: str | None = None
    nbytes: int | None = None
    err_kind: str | None = None

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            latest_resp = await client.get(f"{GCS_BASE}/latest")
            latest_resp.raise_for_status()
            sha = str(latest_resp.text).strip()
            if not sha:
                raise ValueError("latest pointer returned empty body")

            sentinel_path = os.path.join(install_location, ".gcs-sha")

            def _read_sentinel() -> str | None:
                try:
                    with open(sentinel_path, encoding="utf-8") as handle:
                        return handle.read().strip()
                except OSError:
                    return None

            current_sha = await asyncio.to_thread(_read_sentinel)
            if current_sha == sha:
                outcome = "noop"
                return sha

            zip_resp = await client.get(f"{GCS_BASE}/{sha}.zip")
            zip_resp.raise_for_status()
            zip_buf = zip_resp.content
            nbytes = len(zip_buf)

            staging = f"{install_location}.staging"

            def _extract_and_swap() -> None:
                if os.path.exists(staging):
                    shutil.rmtree(staging, ignore_errors=True)
                os.makedirs(staging, exist_ok=True)

                with zipfile.ZipFile(io.BytesIO(zip_buf)) as zf:
                    for zi in zf.infolist():
                        if zi.is_dir():
                            continue
                        arc_path = zi.filename
                        if not arc_path.startswith(ARC_PREFIX):
                            continue
                        rel = arc_path[len(ARC_PREFIX) :]
                        if not rel or rel.endswith("/"):
                            continue
                        dest = os.path.join(staging, rel)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with zf.open(zi) as src, open(dest, "wb") as out:
                            out.write(src.read())
                        unix_mode = (zi.external_attr >> 16) & 0o777777
                        if unix_mode & 0o111:
                            with contextlib.suppress(OSError):
                                os.chmod(dest, unix_mode & 0o777)

                with open(os.path.join(staging, ".gcs-sha"), "w", encoding="utf-8") as handle:
                    handle.write(sha or "")

                if os.path.exists(install_location):
                    shutil.rmtree(install_location, ignore_errors=True)
                os.rename(staging, install_location)

            await asyncio.to_thread(_extract_and_swap)
            outcome = "updated"
            return sha
    except Exception as exc:
        err_kind = classify_gcs_error(exc)
        log_for_debugging(
            f"Official marketplace GCS fetch failed: {error_message(exc)}",
            level="warn",
        )
        return None
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000)
        payload: dict[str, Any] = {
            "source": "marketplace_gcs",
            "host": "downloads.claude.ai",
            "is_official": True,
            "outcome": outcome,
            "duration_ms": duration_ms,
        }
        if nbytes is not None:
            payload["bytes"] = nbytes
        if sha:
            payload["sha"] = sha
        if err_kind:
            payload["error_kind"] = err_kind
        log_event("tengu_plugin_remote_fetch", payload)


__all__ = ["classify_gcs_error", "fetch_official_marketplace_from_gcs"]
