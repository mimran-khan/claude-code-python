"""
JSON Schema extraction for Pydantic models / types (Zod parity layer).

Migrated from: utils/zodToJsonSchema.ts (Zod v4 ``toJSONSchema`` + WeakMap cache).

Python callers pass Pydantic v2 models or annotation types understood by
:class:`pydantic.TypeAdapter`.
"""

from __future__ import annotations

from typing import Any

_cache: dict[int, dict[str, Any]] = {}


def zod_to_json_schema(schema: Any) -> dict[str, Any]:
    """
    Return a JSON Schema dict for ``schema``, caching by object identity.

    Supports:
    - Subclasses of ``pydantic.BaseModel`` (``model_json_schema()``)
    - Other annotations via ``TypeAdapter(...).json_schema()``
    """
    key = id(schema)
    hit = _cache.get(key)
    if hit is not None:
        return hit

    if hasattr(schema, "model_json_schema"):
        result = schema.model_json_schema()
    else:
        from pydantic import TypeAdapter

        result = TypeAdapter(schema).json_schema()

    _cache[key] = result
    return result


def clear_zod_to_json_schema_cache_for_tests() -> None:
    _cache.clear()
