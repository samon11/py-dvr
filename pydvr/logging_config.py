"""
Logging configuration for PyDVR.

Provides centralized logging setup with console and file handlers.
Implements the Single Responsibility Principle for logging configuration.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Configure root logger for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, only console logging is enabled
        log_format: Optional custom log format string. If None, uses default format

    Returns:
        logging.Logger: Configured root logger

    Example:
        >>> from pydvr.logging_config import setup_logging
        >>> logger = setup_logging(log_level="INFO")
        >>> logger.info("Application started")
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Default format: timestamp - logger name - level - message
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file is not None:
        try:
            # Ensure log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Create rotating file handler to prevent log files from growing too large
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,  # Keep 5 backup files
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, log to console but don't crash
            root_logger.warning(f"Failed to setup file logging to {log_file}: {e}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ from the calling module)

    Returns:
        logging.Logger: Logger instance for the specified name

    Example:
        >>> from pydvr.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)
