#!/usr/bin/env python3
"""
Configuration loader for MSP Orchestrator
Loads settings from config.yaml
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Config:
    """Global configuration singleton"""
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def load(self, config_path: Path = None):
        """Load configuration from YAML file"""
        if config_path is None:
            # Default to config.yaml in project root
            config_path = Path(__file__).parent.parent / "config.yaml"

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
            # Load defaults
            self._config = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "version": "1.0",
            "default_max_scratchpad_chars": 8192,
            "default_allowed_tools": ["file_read", "file_write", "shell"],
            "log_level": "INFO",
            "clarification_server_port_range": {"min": 8000, "max": 9000},
            "agent_timeout_seconds": 300,
            "default_agent_port": 8000,
            "enable_status_display": True,
            "status_refresh_seconds": 2
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        if self._config is None:
            self.load()
        return self._config.get(key, default)

    @property
    def max_scratchpad_chars(self) -> int:
        if self._config is None:
            self.load()
        return self.get("default_max_scratchpad_chars", 8192)

    @property
    def allowed_tools(self) -> List[str]:
        if self._config is None:
            self.load()
        return self.get("default_allowed_tools", ["file_read", "file_write", "shell"])

    @property
    def log_level(self) -> str:
        if self._config is None:
            self.load()
        return self.get("log_level", "INFO")

    @property
    def agent_timeout(self) -> int:
        if self._config is None:
            self.load()
        return self.get("agent_timeout_seconds", 300)

    @property
    def port_range(self) -> tuple:
        if self._config is None:
            self.load()
        pr = self.get("clarification_server_port_range", {"min": 8000, "max": 9000})
        return (pr["min"], pr["max"])

    @property
    def enable_status_display(self) -> bool:
        if self._config is None:
            self.load()
        return self.get("enable_status_display", True)

    @property
    def status_refresh_seconds(self) -> int:
        if self._config is None:
            self.load()
        return self.get("status_refresh_seconds", 2)


# Global config instance
config = Config()
