#!/usr/bin/env python3
"""
Logging configuration for MSP Orchestrator
"""
import logging
import sys
from pathlib import Path

try:
    from src.config_loader import config
except ImportError:
    # Fallback if config loader not available
    class FallbackConfig:
        def get(self, key, default):
            defaults = {
                "log_level": "INFO",
                "log_format": "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
            }
            return defaults.get(key, default)
    config = FallbackConfig()


def setup_logging(log_file: Path = None):
    """
    Configure logging for the application
    :param log_file: Optional log file path
    """
    log_level = getattr(logging, config.get("log_level", "INFO").upper(), logging.INFO)
    log_format = config.get("log_format", "[%(asctime)s] %(levelname)s - %(name)s - %(message)s")

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Add file handler if log_file specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

    # Set levels for specific loggers to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    logging.info("Logging system initialized")
