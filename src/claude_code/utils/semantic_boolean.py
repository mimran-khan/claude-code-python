"""
Boolean coercion tolerant of ``\"true\"`` / ``\"false\"`` strings (``utils/semanticBoolean.ts``).

Use with Pydantic v2 :class:`BeforeValidator`.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BeforeValidator


def _coerce_bool(v: Any) -> Any:
    if v == "true":
        return True
    if v == "false":
        return False
    return v


def semantic_boolean_schema() -> BeforeValidator:
    return BeforeValidator(_coerce_bool)


SemanticBool = Annotated[bool, semantic_boolean_schema()]

__all__ = ["SemanticBool", "semantic_boolean_schema", "_coerce_bool"]
