#!/usr/bin/env python3
"""
Documenter Agent - MSP Agent for documentation generation using LLM.

Generates comprehensive documentation via LLM based on task and code context.
No templates or hardcoded formats.
"""
import argparse
import json
import sys
import re
from pathlib import Path
from typing import List

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent  # Go up 3 levels to project root
sys.path.insert(0, str(project_root))

from agent_contract import AgentContract
from bridge import BridgeManager
from src.fallbacks import get_fallback_config, get_timestamp
from src.llm_client import create_llm_client_from_config

config = get_fallback_config()

# Load system prompt for documenter agent
def load_documenter_prompt() -> str:
    """Load documenter agent system prompt"""
    prompt_path = current_dir.parent.parent.parent / "prompts" / "documenter_agent.txt"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, FileNotFoundError):
        return "You are a technical documentation specialist. Create clear, comprehensive documentation."


class DocumenterAgent(AgentContract):
    """
    Agent responsible for documentation generation using LLM
    """

    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = None, bridge_manager=None):
        super().__init__(scratchpad_path, max_scratchpad_chars, bridge_manager)
        self.llm_client = create_llm_client_from_config(config)
        self.system_prompt = load_documenter_prompt()
    
    def execute(self, task: dict, allowed_tools: list, clarification_endpoint: str = None) -> dict:
        """
        Execute the documentation task using LLM
        :param task: Task description with context
        :param allowed_tools: List of allowed tools
        :param clarification_endpoint: Clarification endpoint URL
        :return: Result dictionary
        """
        task_description = task.get("description", "")

        # Write initial status to scratchpad
        self.scratchpad.append(f"[{get_timestamp()}] Documenter Agent started (LLM-driven)\n")
        self.scratchpad.append(f"[{get_timestamp()}] Task: {task_description}\n")

        # Check for input from other agents via bridges
        bridge_context = ""
        if self.bridge_manager:
            code_to_doc_bridge = self.bridge_manager.get_bridge("coder_to_documenter")
            if code_to_doc_bridge:
                api_info_msg = code_to_doc_bridge.get_latest_message("api_specification")
                if api_info_msg:
                    self.scratchpad.append(f"[{get_timestamp()}] Received API information from coder\n")
                    api_info = api_info_msg.get("data", {})
                    bridge_context = f"\nAPI Information from coder:\n{json.dumps(api_info, indent=2)}"

        # Analyze task requirements
        self.scratchpad.append(f"[{get_timestamp()}] Analyzing documentation requirements via LLM...\n")

        # Build LLM prompt
        user_prompt = f"""
Task: {task_description}
{bridge_context}

Generate comprehensive documentation for this project. Include:
1. README.md with project overview, setup instructions, and usage examples
2. OpenAPI specification if this is an API project (in YAML format)
3. Any other relevant documentation files

Output format: Markdown code blocks with filenames as comments.

Example:
```markdown
# README.md
<actual content here>
```

```yaml
# openapi.yaml
<actual OpenAPI spec here>
```
"""

        try:
            # Generate documentation via LLM
            self.scratchpad.append(f"[{get_timestamp()}] Generating documentation via LLM...\n")

            generated_content = self.llm_client.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000
            )

            # Parse documentation blocks from LLM response
            produced_files = self._parse_and_write_doc_blocks(generated_content)

            # Send documentation info to other agents via bridges
            if self.bridge_manager and produced_files:
                self._send_doc_spec_to_coder()

            self.scratchpad.append(f"[{get_timestamp()}] Documentation generation completed\n")
            self.scratchpad.append(f"[{get_timestamp()}] Generated {len(produced_files)} documentation files\n")

            return {
                "status": "success",
                "result": {
                    "message": "Documentation generated successfully via LLM",
                    "files_created": produced_files
                },
                "produced_files": produced_files
            }

        except Exception as e:
            error_msg = f"LLM documentation generation failed: {str(e)}"
            self.scratchpad.append(f"[{get_timestamp()}] ERROR: {error_msg}\n")
            return {
                "status": "failed",
                "error": error_msg
            }

    def _parse_and_write_doc_blocks(self, llm_response: str) -> List[str]:
        """
        Parse documentation blocks from LLM response and write to files.

        :param llm_response: LLM generated text with doc blocks
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
            if first_line in ['markdown', 'yaml', 'json', 'python', 'dockerfile', '']:
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
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                produced_files.append(str(file_path))
                self.scratchpad.append(f"[{get_timestamp()}] Generated {filename}\n")
            except (IOError, PermissionError, OSError) as e:
                self.scratchpad.append(f"[{get_timestamp()}] Failed to write {filename}: {e}\n")

        return produced_files

    def _send_doc_spec_to_coder(self):
        """
        Send documentation specifications to coder via bridge.
        """
        doc_to_code_bridge = self.bridge_manager.get_bridge("documenter_to_coder")
        if doc_to_code_bridge:
            doc_spec = {
                "required_docs": ["README.md", "API documentation", "installation guide"],
                "standards": ["Markdown", "OpenAPI 3.0"],
                "generated": True
            }
            doc_to_code_bridge.send_message("documenter", "api_specification", doc_spec)
            self.scratchpad.append(f"[{get_timestamp()}] Sent documentation requirements to coder via bridge\n")


def main():
    parser = argparse.ArgumentParser(description="Documenter Agent - MSP Documentation Generation Agent")
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

    # Create and run the documenter agent
    agent = DocumenterAgent(Path(args.scratchpad_path), max_scratchpad_chars=args.max_scratchpad_chars, bridge_manager=bridge_manager)
    result = agent.execute(task, allowed_tools, args.clarification_endpoint)

    # Output result as JSON to stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()