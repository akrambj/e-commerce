# app/core/image_errors.py
from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import AppError, ValidationError


@dataclass
class ImageValidationError(ValidationError):
    code: str = "image_validation_error"


@dataclass
class ImageUploadError(AppError):
    code: str = "image_upload_failed"
