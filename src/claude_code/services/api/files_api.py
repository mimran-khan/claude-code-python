"""
Anthropic Files API client (download / upload / list).

Migrated from: services/api/filesApi.ts
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import aiofiles
import httpx
import structlog

from ...utils.http import get_user_agent

logger = structlog.get_logger(__name__)

FILES_API_BETA_HEADER = "files-api-2025-04-14,oauth-2025-04-20"
ANTHROPIC_VERSION = "2023-06-01"
MAX_RETRIES = 3
BASE_DELAY_MS = 500
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024
DEFAULT_CONCURRENCY = 5


def _default_api_base_url() -> str:
    return (
        os.environ.get("ANTHROPIC_BASE_URL")
        or os.environ.get("CLAUDE_CODE_API_BASE_URL")
        or "https://api.anthropic.com"
    )


@dataclass
class FileAttachment:
    file_id: str
    relative_path: str


@dataclass
class FilesApiConfig:
    oauth_token: str
    session_id: str
    base_url: str | None = None


@dataclass
class DownloadResult:
    file_id: str
    path: str
    success: bool
    error: str | None = None
    bytes_written: int | None = None


@dataclass
class UploadSuccess:
    path: str
    file_id: str
    size: int
    success: Literal[True] = True


@dataclass
class UploadFailure:
    path: str
    error: str
    success: Literal[False] = False


UploadResult = UploadSuccess | UploadFailure


@dataclass
class FileMetadata:
    filename: str
    file_id: str
    size: int


def _beta_headers(oauth_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {oauth_token}",
        "anthropic-version": ANTHROPIC_VERSION,
        "anthropic-beta": FILES_API_BETA_HEADER,
        "User-Agent": get_user_agent(),
    }


async def _sleep_ms(ms: float) -> None:
    await asyncio.sleep(ms / 1000.0)


async def _retry_with_backoff(operation: str, attempt_fn: Any) -> Any:
    last_err = ""
    for attempt in range(1, MAX_RETRIES + 1):
        result = await attempt_fn(attempt)
        if result[0] == "ok":
            return result[1]
        last_err = result[1] if len(result) > 1 else f"{operation} failed"
        logger.debug("files_api_retry", operation=operation, attempt=attempt, error=last_err)
        if attempt < MAX_RETRIES:
            await _sleep_ms(BASE_DELAY_MS * (2 ** (attempt - 1)))
    raise RuntimeError(f"{last_err} after {MAX_RETRIES} attempts")


async def download_file(file_id: str, config: FilesApiConfig) -> bytes:
    base = config.base_url or _default_api_base_url()
    url = f"{base}/v1/files/{file_id}/content"
    headers = _beta_headers(config.oauth_token)

    async def attempt_fn(attempt: int) -> tuple[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.get(url, headers=headers)
            if r.status_code == 200:
                return ("ok", r.content)
            if r.status_code == 404:
                raise FileNotFoundError(f"File not found: {file_id}")
            if r.status_code == 401:
                raise PermissionError("Authentication failed: invalid or missing API key")
            if r.status_code == 403:
                raise PermissionError(f"Access denied to file: {file_id}")
            return ("retry", f"status {r.status_code}")
        except (FileNotFoundError, PermissionError):
            raise
        except Exception as exc:
            return ("retry", str(exc))

    return await _retry_with_backoff(f"Download file {file_id}", attempt_fn)


def build_download_path(base_path: str, session_id: str, relative_path: str) -> str | None:
    normalized = os.path.normpath(relative_path)
    if normalized.startswith(".."):
        logger.error("files_api_invalid_path", relative_path=relative_path)
        return None
    uploads_base = os.path.join(base_path, session_id, "uploads")
    redundant = [
        os.path.join(base_path, session_id, "uploads") + os.sep,
        os.sep + "uploads" + os.sep,
    ]
    clean = normalized
    for p in redundant:
        if normalized.startswith(p):
            clean = normalized[len(p) :]
            break
    return os.path.join(uploads_base, clean)


async def download_and_save_file(
    attachment: FileAttachment,
    config: FilesApiConfig,
    *,
    cwd: str | None = None,
) -> DownloadResult:
    root = cwd or os.getcwd()
    full_path = build_download_path(root, config.session_id, attachment.relative_path)
    if not full_path:
        return DownloadResult(
            file_id=attachment.file_id,
            path="",
            success=False,
            error=f"Invalid file path: {attachment.relative_path}",
        )
    try:
        content = await download_file(attachment.file_id, config)
        parent = os.path.dirname(full_path)
        Path(parent).mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return DownloadResult(
            file_id=attachment.file_id,
            path=full_path,
            success=True,
            bytes_written=len(content),
        )
    except Exception as exc:
        logger.error("files_api_download_save_failed", file_id=attachment.file_id, error=str(exc))
        return DownloadResult(
            file_id=attachment.file_id,
            path=full_path,
            success=False,
            error=str(exc),
        )


async def _parallel_with_limit(items: list[Any], fn: Any, concurrency: int) -> list[Any]:
    sem = asyncio.Semaphore(max(1, concurrency))

    async def run(i: int, item: Any) -> Any:
        async with sem:
            return await fn(item, i)

    return list(await asyncio.gather(*[run(i, x) for i, x in enumerate(items)]))


async def download_session_files(
    files: list[FileAttachment],
    config: FilesApiConfig,
    concurrency: int = DEFAULT_CONCURRENCY,
    *,
    cwd: str | None = None,
) -> list[DownloadResult]:
    if not files:
        return []
    return await _parallel_with_limit(
        files,
        lambda att, _i: download_and_save_file(att, config, cwd=cwd),
        concurrency,
    )


async def upload_file(
    file_path: str,
    relative_path: str,
    config: FilesApiConfig,
) -> UploadResult:
    base = config.base_url or _default_api_base_url()
    url = f"{base}/v1/files"
    headers = _beta_headers(config.oauth_token)
    try:
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
    except OSError as exc:
        return UploadFailure(path=relative_path, error=str(exc))
    if len(content) > MAX_FILE_SIZE_BYTES:
        return UploadFailure(
            path=relative_path,
            error=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES} bytes",
        )
    boundary = f"----FormBoundary{uuid.uuid4()}"
    filename = os.path.basename(relative_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n".encode()
        + content
        + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\nuser_data\r\n'.encode()
        + f"--{boundary}--\r\n".encode()
    )
    req_headers = {
        **headers,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    }

    async def attempt_fn(attempt: int) -> tuple[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(url, content=body, headers=req_headers)
            if r.status_code in (200, 201):
                data = r.json()
                if isinstance(data, dict) and isinstance(data.get("id"), str):
                    return (
                        "ok",
                        UploadSuccess(
                            path=relative_path,
                            file_id=data["id"],
                            size=len(content),
                        ),
                    )
                return ("retry", "Upload succeeded but no file ID returned")
            if r.status_code == 401:
                return (
                    "fail",
                    UploadFailure(
                        path=relative_path,
                        error="Authentication failed: invalid or missing API key",
                    ),
                )
            if r.status_code == 403:
                return ("fail", UploadFailure(path=relative_path, error="Access denied for upload"))
            if r.status_code == 413:
                return (
                    "fail",
                    UploadFailure(path=relative_path, error="File too large for upload"),
                )
            return ("retry", f"status {r.status_code}")
        except Exception as exc:
            return ("retry", str(exc))

    last_fail: UploadFailure | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        tag, val = await attempt_fn(attempt)
        if tag == "ok" and isinstance(val, UploadSuccess):
            return val
        if tag == "fail" and isinstance(val, UploadFailure):
            return val
        last_fail = UploadFailure(path=relative_path, error=str(val))
        if attempt < MAX_RETRIES:
            await _sleep_ms(BASE_DELAY_MS * (2 ** (attempt - 1)))
    return last_fail or UploadFailure(path=relative_path, error="upload failed")


async def upload_session_files(
    files: list[dict[str, str]],
    config: FilesApiConfig,
    concurrency: int = DEFAULT_CONCURRENCY,
) -> list[UploadResult]:
    if not files:
        return []

    async def one(spec: dict[str, str], _i: int) -> UploadResult:
        return await upload_file(spec["path"], spec["relativePath"], config)

    return await _parallel_with_limit(files, one, concurrency)


async def list_files_created_after(
    after_created_at: str,
    config: FilesApiConfig,
) -> list[FileMetadata]:
    base = config.base_url or _default_api_base_url()
    headers = _beta_headers(config.oauth_token)
    all_files: list[FileMetadata] = []
    after_id: str | None = None
    while True:
        params: dict[str, str] = {"after_created_at": after_created_at}
        if after_id:
            params["after_id"] = after_id

        page_params = dict(params)

        async def attempt_fn(
            attempt: int,
            qp: dict[str, str] = page_params,
        ) -> tuple[str, Any]:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    r = await client.get(f"{base}/v1/files", headers=headers, params=qp)
                if r.status_code == 200:
                    return ("ok", r.json())
                if r.status_code == 401:
                    raise PermissionError("Authentication failed: invalid or missing API key")
                if r.status_code == 403:
                    raise PermissionError("Access denied to list files")
                return ("retry", f"status {r.status_code}")
            except PermissionError:
                raise
            except Exception as exc:
                return ("retry", str(exc))

        page = await _retry_with_backoff("List files", attempt_fn)
        if not isinstance(page, dict):
            break
        files = page.get("data", [])
        if not isinstance(files, list):
            break
        for f in files:
            if isinstance(f, dict) and isinstance(f.get("id"), str):
                sz = f.get("size_bytes", f.get("size", 0))
                all_files.append(
                    FileMetadata(
                        filename=str(f.get("filename", "")),
                        file_id=f["id"],
                        size=int(sz) if isinstance(sz, (int, float)) else 0,
                    )
                )
        if not page.get("has_more"):
            break
        last = files[-1] if files else None
        if isinstance(last, dict) and isinstance(last.get("id"), str):
            after_id = last["id"]
        else:
            break
    return all_files


def parse_file_specs(file_specs: list[str]) -> list[FileAttachment]:
    out: list[FileAttachment] = []
    expanded: list[str] = []
    for s in file_specs:
        expanded.extend(p for p in s.split() if p)
    for spec in expanded:
        colon = spec.find(":")
        if colon == -1:
            continue
        file_id = spec[:colon]
        rel = spec[colon + 1 :]
        if file_id and rel:
            out.append(FileAttachment(file_id=file_id, relative_path=rel))
        else:
            logger.error("files_api_bad_spec", spec=spec)
    return out
