"""`claude update` command. Migrated from: cli/update.ts (simplified)."""

from __future__ import annotations

import os
import sys

import httpx

from .. import __version__


async def update_cli() -> None:
    """Check PyPI / registry for newer claude-code package (simplified vs npm doctor flow)."""
    sys.stdout.write(f"Current version: {__version__}\n")
    pkg = os.environ.get("CLAUDE_CODE_PYPI_PACKAGE", "claude-code")
    url = f"https://pypi.org/pypi/{pkg}/json"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url)
        if r.status_code != 200:
            sys.stderr.write("Could not reach PyPI for version check.\n")
            return
        data = r.json()
        latest = data.get("info", {}).get("version", "")
        sys.stdout.write(f"Latest published {pkg}: {latest}\n")
        if latest and latest != __version__:
            sys.stdout.write(f"Update with: pip install -U {pkg}\n")
        else:
            sys.stdout.write("You are up to date.\n")
    except httpx.HTTPError as e:
        sys.stderr.write(f"Update check failed: {e}\n")
