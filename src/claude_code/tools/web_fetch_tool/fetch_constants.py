"""
Constants for WebFetch HTTP limits and markdown sizing.

Migrated from: tools/WebFetchTool/utils.ts (excerpt)
"""

from __future__ import annotations

MAX_MARKDOWN_LENGTH = 100_000
MAX_URL_LENGTH = 2000
MAX_HTTP_CONTENT_LENGTH = 10 * 1024 * 1024
FETCH_TIMEOUT_SEC = 60.0
DOMAIN_CHECK_TIMEOUT_SEC = 10.0
CACHE_TTL_SEC = 15 * 60
MAX_CACHE_SIZE_BYTES = 50 * 1024 * 1024
