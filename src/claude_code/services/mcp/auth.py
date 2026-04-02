"""
MCP OAuth authentication.

OAuth flow handling for MCP servers.

Migrated from: services/mcp/auth.ts (2466 lines)
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlencode, urlparse

# Timeout for OAuth requests
AUTH_REQUEST_TIMEOUT_MS = 30000

# Maximum lock retries
MAX_LOCK_RETRIES = 5

# Sensitive OAuth params to redact in logs
SENSITIVE_OAUTH_PARAMS = [
    "state",
    "nonce",
    "code_challenge",
    "code_verifier",
    "code",
]

# Non-standard invalid_grant aliases
NONSTANDARD_INVALID_GRANT_ALIASES = {
    "invalid_refresh_token",
    "expired_refresh_token",
    "token_expired",
}


@dataclass
class OAuthTokens:
    """OAuth tokens."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None


@dataclass
class OAuthClientInfo:
    """OAuth client information."""

    client_id: str
    client_secret: str | None = None
    redirect_uri: str = ""


@dataclass
class AuthorizationServerMetadata:
    """OAuth authorization server metadata."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: str | None = None
    scopes_supported: list[str] = field(default_factory=list)
    response_types_supported: list[str] = field(default_factory=list)
    code_challenge_methods_supported: list[str] = field(default_factory=list)


@dataclass
class OAuthState:
    """State for an OAuth flow."""

    state: str
    code_verifier: str
    redirect_uri: str
    server_name: str
    started_at: float = 0.0


def redact_sensitive_url_params(url: str) -> str:
    """
    Redact sensitive OAuth parameters from a URL for logging.

    Args:
        url: URL to redact

    Returns:
        Redacted URL string
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        for param in SENSITIVE_OAUTH_PARAMS:
            if param in params:
                params[param] = ["[REDACTED]"]

        # Rebuild query string
        query = urlencode(params, doseq=True)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{query}"
    except Exception:
        return url


