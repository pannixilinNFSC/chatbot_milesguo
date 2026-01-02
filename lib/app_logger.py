import logging
import os
import sys
from typing import Optional


_CONFIGURED = False


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure application logging for Cloud Run.

    Motivation:
    - Cloud Run automatically captures stdout/stderr into Cloud Logging.
    - Using Python's logging (instead of print) preserves severity levels and stack traces.
    - Keep configuration idempotent to avoid duplicate handlers on import/reload.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)

    # Avoid duplicate handlers if something else already configured logging.
    if not root.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)

    # Make common server loggers follow the same level/handlers.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).setLevel(log_level)

    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger after ensuring logging is configured.
    """
    setup_logging()
    return logging.getLogger(name or "app")


