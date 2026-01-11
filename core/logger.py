"""
Structured logging for profile builder.

Provides consistent logging with timestamps, levels, and optional file output.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Log directory
LOG_DIR = Path("logs")


class ColorFormatter(logging.Formatter):
    """Colored console output formatter."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# Use ASCII pipe for Windows compatibility
PIPE = "|"


def setup_logger(
    name: str = "profile_builder",
    level: int = logging.DEBUG,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to write to file
        log_to_console: Whether to write to console

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler with colors
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_format = ColorFormatter(
            f'%(asctime)s {PIPE} %(levelname)-8s {PIPE} %(name)s {PIPE} %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        LOG_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"session_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_format = logging.Formatter(
            f'%(asctime)s {PIPE} %(levelname)-8s {PIPE} %(name)s {PIPE} %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        logger.info(f"Logging to: {log_file}")

    return logger


# Pre-configured loggers for each module
def get_logger(module: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        module: Module name (e.g., "screenshot", "vlm", "mouse")

    Returns:
        Logger instance
    """
    # Ensure root logger is set up
    setup_logger()
    return logging.getLogger(f"profile_builder.{module}")


# Convenience loggers
class Log:
    """Static access to module loggers."""

    _initialized = False

    @classmethod
    def _ensure_init(cls):
        if not cls._initialized:
            setup_logger()
            cls._initialized = True

    @classmethod
    def screenshot(cls) -> logging.Logger:
        cls._ensure_init()
        return logging.getLogger("profile_builder.screenshot")

    @classmethod
    def vlm(cls) -> logging.Logger:
        cls._ensure_init()
        return logging.getLogger("profile_builder.vlm")

    @classmethod
    def mouse(cls) -> logging.Logger:
        cls._ensure_init()
        return logging.getLogger("profile_builder.mouse")

    @classmethod
    def window(cls) -> logging.Logger:
        cls._ensure_init()
        return logging.getLogger("profile_builder.window")

    @classmethod
    def verify(cls) -> logging.Logger:
        cls._ensure_init()
        return logging.getLogger("profile_builder.verify")

    @classmethod
    def session(cls) -> logging.Logger:
        cls._ensure_init()
        return logging.getLogger("profile_builder.session")


# Quick access functions
def debug(msg: str, module: str = "main"):
    """Log debug message."""
    get_logger(module).debug(msg)


def info(msg: str, module: str = "main"):
    """Log info message."""
    get_logger(module).info(msg)


def warn(msg: str, module: str = "main"):
    """Log warning message."""
    get_logger(module).warning(msg)


def error(msg: str, module: str = "main"):
    """Log error message."""
    get_logger(module).error(msg)