def generate_code_verifier() -> str:
    """Generate a PKCE code verifier."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(verifier: str) -> str:
    """
    Generate a PKCE code challenge from a verifier.

    Uses S256 method (SHA-256 hash, base64url encoded).
    """
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def generate_state() -> str:
    """Generate a random state parameter."""
    return secrets.token_urlsafe(16)


def generate_nonce() -> str:
    """Generate a random nonce."""
    return secrets.token_urlsafe(16)


async def discover_oauth_metadata(
    base_url: str,
    timeout: float = AUTH_REQUEST_TIMEOUT_MS / 1000,
) -> AuthorizationServerMetadata | None:
    """
    Discover OAuth authorization server metadata.

    Checks .well-known/oauth-authorization-server first,
    then falls back to .well-known/openid-configuration.

    Args:
        base_url: Base URL of the server
        timeout: Request timeout in seconds

    Returns:
        AuthorizationServerMetadata or None if not found
    """
    import httpx

    # URLs to try
    well_known_paths = [
        "/.well-known/oauth-authorization-server",
        "/.well-known/openid-configuration",
    ]

    async with httpx.AsyncClient(timeout=timeout) as client:
        for path in well_known_paths:
            try:
                url = f"{base_url.rstrip('/')}{path}"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    return AuthorizationServerMetadata(
                        issuer=data.get("issuer", base_url),
                        authorization_endpoint=data.get("authorization_endpoint", ""),
                        token_endpoint=data.get("token_endpoint", ""),
                        registration_endpoint=data.get("registration_endpoint"),
                        scopes_supported=data.get("scopes_supported", []),
                        response_types_supported=data.get("response_types_supported", []),
                        code_challenge_methods_supported=data.get("code_challenge_methods_supported", []),
                    )
            except Exception:
                continue

    return None


async def exchange_code_for_tokens(
    token_endpoint: str,
    code: str,
    code_verifier: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str | None = None,
) -> OAuthTokens | None:
    """
    Exchange an authorization code for tokens.

    Args:
        token_endpoint: Token endpoint URL
        code: Authorization code
        code_verifier: PKCE code verifier
        redirect_uri: Redirect URI used in authorization
        client_id: OAuth client ID
        client_secret: Optional client secret

    Returns:
        OAuthTokens or None on failure
    """
    import httpx

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if client_secret:
        data["client_secret"] = client_secret

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers=headers,
            )

            if response.status_code == 200:
                token_data = response.json()
                return OAuthTokens(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope"),
                )
    except Exception:
        pass

    return None


async def refresh_tokens(
    token_endpoint: str,
    refresh_token: str,
    client_id: str,
    client_secret: str | None = None,
) -> OAuthTokens | None:
    """
    Refresh OAuth tokens.

    Args:
        token_endpoint: Token endpoint URL
        refresh_token: Refresh token
        client_id: OAuth client ID
        client_secret: Optional client secret

    Returns:
        New OAuthTokens or None on failure
    """
    import httpx

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }

    if client_secret:
        data["client_secret"] = client_secret

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                token_data = response.json()
                return OAuthTokens(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token", refresh_token),
                    scope=token_data.get("scope"),
                )
    except Exception:
        pass

    return None


def build_authorization_url(
    authorization_endpoint: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    scope: str = "",
) -> str:
    """
    Build an OAuth authorization URL.

    Args:
        authorization_endpoint: Authorization endpoint URL
        client_id: OAuth client ID
        redirect_uri: Redirect URI
        state: State parameter
        code_challenge: PKCE code challenge
        scope: Requested scopes

    Returns:
        Authorization URL
    """
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    if scope:
        params["scope"] = scope

    query = urlencode(params)
    return f"{authorization_endpoint}?{query}"


def is_invalid_grant_error(error_code: str) -> bool:
    """Check if an error code indicates invalid grant."""
    return error_code == "invalid_grant" or error_code in NONSTANDARD_INVALID_GRANT_ALIASES


class OAuthFlowManager:
    """Manages OAuth flows for MCP servers."""

    def __init__(self):
        self._active_flows: dict[str, OAuthState] = {}
        self._tokens: dict[str, OAuthTokens] = {}

    def start_flow(
        self,
        server_name: str,
        redirect_uri: str,
    ) -> OAuthState:
        """
        Start a new OAuth flow.

        Args:
            server_name: Name of the MCP server
            redirect_uri: Redirect URI for the flow

        Returns:
            OAuthState for the flow
        """
        import time

        state = OAuthState(
            state=generate_state(),
            code_verifier=generate_code_verifier(),
            redirect_uri=redirect_uri,
            server_name=server_name,
            started_at=time.time(),
        )

        self._active_flows[state.state] = state
        return state

    def complete_flow(
        self,
        state: str,
        tokens: OAuthTokens,
    ) -> bool:
        """
        Complete an OAuth flow.

        Args:
            state: State parameter from callback
            tokens: Received tokens

        Returns:
            True if flow was found and completed
        """
        if state not in self._active_flows:
            return False

        flow = self._active_flows.pop(state)
        self._tokens[flow.server_name] = tokens
        return True

    def cancel_flow(self, state: str) -> bool:
        """Cancel an active flow."""
        if state in self._active_flows:
            del self._active_flows[state]
            return True
        return False

    def get_tokens(self, server_name: str) -> OAuthTokens | None:
        """Get tokens for a server."""
        return self._tokens.get(server_name)

    def clear_tokens(self, server_name: str) -> bool:
        """Clear tokens for a server."""
        if server_name in self._tokens:
            del self._tokens[server_name]
            return True
        return False


# Global flow manager
_flow_manager: OAuthFlowManager | None = None


def get_oauth_flow_manager() -> OAuthFlowManager:
    """Get the global OAuth flow manager."""
    global _flow_manager
    if _flow_manager is None:
        _flow_manager = OAuthFlowManager()
    return _flow_manager
