# app/core/exceptions.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AppError(Exception):
    """
    Base application exception (domain-level, not HTTP).
    - message: human-readable
    - code: stable machine-readable identifier
    - details: optional dict for extra context (safe to expose if needed)
    """

    message: str
    code: str = "app_error"
    details: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.message


# ---------------------------
# Generic domain errors
# ---------------------------

@dataclass
class NotFoundError(AppError):
    code: str = "not_found"


@dataclass
class ValidationError(AppError):
    code: str = "validation_error"


@dataclass
class ConflictError(AppError):
    code: str = "conflict"


@dataclass
class ForbiddenError(AppError):
    code: str = "forbidden"


# ---------------------------
# Products domain errors
# ---------------------------

@dataclass
class ProductNotFoundError(NotFoundError):
    code: str = "product_not_found"


@dataclass
class ProductNotPublicError(ForbiddenError):
    """
    Used when a product exists but is not publicly visible
    (inactive or soft-deleted).
    """
    code: str = "product_not_public"


@dataclass
class ProductSlugConflictError(ConflictError):
    code: str = "product_slug_conflict"
