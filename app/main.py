from fastapi import FastAPI
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import request_logging_middleware
from app.infrastructure.db.session import db_ping

setup_logging()
logger = get_logger("startup")
logger.info("Logging system initialized")

settings = get_settings()

app = FastAPI()
app.middleware("http")(request_logging_middleware)

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.app_name, "version": settings.version, "environment": settings.env, "log_level": settings.log_level}

@app.get("/health/db")
def health_db():
    db_ping()
    return {"status": "ok", "db": "up"}