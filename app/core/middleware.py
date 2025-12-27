import time
from uuid import uuid4

from fastapi import Request
from starlette.responses import Response

from app.core.logging import get_logger


logger = get_logger("http")


async def request_logging_middleware(request: Request, call_next) -> Response:
    request_id = str(uuid4())
    request.state.request_id = request_id

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "Unhandled exception during request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise

    duration_ms = int((time.perf_counter() - start) * 1000)

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response
