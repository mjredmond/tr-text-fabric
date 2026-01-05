"""
Logging utilities for the TR Text-Fabric pipeline.

Provides consistent logging across all scripts with file and console output.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import load_config


# Global flag to track if logging has been set up
_logging_configured = False


def setup_logging(
    script_name: str = None,
    config: dict = None,
    log_level: str = None,
) -> logging.Logger:
    """
    Set up logging for a script.

    Args:
        script_name: Name of the script (used for log file naming)
        config: Loaded config dict. If None, loads from default location.
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured root logger
    """
    global _logging_configured

    if config is None:
        config = load_config()

    log_config = config.get("logging", {})

    # Determine log level
    level_str = log_level or log_config.get("level", "INFO")
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Get format strings
    log_format = log_config.get(
        "format",
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    date_format = log_config.get("date_format", "%Y-%m-%d %H:%M:%S")

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    if log_config.get("console", True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if script_name and log_config.get("per_script", True):
        log_dir = Path(config["paths"]["logs"])
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{script_name}_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"Logging to: {log_file}")

    _logging_configured = True
    return root_logger


def get_logger(name: str, config: dict = None) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Logger name (typically __name__)
        config: Optional config dict

    Returns:
        Configured logger
    """
    global _logging_configured

    if not _logging_configured:
        setup_logging(config=config)

    return logging.getLogger(name)


class ScriptLogger:
    """
    Context manager for script logging with timing.

    Usage:
        with ScriptLogger("p1_02_schema_scout") as logger:
            logger.info("Starting schema extraction...")
            # do work
            logger.info("Done!")
    """

    def __init__(self, script_name: str, config: dict = None):
        self.script_name = script_name
        self.config = config
        self.start_time = None
        self.logger = None

    def __enter__(self) -> logging.Logger:
        self.logger = setup_logging(self.script_name, self.config)
        self.start_time = datetime.now()
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Starting: {self.script_name}")
        self.logger.info(f"{'='*60}")
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = datetime.now() - self.start_time
        if exc_type is None:
            self.logger.info(f"{'='*60}")
            self.logger.info(f"Completed: {self.script_name}")
            self.logger.info(f"Duration: {elapsed}")
            self.logger.info(f"{'='*60}")
        else:
            self.logger.error(f"{'='*60}")
            self.logger.error(f"FAILED: {self.script_name}")
            self.logger.error(f"Error: {exc_type.__name__}: {exc_val}")
            self.logger.error(f"Duration: {elapsed}")
            self.logger.error(f"{'='*60}")
        return False  # Don't suppress exceptions


if __name__ == "__main__":
    # Test logging
    with ScriptLogger("test_logging") as logger:
        logger.info("This is an info message")
        logger.warning("This is a warning")
        logger.debug("This debug message may not show depending on level")
