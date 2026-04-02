"""Read session-ingress auth from environment (TS sessionIngressAuth parity)."""

from __future__ import annotations

import os


def get_session_ingress_auth_token() -> str | None:
    return os.environ.get("CLAUDE_CODE_SESSION_ACCESS_TOKEN")


def get_session_ingress_auth_headers() -> dict[str, str]:
    tok = get_session_ingress_auth_token()
    if tok:
        return {"Authorization": f"Bearer {tok}"}
    return {}


def get_claude_code_user_agent() -> str:
    return os.environ.get("CLAUDE_CODE_USER_AGENT", "claude-code-python/0.1")


def is_env_truthy(name: str) -> bool:
    v = os.environ.get(name, "").lower()
    return v in ("1", "true", "yes", "on")
