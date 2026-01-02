# app/core/responses.py
from __future__ import annotations

from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiSuccess(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T


class ApiError(BaseModel):
    success: bool = False
    message: str = "Error"
    errors: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = Field(default=None, alias="trace_id")


def ok(data: T, message: str = "OK") -> ApiSuccess[T]:
    return ApiSuccess[T](message=message, data=data)
