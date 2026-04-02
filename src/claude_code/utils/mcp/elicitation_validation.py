"""
MCP elicitation primitive schema validation.

Migrated from: utils/mcp/elicitationValidation.ts
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal, cast

from pydantic import TypeAdapter, ValidationError

from ..json import json_stringify
from ..string_utils import plural
from .date_time_parser import (
    DateTimeParseSuccess,
    looks_like_iso8601,
    parse_natural_language_date_time,
)


@dataclass
class ValidationResult:
    value: str | int | float | bool | None = None
    is_valid: bool = False
    error: str | None = None


PrimitiveSchema = dict[str, Any]


def is_enum_schema(schema: PrimitiveSchema) -> bool:
    return schema.get("type") == "string" and ("enum" in schema or "oneOf" in schema)


def is_multi_select_enum_schema(schema: PrimitiveSchema) -> bool:
    items = schema.get("items")
    if schema.get("type") != "array" or not isinstance(items, dict):
        return False
    return "enum" in items or "anyOf" in items


def get_multi_select_values(schema: PrimitiveSchema) -> list[str]:
    items = cast(dict[str, Any], schema.get("items"))
    if "anyOf" in items:
        return [str(x["const"]) for x in items["anyOf"] if isinstance(x, dict) and "const" in x]
    if "enum" in items:
        return [str(x) for x in items["enum"]]
    return []


def get_multi_select_labels(schema: PrimitiveSchema) -> list[str]:
    items = cast(dict[str, Any], schema.get("items"))
    if "anyOf" in items:
        return [str(x.get("title", x.get("const", ""))) for x in items["anyOf"] if isinstance(x, dict)]
    if "enum" in items:
        return [str(x) for x in items["enum"]]
    return []


def get_multi_select_label(schema: PrimitiveSchema, value: str) -> str:
    vals = get_multi_select_values(schema)
    labels = get_multi_select_labels(schema)
    try:
        i = vals.index(value)
        return labels[i] if i < len(labels) else value
    except ValueError:
        return value


def get_enum_values(schema: PrimitiveSchema) -> list[str]:
    if "oneOf" in schema:
        return [str(x["const"]) for x in schema["oneOf"] if isinstance(x, dict) and "const" in x]
    if "enum" in schema:
        return [str(x) for x in schema["enum"]]
    return []


def get_enum_labels(schema: PrimitiveSchema) -> list[str]:
    if "oneOf" in schema:
        return [str(x.get("title", x.get("const", ""))) for x in schema["oneOf"] if isinstance(x, dict)]
    if "enum" in schema:
        names = schema.get("enumNames")
        if isinstance(names, list) and len(names) == len(schema["enum"]):
            return [str(x) for x in names]
        return [str(x) for x in schema["enum"]]
    return []


def get_enum_label(schema: PrimitiveSchema, value: str) -> str:
    vals = get_enum_values(schema)
    labels = get_enum_labels(schema)
    try:
        i = vals.index(value)
        return labels[i] if i < len(labels) else value
    except ValueError:
        return value


def _validate_string_schema(schema: PrimitiveSchema, string_value: str) -> ValidationResult:
    fmt = schema.get("format")
    min_len = schema.get("minLength")
    max_len = schema.get("maxLength")
    s = string_value
    if min_len is not None and len(s) < int(min_len):
        return ValidationResult(
            is_valid=False,
            error=f"Must be at least {min_len} {plural(int(min_len), 'character')}",
        )
    if max_len is not None and len(s) > int(max_len):
        return ValidationResult(
            is_valid=False,
            error=f"Must be at most {max_len} {plural(int(max_len), 'character')}",
        )
    if fmt == "email":
        ta = TypeAdapter(str)
        try:
            # pydantic 2 email validation
            from pydantic import EmailStr

            EmailStr._validate(s)  # type: ignore[attr-defined]
        except Exception:
            try:
                ta.validate_python(s)
            except ValidationError as e:
                return ValidationResult(is_valid=False, error="; ".join(str(x) for x in e.errors()))
        if "@" not in s:
            return ValidationResult(is_valid=False, error="Must be a valid email address")
    elif fmt == "uri":
        if not re.match(r"^https?://", s):
            return ValidationResult(is_valid=False, error="Must be a valid URI")
    elif fmt == "date":
        try:
            date.fromisoformat(s[:10])
        except ValueError:
            return ValidationResult(is_valid=False, error="Must be a valid date")
    elif fmt == "date-time":
        try:
            datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return ValidationResult(is_valid=False, error="Must be a valid date-time")
    return ValidationResult(value=s, is_valid=True)


def validate_elicitation_input(string_value: str, schema: PrimitiveSchema) -> ValidationResult:
    if is_enum_schema(schema):
        vals = get_enum_values(schema)
        if not vals:
            return ValidationResult(is_valid=False, error="Invalid enum schema")
        if string_value not in vals:
            return ValidationResult(is_valid=False, error=f"Must be one of: {', '.join(vals)}")
        return ValidationResult(value=string_value, is_valid=True)

    st = schema.get("type")
    if st == "string":
        return _validate_string_schema(schema, string_value)
    if st in ("number", "integer"):
        try:
            num = float(string_value) if st == "number" else int(float(string_value))
        except ValueError:
            return ValidationResult(is_valid=False, error=f"Must be a valid {st}")
        mn, mx = schema.get("minimum"), schema.get("maximum")
        if mn is not None and num < float(mn):
            return ValidationResult(is_valid=False, error=f"Must be >= {mn}")
        if mx is not None and num > float(mx):
            return ValidationResult(is_valid=False, error=f"Must be <= {mx}")
        if st == "integer" and not float(num).is_integer():
            return ValidationResult(is_valid=False, error="Must be an integer")
        return ValidationResult(value=num, is_valid=True)
    if st == "boolean":
        low = string_value.strip().lower()
        if low in ("true", "1", "yes"):
            return ValidationResult(value=True, is_valid=True)
        if low in ("false", "0", "no"):
            return ValidationResult(value=False, is_valid=True)
        return ValidationResult(is_valid=False, error="Must be a boolean")

    return ValidationResult(is_valid=False, error=f"Unsupported schema: {json_stringify(schema)}")


STRING_FORMATS: dict[str, tuple[str, str]] = {
    "email": ("email address", "user@example.com"),
    "uri": ("URI", "https://example.com"),
    "date": ("date", "2024-03-15"),
    "date-time": ("date-time", "2024-03-15T14:30:00Z"),
}


def get_format_hint(schema: PrimitiveSchema) -> str | None:
    st = schema.get("type")
    if st == "string" and isinstance(schema.get("format"), str):
        desc, ex = STRING_FORMATS.get(schema["format"], (schema["format"], ""))
        return f"{desc}, e.g. {ex}" if ex else desc
    if st in ("number", "integer"):
        mn, mx = schema.get("minimum"), schema.get("maximum")
        if mn is not None and mx is not None:
            return f"({st} between {mn} and {mx})"
        if mn is not None:
            return f"({st} >= {mn})"
        if mx is not None:
            return f"({st} <= {mx})"
        ex = "42" if st == "integer" else "3.14"
        return f"({st}, e.g. {ex})"
    return None


def is_date_time_schema(
    schema: PrimitiveSchema,
) -> bool:
    return schema.get("type") == "string" and schema.get("format") in ("date", "date-time")


async def validate_elicitation_input_async(
    string_value: str,
    schema: PrimitiveSchema,
    cancel_event: asyncio.Event | None = None,
) -> ValidationResult:
    sync = validate_elicitation_input(string_value, schema)
    if sync.is_valid:
        return sync
    if is_date_time_schema(schema) and not looks_like_iso8601(string_value):
        parse_result = await parse_natural_language_date_time(
            string_value,
            cast(Literal["date", "date-time"], schema["format"]),
            cancel_event,
        )
        if isinstance(parse_result, DateTimeParseSuccess):
            reparsed = validate_elicitation_input(parse_result.value, schema)
            if reparsed.is_valid:
                return reparsed
    return sync
