"""
Upstream proxy initialization.

Migrated from: upstreamproxy/upstreamproxy.ts
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

SESSION_TOKEN_PATH = "/run/ccr/session_token"
SYSTEM_CA_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"

# Hosts the proxy must NOT intercept
NO_PROXY_LIST = ",".join(
    [
        "localhost",
        "127.0.0.1",
        "::1",
        "169.254.0.0/16",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        # Anthropic API
        "anthropic.com",
        ".anthropic.com",
        "*.anthropic.com",
        # GitHub
        "github.com",
        "api.github.com",
        "*.github.com",
        "*.githubusercontent.com",
        # Package registries
        "registry.npmjs.org",
        "pypi.org",
        "files.pythonhosted.org",
        "index.crates.io",
        "proxy.golang.org",
    ]
)


@dataclass
class UpstreamProxyState:
    """State of the upstream proxy."""

    enabled: bool = False
    port: int | None = None
    ca_bundle_path: str | None = None


_state = UpstreamProxyState()


def is_env_truthy(value: str | None) -> bool:
    """Check if environment variable is truthy."""
    if not value:
        return False
    return value.lower() in ("1", "true", "yes")


async def init_upstream_proxy(
    token_path: str | None = None,
    system_ca_path: str | None = None,
    ca_bundle_path: str | None = None,
    ccr_base_url: str | None = None,
) -> UpstreamProxyState:
    """Initialize upstream proxy for CCR sessions.

    Steps:
    1. Read session token from file
    2. Set process to non-dumpable (security)
    3. Download and merge CA certificates
    4. Start local relay
    5. Clean up token file
    6. Set environment variables

    All steps fail open - errors log warnings and disable proxy.
    """
    global _state

    # Check if running in CCR
    if not is_env_truthy(os.environ.get("CLAUDE_CODE_REMOTE")):
        return _state

    if not is_env_truthy(os.environ.get("CCR_UPSTREAM_PROXY_ENABLED")):
        return _state

    session_id = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID")
    if not session_id:
        logger.warning("[upstreamproxy] CLAUDE_CODE_REMOTE_SESSION_ID unset; proxy disabled")
        return _state

    token_path = token_path or SESSION_TOKEN_PATH

    # Read session token
    try:
        token = Path(token_path).read_text().strip()
        if not token:
            logger.warning("[upstreamproxy] Empty token file; proxy disabled")
            return _state
    except FileNotFoundError:
        logger.debug("[upstreamproxy] Token file not found; proxy disabled")
        return _state
    except Exception as e:
        logger.warning(f"[upstreamproxy] Failed to read token: {e}")
        return _state

    # TODO: Full implementation would:
    # 1. Set PR_SET_DUMPABLE to block ptrace
    # 2. Download CA certificate
    # 3. Start relay server
    # 4. Unlink token file
    # 5. Set HTTPS_PROXY and SSL_CERT_FILE

    logger.info("[upstreamproxy] Proxy initialization stubbed")

    return _state


def get_proxy_state() -> UpstreamProxyState:
    """Get current proxy state."""
    return _state


def is_proxy_enabled() -> bool:
    """Check if proxy is enabled."""
    return _state.enabled


def get_proxy_env_vars() -> dict:
    """Get environment variables for subprocess."""
    if not _state.enabled:
        return {}

    env = {
        "NO_PROXY": NO_PROXY_LIST,
        "no_proxy": NO_PROXY_LIST,
    }

    if _state.port:
        proxy_url = f"http://127.0.0.1:{_state.port}"
        env["HTTPS_PROXY"] = proxy_url
        env["https_proxy"] = proxy_url

    if _state.ca_bundle_path:
        env["SSL_CERT_FILE"] = _state.ca_bundle_path
        env["REQUESTS_CA_BUNDLE"] = _state.ca_bundle_path

    return env
