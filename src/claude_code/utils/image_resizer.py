"""
Image resize, compress, and format detection for API limits.

Migrated from: utils/imageResizer.ts (uses Pillow instead of sharp).
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any, Literal

from PIL import Image

from ..constants.api_limits import (
    API_IMAGE_MAX_BASE64_SIZE,
    IMAGE_MAX_HEIGHT,
    IMAGE_MAX_WIDTH,
    IMAGE_TARGET_RAW_SIZE,
)
from .debug import log_for_debugging
from .errors import error_message
from .format import format_file_size
from .log import log_error
from .telemetry.events import log_otel_event

ImageMediaType = Literal["image/png", "image/jpeg", "image/gif", "image/webp"]


class ImageResizeError(Exception):
    """Raised when an image cannot be resized to satisfy API constraints."""


@dataclass
class ImageDimensions:
    original_width: int | None = None
    original_height: int | None = None
    display_width: int | None = None
    display_height: int | None = None


@dataclass
class ResizeResult:
    buffer: bytes
    media_type: str
    dimensions: ImageDimensions | None = None


@dataclass
class CompressedImageResult:
    base64: str
    media_type: str
    original_size: int


def _classify_image_error(err: BaseException) -> int:
    msg = error_message(err).lower()
    if "cannot identify image" in msg or "broken data" in msg:
        return 2
    if "memory" in msg:
        return 5
    return 3


def _hash_string(s: str) -> int:
    h = 5381
    for ch in s:
        h = ((h << 5) + h + ord(ch)) & 0xFFFFFFFF
    return h


def detect_image_format_from_buffer(buf: bytes) -> ImageMediaType:
    if len(buf) < 4:
        return "image/png"
    if buf[:4] == b"\x89PNG":
        return "image/png"
    if buf[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if buf[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if len(buf) >= 12 and buf[:4] == b"RIFF" and buf[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def detect_image_format_from_base64(data: str) -> ImageMediaType:
    try:
        raw = base64.b64decode(data, validate=False)
        return detect_image_format_from_buffer(raw)
    except Exception:
        return "image/png"


async def maybe_resize_and_downsample_image_buffer(
    image_buffer: bytes,
    original_size: int,
    ext: str,
) -> ResizeResult:
    if not image_buffer:
        raise ImageResizeError("Image file is empty (0 bytes)")
    try:
        with Image.open(io.BytesIO(image_buffer)) as im:
            w, h = im.size
            fmt = (im.format or ext or "PNG").lower()
            if fmt == "jpg":
                fmt = "jpeg"

            if original_size <= IMAGE_TARGET_RAW_SIZE and w <= IMAGE_MAX_WIDTH and h <= IMAGE_MAX_HEIGHT:
                return ResizeResult(
                    buffer=image_buffer,
                    media_type=fmt,
                    dimensions=ImageDimensions(w, h, w, h),
                )

            work = im.convert("RGB") if im.mode not in ("RGB", "L") else im.convert("RGB")
            ratio = min(IMAGE_MAX_WIDTH / max(w, 1), IMAGE_MAX_HEIGHT / max(h, 1), 1.0)
            nw, nh = max(1, int(w * ratio)), max(1, int(h * ratio))
            resized = work.resize((nw, nh), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            resized.save(out, format="JPEG", quality=80, optimize=True)
            data = out.getvalue()
            if len(data) > IMAGE_TARGET_RAW_SIZE:
                out = io.BytesIO()
                resized.save(out, format="JPEG", quality=40, optimize=True)
                data = out.getvalue()
            log_for_debugging(f"Resized image to {nw}x{nh}, bytes={len(data)}")
            return ResizeResult(
                buffer=data,
                media_type="jpeg",
                dimensions=ImageDimensions(w, h, nw, nh),
            )
    except Exception as e:
        log_error(e)
        await log_otel_event(
            "tengu_image_resize_failed",
            {
                "original_size_bytes": str(original_size),
                "error_type": str(_classify_image_error(e)),
                "error_message_hash": str(_hash_string(error_message(e))),
            },
        )
        detected = detect_image_format_from_buffer(image_buffer)
        ext_norm = detected.split("/", 1)[1]
        b64_size = (original_size * 4 + 2) // 3
        over_dim = False
        if len(image_buffer) >= 24 and image_buffer[:4] == b"\x89PNG":
            try:
                pw = int.from_bytes(image_buffer[16:20], "big")
                ph = int.from_bytes(image_buffer[20:24], "big")
                over_dim = pw > IMAGE_MAX_WIDTH or ph > IMAGE_MAX_HEIGHT
            except Exception:
                pass
        if b64_size <= API_IMAGE_MAX_BASE64_SIZE and not over_dim:
            await log_otel_event(
                "tengu_image_resize_fallback",
                {
                    "original_size_bytes": str(original_size),
                    "base64_size_bytes": str(b64_size),
                },
            )
            return ResizeResult(buffer=image_buffer, media_type=ext_norm)
        raise ImageResizeError(
            "Unable to resize image — dimensions or size exceed API limits."
            if over_dim
            else f"Unable to resize image ({format_file_size(original_size)} raw). Please use a smaller image."
        ) from e


async def maybe_resize_and_downsample_image_block(image_block: dict[str, Any]) -> dict[str, Any]:
    src = image_block.get("source") or {}
    if src.get("type") != "base64":
        return {"block": image_block}
    raw = base64.b64decode(src.get("data", ""), validate=False)
    media = src.get("media_type") or "image/png"
    ext = media.split("/")[-1] if "/" in media else "png"
    resized = await maybe_resize_and_downsample_image_buffer(raw, len(raw), ext)
    return {
        "block": {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": f"image/{resized.media_type}",
                "data": base64.b64encode(resized.buffer).decode("ascii"),
            },
        },
        "dimensions": resized.dimensions,
    }


async def compress_image_buffer(
    image_buffer: bytes,
    max_bytes: int = IMAGE_TARGET_RAW_SIZE,
    original_media_type: str | None = None,
) -> CompressedImageResult:
    if len(image_buffer) <= max_bytes:
        fmt = (original_media_type or "image/jpeg").split("/")[-1]
        if fmt == "jpg":
            fmt = "jpeg"
        return CompressedImageResult(
            base64=base64.b64encode(image_buffer).decode("ascii"),
            media_type=f"image/{fmt}",
            original_size=len(image_buffer),
        )
    try:
        with Image.open(io.BytesIO(image_buffer)) as src:
            base_im = src.convert("RGB")
            for scale in (1.0, 0.75, 0.5, 0.25):
                w, h = base_im.size
                nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                sm = base_im.resize((nw, nh), Image.Resampling.LANCZOS)
                out = io.BytesIO()
                sm.save(out, format="JPEG", quality=75, optimize=True)
                data = out.getvalue()
                if len(data) <= max_bytes:
                    return CompressedImageResult(
                        base64=base64.b64encode(data).decode("ascii"),
                        media_type="image/jpeg",
                        original_size=len(image_buffer),
                    )
            out = io.BytesIO()
            base_im.resize((400, 400), Image.Resampling.LANCZOS).save(out, format="JPEG", quality=20, optimize=True)
            data = out.getvalue()
        return CompressedImageResult(
            base64=base64.b64encode(data).decode("ascii"),
            media_type="image/jpeg",
            original_size=len(image_buffer),
        )
    except Exception as e:
        log_error(e)
        if len(image_buffer) <= max_bytes:
            det = detect_image_format_from_buffer(image_buffer)
            return CompressedImageResult(
                base64=base64.b64encode(image_buffer).decode("ascii"),
                media_type=det,
                original_size=len(image_buffer),
            )
        raise ImageResizeError(
            f"Unable to compress image ({format_file_size(len(image_buffer))}) "
            f"to fit within {format_file_size(max_bytes)}."
        ) from e


async def compress_image_buffer_with_token_limit(
    image_buffer: bytes,
    max_tokens: float,
    original_media_type: str | None = None,
) -> CompressedImageResult:
    max_base64_chars = int(max_tokens / 0.125)
    max_bytes = int(max_base64_chars * 0.75)
    return await compress_image_buffer(image_buffer, max_bytes, original_media_type)


async def compress_image_block(
    image_block: dict[str, Any],
    max_bytes: int = IMAGE_TARGET_RAW_SIZE,
) -> dict[str, Any]:
    src = image_block.get("source") or {}
    if src.get("type") != "base64":
        return image_block
    raw = base64.b64decode(src.get("data", ""), validate=False)
    if len(raw) <= max_bytes:
        return image_block
    comp = await compress_image_buffer(raw, max_bytes)
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": comp.media_type,
            "data": comp.base64,
        },
    }


def create_image_metadata_text(
    dims: ImageDimensions,
    source_path: str | None = None,
) -> str | None:
    ow, oh, dw, dh = (
        dims.original_width,
        dims.original_height,
        dims.display_width,
        dims.display_height,
    )
    if not ow or not oh or not dw or not dh or dw <= 0 or dh <= 0:
        return f"[Image source: {source_path}]" if source_path else None
    resized = ow != dw or oh != dh
    if not resized and not source_path:
        return None
    parts: list[str] = []
    if source_path:
        parts.append(f"source: {source_path}")
    if resized:
        scale = ow / dw
        parts.append(
            f"original {ow}x{oh}, displayed at {dw}x{dh}. Multiply coordinates by {scale:.2f} to map to original image."
        )
    return f"[Image: {', '.join(parts)}]"
