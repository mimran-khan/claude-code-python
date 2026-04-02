"""Bridge terminal UI / logger factory (ported from bridge/bridgeUI.ts)."""

from __future__ import annotations

import logging
from typing import Any

from claude_code.bridge.types import BridgeConfig, SessionActivity, SpawnMode

logger = logging.getLogger(__name__)


def create_bridge_logger(options: dict[str, Any]) -> Any:
    """Returns a BridgeLogger-compatible object (TODO: Rich/Ink parity)."""
    verbose = bool(options.get("verbose", False))

    class _Logger:
        def print_banner(self, config: BridgeConfig, environment_id: str) -> None:
            logger.info("bridge banner env=%s dir=%s", environment_id, config.dir)

        def log_session_start(self, session_id: str, prompt: str) -> None:
            logger.info("session start %s", session_id)

        def log_session_complete(self, session_id: str, duration_ms: int) -> None:
            logger.info("session complete %s %sms", session_id, duration_ms)

        def log_session_failed(self, session_id: str, error: str) -> None:
            logger.error("session failed %s: %s", session_id, error)

        def log_status(self, message: str) -> None:
            logger.info("%s", message)

        def log_verbose(self, message: str) -> None:
            if verbose:
                logger.debug("%s", message)

        def log_error(self, message: str) -> None:
            logger.error("%s", message)

        def log_reconnected(self, disconnected_ms: int) -> None:
            logger.info("reconnected after %sms", disconnected_ms)

        def update_idle_status(self) -> None:
            pass

        def update_reconnecting_status(self, delay_str: str, elapsed_str: str) -> None:
            pass

        def update_session_status(
            self,
            session_id: str,
            elapsed: str,
            activity: SessionActivity,
            trail: list[str],
        ) -> None:
            pass

        def clear_status(self) -> None:
            pass

        def set_repo_info(self, repo_name: str, branch: str) -> None:
            pass

        def set_debug_log_path(self, path: str) -> None:
            pass

        def set_attached(self, session_id: str) -> None:
            pass

        def update_failed_status(self, error: str) -> None:
            pass

        def toggle_qr(self) -> None:
            pass

        def update_session_count(self, active: int, max_sessions: int, mode: SpawnMode) -> None:
            pass

        def set_spawn_mode_display(self, mode: str | None) -> None:
            pass

        def add_session(self, session_id: str, url: str) -> None:
            pass

        def update_session_activity(self, session_id: str, activity: SessionActivity) -> None:
            pass

        def set_session_title(self, session_id: str, title: str) -> None:
            pass

        def remove_session(self, session_id: str) -> None:
            pass

        def refresh_display(self) -> None:
            pass

    return _Logger()
