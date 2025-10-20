from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.fallbacks import get_fallback_config

config = get_fallback_config()


class AgentContract(ABC):
    """
    Abstract base class defining the contract that all MSP agents must implement.
    """

    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = None, bridge_manager=None):
        """
        Initialize the agent with a scratchpad.
        :param scratchpad_path: Path to the agent's scratchpad file
        :param max_scratchpad_chars: Maximum number of characters in scratchpad (default from config)
        :param bridge_manager: Optional bridge manager for inter-agent communication
        """
        from scratchpad import Scratchpad
        if max_scratchpad_chars is None:
            max_scratchpad_chars = config.max_scratchpad_chars
        self.scratchpad = Scratchpad(scratchpad_path, max_chars=max_scratchpad_chars)
        self.scratchpad_path = scratchpad_path
        self.max_scratchpad_chars = max_scratchpad_chars
        self.bridge_manager = bridge_manager
    
    @abstractmethod
    def execute(self, task: Dict[str, Any], allowed_tools: List[str], 
                clarification_endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the agent's task.
        :param task: Task description with context
        :param allowed_tools: List of tools the agent is permitted to use
        :param clarification_endpoint: Optional HTTP endpoint for clarification requests
        :return: Result dictionary with status, result, and produced files
        """
        pass
    
    def request_clarification(self, question: str, endpoint: str) -> Optional[str]:
        """
        Send a clarification request to the orchestrator.
        :param question: The question needing clarification
        :param endpoint: The clarification endpoint URL
        :return: Clarification response or None if failed
        """
        import requests
        try:
            response = requests.post(endpoint, json={
                "need_clarification": True,
                "question": question
            })
            if response.status_code == 200:
                result = response.json()
                return result.get("clarification_response")
        except Exception as e:
            self.scratchpad.append(f"Error requesting clarification: {e}\n")
        
        return None
    
    def validate_tools(self, requested_tool: str, allowed_tools: List[str]) -> bool:
        """
        Validate if the agent is allowed to use a specific tool.
        :param requested_tool: The tool being requested
        :param allowed_tools: List of allowed tools
        :return: True if tool is allowed, False otherwise
        """
        return requested_tool in allowed_tools

    def log(self, message: str):
        """
        Log message to scratchpad with timestamp.

        Convenience method to reduce boilerplate in agent implementations.
        Automatically prepends timestamp in [HH:MM:SS] format.

        :param message: Message to log
        """
        from src.fallbacks import get_timestamp
        self.scratchpad.append(f"[{get_timestamp()}] {message}\n")