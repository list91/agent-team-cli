#!/usr/bin/env python3
"""
Coder Agent - MSP agent for code generation using LLM.

Generates production-ready code via LLM based on task descriptions.
No templates or hardcoded keywords.
"""
# Standard library imports
import argparse
import json
import sys
from pathlib import Path
from typing import List

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from agent_contract import AgentContract
from bridge import BridgeManager
from src.fallbacks import get_fallback_config, get_timestamp
from src.llm_client import create_llm_client_from_config
import re

config = get_fallback_config()

# Load system prompt for coder agent
def load_coder_prompt() -> str:
    """Load coder agent system prompt"""
    prompt_path = current_dir.parent.parent.parent / "prompts" / "coder_agent.txt"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, FileNotFoundError):
        return "You are a senior software engineer. Generate production-ready code based on requirements."


class CoderAgent(AgentContract):
    """
    Agent responsible for code generation using LLM
    """

    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = None, bridge_manager=None):
        super().__init__(scratchpad_path, max_scratchpad_chars, bridge_manager)
        self.llm_client = create_llm_client_from_config(config)
        self.system_prompt = load_coder_prompt()
    
    def execute(self, task: dict, allowed_tools: list, clarification_endpoint: str = None) -> dict:
        """
        Execute the coding task using LLM code generation
        :param task: Task description with context
        :param allowed_tools: List of allowed tools
        :param clarification_endpoint: Clarification endpoint URL
        :return: Result dictionary
        """
        task_description = task.get("description", "")
        feedback = task.get("feedback_from_tester", None)

        # Write initial status to scratchpad
        self.scratchpad.append(f"[{get_timestamp()}] Coder Agent started (LLM-driven)\n")
        self.scratchpad.append(f"[{get_timestamp()}] Task: {task_description}\n")

        if feedback:
            self.scratchpad.append(f"[{get_timestamp()}] Feedback from tester: {feedback}\n")

        # Check for input from other agents via bridges
        bridge_context = ""
        if self.bridge_manager:
            doc_to_code_bridge = self.bridge_manager.get_bridge("documenter_to_coder")
            if doc_to_code_bridge:
                spec_msg = doc_to_code_bridge.get_latest_message("api_specification")
                if spec_msg:
                    self.scratchpad.append(f"[{get_timestamp()}] Received specification from documenter\n")
                    bridge_context = f"\nSpecification from documenter:\n{spec_msg.get('data', {})}"

        # Analyze task requirements
        self.scratchpad.append(f"[{get_timestamp()}] Analyzing requirements via LLM...\n")

        # Build LLM prompt
        user_prompt = f"""
Task: {task_description}
{bridge_context}
{"Feedback to address: " + feedback if feedback else ""}

Generate production-ready code for this task. Include:
1. All necessary files (main code, Dockerfile if containerization mentioned, etc.)
2. Complete working implementations, not placeholders
3. Proper error handling and validation
4. Clear comments and documentation

Output format: Markdown code blocks with filenames as comments.

Example:
```python
# main.py
<actual code here>
```

```dockerfile
# Dockerfile
<actual dockerfile here>
```
"""

        try:
            # Generate code via LLM
            self.scratchpad.append(f"[{get_timestamp()}] Generating code via LLM...\n")

            generated_content = self.llm_client.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000
            )

            # Parse code blocks from LLM response
            produced_files = self._parse_and_write_code_blocks(generated_content)

            # Send API info to documenter if API endpoints were generated
            if produced_files:
                self._send_api_spec_to_documenter(generated_content)

            self.scratchpad.append(f"[{get_timestamp()}] Code generation completed\n")
            self.scratchpad.append(f"[{get_timestamp()}] Generated {len(produced_files)} files\n")

            return {
                "status": "success",
                "result": {
                    "message": "Code generated successfully via LLM",
                    "files_created": produced_files
                },
                "produced_files": produced_files
            }

        except Exception as e:
            error_msg = f"LLM code generation failed: {str(e)}"
            self.scratchpad.append(f"[{get_timestamp()}] ERROR: {error_msg}\n")
            return {
                "status": "failed",
                "error": error_msg
            }

    def _parse_and_write_code_blocks(self, llm_response: str) -> List[str]:
        """
        Parse code blocks from LLM response and write to files.

        :param llm_response: LLM generated text with code blocks
        :return: List of created file paths
        """
        produced_files = []

        # Split response into code blocks
        blocks = llm_response.split('```')

        # Process blocks in pairs (odd indices are code, even are text)
        for i in range(1, len(blocks), 2):
            if i >= len(blocks):
                break

            block = blocks[i]
            lines = block.split('\n')

            if len(lines) < 2:
                continue

            # First line might be language identifier
            first_line = lines[0].strip()
            if first_line in ['python', 'dockerfile', 'yaml', 'json', 'bash', '']:
                # Next line should be # filename
                if len(lines) > 1 and lines[1].strip().startswith('#'):
                    filename = lines[1].strip()[1:].strip()
                    content = '\n'.join(lines[2:])
                else:
                    continue
            elif first_line.startswith('#'):
                # First line is # filename
                filename = first_line[1:].strip()
                content = '\n'.join(lines[1:])
            else:
                continue

            # Write file
            file_path = Path(self.scratchpad_path.parent) / filename
            try:
                self._write_file_safely(file_path, content, filename)
                produced_files.append(str(file_path))
            except (IOError, PermissionError) as e:
                self.scratchpad.append(f"[{get_timestamp()}] Failed to write {filename}: {e}\n")

        return produced_files

    def _send_api_spec_to_documenter(self, generated_code: str = None):
        """
        Send API specification to documenter via bridge if available.
        """
        if not self.bridge_manager:
            return

        code_to_doc_bridge = self.bridge_manager.get_bridge("coder_to_documenter")
        if not code_to_doc_bridge:
            return

        # Extract API endpoints from generated code
        api_info = {
            "endpoints": [],
            "generated": True
        }

        if generated_code:
            # Simple regex to find FastAPI route decorators
            route_pattern = r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']\)'
            matches = re.findall(route_pattern, generated_code)
            for method, path in matches:
                api_info["endpoints"].append({
                    "method": method.upper(),
                    "path": path
                })

        code_to_doc_bridge.send_message("coder", "api_specification", api_info)
        self.scratchpad.append(f"[{get_timestamp()}] Sent API specification to documenter via bridge\n")

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


