"""
Plugin versioning.

Version calculation and comparison for plugins.

Migrated from: utils/plugins/pluginVersioning.ts
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass


@dataclass
class VersionInfo:
    """Parsed version information."""

    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: str | None = None
    build: str | None = None

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version


def parse_version(version: str) -> VersionInfo:
    """
    Parse a semver version string.

    Args:
        version: Version string (e.g., "1.2.3-beta+build")

    Returns:
        Parsed VersionInfo
    """
    # Remove leading 'v' if present
    version = version.lstrip("v")

    # Split off build metadata
    build = None
    if "+" in version:
        version, build = version.split("+", 1)

    # Split off prerelease
    prerelease = None
    if "-" in version:
        version, prerelease = version.split("-", 1)

    # Parse major.minor.patch
    parts = version.split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    return VersionInfo(
        major=major,
        minor=minor,
        patch=patch,
        prerelease=prerelease,
        build=build,
    )


def compare_versions(a: str, b: str) -> int:
    """
    Compare two version strings.

    Args:
        a: First version
        b: Second version

    Returns:
        -1 if a < b, 0 if a == b, 1 if a > b
    """
    va = parse_version(a)
    vb = parse_version(b)

    # Compare major
    if va.major != vb.major:
        return -1 if va.major < vb.major else 1

    # Compare minor
    if va.minor != vb.minor:
        return -1 if va.minor < vb.minor else 1

    # Compare patch
    if va.patch != vb.patch:
        return -1 if va.patch < vb.patch else 1

    # Handle prerelease (no prerelease > has prerelease)
    if va.prerelease and not vb.prerelease:
        return -1
    if not va.prerelease and vb.prerelease:
        return 1
    if va.prerelease and vb.prerelease:
        if va.prerelease < vb.prerelease:
            return -1
        if va.prerelease > vb.prerelease:
            return 1

    return 0


def is_newer_version(current: str, candidate: str) -> bool:
    """
    Check if candidate version is newer than current.

    Args:
        current: Current version
        candidate: Candidate version

    Returns:
        True if candidate is newer
    """
    return compare_versions(candidate, current) > 0


def calculate_plugin_version(plugin_path: str) -> str:
    """
    Calculate a version hash for a plugin directory.

    Used for local plugins without explicit versions.

    Args:
        plugin_path: Path to the plugin directory

    Returns:
        Version hash string
    """
    hasher = hashlib.sha256()

    for root, dirs, files in os.walk(plugin_path):
        # Skip hidden directories and node_modules
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]

        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
            except OSError:
                continue

    return hasher.hexdigest()[:12]


def increment_version(version: str, part: str = "patch") -> str:
    """
    Increment a version number.

    Args:
        version: Current version
        part: Which part to increment (major, minor, patch)

    Returns:
        Incremented version string
    """
    v = parse_version(version)

    if part == "major":
        v.major += 1
        v.minor = 0
        v.patch = 0
    elif part == "minor":
        v.minor += 1
        v.patch = 0
    else:  # patch
        v.patch += 1

    v.prerelease = None
    v.build = None

    return str(v)
