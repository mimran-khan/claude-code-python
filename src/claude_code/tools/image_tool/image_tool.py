"""
Image processor loader — migrated from tools/FileReadTool/imageProcessor.ts.

TODO: Optional native `image-processor-napi` equivalent; full sharp-like API surface.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from ..base import Tool, ToolResult, ToolUseContext
from .constants import DESCRIPTION, IMAGE_TOOL_NAME
from .types import ImageProcessorFn

_image_processor_module: ImageProcessorFn | None = None


def get_image_processor() -> ImageProcessorFn:
    """Return callable(buffer: bytes) -> PIL.Image (or future Sharp-like wrapper)."""
    global _image_processor_module
    if _image_processor_module is not None:
        return _image_processor_module

    try:
        from PIL import Image  # type: ignore[import-untyped]
    except ImportError as e:
        raise RuntimeError("No image processor available; install Pillow or wire native processor (TODO).") from e

    def _pillow_processor(data: bytes) -> Any:
        return Image.open(BytesIO(data))

    _image_processor_module = _pillow_processor
    return _pillow_processor


class ImageTool(Tool[dict[str, Any], dict[str, Any]]):
    """Probe whether an image backend is available (optional utility tool)."""

    @property
    def name(self) -> str:
        return IMAGE_TOOL_NAME

    @property
    def search_hint(self) -> str:
        return "image load resize convert"

    async def description(self) -> str:
        return DESCRIPTION

    async def prompt(self) -> str:
        return DESCRIPTION

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["probe"],
                    "description": "probe checks whether a processor is available",
                }
            },
            "required": ["action"],
        }

    def get_output_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"available": {"type": "boolean"}}}

    async def execute(
        self,
        input: dict[str, Any],
        context: ToolUseContext,
    ) -> ToolResult:
        try:
            get_image_processor()
            return ToolResult(success=True, output={"available": True})
        except RuntimeError:
            return ToolResult(success=True, output={"available": False})
