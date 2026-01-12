# app/infrastructure/integrations/cloudinary/uploader.py
from __future__ import annotations

from typing import Any, Dict

import cloudinary.uploader
from fastapi import UploadFile

from app.core.config import get_settings
from app.core.image_errors import ImageUploadError, ImageValidationError

# Accept common formats from browsers/devices
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Your V1 requirement
MAX_BYTES = 2 * 1024 * 1024  # 2MB


def _validate_content_type(file: UploadFile) -> None:
    if not file.content_type or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ImageValidationError(
            message="Unsupported image type",
            details={"content_type": file.content_type},
        )


async def _read_with_limit(file: UploadFile, *, max_bytes: int) -> bytes:
    """
    Read the full file into memory with a hard limit.
    For V1 (<2MB) this is fine and simple.
    """
    data = await file.read()
    size = len(data)
    if size > max_bytes:
        raise ImageValidationError(
            message="Image too large",
            details={"max_bytes": max_bytes, "size_bytes": size},
        )
    return data


def _thumbnail_transform() -> list[dict]:
    # 300x300, fill + auto gravity, deliver as webp
    return [
        {
            "width": 300,
            "height": 300,
            "crop": "fill",
            "gravity": "auto",
            "quality": "auto",
            "fetch_format": "webp",
        }
    ]


def _full_image_transform() -> list[dict]:
    # Max 1920x1080, limit (no upscaling), deliver as webp
    return [
        {
            "width": 1920,
            "height": 1080,
            "crop": "limit",
            "quality": "auto",
            "fetch_format": "webp",
        }
    ]


async def upload_product_thumbnail(*, file: UploadFile, public_id: str) -> str:
    """
    Uploads and transforms a thumbnail.
    Returns secure delivery URL.
    """
    return await _upload_image(file=file, public_id=public_id, transformation=_thumbnail_transform())


async def upload_product_image(*, file: UploadFile, public_id: str) -> str:
    """
    Uploads and transforms a full product image.
    Returns secure delivery URL.
    """
    return await _upload_image(file=file, public_id=public_id, transformation=_full_image_transform())


async def _upload_image(*, file: UploadFile, public_id: str, transformation: list[dict]) -> str:
    _validate_content_type(file)
    data = await _read_with_limit(file, max_bytes=MAX_BYTES)

    s = get_settings()

    try:
        # Upload bytes; Cloudinary applies transformations on delivery.
        # We still request webp delivery format + resizing transform.
        res: Dict[str, Any] = cloudinary.uploader.upload(
            data,
            folder=s.cloudinary_products_folder,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            transformation=transformation,
        )
    except Exception as e:
        raise ImageUploadError(
            message="Cloudinary upload failed",
            details={"reason": str(e)},
        ) from e
    finally:
        # Good hygiene; UploadFile holds an internal SpooledTemporaryFile
        try:
            await file.close()
        except Exception:
            pass

    url = res.get("secure_url")
    if not url:
        raise ImageUploadError(message="Cloudinary did not return a secure_url", details={"result": res})

    return str(url)
