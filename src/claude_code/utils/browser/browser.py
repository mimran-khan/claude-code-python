"""Browser and file-opener helpers."""

from __future__ import annotations

import asyncio
import os
import platform
import subprocess
from urllib.parse import urlparse


def _validate_http_url(url: str) -> None:
    try:
        parsed = urlparse(url)
    except Exception as e:  # noqa: BLE001 — mirror TS URL ctor
        raise ValueError(f"Invalid URL format: {url}") from e
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL protocol: must use http:// or https://, got {parsed.scheme}:")


async def open_path(path: str) -> bool:
    """Open a file or folder with the OS default application."""
    try:
        system = platform.system()
        if system == "Windows":
            proc = await asyncio.to_thread(
                subprocess.run,
                ["explorer", path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return proc.returncode == 0
        cmd = "open" if system == "Darwin" else "xdg-open"
        proc = await asyncio.to_thread(
            subprocess.run,
            [cmd, path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


async def open_browser(url: str) -> bool:
    """Open an http(s) URL in the user's browser."""
    try:
        _validate_http_url(url)
    except ValueError:
        return False
    try:
        system = platform.system()
        browser_env = os.environ.get("BROWSER")
        if system == "Windows":
            if browser_env:
                proc = await asyncio.to_thread(
                    subprocess.run,
                    browser_env,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                return proc.returncode == 0
            proc = await asyncio.to_thread(
                subprocess.run,
                ["rundll32", "url,OpenURL", url],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return proc.returncode == 0
        cmd = browser_env or ("open" if system == "Darwin" else "xdg-open")
        proc = await asyncio.to_thread(
            subprocess.run,
            [cmd, url],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
