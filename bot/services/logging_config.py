from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from bot.config.settings import LOG_DIR


LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "yam-sale-notify-bot.log"

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
formatter = logging.Formatter(LOG_FORMAT)


def setup_logging() -> None:
    """
    Configure logging so that:
    - INFO/WARNING/ERROR go to stdout (Docker captures it via `docker logs`)
    - INFO/WARNING/ERROR are also written to a rotating file
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicate logs if called multiple times
    root.handlers.clear()

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=3 * 1024 * 1024,  # 3 MB
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Silence noisy HTTPX request logs and job scheduler logs, but keep warnings/errors
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialized: file=INFO+, console=INFO+"
    )


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
