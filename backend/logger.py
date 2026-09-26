import os
import logging
from logging.handlers import RotatingFileHandler

# Define workspace logs directory
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

APP_LOG_PATH = os.path.join(LOGS_DIR, "app.log")
ERROR_LOG_PATH = os.path.join(LOGS_DIR, "error.log")

LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class ErrorFilter(logging.Filter):
    """Filters log records to only allow ERROR and CRITICAL levels."""
    def filter(self, record):
        return record.levelno >= logging.ERROR

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configures centralized rotating file logging and console logging.
    - logs/app.log: Captures INFO, WARNING, ERROR, CRITICAL
    - logs/error.log: Captures ERROR and CRITICAL only with stack trace
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Rotating App Log Handler (5MB max per file, keep 5 backups)
    app_file_handler = RotatingFileHandler(
        APP_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    app_file_handler.setLevel(log_level)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # 3. Rotating Error Log Handler (Only ERROR and CRITICAL)
    error_file_handler = RotatingFileHandler(
        ERROR_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.addFilter(ErrorFilter())
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    logger = logging.getLogger("governance_platform")
    logger.info("Centralized production logging initialized. Logs: %s, %s", APP_LOG_PATH, ERROR_LOG_PATH)
    return logger

# Module-level logger instance
logger = setup_logging()
