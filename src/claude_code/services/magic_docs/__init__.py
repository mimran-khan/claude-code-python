"""
Magic Docs - automatic documentation maintenance.

Automatically maintains markdown documentation files marked with special headers.
When a file with "# MAGIC DOC: [title]" is read, it runs periodically in the
background using a forked subagent to update the document with new learnings.

Migrated from: services/MagicDocs/*.ts
"""

from .magic_docs import (
    MAGIC_DOC_HEADER_PATTERN,
    clear_tracked_magic_docs,
    detect_magic_doc_header,
    get_tracked_magic_docs,
    is_magic_doc,
    register_magic_doc,
)
from .prompts import (
    build_magic_docs_update_prompt,
)

__all__ = [
    "MAGIC_DOC_HEADER_PATTERN",
    "detect_magic_doc_header",
    "register_magic_doc",
    "clear_tracked_magic_docs",
    "get_tracked_magic_docs",
    "is_magic_doc",
    "build_magic_docs_update_prompt",
]
