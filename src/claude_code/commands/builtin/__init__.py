"""
Builtin commands.

Standard commands available in Claude Code.

Migrated from: commands/**/*.ts
"""

# Register all builtin commands
from ..registry import register_command
from ..security_review.command import SecurityReviewCommand
from .clear import ClearCommand
from .compact import CompactCommand
from .config import ConfigCommand
from .context import ContextCommand
from .cost import CostCommand
from .diff import DiffCommand
from .doctor import DoctorCommand
from .exit import ExitCommand
from .files import FilesCommand
from .help import HelpCommand
from .hooks import HooksCommand
from .init import InitCommand
from .login import LoginCommand
from .logout import LogoutCommand
from .mcp import MCPCommand
from .memory import MemoryCommand
from .model import ModelCommand
from .permissions import PermissionsCommand
from .plugin import PluginCommand
from .resume import ResumeCommand
from .review import ReviewCommand
from .status import StatusCommand
from .version import VersionCommand
from .vim import VimCommand

_builtin_commands = [
    HelpCommand(),
    ClearCommand(),
    ExitCommand(),
    ConfigCommand(),
    CompactCommand(),
    CostCommand(),
    DiffCommand(),
    FilesCommand(),
    PermissionsCommand(),
    ModelCommand(),
    ResumeCommand(),
    MemoryCommand(),
    VersionCommand(),
    StatusCommand(),
    ReviewCommand(),
    DoctorCommand(),
    MCPCommand(),
    PluginCommand(),
    LoginCommand(),
    LogoutCommand(),
    InitCommand(),
    HooksCommand(),
    VimCommand(),
    ContextCommand(),
    SecurityReviewCommand(),
]

for cmd in _builtin_commands:
    register_command(cmd)

__all__ = [
    "HelpCommand",
    "ClearCommand",
    "ExitCommand",
    "ConfigCommand",
    "CompactCommand",
    "CostCommand",
    "DiffCommand",
    "FilesCommand",
    "PermissionsCommand",
    "ModelCommand",
    "ResumeCommand",
    "MemoryCommand",
    "VersionCommand",
    "StatusCommand",
    "ReviewCommand",
    "DoctorCommand",
    "MCPCommand",
    "PluginCommand",
    "LoginCommand",
    "LogoutCommand",
    "InitCommand",
    "HooksCommand",
    "VimCommand",
    "ContextCommand",
    "SecurityReviewCommand",
]
