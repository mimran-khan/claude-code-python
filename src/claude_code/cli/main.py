"""
Main CLI entry point (Typer).

Mirrors the TypeScript CLI: default interactive session, config, doctor, version.

Migrated from: cli/print.ts (partial)
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from importlib import metadata
from typing import Any

import structlog
import typer

from ..bootstrap.state import get_session_id, set_client_type, set_is_interactive
from ..config import get_config_path, get_global_config
from ..engine.query_engine import (
    AppState,
    QueryEngine,
    QueryEngineConfig,
    SDKResultMessage,
)

_LOG = structlog.get_logger(__name__)

app = typer.Typer(
    name="claude",
    help="Claude Code — AI-powered coding assistant",
    add_completion=False,
    pretty_exceptions_enable=True,
)


def _package_version() -> str:
    try:
        return metadata.version("claude-code")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(message)s",
        level=level,
        stream=sys.stderr,
        force=True,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def _create_cli_query_engine(
    *,
    cwd: str | None = None,
    model: str | None = None,
    verbose: bool = False,
) -> QueryEngine:
    """Build a QueryEngine with minimal defaults for the CLI."""
    from ..core.tool import get_empty_tool_permission_context

    resolved_cwd = cwd or os.getcwd()
    app_state_holder: list[AppState] = [AppState(tool_permission_context=get_empty_tool_permission_context())]

    def get_app_state() -> AppState:
        return app_state_holder[0]

    def set_app_state(updater: Callable[[AppState], AppState]) -> None:
        app_state_holder[0] = updater(app_state_holder[0])

    def can_use_tool(_tool_name: str, _tool_input: dict[str, Any]) -> dict[str, Any]:
        return {"allowed": True}

    config = QueryEngineConfig(
        cwd=resolved_cwd,
        tools=[],
        commands=[],
        mcp_clients=[],
        agents=[],
        can_use_tool=can_use_tool,
        get_app_state=get_app_state,
        set_app_state=set_app_state,
        user_specified_model=model,
        verbose=verbose,
    )
    return QueryEngine(config)


def _print_version() -> None:
    typer.echo(f"claude-code {_package_version()}")
    typer.echo(f"Session ID: {get_session_id()}")


def _print_help_text() -> None:
    typer.echo(
        """
Available commands:
  /help     - Show this help message
  /exit     - Exit the application
  /clear    - Clear the conversation
  /status   - Show session status

Tips:
  - Type your message and press Enter to send
  - Use Ctrl+C to interrupt; /exit to quit
"""
    )


def _print_status(engine: QueryEngine) -> None:
    n = len(engine.get_messages())
    typer.echo(f"Session ID: {get_session_id()}")
    typer.echo(f"Messages in conversation: {n}")


async def _run_turn(engine: QueryEngine, user_text: str) -> None:
    async for msg in engine.submit_message(user_text):
        if isinstance(msg, SDKResultMessage):
            if msg.is_error and msg.errors:
                typer.secho(f"Error: {msg.errors}", fg=typer.colors.RED, err=True)
            elif msg.result:
                typer.echo(msg.result)
        elif getattr(msg, "type", None) == "assistant":
            _LOG.debug("assistant_sdk_message", msg_type=msg.type)


def _handle_slash_command(
    cmd: str,
    *,
    engine: QueryEngine,
    model: str | None,
    verbose: bool,
) -> tuple[QueryEngine, bool]:
    """Returns (possibly new engine, should_break_loop)."""
    if cmd in ("exit", "quit", "q"):
        typer.echo("Goodbye!")
        return engine, True
    if cmd == "help":
        _print_help_text()
        return engine, False
    if cmd == "clear":
        typer.echo("Conversation cleared.")
        return _create_cli_query_engine(model=model, verbose=verbose), False
    if cmd == "status":
        _print_status(engine)
        return engine, False
    typer.echo(f"Unknown command: /{cmd}. Type /help for commands.")
    return engine, False


async def _run_interactive_chat(*, model: str | None, verbose: bool) -> None:
    set_client_type("cli")
    set_is_interactive(True)
    _LOG.info("interactive_start", model=model)

    typer.echo(f"Claude Code v{_package_version()}")
    typer.echo("Type a message and press Enter. /help for commands, /exit to quit.\n")

    engine = _create_cli_query_engine(model=model, verbose=verbose)

    while True:
        try:
            user_input = (await asyncio.to_thread(input, "> ")).strip()
        except EOFError:
            typer.echo("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input[1:].split(maxsplit=1)
            cmd = parts[0].lower() if parts else ""
            engine, stop = _handle_slash_command(cmd, engine=engine, model=model, verbose=verbose)
            if stop:
                break
            continue

        try:
            await _run_turn(engine, user_input)
        except KeyboardInterrupt:
            typer.echo("\nInterrupted. Type /exit to quit or continue chatting.")


async def _run_print_mode(prompt: str, *, model: str | None, verbose: bool) -> None:
    set_client_type("cli")
    set_is_interactive(False)
    engine = _create_cli_query_engine(model=model, verbose=verbose)
    await _run_turn(engine, prompt)


@app.callback(invoke_without_command=True)
def cli_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    model: str | None = typer.Option(None, "--model", "-m", help="Model override"),
    print_mode: bool = typer.Option(False, "--print", help="Print reply and exit"),
    prompt_opt: str | None = typer.Option(None, "--prompt", "-p", help="Prompt string"),
) -> None:
    """Claude Code CLI."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["model"] = model

    _configure_logging(verbose)

    if version:
        _print_version()
        raise typer.Exit(0)

    if ctx.invoked_subcommand is not None:
        return

    set_client_type("cli")

    prompt = prompt_opt
    if print_mode or prompt_opt is not None:
        if not prompt:
            typer.secho("Error: no prompt provided (use --prompt).", err=True)
            raise typer.Exit(1)
        set_is_interactive(False)
        try:
            asyncio.run(_run_print_mode(prompt, model=model, verbose=verbose))
        except KeyboardInterrupt:
            typer.secho("Interrupted.", err=True)
            raise typer.Exit(130) from None
        raise typer.Exit(0)

    try:
        asyncio.run(_run_interactive_chat(model=model, verbose=verbose))
    except KeyboardInterrupt:
        typer.echo("\nInterrupted.")
    raise typer.Exit(0)


