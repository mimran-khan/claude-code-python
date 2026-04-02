"""
Deep link URL parsing.

Migrated from: utils/deepLink/parseDeepLink.ts
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

DEEP_LINK_PROTOCOL = "claude-cli"

# Maximum lengths for security
MAX_QUERY_LENGTH = 5000
MAX_CWD_LENGTH = 4096

# Repo slug pattern: owner/repo
REPO_SLUG_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")


@dataclass
class DeepLinkAction:
    """Parsed deep link action."""

    query: str | None = None
    cwd: str | None = None
    repo: str | None = None


def _contains_control_chars(s: str) -> bool:
    """
    Check if string contains ASCII control characters.

    These can act as command separators in shells.
    """
    for char in s:
        code = ord(char)
        if code <= 0x1F or code == 0x7F:
            return True
    return False


def _sanitize_unicode(s: str) -> str:
    """
    Sanitize Unicode string.

    Normalizes and removes potentially dangerous characters.
    """
    import unicodedata

    # Normalize to NFC form
    s = unicodedata.normalize("NFC", s)

    # Remove zero-width characters and other invisibles
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)

    return s


def is_deep_link(url: str) -> bool:
    """
    Check if a URL is a deep link.

    Args:
        url: URL to check

    Returns:
        True if it's a deep link
    """
    return url.startswith(f"{DEEP_LINK_PROTOCOL}://")


def parse_deep_link(url: str) -> DeepLinkAction | None:
    """
    Parse a deep link URL.

    Args:
        url: Deep link URL

    Returns:
        DeepLinkAction or None if invalid
    """
    try:
        parsed = urlparse(url)

        # Verify protocol
        if parsed.scheme != DEEP_LINK_PROTOCOL:
            return None

        # Only support 'open' action
        if parsed.netloc != "open":
            return None

        # Parse query parameters
        params = parse_qs(parsed.query)

        action = DeepLinkAction()

        # Parse query (q parameter)
        if "q" in params:
            query = params["q"][0]
            query = unquote(query)
            query = _sanitize_unicode(query)

            # Security checks
            if len(query) > MAX_QUERY_LENGTH:
                return None

            if _contains_control_chars(query):
                return None

            action.query = query

        # Parse cwd parameter
        if "cwd" in params:
            cwd = params["cwd"][0]
            cwd = unquote(cwd)
            cwd = _sanitize_unicode(cwd)

            # Security checks
            if len(cwd) > MAX_CWD_LENGTH:
                return None

            if _contains_control_chars(cwd):
                return None

            # Must be absolute path
            if not cwd.startswith("/"):
                return None

            action.cwd = cwd

        # Parse repo parameter
        if "repo" in params:
            repo = params["repo"][0]
            repo = unquote(repo)

            # Validate repo slug format
            if not REPO_SLUG_PATTERN.match(repo):
                return None

            action.repo = repo

        return action

    except Exception:
        return None


def build_deep_link(
    query: str | None = None,
    cwd: str | None = None,
    repo: str | None = None,
) -> str:
    """
    Build a deep link URL.

    Args:
        query: Pre-fill query
        cwd: Working directory
        repo: Repository slug

    Returns:
        Deep link URL
    """
    from urllib.parse import quote, urlencode

    params = {}

    if query:
        params["q"] = query

    if cwd:
        params["cwd"] = cwd

    if repo:
        params["repo"] = repo

    if params:
        query_string = urlencode(params, quote_via=quote)
        return f"{DEEP_LINK_PROTOCOL}://open?{query_string}"

    return f"{DEEP_LINK_PROTOCOL}://open"
