#!/usr/bin/env python3
"""
Documenter Agent - MSP Agent for documentation generation
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent  # Go up 3 levels to project root
sys.path.insert(0, str(project_root))

from agent_contract import AgentContract
from bridge import BridgeManager
from src.fallbacks import get_fallback_config, get_timestamp

config = get_fallback_config()

try:
    from src.template_loader import load_and_render_template
except ImportError:
    # Fallback if template loader not available
    def load_and_render_template(template_name, variables):
        raise ImportError("Template loader not available")


class DocumenterAgent(AgentContract):
    """
    Agent responsible for documentation generation
    """

    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = None, bridge_manager=None):
        super().__init__(scratchpad_path, max_scratchpad_chars, bridge_manager)
    
    def execute(self, task: dict, allowed_tools: list, clarification_endpoint: str = None) -> dict:
        """
        Execute the documentation task
        :param task: Task description with context
        :param allowed_tools: List of allowed tools
        :param clarification_endpoint: Clarification endpoint URL
        :return: Result dictionary
        """
        task_description = task.get("description", "")
        
        # Write initial status to scratchpad
        self.scratchpad.append(f"[{get_timestamp()}] Documenter Agent started\n")
        self.scratchpad.append(f"[{get_timestamp()}] Task: {task_description}\n")
        
        # Check for input from other agents via bridges
        if self.bridge_manager:
            # Look for API information from coder agent
            code_to_doc_bridge = self.bridge_manager.get_bridge("coder_to_documenter")
            if code_to_doc_bridge:
                api_info_msg = code_to_doc_bridge.get_latest_message("api_specification")
                if api_info_msg:
                    self.scratchpad.append(f"[{get_timestamp()}] Received API information from coder\n")
                    api_info = api_info_msg.get("data", {})
                    # Use the API information to improve documentation generation
        
        # Simulate analysis of the task
        self.scratchpad.append(f"[{get_timestamp()}] Analyzing documentation requirements...\n")
        time.sleep(1)
        
        # Generate documentation based on task
        self.scratchpad.append(f"[{get_timestamp()}] Generating documentation...\n")
        time.sleep(2)
        
        # Determine what type of documentation to generate based on task
        produced_files = []
        
        if "fastapi" in task_description.lower() or "api" in task_description.lower():
            # Generate README.md using template
            template_vars = {
                "app_title": config.default_app_title,
                "port": str(config.default_agent_port)
            }
            readme_content = load_and_render_template("README.md.template", template_vars)
            
            # Write the README
            readme_path = Path(self.scratchpad_path.parent) / "README.md"
            try:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                produced_files.append(str(readme_path))
                self.scratchpad.append(f"[{get_timestamp()}] Generated README.md\n")
            except (IOError, PermissionError, OSError) as e:
                error_msg = f"Failed to write README.md: {str(e)}"
                self.scratchpad.append(f"[{get_timestamp()}] ERROR: {error_msg}\n")
                raise IOError(error_msg)
        
        if "openapi" in task_description.lower() or "documentation" in task_description.lower():
            # Generate OpenAPI specification
            openapi_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": config.default_app_title,
                    "version": config.default_app_version,
                    "description": "A simple API for managing tasks"
                },
                "paths": {
                    "/": {
                        "get": {
                            "summary": "Root endpoint",
                            "responses": {
                                "200": {
                                    "description": "Welcome message"
                                }
                            }
                        }
                    },
                    "/tasks": {
                        "get": {
                            "summary": "Get all tasks",
                            "responses": {
                                "200": {
                                    "description": "List of tasks",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "array",
                                                "items": {
                                                    "$ref": "#/components/schemas/Task"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "post": {
                            "summary": "Create a new task",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Task"
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Task created",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/Task"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/tasks/{task_id}": {
                        "get": {
                            "summary": "Get a specific task",
                            "parameters": [
                                {
                                    "name": "task_id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {
                                        "type": "integer"
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "A single task",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/Task"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "put": {
                            "summary": "Update a specific task",
                            "parameters": [
                                {
                                    "name": "task_id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {
                                        "type": "integer"
                                    }
                                }
                            ],
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Task"
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Task updated",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/Task"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "delete": {
                            "summary": "Delete a specific task",
                            "parameters": [
                                {
                                    "name": "task_id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {
                                        "type": "integer"
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Task deleted"
                                }
                            }
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "Task": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "description": "Unique identifier for the task"
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Task title"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Task description"
                                },
                                "completed": {
                                    "type": "boolean",
                                    "description": "Whether the task is completed"
                                }
                            },
                            "required": ["title", "description"]
                        }
                    }
                }
            }
            
            # Write the OpenAPI spec
            openapi_path = Path(self.scratchpad_path.parent) / "openapi.yaml"
            try:
                import yaml
                with open(openapi_path, 'w', encoding='utf-8') as f:
                    yaml.dump(openapi_spec, f, default_flow_style=False)
                produced_files.append(str(openapi_path))
                self.scratchpad.append(f"[{get_timestamp()}] Generated openapi.yaml\n")
            except (IOError, PermissionError, OSError) as e:
                error_msg = f"Failed to write openapi.yaml: {str(e)}"
                self.scratchpad.append(f"[{get_timestamp()}] ERROR: {error_msg}\n")
                raise IOError(error_msg)
            except ImportError as e:
                error_msg = f"Failed to import yaml module: {str(e)}"
                self.scratchpad.append(f"[{get_timestamp()}] ERROR: {error_msg}\n")
                raise ImportError(error_msg)
        
        # Send documentation information to other agents via bridges
        if self.bridge_manager:
            doc_to_code_bridge = self.bridge_manager.get_bridge("documenter_to_coder")
            if doc_to_code_bridge:
                # Send documentation specification to coder
                doc_spec = {
                    "required_docs": ["README.md", "API documentation", "installation guide"],
                    "standards": ["Markdown", "OpenAPI 3.0"]
                }
                doc_to_code_bridge.send_message("documenter", "api_specification", doc_spec)
                self.scratchpad.append(f"[{get_timestamp()}] Sent documentation requirements to coder via bridge\n")
        
        # Complete the task
        self.scratchpad.append(f"[{get_timestamp()}] Documentation generation completed\n")
        
        return {
            "status": "success",
            "result": {
                "message": "Documentation generated successfully",
                "files_created": produced_files
            },
            "produced_files": produced_files
        }


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