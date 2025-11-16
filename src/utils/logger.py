"""Logging configuration for the AI File Classifier."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class ClassifierLogger:
    """Manages logging configuration for the application."""

    _instance: Optional['ClassifierLogger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        """Singleton pattern to ensure only one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger (only once)."""
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(
        self,
        name: str = "ai_file_classifier",
        level: str = "INFO",
        log_file: Optional[str] = None,
        log_rotation: bool = True,
        max_log_size_mb: int = 10,
        backup_count: int = 5
    ):
        """
        Set up the logger with console and file handlers.

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (None for no file logging)
            log_rotation: Whether to rotate log files
            max_log_size_mb: Maximum log file size in MB
            backup_count: Number of backup files to keep
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        self._logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self._logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            if log_rotation:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_log_size_mb * 1024 * 1024,
                    backupCount=backup_count
                )
            else:
                file_handler = logging.FileHandler(log_file)

            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self._logger.addHandler(file_handler)

    def configure(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        log_rotation: bool = True,
        max_log_size_mb: int = 10
    ):
        """
        Configure the logger with custom settings.

        Args:
            level: Logging level
            log_file: Path to log file
            log_rotation: Whether to rotate log files
            max_log_size_mb: Maximum log file size in MB
        """
        self._setup_logger(
            level=level,
            log_file=log_file,
            log_rotation=log_rotation,
            max_log_size_mb=max_log_size_mb
        )

    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.

        Returns:
            Logger instance
        """
        if self._logger is None:
            self._setup_logger()
        return self._logger


# Global logger instance
_classifier_logger = ClassifierLogger()


def get_logger() -> logging.Logger:
    """
    Get the global logger instance.

    Returns:
        Configured logger
    """
    return _classifier_logger.get_logger()


def configure_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_rotation: bool = True,
    max_log_size_mb: int = 10
):
    """
    Configure the global logger.

    Args:
        level: Logging level
        log_file: Path to log file
        log_rotation: Whether to rotate log files
        max_log_size_mb: Maximum log file size in MB
    """
    _classifier_logger.configure(
        level=level,
        log_file=log_file,
        log_rotation=log_rotation,
        max_log_size_mb=max_log_size_mb
    )
