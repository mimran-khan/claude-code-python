"""
Claude memory file utilities.

Handles loading and processing CLAUDE.md memory files.

Migrated from: utils/claudemd.ts (1480 lines)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .git import find_git_root
from .log import log_error

# Constants
MAX_MEMORY_CHARACTER_COUNT = 40000

MEMORY_INSTRUCTION_PROMPT = (
    "Codebase and user instructions are shown below. "
    "Be sure to adhere to these instructions. "
    "IMPORTANT: These instructions OVERRIDE any default behavior and "
    "you MUST follow them exactly as written."
)

# File extensions allowed for @include directives
TEXT_FILE_EXTENSIONS = {
    # Markdown and text
    ".md",
    ".txt",
    ".text",
    # Data formats
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".csv",
    # Web
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    # JavaScript/TypeScript
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".mjs",
    ".cjs",
    ".mts",
    ".cts",
    # Python
    ".py",
    ".pyi",
    ".pyw",
    # Ruby
    ".rb",
    ".erb",
    ".rake",
    # Go
    ".go",
    # Rust
    ".rs",
    # Java/Kotlin/Scala
    ".java",
    ".kt",
    ".kts",
    ".scala",
    # C/C++
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".hxx",
    # C#
    ".cs",
    # Swift
    ".swift",
    # Shell
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".ps1",
    ".bat",
    ".cmd",
    # Config
    ".env",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
    ".properties",
    # Database
    ".sql",
    ".graphql",
    ".gql",
    # Protocol
    ".proto",
    # Frontend frameworks
    ".vue",
    ".svelte",
    ".astro",
    # Templating
    ".ejs",
    ".hbs",
    ".pug",
    ".jade",
    # Other languages
    ".php",
    ".pl",
    ".pm",
    ".lua",
    ".r",
    ".R",
    ".dart",
    ".ex",
    ".exs",
    ".erl",
    ".hrl",
    ".clj",
    ".cljs",
    ".cljc",
    ".edn",
    ".hs",
    ".lhs",
    ".nim",
    ".ml",
    ".mli",
}

# Memory file names
MEMORY_FILENAME = "CLAUDE.md"
LOCAL_MEMORY_FILENAME = "CLAUDE.local.md"
RULES_DIR = ".claude/rules"


@dataclass
class MemoryFileInfo:
    """Information about a memory file."""

    path: str
    content: str = ""
    memory_type: str = "project"  # "managed", "user", "project", "local"
    source_dir: str = ""
    is_injected: bool = False
    character_count: int = 0


@dataclass
class MemoryLoadResult:
    """Result of loading memory files."""

    files: list[MemoryFileInfo] = field(default_factory=list)
    total_characters: int = 0
    has_user_memory: bool = False
    has_project_memory: bool = False
    has_local_memory: bool = False


def get_memory_path() -> str:
    """Get the path to the user memory directory."""
    from .env_utils import get_claude_config_home_dir

    return os.path.join(get_claude_config_home_dir(), "memory")


def get_user_memory_path() -> str:
    """Get the path to the user's global CLAUDE.md file."""
    from .env_utils import get_claude_config_home_dir

    return os.path.join(get_claude_config_home_dir(), MEMORY_FILENAME)


def get_user_claude_rules_dir() -> str:
    """Get the path to the user's rules directory."""
    from .env_utils import get_claude_config_home_dir

    return os.path.join(get_claude_config_home_dir(), "rules")


def get_managed_claude_rules_dir() -> str:
    """Get the path to managed rules directory."""
    return "/etc/claude-code"


