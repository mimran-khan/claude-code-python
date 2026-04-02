"""Product URLs and remote session utilities."""

PRODUCT_URL = "https://claude.com/claude-code"

# Claude Code Remote session URLs
CLAUDE_AI_BASE_URL = "https://claude.ai"
CLAUDE_AI_STAGING_BASE_URL = "https://claude-ai.staging.ant.dev"
CLAUDE_AI_LOCAL_BASE_URL = "http://localhost:4000"


def is_remote_session_staging(
    session_id: str | None = None,
    ingress_url: str | None = None,
) -> bool:
    """Determine if we're in a staging environment for remote sessions.

    Checks session ID format and ingress URL.
    """
    if session_id and "_staging_" in session_id:
        return True
    return bool(ingress_url and "staging" in ingress_url)


def is_remote_session_local(
    session_id: str | None = None,
    ingress_url: str | None = None,
) -> bool:
    """Determine if we're in a local-dev environment for remote sessions.

    Checks session ID format (e.g. `session_local_...`) and ingress URL.
    """
    if session_id and "_local_" in session_id:
        return True
    return bool(ingress_url and "localhost" in ingress_url)


def get_claude_ai_base_url(
    session_id: str | None = None,
    ingress_url: str | None = None,
) -> str:
    """Get the base URL for Claude AI based on environment."""
    if is_remote_session_local(session_id, ingress_url):
        return CLAUDE_AI_LOCAL_BASE_URL
    if is_remote_session_staging(session_id, ingress_url):
        return CLAUDE_AI_STAGING_BASE_URL
    return CLAUDE_AI_BASE_URL


def get_remote_session_url(session_id: str, ingress_url: str | None = None) -> str:
    """Get the full session URL for a remote session."""
    # Note: In full migration, would need to import toCompatSessionId
    compat_id = session_id
    base_url = get_claude_ai_base_url(compat_id, ingress_url)
    return f"{base_url}/code/{compat_id}"
