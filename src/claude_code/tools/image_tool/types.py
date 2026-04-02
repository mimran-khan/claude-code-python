"""Minimal types for image processing pipeline."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class ImageMetadata:
    width: int
    height: int
    format: str


# Callable taking raw bytes, returns an object with resize/jpeg/png/to_buffer API (TS Sharp subset)
ImageProcessorFn = Callable[[bytes], Any]
