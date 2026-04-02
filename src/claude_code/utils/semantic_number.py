"""
Number coercion tolerant of decimal numeric strings (``utils/semanticNumber.ts``).

Use with Pydantic v2 :class:`BeforeValidator`.
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BeforeValidator

_NUM = re.compile(r"^-?\d+(\.\d+)?$")


def _coerce_num(v: Any) -> Any:
    if isinstance(v, str) and _NUM.fullmatch(v):
        n = float(v) if "." in v else int(v)
        if isinstance(n, float) and n.is_integer():
            return int(n)
        return n
    return v


def semantic_number_schema() -> BeforeValidator:
    return BeforeValidator(_coerce_num)


SemanticNumber = Annotated[float, semantic_number_schema()]

__all__ = ["SemanticNumber", "semantic_number_schema", "_coerce_num"]
