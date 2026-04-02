"""
Git remote parsing and repository detection.

Migrated from: utils/detectRepository.ts
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass

from .cwd import get_cwd
from .debug import log_for_debugging
from .git import get_remote_url


@dataclass(frozen=True)
class ParsedRepository:
    host: str
    owner: str
    name: str


_repository_with_host_cache: dict[str, ParsedRepository | None] = {}


def clear_repository_caches() -> None:
    _repository_with_host_cache.clear()


async def detect_current_repository() -> str | None:
    result = await detect_current_repository_with_host()
    if not result:
        return None
    if result.host != "github.com":
        return None
    return f"{result.owner}/{result.name}"


async def detect_current_repository_with_host() -> ParsedRepository | None:
    cwd = get_cwd()
    if cwd in _repository_with_host_cache:
        return _repository_with_host_cache[cwd]

    try:
        remote_url = await asyncio.to_thread(get_remote_url, cwd, "origin")
        log_for_debugging(f"Git remote URL: {remote_url}")
        if not remote_url:
            log_for_debugging("No git remote URL found")
            _repository_with_host_cache[cwd] = None
            return None
        parsed = parse_git_remote(remote_url)
        log_for_debugging(
            f"Parsed repository: {parsed.host}/{parsed.owner}/{parsed.name} from URL: {remote_url}"
            if parsed
            else f"Parsed repository: None from URL: {remote_url}"
        )
        _repository_with_host_cache[cwd] = parsed
        return parsed
    except Exception as exc:  # noqa: BLE001 — parity with TS catch
        log_for_debugging(f"Error detecting repository: {exc}")
        _repository_with_host_cache[cwd] = None
        return None


def get_cached_repository() -> str | None:
    parsed = _repository_with_host_cache.get(get_cwd())
    if not parsed or parsed.host != "github.com":
        return None
    return f"{parsed.owner}/{parsed.name}"


def parse_git_remote(input_url: str) -> ParsedRepository | None:
    trimmed = input_url.strip()

    ssh_match = re.match(
        r"^git@([^:]+):([^/]+)/([^/]+?)(?:\.git)?$",
        trimmed,
    )
    if ssh_match:
        host, owner, name = ssh_match.group(1), ssh_match.group(2), ssh_match.group(3)
        if host and owner and name and _looks_like_real_hostname(host):
            return ParsedRepository(host=host, owner=owner, name=name)
        return None

    url_match = re.match(
        r"^(https?|ssh|git)://(?:[^@]+@)?([^/:]+(?::\d+)?)/([^/]+)/([^/]+?)(?:\.git)?$",
        trimmed,
    )
    if url_match:
        protocol = url_match.group(1)
        host_with_port = url_match.group(2)
        owner = url_match.group(3)
        name = url_match.group(4)
        host_without_port = (host_with_port.split(":")[0] if host_with_port else "") or ""
        if not _looks_like_real_hostname(host_without_port):
            return None
        host = host_with_port if protocol in ("https", "http") else host_without_port
        return ParsedRepository(host=host, owner=owner, name=name)

    return None


def parse_github_repository(input_url: str) -> str | None:
    trimmed = input_url.strip()
    parsed = parse_git_remote(trimmed)
    if parsed:
        if parsed.host != "github.com":
            return None
        return f"{parsed.owner}/{parsed.name}"

    if "://" not in trimmed and "@" not in trimmed and "/" in trimmed:
        parts = trimmed.split("/")
        if len(parts) == 2 and parts[0] and parts[1]:
            repo = re.sub(r"\.git$", "", parts[1])
            return f"{parts[0]}/{repo}"

    log_for_debugging(f"Could not parse repository from: {trimmed}")
    return None


def _looks_like_real_hostname(host: str) -> bool:
    if "." not in host:
        return False
    last_segment = host.split(".")[-1]
    if not last_segment:
        return False
    return bool(re.fullmatch(r"[a-zA-Z]+", last_segment))
