from fastapi import FastAPI
from app.core.config import settings

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.app_name, "version": settings.version, "environment": settings.env, "log_level": settings.log_level}