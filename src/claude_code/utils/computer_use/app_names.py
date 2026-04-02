"""
Filter installed-app names for MCP tool descriptions.

Migrated from: utils/computerUse/appNames.ts
"""

from __future__ import annotations

import re
import unicodedata
from typing import TypedDict


class InstalledAppLike(TypedDict):
    bundleId: str
    displayName: str
    path: str


PATH_ALLOWLIST: tuple[str, ...] = (
    "/Applications/",
    "/System/Applications/",
)

NAME_PATTERN_BLOCKLIST: tuple[re.Pattern[str], ...] = (
    re.compile(r"Helper(?:$|\s\()"),
    re.compile(r"Agent(?:$|\s\()"),
    re.compile(r"Service(?:$|\s\()"),
    re.compile(r"Uninstaller(?:$|\s\()"),
    re.compile(r"Updater(?:$|\s\()"),
    re.compile(r"^\."),
)

ALWAYS_KEEP_BUNDLE_IDS: frozenset[str] = frozenset(
    {
        "com.apple.Safari",
        "com.google.Chrome",
        "com.microsoft.edgemac",
        "org.mozilla.firefox",
        "company.thebrowser.Browser",
        "com.tinyspeck.slackmacgap",
        "us.zoom.xos",
        "com.microsoft.teams2",
        "com.microsoft.teams",
        "com.apple.MobileSMS",
        "com.apple.mail",
        "com.microsoft.Word",
        "com.microsoft.Excel",
        "com.microsoft.Powerpoint",
        "com.microsoft.Outlook",
        "com.apple.iWork.Pages",
        "com.apple.iWork.Numbers",
        "com.apple.iWork.Keynote",
        "com.google.GoogleDocs",
        "notion.id",
        "com.apple.Notes",
        "md.obsidian",
        "com.linear",
        "com.figma.Desktop",
        "com.microsoft.VSCode",
        "com.apple.Terminal",
        "com.googlecode.iterm2",
        "com.github.GitHubDesktop",
        "com.apple.finder",
        "com.apple.iCal",
        "com.apple.systempreferences",
    }
)

APP_NAME_MAX_LEN = 40
APP_NAME_MAX_COUNT = 50


def _app_name_chars_ok(s: str) -> bool:
    """Unicode letter/number/mark + safe punctuation (TS APP_NAME_ALLOWED, no \\p in std re)."""
    if "\n" in s or "\r" in s:
        return False
    for c in s:
        if c in " _.&'()+-":
            continue
        cat = unicodedata.category(c)
        if cat[0] not in ("L", "N", "M"):
            return False
    return True


def is_user_facing_path(path: str, home_dir: str | None) -> bool:
    if any(path.startswith(root) for root in PATH_ALLOWLIST):
        return True
    if home_dir:
        base = home_dir.rstrip("/")
        user_apps = f"{base}/Applications/"
        if path.startswith(user_apps):
            return True
    return False


def is_noisy_name(name: str) -> bool:
    return any(p.search(name) for p in NAME_PATTERN_BLOCKLIST)


def _sanitize_core(raw: list[str], apply_char_filter: bool) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for name in raw:
        trimmed = name.strip()
        if not trimmed or len(trimmed) > APP_NAME_MAX_LEN:
            continue
        if apply_char_filter and not _app_name_chars_ok(trimmed):
            continue
        if trimmed in seen:
            continue
        seen.add(trimmed)
        out.append(trimmed)
    out.sort(key=lambda s: s.casefold())
    return out


def _sanitize_app_names(raw: list[str]) -> list[str]:
    filtered = _sanitize_core(raw, True)
    if len(filtered) <= APP_NAME_MAX_COUNT:
        return filtered
    extra = len(filtered) - APP_NAME_MAX_COUNT
    return [
        *filtered[:APP_NAME_MAX_COUNT],
        f"… and {extra} more",
    ]


def _sanitize_trusted_names(raw: list[str]) -> list[str]:
    return _sanitize_core(raw, False)


def filter_apps_for_description(
    installed: list[InstalledAppLike],
    home_dir: str | None,
) -> list[str]:
    always_kept: list[str] = []
    rest: list[str] = []
    for app in installed:
        bid = app.get("bundleId", "")
        dname = app.get("displayName", "")
        path = app.get("path", "")
        if bid in ALWAYS_KEEP_BUNDLE_IDS:
            always_kept.append(dname)
        elif is_user_facing_path(path, home_dir) and not is_noisy_name(dname):
            rest.append(dname)
    sanitized_always = _sanitize_trusted_names(always_kept)
    always_set = set(sanitized_always)
    return [
        *sanitized_always,
        *[n for n in _sanitize_app_names(rest) if n not in always_set],
    ]
