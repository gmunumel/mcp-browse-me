"""Centralized logging setup for the project."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE_NAME = "mcp-browse-me.log"
_LOG_PATH = Path(__file__).resolve().parent.parent / LOG_FILE_NAME


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        message = record.getMessage()
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def _get_logger(name: str) -> logging.Logger:
    """Return a logger with default formatting configured once."""
    _LOG_PATH.touch(exist_ok=True)
    formatter = JsonFormatter()
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(_LOG_PATH, encoding="utf-8"),
    ]
    for handler in handlers:
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in handlers:
        root_logger.addHandler(handler)

    return logging.getLogger(name)


# Default logger for modules that prefer importing the shared instance.
logger = _get_logger(__name__)
