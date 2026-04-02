"""
Web Fetch Tool.

Fetch content from URLs.

Migrated from: tools/WebFetchTool/*.ts
"""

from .fetch_utils import DomainBlockedError, DomainCheckFailedError, EgressBlockedError
from .web_fetch_tool import (
    WEB_FETCH_TOOL_NAME,
    WebFetchTool,
    fetch_url,
)

__all__ = [
    "DomainBlockedError",
    "DomainCheckFailedError",
    "EgressBlockedError",
    "WebFetchTool",
    "WEB_FETCH_TOOL_NAME",
    "fetch_url",
]
