"""Centralized logging utilities."""

import logging
import sys


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure and return root logger for the application."""
    level = logging.DEBUG if debug else logging.INFO
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%H:%M:%S",
    )

    root_logger = logging.getLogger("wayground")
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Retrieve a namespaced child logger."""
    return logging.getLogger(f"wayground.{name}")
