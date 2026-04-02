"""
Skills system: load, register, and resolve prompt skills.

TS sources: ``loadSkillsDir`` and ``mcpSkillBuilders``.

The primary API lives in :mod:`load_skills_dir` (async discovery, dedup, conditional skills).
A simplified synchronous loader in :mod:`loader` remains for bundled samples and legacy callers.
"""

from .builder import (
    SkillBuilder,
    build_skill_from_markdown,
    parse_skill_frontmatter,
)
from .bundled import (
    BUNDLED_SKILLS,
    get_bundled_skill,
    is_bundled_skill,
)
from .load_skills_dir import (
    MarkdownFile,
    SkillWithPath,
    activate_conditional_skills_for_paths,
    add_skill_directories,
    clear_command_caches,
    clear_dynamic_skills,
    clear_skill_caches,
    create_skill_command,
    discover_skill_dirs_for_paths,
    estimate_skill_frontmatter_tokens,
    fnmatch_path,
    get_command_dir_commands,
    get_conditional_skill_count,
    get_dynamic_skills,
    get_project_dirs_up_to_home,
    get_skill_dir_commands,
    get_skills_path,
    load_skills_from_commands_dir,
    load_skills_from_skills_dir,
    on_dynamic_skills_loaded,
    parse_skill_frontmatter_fields,
    transform_skill_files,
)
from .loader import (
    Skill,
    SkillFrontmatter,
    SkillSource,
    get_all_skills,
)
from .loader import (
    get_skills_path as get_default_skills_directory_path,
)
from .loader import (
    load_skills_dir as load_skills_from_directory_sync,
)
from .mcp_skill_builders import (
    MCPSkillBuilders,
    get_mcp_skill_builders,
    register_mcp_skill_builders,
)
from .types import (
    BundledSkillDefinition,
    GetPromptForCommand,
    LoadedFrom,
    ParsedSkillFrontmatter,
    PromptContentBlock,
    SkillCommand,
    ToolUseContext,
)

__all__ = [
    # Types (dataclasses / protocols)
    "BundledSkillDefinition",
    "GetPromptForCommand",
    "LoadedFrom",
    "ParsedSkillFrontmatter",
    "PromptContentBlock",
    "SkillCommand",
    "ToolUseContext",
    # MCP registry (mcpSkillBuilders.ts)
    "MCPSkillBuilders",
    "get_mcp_skill_builders",
    "register_mcp_skill_builders",
    # loadSkillsDir.ts — async / full pipeline
    "MarkdownFile",
    "SkillWithPath",
    "activate_conditional_skills_for_paths",
    "add_skill_directories",
    "clear_command_caches",
    "clear_dynamic_skills",
    "clear_skill_caches",
    "create_skill_command",
    "discover_skill_dirs_for_paths",
    "estimate_skill_frontmatter_tokens",
    "fnmatch_path",
    "get_command_dir_commands",
    "get_conditional_skill_count",
    "get_dynamic_skills",
    "get_project_dirs_up_to_home",
    "get_skill_dir_commands",
    "get_skills_path",
    "load_skills_from_commands_dir",
    "load_skills_from_skills_dir",
    "on_dynamic_skills_loaded",
    "parse_skill_frontmatter_fields",
    "transform_skill_files",
    # Legacy sync loader (simplified)
    "Skill",
    "SkillFrontmatter",
    "SkillSource",
    "get_all_skills",
    "get_default_skills_directory_path",
    "load_skills_from_directory_sync",
    # Bundled catalog (markdown samples)
    "BUNDLED_SKILLS",
    "get_bundled_skill",
    "is_bundled_skill",
    # Builder helpers
    "SkillBuilder",
    "build_skill_from_markdown",
    "parse_skill_frontmatter",
]