@app.command("chat")
def chat_cmd(
    ctx: typer.Context,
    print_mode: bool = typer.Option(False, "--print", help="Print reply and exit"),
    prompt_opt: str | None = typer.Option(None, "--prompt", "-p"),
    text: str | None = typer.Argument(None, help="Prompt text"),
) -> None:
    """Start or run a chat (interactive unless --print or a prompt is given)."""
    verbose = bool(ctx.obj.get("verbose"))
    model = ctx.obj.get("model")

    prompt = prompt_opt or text
    if print_mode or prompt is not None:
        if not prompt:
            typer.secho("Error: no prompt provided.", err=True)
            raise typer.Exit(1)
        try:
            asyncio.run(_run_print_mode(prompt, model=model, verbose=verbose))
        except KeyboardInterrupt:
            typer.secho("Interrupted.", err=True)
            raise typer.Exit(130) from None
        return

    try:
        asyncio.run(_run_interactive_chat(model=model, verbose=verbose))
    except KeyboardInterrupt:
        typer.echo("\nInterrupted.")


@app.command("config")
def config_cmd(
    edit: bool = typer.Option(False, "--edit", "-e", help="Open config file in $EDITOR"),
) -> None:
    """Show global config path and summary, or open the config file for editing."""
    path = get_config_path()
    if edit:
        editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
        if not editor:
            typer.secho(
                "EDITOR (or VISUAL) is not set. Set it to open the config, or edit manually:",
                err=True,
            )
            typer.echo(path)
            raise typer.Exit(1)
        typer.echo(f"Opening {path} with {editor} …")
        result = subprocess.run([editor, path], check=False)
        raise typer.Exit(result.returncode)

    cfg = get_global_config()
    typer.echo(f"Config file: {path}")
    typer.echo(f"Exists: {os.path.isfile(path)}")
    typer.echo(f"Theme: {cfg.theme}")
    typer.echo(f"Release channel: {cfg.release_channel}")
    typer.echo(f"Verbose mode (saved): {cfg.verbose_mode}")
    typer.echo(f"Install method: {cfg.install_method}")


@app.command("doctor")
def doctor_cmd() -> None:
    """Run environment diagnostics."""
    typer.echo("Claude Code — doctor")
    ok = True

    py = sys.version_info
    typer.echo(f"Python: {py.major}.{py.minor}.{py.micro} (executable: {sys.executable})")
    if py < (3, 11):
        typer.secho("  Warning: package metadata requires Python >= 3.11.", fg=typer.colors.YELLOW)
        ok = False

    key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    typer.echo(f"ANTHROPIC_API_KEY set: {key_set}")
    if not key_set:
        typer.secho("  Set ANTHROPIC_API_KEY for API access.", fg=typer.colors.YELLOW)

    cpath = get_config_path()
    typer.echo(f"Global config: {cpath} (exists: {os.path.isfile(cpath)})")

    for name, path in (("git", shutil.which("git")),):
        typer.echo(f"{name}: {path or '(not found)'}")

    try:
        _create_cli_query_engine()
        typer.echo("QueryEngine: OK (minimal config)")
    except Exception as exc:
        typer.secho(f"QueryEngine: failed ({exc})", fg=typer.colors.RED)
        ok = False

    if ok and key_set:
        typer.secho("Doctor finished with no blocking issues.", fg=typer.colors.GREEN)
    else:
        typer.secho("Doctor finished (see warnings above).", fg=typer.colors.YELLOW)


@app.command("version")
def version_cmd() -> None:
    """Print version information."""
    _print_version()


def main() -> None:
    """Setuptools / pip console_scripts entry point."""
    app()


if __name__ == "__main__":
    main()
