"""
GitHub CLI authentication status.

Migrated from: utils/github/ghAuthStatus.ts
"""

import asyncio
import shutil
from typing import Literal

GhAuthStatus = Literal["authenticated", "not_authenticated", "not_installed"]


async def get_gh_auth_status() -> GhAuthStatus:
    """Get gh CLI install + auth status.

    Uses shutil.which first (no subprocess) to detect install, then
    exit code of `gh auth token` to detect auth. Uses `auth token` instead
    of `auth status` because the latter makes a network request to GitHub's
    API, while `auth token` only reads local config/keyring.

    Returns:
        "authenticated", "not_authenticated", or "not_installed"
    """
    # Check if gh is installed
    gh_path = shutil.which("gh")
    if not gh_path:
        return "not_installed"

    try:
        proc = await asyncio.create_subprocess_exec(
            "gh",
            "auth",
            "token",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        # Wait with timeout
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except TimeoutError:
            proc.kill()
            return "not_authenticated"

        return "authenticated" if proc.returncode == 0 else "not_authenticated"

    except Exception:
        return "not_authenticated"


def is_gh_installed() -> bool:
    """Check if gh CLI is installed."""
    return shutil.which("gh") is not None


async def is_gh_authenticated() -> bool:
    """Check if gh CLI is authenticated."""
    status = await get_gh_auth_status()
    return status == "authenticated"
