import json
import logging
import logging.config
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        # Include "extra" fields passed via logger.info(..., extra={...})
        reserved = {
            "name", "msg", "args", "levelname", "levelno",
            "pathname", "filename", "module", "exc_info", "exc_text",
            "stack_info", "lineno", "funcName", "created", "msecs",
            "relativeCreated", "thread", "threadName", "processName", "process", "taskName",
        }

        for key, value in record.__dict__.items():
            if key in reserved or key.startswith("_"):
                continue
            # Make sure the value is JSON-serializable (fallback to string)
            try:
                json.dumps(value)
                log_object[key] = value
            except TypeError:
                log_object[key] = str(value)

        return json.dumps(log_object)


def setup_logging() -> None:
    config_path = Path(__file__).resolve().parent.parent / "config" / "logging.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Logging config not found at {config_path}")
    
    with config_path.open() as f:
        config = json.load(f)

    log_level = settings.log_level.upper()

    config["root"]["level"] = log_level

    for handler in config.get("handlers", {}).values():
        handler["level"] = log_level

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)