def find_memory_files_in_directory(directory: str) -> list[str]:
    """
    Find all memory files in a directory.

    Looks for:
    - CLAUDE.md
    - .claude/CLAUDE.md
    - .claude/rules/*.md
    """
    files = []

    # Check CLAUDE.md in root
    root_file = os.path.join(directory, MEMORY_FILENAME)
    if os.path.isfile(root_file):
        files.append(root_file)

    # Check .claude/CLAUDE.md
    claude_dir_file = os.path.join(directory, ".claude", MEMORY_FILENAME)
    if os.path.isfile(claude_dir_file):
        files.append(claude_dir_file)

    # Check .claude/rules/*.md
    rules_dir = os.path.join(directory, RULES_DIR)
    if os.path.isdir(rules_dir):
        try:
            for entry in os.listdir(rules_dir):
                if entry.endswith(".md"):
                    files.append(os.path.join(rules_dir, entry))
        except Exception as e:
            log_error(e)

    return files


def find_local_memory_file(directory: str) -> str | None:
    """Find the local memory file in a directory."""
    local_file = os.path.join(directory, LOCAL_MEMORY_FILENAME)
    if os.path.isfile(local_file):
        return local_file

    claude_local = os.path.join(directory, ".claude", LOCAL_MEMORY_FILENAME)
    if os.path.isfile(claude_local):
        return claude_local

    return None


def get_memory_files(
    cwd: str | None = None,
    *,
    include_local: bool = True,
    include_user: bool = True,
    include_managed: bool = True,
) -> list[MemoryFileInfo]:
    """
    Get all memory files applicable to the current directory.

    Files are returned in order of priority (lowest first):
    1. Managed memory
    2. User memory
    3. Project memory (from git root up to cwd)
    4. Local memory

    Args:
        cwd: Current working directory
        include_local: Include local memory files
        include_user: Include user memory files
        include_managed: Include managed memory files

    Returns:
        List of MemoryFileInfo objects
    """
    from .cwd import get_cwd

    if cwd is None:
        cwd = get_cwd()

    files: list[MemoryFileInfo] = []

    # 1. Managed memory (lowest priority)
    if include_managed:
        managed_dir = get_managed_claude_rules_dir()
        managed_file = os.path.join(managed_dir, MEMORY_FILENAME)
        if os.path.isfile(managed_file):
            try:
                content = Path(managed_file).read_text(encoding="utf-8")
                files.append(
                    MemoryFileInfo(
                        path=managed_file,
                        content=content,
                        memory_type="managed",
                        source_dir=managed_dir,
                        character_count=len(content),
                    )
                )
            except Exception as e:
                log_error(e)

    # 2. User memory
    if include_user:
        user_file = get_user_memory_path()
        if os.path.isfile(user_file):
            try:
                content = Path(user_file).read_text(encoding="utf-8")
                files.append(
                    MemoryFileInfo(
                        path=user_file,
                        content=content,
                        memory_type="user",
                        source_dir=os.path.dirname(user_file),
                        character_count=len(content),
                    )
                )
            except Exception as e:
                log_error(e)

        # User rules directory
        user_rules_dir = get_user_claude_rules_dir()
        if os.path.isdir(user_rules_dir):
            try:
                for entry in sorted(os.listdir(user_rules_dir)):
                    if entry.endswith(".md"):
                        rule_path = os.path.join(user_rules_dir, entry)
                        content = Path(rule_path).read_text(encoding="utf-8")
                        files.append(
                            MemoryFileInfo(
                                path=rule_path,
                                content=content,
                                memory_type="user",
                                source_dir=user_rules_dir,
                                character_count=len(content),
                            )
                        )
            except Exception as e:
                log_error(e)

    # 3. Project memory - traverse from git root to cwd
    git_root = find_git_root(cwd)
    if git_root:
        # Walk from git root to cwd
        current = git_root
        while True:
            for mem_file in find_memory_files_in_directory(current):
                try:
                    content = Path(mem_file).read_text(encoding="utf-8")
                    files.append(
                        MemoryFileInfo(
                            path=mem_file,
                            content=content,
                            memory_type="project",
                            source_dir=current,
                            character_count=len(content),
                        )
                    )
                except Exception as e:
                    log_error(e)

            # Move to next directory towards cwd
            if current == cwd:
                break

            rel_path = os.path.relpath(cwd, current)
            next_part = rel_path.split(os.sep)[0]
            if next_part == ".." or next_part == "":
                break
            current = os.path.join(current, next_part)

    # 4. Local memory (highest priority)
    if include_local:
        local_file = find_local_memory_file(cwd)
        if local_file:
            try:
                content = Path(local_file).read_text(encoding="utf-8")
                files.append(
                    MemoryFileInfo(
                        path=local_file,
                        content=content,
                        memory_type="local",
                        source_dir=os.path.dirname(local_file),
                        character_count=len(content),
                    )
                )
            except Exception as e:
                log_error(e)

    return files


