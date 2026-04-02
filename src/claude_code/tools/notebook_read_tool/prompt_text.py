"""Prompt for reading Jupyter notebooks as structured summaries."""

from __future__ import annotations

DESCRIPTION = (
    "Read a Jupyter notebook (.ipynb) and return a structured summary of cells (index, type, and source preview)."
)

PROMPT = """
Read the notebook at the given path and return each cell's index, cell_type, and a truncated
preview of the source. Use absolute paths. Does not execute code.
""".strip()
