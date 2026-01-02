# app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exception_handlers import (
    app_error_handler,
    http_exception_handler,
    request_validation_error_handler,
    unhandled_exception_handler,
)
from app.core.exceptions import AppError, ProductNotFoundError
from app.core.logging import get_logger, setup_logging
from app.core.middleware import request_logging_middleware
from app.api.v1.routes import router as v1_router


# --- startup wiring (logging first) ---
setup_logging()
logger = get_logger("startup")

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.version)

# --- middleware ---
app.middleware("http")(request_logging_middleware)
app.include_router(v1_router)

# --- exception handlers (global) ---
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# --- routes ---
@app.get("/health")
def health():
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.env,
        "log_level": settings.log_level,
    }


@app.get("/health/db")
def health_db():
    return {"status": "ok", "db": "up"}


@app.get("/_debug/error")
def debug_error():
    raise ProductNotFoundError("Product not found.", details={"slug": "x"})


logger.info("App initialized", extra={"env": settings.env, "version": settings.version})
