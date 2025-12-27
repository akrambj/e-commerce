from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import request_logging_middleware

setup_logging()
logger = get_logger("startup")
logger.info("Logging system initialized")

app = FastAPI()
app.middleware("http")(request_logging_middleware)

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.app_name, "version": settings.version, "environment": settings.env, "log_level": settings.log_level}