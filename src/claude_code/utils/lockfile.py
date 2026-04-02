"""
File Locking Utilities.

Provides file locking functionality.
"""

from __future__ import annotations

import asyncio
import fcntl
import os
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager, suppress
from pathlib import Path


class LockError(Exception):
    """Error acquiring a lock."""

    pass


def _get_lock_path(file_path: str) -> str:
    """Get the lock file path for a file.

    Args:
        file_path: The file to lock

    Returns:
        The lock file path
    """
    return f"{file_path}.lock"


@contextmanager
def lock_sync(file_path: str, *, timeout: float = 10.0) -> Iterator[None]:
    """Acquire a file lock synchronously.

    Args:
        file_path: The file to lock
        timeout: Timeout in seconds

    Yields:
        None when lock is acquired

    Raises:
        LockError: If lock cannot be acquired
    """
    lock_path = _get_lock_path(file_path)

    # Ensure parent directory exists
    Path(lock_path).parent.mkdir(parents=True, exist_ok=True)

    lock_file = None
    try:
        lock_file = open(lock_path, "w")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except BlockingIOError:
        raise LockError(f"Could not acquire lock on {file_path}")
    finally:
        if lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            with suppress(OSError):
                os.unlink(lock_path)


@asynccontextmanager
async def lock(file_path: str, *, timeout: float = 10.0) -> AsyncIterator[None]:
    """Acquire a file lock asynchronously.

    Args:
        file_path: The file to lock
        timeout: Timeout in seconds

    Yields:
        None when lock is acquired

    Raises:
        LockError: If lock cannot be acquired
    """
    lock_path = _get_lock_path(file_path)

    # Ensure parent directory exists
    Path(lock_path).parent.mkdir(parents=True, exist_ok=True)

    lock_file = None
    start_time = asyncio.get_event_loop().time()

    while True:
        try:
            lock_file = open(lock_path, "w")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if lock_file:
                lock_file.close()
                lock_file = None

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise LockError(f"Could not acquire lock on {file_path}")

            await asyncio.sleep(0.1)

    try:
        yield
    finally:
        if lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            with suppress(OSError):
                os.unlink(lock_path)


async def unlock(file_path: str) -> None:
    """Release a file lock.

    Args:
        file_path: The file to unlock
    """
    lock_path = _get_lock_path(file_path)
    with suppress(OSError):
        os.unlink(lock_path)


async def check(file_path: str) -> bool:
    """Check if a file is locked.

    Args:
        file_path: The file to check

    Returns:
        True if locked
    """
    lock_path = _get_lock_path(file_path)

    if not os.path.exists(lock_path):
        return False

    try:
        with open(lock_path, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
