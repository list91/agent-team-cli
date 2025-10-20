#!/usr/bin/env python3
"""
Coder Agent - MSP agent for code generation.

Generates code from templates based on task descriptions.
Supports FastAPI application generation and Docker containerization.
"""
# Standard library imports
import argparse
import json
import sys
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from agent_contract import AgentContract
from bridge import BridgeManager

try:
    from src.config_loader import config
except ImportError:
    # Fallback if config loader not available
    class FallbackConfig:
        @property
        def max_scratchpad_chars(self):
            return 8192
    config = FallbackConfig()

try:
    from src.template_loader import load_and_render_template
except ImportError:
    # Fallback if template loader not available
    def load_and_render_template(template_name, variables):
        raise ImportError("Template loader not available")

try:
    from src.utils import get_timestamp
except ImportError:
    # Fallback if utils not available
    import time
    def get_timestamp():
        return time.strftime('%H:%M:%S')


class CoderAgent(AgentContract):
    """
    Agent responsible for code generation
    """

    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = None, bridge_manager=None):
        super().__init__(scratchpad_path, max_scratchpad_chars, bridge_manager)
    
    def execute(self, task: dict, allowed_tools: list, clarification_endpoint: str = None) -> dict:
        """
        Execute the coding task
        :param task: Task description with context
        :param allowed_tools: List of allowed tools
        :param clarification_endpoint: Clarification endpoint URL
        :return: Result dictionary
        """
        task_description = task.get("description", "")
        
        # Write initial status to scratchpad
        self.scratchpad.append(f"[{get_timestamp()}] Coder Agent started\n")
        self.scratchpad.append(f"[{get_timestamp()}] Task: {task_description}\n")
        
        # Check for input from other agents via bridges
        if self.bridge_manager:
            # Look for specification from documenter agent
            doc_to_code_bridge = self.bridge_manager.get_bridge("documenter_to_coder")
            if doc_to_code_bridge:
                spec_msg = doc_to_code_bridge.get_latest_message("api_specification")
                if spec_msg:
                    self.scratchpad.append(f"[{get_timestamp()}] Received API specification from documenter\n")
                    api_spec = spec_msg.get("data", {})
                    # Use the specification to guide code generation
        
        # Simulate analysis of the task
        self.scratchpad.append(f"[{get_timestamp()}] Analyzing task requirements...\n")
        import time
        time.sleep(1)
        
        # Check if we need clarification
        if "port" not in task_description.lower() and "8000" not in task_description.lower():
            if clarification_endpoint:
                question = "Which port should the API server use?"
                self.scratchpad.append(f"[{get_timestamp()}] Requesting clarification: {question}\n")

                # For this example, we'll just simulate the response
                # In a real implementation, we would call self.request_clarification()
                clarification_response = "8000"
                self.scratchpad.append(f"[{get_timestamp()}] Received clarification: {clarification_response}\n")
            else:
                # If no clarification endpoint, use default
                clarification_response = "8000"
        
        # Generate code based on task
        self.scratchpad.append(f"[{get_timestamp()}] Generating code...\n")
        time.sleep(2)
        
        # Generate code based on task type
        produced_files = []

        if "fastapi" in task_description.lower():
            main_py_path = self._generate_fastapi_code()
            produced_files.append(str(main_py_path))

        if "docker" in task_description.lower() or "container" in task_description.lower():
            dockerfile_path = self._generate_dockerfile()
            produced_files.append(str(dockerfile_path))

        self._send_api_spec_to_documenter()

        self.scratchpad.append(f"[{get_timestamp()}] Code generation completed\n")

        return {
            "status": "success",
            "result": {
                "message": "Code generated successfully",
                "files_created": produced_files
            },
            "produced_files": produced_files
        }

    def _write_file_safely(self, file_path: Path, content: str, file_description: str) -> bool:
        """
        Write a file with proper error handling and logging.

        :param file_path: Path to the file to write
        :param content: Content to write
        :param file_description: Description for logging (e.g., 'main.py', 'Dockerfile')
        :return: True if successful
        :raises PermissionError: If write fails due to permissions
        :raises IOError: If write fails due to I/O error
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.scratchpad.append(f"[{get_timestamp()}] Generated {file_description}\n")
            return True
        except PermissionError as e:
            error_msg = f"Failed to write {file_description}: {str(e)}"
            self.scratchpad.append(f"[{get_timestamp()}] ERROR: {error_msg}\n")
            raise PermissionError(error_msg)
        except (IOError, OSError) as e:
            error_msg = f"Failed to write {file_description}: {str(e)}"
            self.scratchpad.append(f"[{get_timestamp()}] ERROR: {error_msg}\n")
            raise IOError(error_msg)

    def _generate_fastapi_code(self) -> Path:
        """
        Generate FastAPI application code.

        :return: Path to generated main.py file
        """
        template_vars = {
            "app_title": "Task Management API",
            "app_version": "1.0.0",
            "port": "8000"
        }
        main_py_content = load_and_render_template("fastapi_main.py.template", template_vars)

        main_py_path = Path(self.scratchpad_path.parent) / "main.py"
        self._write_file_safely(main_py_path, main_py_content, "main.py")
        return main_py_path

    def _generate_dockerfile(self) -> Path:
        """
        Generate Dockerfile for containerization.

        :return: Path to generated Dockerfile
        """
        template_vars = {"port": "8000"}
        dockerfile_content = load_and_render_template("Dockerfile.template", template_vars)

        dockerfile_path = Path(self.scratchpad_path.parent) / "Dockerfile"
        self._write_file_safely(dockerfile_path, dockerfile_content, "Dockerfile")
        return dockerfile_path

    def _send_api_spec_to_documenter(self):
        """
        Send API specification to documenter via bridge if available.
        """
        if self.bridge_manager:
            code_to_doc_bridge = self.bridge_manager.get_bridge("coder_to_documenter")
            if code_to_doc_bridge:
                # Send API specification or other relevant information to documenter
                api_info = {
                    "endpoints": [
                        {"path": "/", "method": "GET", "description": "Root endpoint"},
                        {"path": "/tasks", "method": "GET", "description": "Get all tasks"},
                        {"path": "/tasks/{task_id}", "method": "GET", "description": "Get specific task"},
                        {"path": "/tasks", "method": "POST", "description": "Create new task"},
                        {"path": "/tasks/{task_id}", "method": "PUT", "description": "Update task"},
                        {"path": "/tasks/{task_id}", "method": "DELETE", "description": "Delete task"}
                    ]
                }
                code_to_doc_bridge.send_message("coder", "api_specification", api_info)
                self.scratchpad.append(f"[{get_timestamp()}] Sent API specification to documenter via bridge\n")


def main():
    parser = argparse.ArgumentParser(description="Coder Agent - MSP Code Generation Agent")
    parser.add_argument("--task", required=True, help="Task JSON string")
    parser.add_argument("--scratchpad-path", required=True, help="Path to scratchpad file")
    parser.add_argument("--max-scratchpad-chars", type=int, default=config.max_scratchpad_chars, help="Max scratchpad characters")
    parser.add_argument("--allowed-tools", default="", help="Comma-separated list of allowed tools")
    parser.add_argument("--clarification-endpoint", help="HTTP endpoint for clarification requests")
    
    args = parser.parse_args()
    
    # Parse task
    task = json.loads(args.task)
    allowed_tools = args.allowed_tools.split(",") if args.allowed_tools else []
    
    # For now, we don't have access to the bridge manager here
    # In a real implementation, the bridge manager would be passed from the master
    # For this example, we'll create a dummy one
    bridge_manager = None
    
    # Create and run the coder agent
    agent = CoderAgent(Path(args.scratchpad_path), max_scratchpad_chars=args.max_scratchpad_chars, bridge_manager=bridge_manager)
    result = agent.execute(task, allowed_tools, args.clarification_endpoint)
    
    # Output result as JSON to stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()