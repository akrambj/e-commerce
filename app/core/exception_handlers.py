# app/core/exception_handlers.py
from __future__ import annotations

from typing import Dict, Type, cast

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.responses import ApiError

logger = get_logger("exceptions")


def _trace_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _api_error_payload(*, message: str, errors: dict | None, trace_id: str | None) -> dict:
    # by_alias=True ensures "trace_id" key is used
    return ApiError(message=message, errors=errors, trace_id=trace_id).model_dump(
        by_alias=True,
        exclude_none=True,
    )


def _status_for_app_error(exc: AppError) -> int:
    mapping: Dict[Type[AppError], int] = {
        NotFoundError: 404,
        ValidationError: 422,
        ConflictError: 409,
        ForbiddenError: 403,
    }
    for exc_type, status in mapping.items():
        if isinstance(exc, exc_type):
            return status
    return 400


# NOTE:
# FastAPI's add_exception_handler typing expects handlers shaped like:
#   (Request, Exception) -> Response
# even if the handler is only ever called for a specific exception type at runtime.
# So we widen the type annotation to `Exception` and `cast(...)` inside for editor/type-checker harmony.


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    app_exc = cast(AppError, exc)

    trace_id = _trace_id(request)
    status_code = _status_for_app_error(app_exc)

    level = "warning" if status_code < 500 else "error"
    getattr(logger, level)(
        "Application error",
        extra={
            "trace_id": trace_id,
            "path": str(request.url.path),
            "code": getattr(app_exc, "code", "app_error"),
        },
    )

    payload = _api_error_payload(
        message=app_exc.message,
        errors=app_exc.details,
        trace_id=trace_id,
    )
    return JSONResponse(status_code=status_code, content=payload)


async def request_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    val_exc = cast(RequestValidationError, exc)
    trace_id = _trace_id(request)

    payload = _api_error_payload(
        message="Validation error",
        errors={"validation": val_exc.errors()},
        trace_id=trace_id,
    )
    return JSONResponse(status_code=422, content=payload)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(StarletteHTTPException, exc)
    trace_id = _trace_id(request)

    message = http_exc.detail if isinstance(http_exc.detail, str) else "HTTP error"
    payload = _api_error_payload(
        message=message,
        errors={"detail": http_exc.detail} if not isinstance(http_exc.detail, str) else None,
        trace_id=trace_id,
    )
    return JSONResponse(status_code=http_exc.status_code, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = _trace_id(request)

    logger.exception(
        "Unhandled exception",
        extra={
            "trace_id": trace_id,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    payload = _api_error_payload(
        message="Internal server error",
        errors=None,
        trace_id=trace_id,
    )
    return JSONResponse(status_code=500, content=payload)
