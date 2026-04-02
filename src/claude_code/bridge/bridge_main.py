"""Standalone `claude remote-control` bridge (ported from bridge/bridgeMain.ts — skeleton)."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from typing import Any

# TODO: full run_bridge_loop (~1400 lines), headless mode, signal handlers

logger = logging.getLogger(__name__)


@dataclass
class BackoffConfig:
    base_delay_ms: int = 500
    max_delay_ms: int = 30_000
    jitter_fraction: float = 0.25


def is_connection_error(err: object) -> bool:
    name = type(err).__name__
    msg = str(err).lower()
    if "ECONNRESET" in msg or "ETIMEDOUT" in msg or "socket" in msg:
        return True
    return "Connect" in name or "Timeout" in name


def is_server_error(err: object) -> bool:
    status = getattr(err, "status", None) or getattr(err, "status_code", None)
    if isinstance(status, int) and 500 <= status < 600:
        return True
    msg = str(err).lower()
    return "502" in msg or "503" in msg or "504" in msg


@dataclass
class ParsedArgs:
    dir: str
    max_sessions: int = 4
    spawn_mode: str = "single-session"
    verbose: bool = False
    session_id: str | None = None
    continue_resume: bool = False


def parse_args(argv: list[str]) -> ParsedArgs:
    p = argparse.ArgumentParser(prog="claude remote-control")
    p.add_argument("dir", nargs="?", default=".")
    p.add_argument("--max-sessions", type=int, default=4)
    p.add_argument(
        "--spawn-mode",
        choices=["single-session", "worktree", "same-dir"],
        default="single-session",
    )
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--session-id", dest="session_id", default=None)
    p.add_argument("--continue", dest="continue_resume", action="store_true")
    ns = p.parse_args(argv)
    return ParsedArgs(
        dir=ns.dir,
        max_sessions=ns.max_sessions,
        spawn_mode=ns.spawn_mode,
        verbose=ns.verbose,
        session_id=ns.session_id,
        continue_resume=ns.continue_resume,
    )


async def run_bridge_loop(*args: Any, **kwargs: Any) -> None:
    """TODO: register environment, poll/ack/spawn sessions."""
    logger.warning("run_bridge_loop is a stub (TODO bridgeMain.ts port)")
    _ = (args, kwargs)


async def bridge_main(args: list[str]) -> None:
    parsed = parse_args(args)
    logger.info("bridge_main stub cwd=%s", parsed.dir)
    # TODO: wire create_bridge_api_client, session spawner, UI logger


class BridgeHeadlessPermanentError(Exception):
    pass


async def run_bridge_headless(*args: Any, **kwargs: Any) -> None:
    """TODO: non-interactive bridge for CI/daemon."""
    _ = (args, kwargs)
    raise BridgeHeadlessPermanentError("run_bridge_headless not implemented")
