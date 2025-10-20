#!/usr/bin/env python3
"""
Coder Agent - MSP Agent for code generation
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


class CoderAgent(AgentContract):
    """
    Agent responsible for code generation
    """
    
    def __init__(self, scratchpad_path: Path, max_scratchpad_chars: int = 8192, bridge_manager=None):
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
        self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Coder Agent started\n")
        self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Task: {task_description}\n")
        
        # Check for input from other agents via bridges
        if self.bridge_manager:
            # Look for specification from documenter agent
            doc_to_code_bridge = self.bridge_manager.get_bridge("documenter_to_coder")
            if doc_to_code_bridge:
                spec_msg = doc_to_code_bridge.get_latest_message("api_specification")
                if spec_msg:
                    self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Received API specification from documenter\n")
                    api_spec = spec_msg.get("data", {})
                    # Use the specification to guide code generation
        
        # Simulate analysis of the task
        self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Analyzing task requirements...\n")
        time.sleep(1)
        
        # Check if we need clarification
        if "port" not in task_description.lower() and "8000" not in task_description.lower():
            if clarification_endpoint:
                question = "Which port should the API server use?"
                self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Requesting clarification: {question}\n")
                
                # For this example, we'll just simulate the response
                # In a real implementation, we would call self.request_clarification()
                clarification_response = "8000"
                self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Received clarification: {clarification_response}\n")
            else:
                # If no clarification endpoint, use default
                clarification_response = "8000"
        
        # Generate code based on task
        self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Generating code...\n")
        time.sleep(2)
        
        # Determine what type of code to generate based on task
        produced_files = []
        
        if "fastapi" in task_description.lower():
            # Generate FastAPI app
            main_py_content = '''from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="Task Management API", version="1.0.0")

# Data model
class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    completed: bool = False

# In-memory storage (for demo purposes)
tasks_db = []
next_id = 1

@app.get("/")
def read_root():
    return {"message": "Task Management API"}

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks_db

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    for task in tasks_db:
        if task.id == task_id:
            return task
    return {"error": "Task not found"}

@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    global next_id
    task.id = next_id
    next_id += 1
    tasks_db.append(task)
    return task

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: Task):
    for i, task in enumerate(tasks_db):
        if task.id == task_id:
            updated_task = task_update.copy(update={"id": task_id})
            tasks_db[i] = updated_task
            return updated_task
    return {"error": "Task not found"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    global tasks_db
    tasks_db = [task for task in tasks_db if task.id != task_id]
    return {"message": "Task deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
            
            # Write the generated code to file
            main_py_path = Path(self.scratchpad_path.parent) / "main.py"
            with open(main_py_path, 'w') as f:
                f.write(main_py_content)
            
            produced_files.append(str(main_py_path))
            
            self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Generated main.py\n")
        
        if "docker" in task_description.lower() or "container" in task_description.lower():
            # Generate Dockerfile
            dockerfile_content = '''FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
            
            # Write the Dockerfile
            dockerfile_path = Path(self.scratchpad_path.parent) / "Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            produced_files.append(str(dockerfile_path))
            
            self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Generated Dockerfile\n")
        
        # Send information to other agents via bridges
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
                self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Sent API specification to documenter via bridge\n")
        
        # Complete the task
        self.scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Code generation completed\n")
        
        return {
            "status": "success",
            "result": {
                "message": "Code generated successfully",
                "files_created": produced_files
            },
            "produced_files": produced_files
        }


def main():
    parser = argparse.ArgumentParser(description="Coder Agent - MSP Code Generation Agent")
    parser.add_argument("--task", required=True, help="Task JSON string")
    parser.add_argument("--scratchpad-path", required=True, help="Path to scratchpad file")
    parser.add_argument("--max-scratchpad-chars", type=int, default=8192, help="Max scratchpad characters")
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