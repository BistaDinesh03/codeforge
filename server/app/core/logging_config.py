"""
Production logging configuration.
Structured output, file rotation, correlation IDs.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configure logging for the entire application.
    
    Console: INFO and above, simple format
    File: DEBUG and above, detailed format with timestamps
    Error file: ERROR and above, separate file for quick debugging
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Formatters
    console_fmt = logging.Formatter(
        fmt="%(levelname)-8s | %(message)s"
    )
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter
    root_logger.handlers.clear()

    # Console handler (human-readable)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(console_fmt)
    root_logger.addHandler(console)

    # File handler (all logs, rotates at 10MB, keeps 5 backups)
    log_file = settings.LOGS_DIR / "codeforge.log"
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_fmt)
    root_logger.addHandler(file_handler)

    # Error file handler (only errors, for quick scanning)
    error_file = settings.LOGS_DIR / "errors.log"
    error_handler = RotatingFileHandler(
        filename=error_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_fmt)
    root_logger.addHandler(error_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized (level={settings.LOG_LEVEL})")
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(name)