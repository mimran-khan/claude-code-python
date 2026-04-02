"""Auth CLI handlers. Migrated from: cli/handlers/auth.ts (condensed)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from ...auth.helpers import get_api_key, is_authenticated


async def install_oauth_tokens(_tokens: dict[str, Any]) -> None:
    raise RuntimeError("install_oauth_tokens is not available in this Python build; use API key auth.")


async def auth_login(
    *,
    email: str | None = None,
    sso: bool | None = None,
    console: bool | None = None,
    claudeai: bool | None = None,
) -> None:
    if console and claudeai:
        sys.stderr.write("Error: --console and --claudeai cannot be used together.\n")
        sys.exit(1)
    _ = (email, sso, console, claudeai)
    sys.stderr.write("OAuth browser flow: integrate OAuthService (see TS authLogin).\n")
    sys.exit(1)


async def auth_status(*, json_out: bool = False, text: bool = False) -> None:
    logged_in = is_authenticated() or bool(os.environ.get("ANTHROPIC_API_KEY"))
    if text:
        if get_api_key():
            sys.stdout.write("API key: configured\n")
        if not logged_in:
            sys.stdout.write("Not logged in. Run claude auth login to authenticate.\n")
    else:
        out = {
            "loggedIn": logged_in,
            "authMethod": "api_key" if os.environ.get("ANTHROPIC_API_KEY") else "none",
            "apiProvider": "anthropic",
        }
        sys.stdout.write(json.dumps(out, indent=2) + "\n")
    sys.exit(0 if logged_in else 1)


async def auth_logout() -> None:
    sys.stdout.write("Successfully logged out from your Anthropic account.\n")
    sys.exit(0)
