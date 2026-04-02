"""
Teleport API client.

Migrated from: utils/teleport/api.ts
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Retry configuration
TELEPORT_RETRY_DELAYS = [2000, 4000, 8000, 16000]  # 4 retries with exponential backoff
MAX_TELEPORT_RETRIES = len(TELEPORT_RETRY_DELAYS)

CCR_BYOC_BETA = "ccr-byoc-2025-07-29"

# Session status types
SessionStatus = Literal["requires_action", "running", "idle", "archived"]


@dataclass
class GitSource:
    """Git repository source."""

    type: Literal["git_repository"] = "git_repository"
    url: str = ""
    revision: str | None = None
    allow_unrestricted_git_push: bool = False


@dataclass
class KnowledgeBaseSource:
    """Knowledge base source."""

    type: Literal["knowledge_base"] = "knowledge_base"
    knowledge_base_id: str = ""


SessionContextSource = GitSource | KnowledgeBaseSource


@dataclass
class RemoteMessageContent:
    """Content for remote session messages."""

    type: str
    data: dict[str, Any]


def is_transient_network_error(error: BaseException) -> bool:
    """True for connection/timeout failures and HTTP 5xx (retry candidates)."""
    try:
        import httpx
    except ImportError:
        httpx = None  # type: ignore[assignment]

    if httpx is not None:
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code >= 500
        if isinstance(error, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
            return True

    error_str = str(error).lower()
    if any(term in error_str for term in ("connection", "timeout", "network", "refused", "connect")):
        return True
    return any(code in error_str for code in ("500", "502", "503", "504"))


async def _sleep_ms(ms: int) -> None:
    """Sleep for milliseconds."""
    await asyncio.sleep(ms / 1000)


async def http_get_with_retry(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Make HTTP GET request with automatic retry for transient errors.

    Uses exponential backoff: 2s, 4s, 8s, 16s (4 retries = 5 total attempts)
    """
    import httpx

    last_error: Exception | None = None

    for attempt in range(MAX_TELEPORT_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as error:
            last_error = error

            if not is_transient_network_error(error):
                raise

            if attempt >= MAX_TELEPORT_RETRIES:
                logger.warning(f"Teleport request failed after {attempt + 1} attempts: {error}")
                raise

            delay = TELEPORT_RETRY_DELAYS[attempt] if attempt < len(TELEPORT_RETRY_DELAYS) else 2000
            logger.debug(
                f"Teleport request failed (attempt {attempt + 1}/{MAX_TELEPORT_RETRIES + 1}), "
                f"retrying in {delay}ms: {error}"
            )
            await _sleep_ms(delay)

    if last_error:
        raise last_error
    raise RuntimeError("Unexpected retry loop exit")


async def http_post_with_retry(
    url: str,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Make HTTP POST request with automatic retry for transient errors."""
    import httpx

    last_error: Exception | None = None

    for attempt in range(MAX_TELEPORT_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as error:
            last_error = error

            if not is_transient_network_error(error):
                raise

            if attempt >= MAX_TELEPORT_RETRIES:
                logger.warning(f"Teleport request failed after {attempt + 1} attempts: {error}")
                raise

            delay = TELEPORT_RETRY_DELAYS[attempt] if attempt < len(TELEPORT_RETRY_DELAYS) else 2000
            logger.debug(
                f"Teleport request failed (attempt {attempt + 1}/{MAX_TELEPORT_RETRIES + 1}), "
                f"retrying in {delay}ms: {error}"
            )
            await _sleep_ms(delay)

    if last_error:
        raise last_error
    raise RuntimeError("Unexpected retry loop exit")


@dataclass
class PrepareApiRequestResult:
    """OAuth access token and organization UUID for org-scoped API routes."""

    access_token: str
    org_uuid: str


async def prepare_api_request() -> PrepareApiRequestResult:
    """
    Resolve OAuth credentials for organization API calls.

    Full integration reads from secure token storage; env vars support tests
    and headless use.
    """
    import os

    token = os.environ.get("CLAUDE_OAUTH_ACCESS_TOKEN", "") or os.environ.get(
        "ANTHROPIC_AUTH_TOKEN",
        "",
    )
    org = os.environ.get("CLAUDE_ORG_UUID", "") or os.environ.get(
        "X_ORGANIZATION_UUID",
        "",
    )
    return PrepareApiRequestResult(access_token=token, org_uuid=org)


def get_oauth_headers(access_token: str) -> dict[str, str]:
    """Build Authorization header for Bearer OAuth."""
    return {"Authorization": f"Bearer {access_token}"}


async def send_event_to_remote_session(
    session_id: str,
    event: RemoteMessageContent,
    access_token: str,
    base_url: str | None = None,
) -> bool:
    """Send an event to a remote session.

    Args:
        session_id: The remote session ID
        event: The event to send
        access_token: OAuth access token
        base_url: API base URL (defaults to claude.ai)

    Returns:
        True if successful, False otherwise
    """
    import os

    base_url = base_url or os.environ.get("CLAUDE_AI_BASE_URL", "https://claude.ai")
    url = f"{base_url}/api/sessions/{session_id}/events"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        await http_post_with_retry(
            url,
            data={"type": event.type, "data": event.data},
            headers=headers,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send event to remote session: {e}")
        return False