def get_memory_files_for_nested_directory(directory: str) -> list[MemoryFileInfo]:
    """Get memory files for a nested directory within the project."""
    return get_memory_files(directory, include_user=False, include_managed=False)


def get_managed_and_user_conditional_rules() -> list[MemoryFileInfo]:
    """Get managed and user memory files only."""
    return get_memory_files(include_local=False, include_user=True, include_managed=True)


def get_conditional_rules_for_cwd_level_directory(directory: str) -> list[MemoryFileInfo]:
    """Get conditional rules for a specific directory level."""
    files = []
    for mem_file in find_memory_files_in_directory(directory):
        try:
            content = Path(mem_file).read_text(encoding="utf-8")
            files.append(
                MemoryFileInfo(
                    path=mem_file,
                    content=content,
                    memory_type="project",
                    source_dir=directory,
                    character_count=len(content),
                )
            )
        except Exception as e:
            log_error(e)
    return files


def filter_injected_memory_files(
    files: list[MemoryFileInfo],
) -> list[MemoryFileInfo]:
    """Filter out injected memory files."""
    return [f for f in files if not f.is_injected]


def format_memory_content(files: list[MemoryFileInfo]) -> str:
    """
    Format memory files into a single string for the system prompt.

    Args:
        files: List of memory files

    Returns:
        Formatted memory content string
    """
    if not files:
        return ""

    parts = [MEMORY_INSTRUCTION_PROMPT, ""]

    for file_info in files:
        # Add file header
        rel_path = file_info.path
        parts.append(f"## {rel_path}")
        parts.append("")
        parts.append(file_info.content)
        parts.append("")

    return "\n".join(parts)


def is_text_file_extension(path: str) -> bool:
    """Check if a file has a text file extension."""
    ext = os.path.splitext(path)[1].lower()
    return ext in TEXT_FILE_EXTENSIONS


def process_memory_includes(
    content: str,
    base_path: str,
    processed_paths: set[str] | None = None,
) -> str:
    """
    Process @include directives in memory content.

    Args:
        content: The memory file content
        base_path: The directory containing the memory file
        processed_paths: Set of already processed paths to prevent cycles

    Returns:
        Content with includes expanded
    """
    if processed_paths is None:
        processed_paths = set()

    # Simple implementation - look for @path patterns
    import re

    include_pattern = re.compile(r"@(\.?/[^\s]+|~/[^\s]+|[a-zA-Z0-9_\-./]+\.[a-zA-Z]+)")

    def replace_include(match: re.Match[str]) -> str:
        include_path = match.group(1)

        # Resolve the path
        if include_path.startswith("~/"):
            full_path = os.path.expanduser(include_path)
        elif include_path.startswith("./") or include_path.startswith("/"):
            full_path = os.path.join(base_path, include_path)
        else:
            full_path = os.path.join(base_path, include_path)

        full_path = os.path.normpath(full_path)

        # Prevent cycles
        if full_path in processed_paths:
            return match.group(0)

        # Check if it's a text file
        if not is_text_file_extension(full_path):
            return match.group(0)

        # Try to read the file
        try:
            if not os.path.isfile(full_path):
                return match.group(0)

            processed_paths.add(full_path)
            included_content = Path(full_path).read_text(encoding="utf-8")

            # Recursively process includes
            return process_memory_includes(
                included_content,
                os.path.dirname(full_path),
                processed_paths,
            )
        except Exception:
            return match.group(0)

    return include_pattern.sub(replace_include, content)
