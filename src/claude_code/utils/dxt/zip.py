"""
Zip extraction with zip-bomb guards.

Migrated from: utils/dxt/zip.ts
"""

from __future__ import annotations

import io
import os
import zipfile
from dataclasses import dataclass, field

from ..debug import log_for_debugging
from ..errors import is_enoent
from ..fs_operations import get_fs_implementation
from ..path_utils import contains_path_traversal

LIMITS = {
    "MAX_FILE_SIZE": 512 * 1024 * 1024,
    "MAX_TOTAL_SIZE": 1024 * 1024 * 1024,
    "MAX_FILE_COUNT": 100_000,
    "MAX_COMPRESSION_RATIO": 50,
}


@dataclass
class ZipValidationState:
    file_count: int = 0
    total_uncompressed_size: int = 0
    compressed_size: int = 0
    errors: list[str] = field(default_factory=list)


def is_path_safe(file_path: str) -> bool:
    if contains_path_traversal(file_path):
        return False
    normalized = os.path.normpath(file_path)
    return not os.path.isabs(normalized)


def validate_zip_file(
    name: str,
    original_size: int,
    state: ZipValidationState,
) -> tuple[bool, str | None]:
    state.file_count += 1
    error: str | None = None
    if state.file_count > LIMITS["MAX_FILE_COUNT"]:
        error = f"Archive contains too many files: {state.file_count} (max: {LIMITS['MAX_FILE_COUNT']})"
    elif not is_path_safe(name):
        error = f'Unsafe file path detected: "{name}". Path traversal or absolute paths are not allowed.'
    elif original_size > LIMITS["MAX_FILE_SIZE"]:
        error = (
            f'File "{name}" is too large: {original_size // (1024 * 1024)}MB '
            f"(max: {LIMITS['MAX_FILE_SIZE'] // (1024 * 1024)}MB)"
        )
    else:
        state.total_uncompressed_size += original_size
        if state.total_uncompressed_size > LIMITS["MAX_TOTAL_SIZE"]:
            error = (
                f"Archive total size is too large: "
                f"{state.total_uncompressed_size // (1024 * 1024)}MB "
                f"(max: {LIMITS['MAX_TOTAL_SIZE'] // (1024 * 1024)}MB)"
            )
        elif state.compressed_size > 0:
            ratio = state.total_uncompressed_size / state.compressed_size
            if ratio > LIMITS["MAX_COMPRESSION_RATIO"]:
                error = (
                    f"Suspicious compression ratio detected: {ratio:.1f}:1 "
                    f"(max: {LIMITS['MAX_COMPRESSION_RATIO']}:1). This may be a zip bomb."
                )
    return (error is None, error)


async def unzip_file(zip_data: bytes) -> dict[str, bytes]:
    state = ZipValidationState(compressed_size=len(zip_data))
    out: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            ok, err = validate_zip_file(info.filename, info.file_size, state)
            if not ok:
                raise ValueError(err or "invalid zip entry")
            out[info.filename] = zf.read(info.filename)
    log_for_debugging(
        f"Zip extraction completed: {state.file_count} files, {state.total_uncompressed_size // 1024}KB uncompressed"
    )
    return out


def parse_zip_modes(data: bytes | bytearray | memoryview) -> dict[str, int]:
    buf = memoryview(data)
    modes: dict[str, int] = {}

    def u32le(i: int) -> int:
        return int.from_bytes(buf[i : i + 4], "little")

    def u16le(i: int) -> int:
        return int.from_bytes(buf[i : i + 2], "little")

    min_eocd = max(0, len(buf) - 22 - 0xFFFF)
    eocd = -1
    for i in range(len(buf) - 22, min_eocd - 1, -1):
        if u32le(i) == 0x06054B50:
            eocd = i
            break
    if eocd < 0:
        return modes
    entry_count = u16le(eocd + 10)
    off = u32le(eocd + 16)
    for _ in range(entry_count):
        if off + 46 > len(buf) or u32le(off) != 0x02014B50:
            break
        version_made_by = u16le(off + 4)
        name_len = u16le(off + 28)
        extra_len = u16le(off + 30)
        comment_len = u16le(off + 32)
        external_attr = u32le(off + 38)
        name = bytes(buf[off + 46 : off + 46 + name_len]).decode("utf-8", errors="replace")
        if (version_made_by >> 8) == 3:
            mode = (external_attr >> 16) & 0xFFFF
            if mode:
                modes[name] = mode
        off += 46 + name_len + extra_len + comment_len
    return modes


async def read_and_unzip_file(file_path: str) -> dict[str, bytes]:
    fs = get_fs_implementation()
    try:
        raw = await fs.read_file_bytes(file_path)
        return await unzip_file(raw)
    except Exception as error:
        if is_enoent(error):
            raise
        msg = str(error) if isinstance(error, Exception) else str(error)
        raise RuntimeError(f"Failed to read or unzip file: {msg}") from error
