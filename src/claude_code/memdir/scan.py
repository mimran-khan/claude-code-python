"""
Memory file scanning.

Scan directories for memory files.

Migrated from: memdir/memoryScan.ts
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .memory import ENTRYPOINT_NAME


@dataclass
class MemoryFile:
    """A discovered memory file."""

    path: str
    name: str
    size: int
    is_entrypoint: bool = False
    content: str | None = None


@dataclass
class MemoryScanResult:
    """Result of scanning for memory files."""

    files: list[MemoryFile] = field(default_factory=list)
    entrypoint: MemoryFile | None = None
    total_size: int = 0


def scan_memory_files(
    directory: str,
    max_files: int = 100,
    include_content: bool = False,
) -> MemoryScanResult:
    """
    Scan a directory for memory files.

    Args:
        directory: Directory to scan
        max_files: Maximum files to return
        include_content: Include file content

    Returns:
        MemoryScanResult
    """
    result = MemoryScanResult()

    if not os.path.isdir(directory):
        return result

    try:
        for entry in os.listdir(directory):
            path = os.path.join(directory, entry)

            # Only process markdown files
            if not entry.endswith(".md"):
                continue

            if not os.path.isfile(path):
                continue

            try:
                stat = os.stat(path)
                size = stat.st_size
            except OSError:
                continue

            content = None
            if include_content:
                try:
                    with open(path) as f:
                        content = f.read()
                except (OSError, UnicodeDecodeError):
                    pass

            is_entrypoint = entry == ENTRYPOINT_NAME

            memory_file = MemoryFile(
                path=path,
                name=entry,
                size=size,
                is_entrypoint=is_entrypoint,
                content=content,
            )

            if is_entrypoint:
                result.entrypoint = memory_file

            result.files.append(memory_file)
            result.total_size += size

            if len(result.files) >= max_files:
                break

    except (OSError, PermissionError):
        pass

    return result


def find_all_memory_files(
    project_dir: str,
    max_depth: int = 3,
) -> list[MemoryFile]:
    """
    Find all memory files in a project.

    Searches in .claude/memory directories.

    Args:
        project_dir: Project root
        max_depth: Maximum directory depth

    Returns:
        List of memory files
    """
    files: list[MemoryFile] = []

    def search(directory: str, depth: int) -> None:
        if depth > max_depth:
            return

        memory_dir = os.path.join(directory, ".claude", "memory")
        if os.path.isdir(memory_dir):
            result = scan_memory_files(memory_dir)
            files.extend(result.files)

        # Search subdirectories
        try:
            for entry in os.listdir(directory):
                if entry.startswith("."):
                    continue

                path = os.path.join(directory, entry)
                if os.path.isdir(path):
                    search(path, depth + 1)
        except (OSError, PermissionError):
            pass

    search(project_dir, 0)
    return files
