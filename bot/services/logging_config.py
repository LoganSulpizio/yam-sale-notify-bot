# logging_config.py
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Set

from bot.config.settings import LOG_DIR

# --- Toggle Development Mode -------------------------------------------------
# Set this variable to True to also show INFO and WARNING logs in the console.
# By default (False), only ERROR logs are displayed in the console.
DEVELOPMENT = False

# --- Paths -------------------------------------------------------------------
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "yam-sale-notify-bot.log"

# --- Formatters --------------------------------------------------------------
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
formatter = logging.Formatter(LOG_FORMAT)


# Filter out some telegram logs
class SuppressApschedulerJobFilter(logging.Filter):
    """
    Suppress APScheduler executor logs for specific job names (to avoid noisy
    'Running job ...' / 'executed successfully' lines), while keeping other jobs.

    This targets records emitted by: apscheduler.executors.default
    and filters by substring match on the formatted message, which includes the job name.
    """

    def __init__(self, suppressed_job_names: Set[str]) -> None:
        super().__init__()
        self.suppressed_job_names = suppressed_job_names

    def filter(self, record: logging.LogRecord) -> bool:
        # Only filter APScheduler executor logs. Everything else passes through.
        if record.name != "apscheduler.executors.default":
            return True

        msg = record.getMessage()
        # Drop if the message contains any suppressed job name.
        return not any(job_name in msg for job_name in self.suppressed_job_names)


# Configure which APScheduler job(s) to suppress
apscheduler_noisy_jobs_filter = SuppressApschedulerJobFilter(
    suppressed_job_names={"check for new sales event job"}
)

# --- File handler (always on, INFO/WARNING/ERROR) ----------------------------
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=3 * 1024 * 1024,  # 3 MB
    backupCount=10,
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)  # File captures INFO and above
file_handler.setFormatter(formatter)
if not DEVELOPMENT:
    file_handler.addFilter(apscheduler_noisy_jobs_filter)
    
# --- Console handler for ERROR (always on) -----------------------------------
console_errors = logging.StreamHandler()
console_errors.setLevel(logging.ERROR)  # Always show errors in console
console_errors.setFormatter(formatter)

# --- Optional console handler for INFO/WARNING (dev only) --------------------
console_dev = logging.StreamHandler()
console_dev.setLevel(logging.INFO)  # Show INFO and above (INFO/WARNING/ERROR)
console_dev.setFormatter(formatter)

# --- Root logger setup -------------------------------------------------------
handlers = [file_handler, console_errors]
if DEVELOPMENT:
    handlers.append(console_dev)

logging.basicConfig(
    level=logging.INFO,
    handlers=handlers,
)

def get_logger(name: str) -> logging.Logger:
    """Return a logger with the given name."""
    return logging.getLogger(name)

# Silence noisy HTTPX request logs, but keep warnings/errors
logging.getLogger("httpx").setLevel(logging.WARNING)

# Log that the config is initialized
get_logger(__name__).info(
    "Logging initialized: file=INFO+, console=ERROR"
    + ("+INFO/WARNING (DEV MODE)" if DEVELOPMENT else "")
)
