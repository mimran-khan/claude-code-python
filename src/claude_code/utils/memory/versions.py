"""
Memory versioning.

Migrated from: utils/memory/versions.ts
"""

from dataclasses import dataclass
from typing import Optional

from ..git import find_git_root


@dataclass
class MemoryVersion:
    """Memory format version."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, version_str: str) -> Optional["MemoryVersion"]:
        """Parse version string."""
        try:
            parts = version_str.split(".")
            if len(parts) != 3:
                return None
            return cls(
                major=int(parts[0]),
                minor=int(parts[1]),
                patch=int(parts[2]),
            )
        except (ValueError, IndexError):
            return None


# Current memory format version
CURRENT_VERSION = MemoryVersion(major=1, minor=0, patch=0)


def get_current_version() -> MemoryVersion:
    """Get the current memory format version."""
    return CURRENT_VERSION


def is_version_compatible(version: MemoryVersion) -> bool:
    """Check if a version is compatible with current.

    Compatible if major version matches.
    """
    return version.major == CURRENT_VERSION.major


def needs_migration(version: MemoryVersion) -> bool:
    """Check if a version needs migration."""
    if version.major < CURRENT_VERSION.major:
        return True
    return bool(version.major == CURRENT_VERSION.major and version.minor < CURRENT_VERSION.minor)


def project_is_in_git_repo(cwd: str) -> bool:
    """Return True if *cwd* is inside a git work tree (filesystem walk, no subprocess)."""
    return find_git_root(cwd) is not None
