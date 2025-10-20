#!/usr/bin/env python3
"""
Fallback utilities for MSP Orchestrator.

Provides fallback configuration and utility functions when main modules are unavailable.
This module eliminates DRY violations by centralizing fallback logic used across all agents.
"""
import time


class FallbackConfig:
    """
    Fallback configuration when config_loader is not available.
    Provides same interface as Config class with sensible defaults.
    """

    @property
    def max_scratchpad_chars(self):
        """Maximum characters in scratchpad before truncation"""
        return 8192

    @property
    def allowed_tools(self):
        """Default allowed tools for agents"""
        return ["file_read", "file_write", "shell"]

    @property
    def agent_timeout(self):
        """Default agent timeout in seconds"""
        return 300

    @property
    def port_range(self):
        """Default port range for clarification server"""
        return (8000, 9000)


def get_fallback_config():
    """
    Get configuration, with fallback if config_loader unavailable.

    Returns:
        Config object or FallbackConfig if import fails
    """
    try:
        from src.config_loader import config
        return config
    except ImportError:
        return FallbackConfig()


def get_timestamp():
    """
    Get current timestamp in HH:MM:SS format.

    Returns:
        str: Formatted timestamp string
    """
    return time.strftime('%H:%M:%S')
