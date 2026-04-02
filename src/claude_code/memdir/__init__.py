"""
Memory directory system.

Automatic memory management using MEMORY.md files.

Migrated from: memdir/*.ts (8 files)
"""

from .memory import (
    ENTRYPOINT_NAME,
    MAX_ENTRYPOINT_BYTES,
    MAX_ENTRYPOINT_LINES,
    EntrypointTruncation,
    truncate_entrypoint_content,
)
from .memory_age import (
    memory_age,
    memory_age_days,
    memory_freshness_note,
    memory_freshness_text,
)
from .memory_types import (
    MEMORY_FRONTMATTER_EXAMPLE,
    MEMORY_TYPES,
    TYPES_SECTION_COMBINED,
    TYPES_SECTION_INDIVIDUAL,
    WHAT_NOT_TO_SAVE_SECTION,
)
from .paths import (
    get_auto_mem_path,
    get_memory_dir,
    is_auto_memory_enabled,
)
from .relevance import (
    MemoryMatch,
    find_relevant_memories,
)
from .scan import (
    MemoryFile,
    MemoryScanResult,
    scan_memory_files,
)

__all__ = [
    # Memory
    "ENTRYPOINT_NAME",
    "MAX_ENTRYPOINT_LINES",
    "MAX_ENTRYPOINT_BYTES",
    "truncate_entrypoint_content",
    "EntrypointTruncation",
    # Paths
    "get_auto_mem_path",
    "get_memory_dir",
    "is_auto_memory_enabled",
    # Scan
    "scan_memory_files",
    "MemoryFile",
    "MemoryScanResult",
    # Relevance
    "find_relevant_memories",
    "MemoryMatch",
    "memory_age_days",
    "memory_age",
    "memory_freshness_text",
    "memory_freshness_note",
    "MEMORY_TYPES",
    "MEMORY_FRONTMATTER_EXAMPLE",
    "TYPES_SECTION_COMBINED",
    "TYPES_SECTION_INDIVIDUAL",
    "WHAT_NOT_TO_SAVE_SECTION",
]
