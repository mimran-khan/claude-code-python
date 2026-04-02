"""
Escape XML/HTML for safe interpolation into element text or attributes.

Migrated from: utils/xml.ts
"""

from __future__ import annotations


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_xml_attr(s: str) -> str:
    return escape_xml(s).replace('"', "&quot;").replace("'", "&apos;")
