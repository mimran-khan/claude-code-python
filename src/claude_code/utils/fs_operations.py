"""
Filesystem abstraction and path helpers (Node fs parity subset).

Migrated from: utils/fsOperations.ts
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path
from typing import Any, BinaryIO, Protocol, runtime_checkable

from .errors import get_errno_code


@runtime_checkable
class FsOperations(Protocol):
    def cwd(self) -> str: ...
    def exists_sync(self, path: str) -> bool: ...
    async def stat(self, path: str) -> os.stat_result: ...
    async def readdir(self, path: str) -> list[os.DirEntry]: ...
    async def unlink(self, path: str) -> None: ...
    async def rmdir(self, path: str) -> None: ...
    async def rm(self, path: str, *, recursive: bool = False, force: bool = False) -> None: ...
    async def mkdir(self, path: str, *, mode: int | None = None) -> None: ...
    async def read_file(self, path: str, *, encoding: str) -> str: ...
    async def rename(self, old_path: str, new_path: str) -> None: ...
    def stat_sync(self, path: str) -> os.stat_result: ...
    def lstat_sync(self, path: str) -> os.stat_result: ...
    def read_file_sync(self, path: str, *, encoding: str) -> str: ...
    def read_file_bytes_sync(self, path: str) -> bytes: ...
    def read_sync(self, path: str, *, length: int) -> tuple[bytes, int]: ...
    def append_file_sync(self, path: str, data: str, *, mode: int | None = None) -> None: ...
    def copy_file_sync(self, src: str, dest: str) -> None: ...
    def unlink_sync(self, path: str) -> None: ...
    def rename_sync(self, old_path: str, new_path: str) -> None: ...
    def link_sync(self, target: str, path: str) -> None: ...
    def symlink_sync(self, target: str, path: str, *, dir_fd: int | None = None) -> None: ...
    def readlink_sync(self, path: str) -> str: ...
    def realpath_sync(self, path: str) -> str: ...
    def mkdir_sync(self, path: str, *, mode: int | None = None) -> None: ...
    def readdir_sync(self, path: str) -> list[os.DirEntry]: ...
    def readdir_string_sync(self, path: str) -> list[str]: ...
    def is_dir_empty_sync(self, path: str) -> bool: ...
    def rmdir_sync(self, path: str) -> None: ...
    def rm_sync(self, path: str, *, recursive: bool = False, force: bool = False) -> None: ...
    def create_write_stream(self, path: str) -> BinaryIO: ...
    async def read_file_bytes(self, path: str, max_bytes: int | None = None) -> bytes: ...


class NodeFsOperations:
    def cwd(self) -> str:
        return os.getcwd()

    def exists_sync(self, path: str) -> bool:
        return os.path.exists(path)

    async def stat(self, path: str) -> os.stat_result:
        import asyncio

        return await asyncio.to_thread(os.stat, path)

    async def readdir(self, path: str) -> list[os.DirEntry]:
        import asyncio

        return await asyncio.to_thread(lambda: list(os.scandir(path)))

    async def unlink(self, path: str) -> None:
        import asyncio

        await asyncio.to_thread(os.unlink, path)

    async def rmdir(self, path: str) -> None:
        import asyncio

        await asyncio.to_thread(os.rmdir, path)

    async def rm(self, path: str, *, recursive: bool = False, force: bool = False) -> None:
        import asyncio

        def _rm() -> None:
            if recursive:
                shutil.rmtree(path, ignore_errors=force)
            else:
                os.unlink(path)

        await asyncio.to_thread(_rm)

    async def mkdir(self, path: str, *, mode: int | None = None) -> None:
        import asyncio

        def _mk() -> None:
            try:
                os.makedirs(path, mode=mode or 0o777, exist_ok=True)
            except OSError as e:
                if get_errno_code(e) != "EEXIST":
                    raise

        await asyncio.to_thread(_mk)

    async def read_file(self, path: str, *, encoding: str) -> str:
        import asyncio

        def _r() -> str:
            with open(path, encoding=encoding) as f:
                return f.read()

        return await asyncio.to_thread(_r)

    async def rename(self, old_path: str, new_path: str) -> None:
        import asyncio

        await asyncio.to_thread(os.rename, old_path, new_path)

    def stat_sync(self, path: str) -> os.stat_result:
        return os.stat(path)

    def lstat_sync(self, path: str) -> os.stat_result:
        return os.lstat(path)

    def read_file_sync(self, path: str, *, encoding: str) -> str:
        with open(path, encoding=encoding) as f:
            return f.read()

    def read_file_bytes_sync(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    def read_sync(self, path: str, *, length: int) -> tuple[bytes, int]:
        with open(path, "rb") as f:
            buf = f.read(length)
            return buf, len(buf)

    def append_file_sync(self, path: str, data: str, *, mode: int | None = None) -> None:
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        fd = os.open(path, flags, mode or 0o666)
        try:
            os.write(fd, data.encode("utf-8"))
        finally:
            os.close(fd)

    def copy_file_sync(self, src: str, dest: str) -> None:
        shutil.copy2(src, dest)

    def unlink_sync(self, path: str) -> None:
        os.unlink(path)

    def rename_sync(self, old_path: str, new_path: str) -> None:
        os.rename(old_path, new_path)

    def link_sync(self, target: str, path: str) -> None:
        os.link(target, path)

    def symlink_sync(self, target: str, path: str, *, dir_fd: int | None = None) -> None:
        os.symlink(target, path, dir_fd=dir_fd)

    def readlink_sync(self, path: str) -> str:
        return os.readlink(path)

    def realpath_sync(self, path: str) -> str:
        return str(Path(path).resolve())

    def mkdir_sync(self, path: str, *, mode: int | None = None) -> None:
        try:
            os.makedirs(path, mode=mode or 0o777, exist_ok=True)
        except OSError as e:
            if get_errno_code(e) != "EEXIST":
                raise

    def readdir_sync(self, path: str) -> list[os.DirEntry]:
        return list(os.scandir(path))

    def readdir_string_sync(self, path: str) -> list[str]:
        return os.listdir(path)

    def is_dir_empty_sync(self, path: str) -> bool:
        with os.scandir(path) as it:
            return next(it, None) is None

    def rmdir_sync(self, path: str) -> None:
        os.rmdir(path)

    def rm_sync(self, path: str, *, recursive: bool = False, force: bool = False) -> None:
        if recursive:
            shutil.rmtree(path, ignore_errors=force)
        else:
            os.unlink(path)

    def create_write_stream(self, path: str) -> BinaryIO:
        return open(path, "ab")

    async def read_file_bytes(self, path: str, max_bytes: int | None = None) -> bytes:
        import asyncio

        def _rb() -> bytes:
            with open(path, "rb") as f:
                return f.read() if max_bytes is None else f.read(max_bytes)

        return await asyncio.to_thread(_rb)


_active_fs: FsOperations = NodeFsOperations()


def set_fs_implementation(implementation: FsOperations) -> None:
    global _active_fs
    _active_fs = implementation


def get_fs_implementation() -> FsOperations:
    return _active_fs


def set_original_fs_implementation() -> None:
    set_fs_implementation(NodeFsOperations())


def safe_resolve_path(
    fs: FsOperations,
    file_path: str,
) -> tuple[str, bool, bool]:
    if file_path.startswith("//") or file_path.startswith("\\\\"):
        return file_path, False, False
    try:
        st = fs.lstat_sync(file_path)
        if stat.S_ISFIFO(st.st_mode) or stat.S_ISSOCK(st.st_mode):
            return file_path, False, False
        if stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode):
            return file_path, False, False
        resolved = fs.realpath_sync(file_path)
        return resolved, resolved != file_path, True
    except OSError:
        return file_path, False, False


def is_duplicate_path(fs: FsOperations, file_path: str, loaded_paths: set[str]) -> bool:
    resolved, _, _ = safe_resolve_path(fs, file_path)
    if resolved in loaded_paths:
        return True
    loaded_paths.add(resolved)
    return False


def resolve_deepest_existing_ancestor_sync(fs: FsOperations, absolute_path: str) -> str | None:
    import os.path as op

    directory = absolute_path
    segments: list[str] = []
    while directory != op.dirname(directory):
        try:
            st = fs.lstat_sync(directory)
        except OSError:
            segments.insert(0, op.basename(directory))
            directory = op.dirname(directory)
            continue
        if stat.S_ISLNK(st.st_mode):
            try:
                resolved = fs.realpath_sync(directory)
                return resolved if not segments else op.join(resolved, *segments)
            except OSError:
                target = fs.readlink_sync(directory)
                abs_target = target if op.isabs(target) else op.normpath(op.join(op.dirname(directory), target))
                return abs_target if not segments else op.join(abs_target, *segments)
        try:
            resolved = fs.realpath_sync(directory)
            if resolved != directory:
                return resolved if not segments else op.join(resolved, *segments)
        except OSError:
            return None
        return None
    return None


def get_paths_for_permission_check(input_path: str) -> list[str]:
    import os.path as op

    from .path_utils import contains_path_traversal

    path_set: set[str] = set()
    path = input_path
    home = str(Path.home())
    if path == "~":
        path = home
    elif path.startswith("~/"):
        path = op.join(home, path[2:])
    path_set.add(path)
    if path.startswith("//") or path.startswith("\\\\"):
        return list(path_set)
    fs_impl = get_fs_implementation()
    if contains_path_traversal(path):
        return list(path_set)
    try:
        current = path
        visited: set[str] = set()
        for _ in range(40):
            if current in visited:
                break
            visited.add(current)
            if not fs_impl.exists_sync(current):
                if current == path:
                    deeper = resolve_deepest_existing_ancestor_sync(fs_impl, path)
                    if deeper:
                        path_set.add(deeper)
                break
            st = fs_impl.lstat_sync(current)
            if stat.S_ISFIFO(st.st_mode) or stat.S_ISSOCK(st.st_mode):
                break
            if stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode):
                break
            if not stat.S_ISLNK(st.st_mode):
                break
            target = fs_impl.readlink_sync(current)
            abs_target = target if op.isabs(target) else op.normpath(op.join(op.dirname(current), target))
            path_set.add(abs_target)
            current = abs_target
    except OSError:
        pass
    resolved, is_symlink, _ = safe_resolve_path(fs_impl, path)
    if is_symlink and resolved != path:
        path_set.add(resolved)
    return list(path_set)


async def read_file_range(path: str, offset: int, max_bytes: int) -> dict[str, Any] | None:
    import aiofiles

    async with aiofiles.open(path, "rb") as fh:
        await fh.seek(0, os.SEEK_END)
        size = await fh.tell()
        if size <= offset:
            return None
        to_read = min(size - offset, max_bytes)
        await fh.seek(offset)
        raw = await fh.read(to_read)
    return {
        "content": raw.decode("utf-8", errors="replace"),
        "bytesRead": len(raw),
        "bytesTotal": size,
    }


async def tail_file(path: str, max_bytes: int) -> dict[str, Any]:
    import aiofiles

    async with aiofiles.open(path, "rb") as fh:
        await fh.seek(0, os.SEEK_END)
        size = await fh.tell()
        if size == 0:
            return {"content": "", "bytesRead": 0, "bytesTotal": 0}
        off = max(0, size - max_bytes)
        await fh.seek(off)
        raw = await fh.read(size - off)
    return {
        "content": raw.decode("utf-8", errors="replace"),
        "bytesRead": len(raw),
        "bytesTotal": size,
    }


async def read_lines_reverse(path: str):
    """Yield lines from EOF toward BOF; UTF-8 safe across chunk boundaries."""
    import aiofiles

    chunk_size = 4096
    async with aiofiles.open(path, "rb") as fh:
        await fh.seek(0, os.SEEK_END)
        position = await fh.tell()
        remainder = b""
        while position > 0:
            read_len = min(chunk_size, position)
            position -= read_len
            await fh.seek(position)
            chunk = await fh.read(read_len)
            combined = chunk + remainder
            first_nl = combined.find(b"\n")
            if first_nl == -1:
                remainder = combined
                continue
            remainder = combined[:first_nl]
            text_tail = combined[first_nl + 1 :].decode("utf-8", errors="replace")
            for line in reversed(text_tail.split("\n")):
                if line:
                    yield line
        if remainder:
            yield remainder.decode("utf-8", errors="replace")
