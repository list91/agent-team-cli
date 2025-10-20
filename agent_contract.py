from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class AgentContract(ABC):
    """
    Abstract base class defining the contract that all MSP agents must implement.
    """
    
    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = 8192, bridge_manager=None):
        """
        Initialize the agent with a scratchpad.
        :param scratchpad_path: Path to the agent's scratchpad file
        :param max_scratchpad_chars: Maximum number of characters in scratchpad
        :param bridge_manager: Optional bridge manager for inter-agent communication
        """
        from scratchpad import Scratchpad
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