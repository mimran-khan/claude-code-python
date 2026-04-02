"""
High-level OAuth 2.0 authorization code + PKCE flow.

Migrated from: services/oauth/index.ts (OAuthService class)
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Awaitable, Callable

import structlog

from ..analytics.index import log_event
from . import client as oauth_client
from .auth_code_listener import AuthCodeListener
from .crypto import generate_code_challenge, generate_code_verifier, generate_state
from .types import OAuthTokenAccount, OAuthTokenExchangeResponse, OAuthTokens

_LOG = structlog.get_logger(__name__)


class OAuthService:
    """OAuth PKCE flow with localhost callback or manual code paste."""

    def __init__(self) -> None:
        self._code_verifier = generate_code_verifier()
        self._auth_listener: AuthCodeListener | None = None
        self._port: int | None = None
        self._manual_future: asyncio.Future[str] | None = None

    async def start_oauth_flow(
        self,
        auth_url_handler: Callable[[str, str | None], Awaitable[None]],
        *,
        login_with_claude_ai: bool | None = None,
        inference_only: bool | None = None,
        expires_in: int | None = None,
        org_uuid: str | None = None,
        login_hint: str | None = None,
        login_method: str | None = None,
        skip_browser_open: bool = False,
    ) -> OAuthTokens:
        self._auth_listener = AuthCodeListener()
        self._port = await self._auth_listener.start()
        code_challenge = generate_code_challenge(self._code_verifier)
        state = generate_state()
        opts = {
            "code_challenge": code_challenge,
            "state": state,
            "port": self._port,
            "login_with_claude_ai": login_with_claude_ai,
            "inference_only": inference_only,
            "org_uuid": org_uuid,
            "login_hint": login_hint,
            "login_method": login_method,
        }
        manual_url = oauth_client.build_auth_url(**opts, is_manual=True)
        auto_url = oauth_client.build_auth_url(**opts, is_manual=False)

        loop = asyncio.get_running_loop()
        self._manual_future = loop.create_future()

        async def _on_ready() -> None:
            if skip_browser_open:
                await auth_url_handler(manual_url, auto_url)
            else:
                await auth_url_handler(manual_url, None)
                from ...utils.browser import open_browser

                await open_browser(auto_url)

        assert self._auth_listener is not None
        wait_listener = asyncio.create_task(self._auth_listener.wait_for_authorization(state, _on_ready))
        assert self._manual_future is not None
        wait_manual = asyncio.create_task(self._manual_future)
        done, pending = await asyncio.wait(
            {wait_listener, wait_manual},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

        authorization_code = ""
        for t in done:
            authorization_code = t.result()
            break

        is_automatic = self._auth_listener.has_pending_response()
        log_event("tengu_oauth_auth_code_received", {"automatic": is_automatic})

        try:
            assert self._port is not None
            token_response = await oauth_client.exchange_code_for_tokens(
                authorization_code,
                state,
                self._code_verifier,
                self._port,
                not is_automatic,
                expires_in,
            )
            profile_info = await oauth_client.fetch_profile_info(token_response.access_token)
            if is_automatic:
                scopes = oauth_client.parse_scopes(token_response.scope)
                self._auth_listener.handle_success_redirect(scopes)
            tokens = self._format_tokens(
                token_response,
                profile_info.subscription_type,
                profile_info.rate_limit_tier,
                profile_info.raw_profile,
            )
            oauth_client.save_claude_ai_oauth_tokens(tokens)
            return tokens
        except asyncio.CancelledError:
            _LOG.debug("oauth_flow_cancelled", automatic_flow=is_automatic)
            if is_automatic and self._auth_listener:
                self._auth_listener.handle_error_redirect()
            raise
        except Exception as exc:
            _LOG.warning(
                "oauth_token_exchange_or_profile_failed",
                error_type=type(exc).__name__,
                error=str(exc),
                automatic_flow=is_automatic,
            )
            if is_automatic and self._auth_listener:
                self._auth_listener.handle_error_redirect()
            raise
        finally:
            if self._auth_listener:
                self._auth_listener.close()

    def handle_manual_auth_code_input(
        self,
        *,
        authorization_code: str,
        state: str,
    ) -> None:
        """Complete manual flow when user pastes the authorization code."""
        del state  # validated on token exchange in TS manual path; optional here
        if self._manual_future and not self._manual_future.done():
            self._manual_future.set_result(authorization_code)
        if self._auth_listener:
            self._auth_listener.close()

    def _format_tokens(
        self,
        response: OAuthTokenExchangeResponse,
        subscription_type: str | None,
        rate_limit_tier: str | None,
        profile,
    ) -> OAuthTokens:
        expires_at = int(time.time() * 1000) + int(response.expires_in) * 1000
        token_account = None
        if response.account:
            org_uuid = None
            if response.organization:
                org_uuid = response.organization.get("uuid")
            token_account = OAuthTokenAccount(
                uuid=str(response.account.get("uuid", "")),
                email_address=str(response.account.get("email_address", "")),
                organization_uuid=org_uuid,
            )
        return OAuthTokens(
            access_token=response.access_token,
            refresh_token=response.refresh_token or "",
            expires_at=expires_at,
            scopes=oauth_client.parse_scopes(response.scope),
            subscription_type=subscription_type,  # type: ignore[arg-type]
            rate_limit_tier=rate_limit_tier,
            profile=profile,
            token_account=token_account,
        )

    def cleanup(self) -> None:
        if self._auth_listener:
            self._auth_listener.close()
        self._manual_future = None
