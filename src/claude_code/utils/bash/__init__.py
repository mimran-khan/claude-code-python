"""
Bash utilities module.

Utilities for parsing and analyzing bash commands.

Migrated from: utils/bash/*.ts
"""

from .command_spec import Argument, CommandSpec, Option
from .commands import (
    extract_output_redirections,
    is_control_operator,
    split_command,
    split_command_with_operators,
)
from .parser import (
    ParsedCommandData,
    parse_command,
    parse_command_raw,
)
from .registry import get_command_spec, load_fig_spec
from .shell_quote import (
    quote,
    try_parse_shell_command,
)
from .shell_quoting import (
    has_stdin_redirect,
    quote_shell_command,
    rewrite_windows_null_redirect,
    should_add_stdin_redirect,
)

__all__ = [
    # commands
    "split_command_with_operators",
    "extract_output_redirections",
    "split_command",
    "is_control_operator",
    # shell_quoting
    "quote_shell_command",
    "has_stdin_redirect",
    "should_add_stdin_redirect",
    "rewrite_windows_null_redirect",
    # parser
    "parse_command",
    "parse_command_raw",
    "ParsedCommandData",
    # shell_quote
    "quote",
    "try_parse_shell_command",
    # registry / specs
    "get_command_spec",
    "load_fig_spec",
    "Argument",
    "CommandSpec",
    "Option",
]
