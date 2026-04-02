"""
Main entry points.

Run modes for CLI and SDK.

Migrated from: cli/print.ts (partial - main logic)
"""

from __future__ import annotations

import asyncio
import sys

from ..cli.exit import EXIT_CODE_ERROR, EXIT_CODE_SUCCESS
from ..cli.output import print_error, print_info
from .init import initialize, shutdown


async def run_cli(args: list[str] | None = None) -> int:
    """
    Run the CLI application.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    if args is None:
        args = sys.argv[1:]

    try:
        # Initialize
        await initialize()

        # Parse arguments
        if not args:
            return await run_interactive()

        # Handle commands
        command = args[0]

        if command in ["--help", "-h"]:
            _print_help()
            return EXIT_CODE_SUCCESS

        if command in ["--version", "-v"]:
            _print_version()
            return EXIT_CODE_SUCCESS

        # Run with prompt
        prompt = " ".join(args)
        return await run_non_interactive(prompt)

    except KeyboardInterrupt:
        print_info("\nAborted")
        return 130

    except Exception as e:
        print_error(str(e))
        return EXIT_CODE_ERROR

    finally:
        await shutdown()


async def run_interactive() -> int:
    """
    Run in interactive mode.

    Returns:
        Exit code
    """
    print_info("Claude Code - Interactive Mode")
    print_info("Type your message or /help for commands")
    print()

    while True:
        try:
            prompt = input("> ").strip()

            if not prompt:
                continue

            if prompt == "/exit" or prompt == "/quit":
                break

            if prompt == "/help":
                _print_interactive_help()
                continue

            # Process the prompt
            result = await _process_prompt(prompt)
            print(result)
            print()

        except KeyboardInterrupt:
            print("\nUse /exit to quit")

        except EOFError:
            break

    return EXIT_CODE_SUCCESS


async def run_non_interactive(prompt: str) -> int:
    """
    Run in non-interactive mode with a single prompt.

    Args:
        prompt: The prompt to process

    Returns:
        Exit code
    """
    try:
        result = await _process_prompt(prompt)
        print(result)
        return EXIT_CODE_SUCCESS

    except Exception as e:
        print_error(str(e))
        return EXIT_CODE_ERROR


async def _process_prompt(prompt: str) -> str:
    """
    Process a user prompt.

    Args:
        prompt: User prompt

    Returns:
        Response string
    """
    # In a full implementation, this would:
    # 1. Send the prompt to the query engine
    # 2. Execute tools as needed
    # 3. Return the response

    return f"[Stub] Would process: {prompt}"


def _print_help() -> None:
    """Print help message."""
    print(
        """
Claude Code - AI Coding Assistant

Usage:
  claude-code [options] [prompt]

Options:
  -h, --help     Show this help message
  -v, --version  Show version information
  -p, --print    Print output in structured format
  --no-color     Disable colored output

Examples:
  claude-code "What files are in this directory?"
  claude-code "Create a hello world Python script"
  claude-code  # Start interactive mode
""".strip()
    )


def _print_version() -> None:
    """Print version information."""
    print("claude-code 0.1.0 (Python)")


def _print_interactive_help() -> None:
    """Print interactive mode help."""
    print(
        """
Interactive Commands:
  /help    Show this help
  /exit    Exit the application
  /clear   Clear conversation
  /cost    Show session cost
  /files   List tracked files
""".strip()
    )


def main() -> None:
    """CLI entry point."""
    exit_code = asyncio.run(run_cli())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