def main():
    parser = argparse.ArgumentParser(description="Coder Agent - MSP Code Generation Agent")
    parser.add_argument("--task", required=True, help="Task JSON string")
    parser.add_argument("--scratchpad-path", required=True, help="Path to scratchpad file")
    parser.add_argument("--max-scratchpad-chars", type=int, default=config.max_scratchpad_chars, help="Max scratchpad characters")
    parser.add_argument("--allowed-tools", default="", help="Comma-separated list of allowed tools")
    parser.add_argument("--clarification-endpoint", help="HTTP endpoint for clarification requests")
    parser.add_argument("--bridge-dir", help="Path to shared bridge directory for inter-agent communication")

    args = parser.parse_args()

    # Parse task
    task = json.loads(args.task)
    allowed_tools = args.allowed_tools.split(",") if args.allowed_tools else []

    # Create bridge manager if bridge directory provided
    bridge_manager = None
    if args.bridge_dir:
        bridge_manager = BridgeManager(Path(args.bridge_dir))

    # Create and run the coder agent
    agent = CoderAgent(Path(args.scratchpad_path), max_scratchpad_chars=args.max_scratchpad_chars, bridge_manager=bridge_manager)

    try:
        result = agent.execute(task, allowed_tools, args.clarification_endpoint)
    except Exception as e:
        # Catch any unhandled exceptions and return as failed result
        result = {
            "status": "failed",
            "error": f"Agent execution error: {type(e).__name__}: {str(e)}"
        }
        # Log error to scratchpad if possible
        try:
            agent.scratchpad.append(f"[{get_timestamp()}] FATAL ERROR: {type(e).__name__}: {str(e)}\n")
        except:
            pass

    # Output result as JSON to stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()