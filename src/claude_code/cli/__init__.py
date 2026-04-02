"""
CLI utilities (I/O, transports, handlers).

Migrated from: cli/*.ts
"""

from . import handlers, transports
from .exit import (
    EXIT_CODE_ABORT,
    EXIT_CODE_ERROR,
    EXIT_CODE_SUCCESS,
    cli_error,
    cli_ok,
    exit_with_code,
)
from .io import (
    RemoteIO,
    StructuredIO,
    read_from_stdin,
    write_to_stdout,
)
from .ndjson_safe_stringify import ndjson_safe_stringify
from .output import (
    print_error,
    print_info,
    print_json,
    print_message,
    print_success,
    print_warning,
)
from .print_mode import (
    can_batch_with,
    join_prompt_values,
    remove_interrupted_message,
    run_headless,
)
from .remote_io_sdk import RemoteIOSDK
from .structured_io_sdk import SANDBOX_NETWORK_ACCESS_TOOL_NAME, StructuredIOSDK
from .update_cli import update_cli

__all__ = [
    "StructuredIO",
    "RemoteIO",
    "StructuredIOSDK",
    "RemoteIOSDK",
    "SANDBOX_NETWORK_ACCESS_TOOL_NAME",
    "write_to_stdout",
    "read_from_stdin",
    "print_message",
    "print_error",
    "print_warning",
    "print_info",
    "print_success",
    "print_json",
    "exit_with_code",
    "cli_error",
    "cli_ok",
    "EXIT_CODE_SUCCESS",
    "EXIT_CODE_ERROR",
    "EXIT_CODE_ABORT",
    "ndjson_safe_stringify",
    "join_prompt_values",
    "can_batch_with",
    "run_headless",
    "remove_interrupted_message",
    "update_cli",
    "handlers",
    "transports",
]
