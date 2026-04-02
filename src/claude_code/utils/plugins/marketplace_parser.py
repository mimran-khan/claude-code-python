"""
Parse CLI marketplace source strings into structured sources.

Migrated from: utils/plugins/parseMarketplaceInput.ts
"""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

from ..errors import get_errno_code
from ..fs_operations import get_fs_implementation


@dataclass
class MarketplaceGitSource:
    source: Literal["git"]
    url: str
    ref: str | None = None


@dataclass
class MarketplaceUrlSource:
    source: Literal["url"]
    url: str


@dataclass
class MarketplaceFileSource:
    source: Literal["file"]
    path: str


@dataclass
class MarketplaceDirectorySource:
    source: Literal["directory"]
    path: str


@dataclass
class MarketplaceGithubShorthand:
    source: Literal["github"]
    repo: str
    ref: str | None = None


@dataclass
class MarketplaceParseError:
    error: str


MarketplaceInputResult = (
    MarketplaceGitSource
    | MarketplaceUrlSource
    | MarketplaceFileSource
    | MarketplaceDirectorySource
    | MarketplaceGithubShorthand
    | MarketplaceParseError
    | None
)

_SSH = re.compile(r"^([a-zA-Z0-9._-]+@[^:]+:.+?(?:\.git)?)(#(.+))?$")


def _resolve_local_path(trimmed: str) -> str:
    if trimmed.startswith("~"):
        return os.path.normpath(os.path.expanduser(trimmed))
    return os.path.normpath(os.path.abspath(trimmed))


async def parse_marketplace_input(input_str: str) -> MarketplaceInputResult:
    trimmed = input_str.strip()

    m = _SSH.match(trimmed)
    if m and m.group(1):
        url = m.group(1)
        ref = m.group(3)
        return MarketplaceGitSource(source="git", url=url, ref=ref)

    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        frag = re.match(r"^([^#]+)(#(.+))?$", trimmed)
        url_no_frag = frag.group(1) if frag else trimmed
        ref = frag.group(3) if frag and frag.lastindex and frag.lastindex >= 3 else None

        if url_no_frag.endswith(".git") or "/_git/" in url_no_frag:
            return (
                MarketplaceGitSource(source="git", url=url_no_frag, ref=ref)
                if ref
                else MarketplaceGitSource(source="git", url=url_no_frag)
            )

        try:
            u = urlparse(url_no_frag)
        except Exception:
            return MarketplaceUrlSource(source="url", url=url_no_frag)

        host = (u.hostname or "").lower()
        if host in ("github.com", "www.github.com"):
            pm = re.match(r"^/([^/]+\/[^/]+?)(/|\.git|$)", u.path or "")
            if pm and pm.group(1):
                git_url = url_no_frag if url_no_frag.endswith(".git") else f"{url_no_frag}.git"
                return (
                    MarketplaceGitSource(source="git", url=git_url, ref=ref)
                    if ref
                    else MarketplaceGitSource(source="git", url=git_url)
                )

        return MarketplaceUrlSource(source="url", url=url_no_frag)

    is_windows = os.name == "nt"
    is_windows_path = bool(
        is_windows
        and (trimmed.startswith(".\\") or trimmed.startswith("..\\") or re.match(r"^[a-zA-Z]:[/\\]", trimmed))
    )
    if (
        trimmed.startswith("./")
        or trimmed.startswith("../")
        or trimmed.startswith("/")
        or trimmed.startswith("~")
        or is_windows_path
    ):
        resolved_path = _resolve_local_path(trimmed)
        fs = get_fs_implementation()
        try:
            st = await fs.stat(resolved_path)
        except OSError as e:
            code = get_errno_code(e)
            if code == "ENOENT":
                return MarketplaceParseError(error=f"Path does not exist: {resolved_path}")
            return MarketplaceParseError(
                error=f"Cannot access path: {resolved_path} ({code or e})",
            )

        if stat.S_ISREG(st.st_mode):
            if resolved_path.endswith(".json"):
                return MarketplaceFileSource(source="file", path=resolved_path)
            return MarketplaceParseError(
                error=(f"File path must point to a .json file (marketplace.json), but got: {resolved_path}"),
            )
        if stat.S_ISDIR(st.st_mode):
            return MarketplaceDirectorySource(source="directory", path=resolved_path)
        return MarketplaceParseError(
            error=f"Path is neither a file nor a directory: {resolved_path}",
        )

    if "/" in trimmed and not trimmed.startswith("@"):
        if ":" in trimmed:
            return None
        fm = re.match(r"^([^#@]+)(?:[#@](.+))?$", trimmed)
        repo = fm.group(1) if fm else trimmed
        ref = fm.group(2) if fm and fm.lastindex and fm.lastindex >= 2 else None
        return (
            MarketplaceGithubShorthand(source="github", repo=repo, ref=ref)
            if ref
            else MarketplaceGithubShorthand(source="github", repo=repo)
        )

    return None


# Public names expected by :mod:`claude_code.utils.plugins` package ``__init__``
DirectoryMarketplaceSource = MarketplaceDirectorySource
FileMarketplaceSource = MarketplaceFileSource
GitMarketplaceSource = MarketplaceGitSource
GithubMarketplaceSource = MarketplaceGithubShorthand
UrlMarketplaceSource = MarketplaceUrlSource

__all__ = [
    "DirectoryMarketplaceSource",
    "FileMarketplaceSource",
    "GitMarketplaceSource",
    "GithubMarketplaceSource",
    "MarketplaceDirectorySource",
    "MarketplaceFileSource",
    "MarketplaceGitSource",
    "MarketplaceGithubShorthand",
    "MarketplaceInputResult",
    "MarketplaceParseError",
    "MarketplaceUrlSource",
    "UrlMarketplaceSource",
    "parse_marketplace_input",
]
