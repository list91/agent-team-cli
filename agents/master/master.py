#!/usr/bin/env python3
"""
Master Orchestrator - MSP Orchestrator main component
"""
import argparse
import json
import subprocess
import sys
import time
import threading
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional
import signal
import random
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scratchpad import Scratchpad
from bridge import BridgeManager


class ClarificationHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP handler for clarification requests from sub-agents
    """
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        clarification_request = json.loads(post_data)
        
        # Store the clarification request to be handled by the main thread
        self.server.clarification_requests.append(clarification_request)
        
        # Respond with a simple OK
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "received"}
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def log_message(self, format, *args):
        # Suppress HTTP server log messages
        pass


class MasterOrchestrator:
    """
    The main orchestrator that manages sub-agents and handles clarifications
    """
    
    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.clarification_requests = []
        self.httpd = None
        self.http_thread = None
        self.running_agents = []
        self.status_monitor_thread = None
        self.monitoring = False
        self.agent_scratchpads = {}
        self.bridge_manager = BridgeManager(workdir / "shared")
    
    def start_clarification_server(self) -> int:
        """
        Start an HTTP server for receiving clarification requests from sub-agents
        :return: Port number the server is running on
        """
        # Find a free port
        port = random.randint(8000, 9000)
        while True:
            try:
                self.httpd = socketserver.TCPServer(("", port), ClarificationHandler)
                self.httpd.clarification_requests = self.clarification_requests
                break
            except OSError:
                # Port in use, try another
                port = random.randint(8000, 9000)
        
        # Start server in a thread
        self.http_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.http_thread.start()
        
        return port
    
    def stop_clarification_server(self):
        """
        Stop the HTTP clarification server
        """
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
    
    def start_status_monitoring(self):
        """
        Start the live status monitoring thread
        """
        self.monitoring = True
        self.status_monitor_thread = threading.Thread(target=self._monitor_status_loop, daemon=True)
        self.status_monitor_thread.start()
    
    def stop_status_monitoring(self):
        """
        Stop the live status monitoring
        """
        self.monitoring = False
        if self.status_monitor_thread:
            self.status_monitor_thread.join(timeout=1)
    
    def _monitor_status_loop(self):
        """
        Internal loop for monitoring agent status and outputting to console
        """
        while self.monitoring:
            self._update_status_display()
            time.sleep(1)  # Update every second
    
    def _update_status_display(self):
        """
        Update the console display with current status of all agents
        """
        # Clear the console (works on Windows and Unix-like systems)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("="*60)
        print("MSP ORCHESTRATOR - LIVE STATUS")
        print("="*60)
        
        # Show master status
        master_scratchpad_path = self.workdir / "master.scratchpad.md"
        if master_scratchpad_path.exists():
            with open(master_scratchpad_path, 'r', encoding='utf-8') as f:
                master_content = f.read()
                last_lines = master_content.split('\n')[-3:] if master_content else []
                print(f"[MASTER] Status: Active")
                for line in last_lines:
                    if line.strip():
                        print(f"         {line.strip()}")
        else:
            print("[MASTER] Status: Initializing...")
        
        # Show sub-agent status
        for agent_name, scratchpad_path in self.agent_scratchpads.items():
            status_symbol = "[~]"  # Running
            if scratchpad_path.exists():
                try:
                    with open(scratchpad_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        last_lines = content.split('\n')[-3:] if content else []
                        
                        print(f"[{agent_name.upper()}] {status_symbol}")
                        for line in last_lines:
                            if line.strip():
                                print(f"         {line.strip()}")
                except Exception:
                    print(f"[{agent_name.upper()}] [?] Error reading status")
            else:
                print(f"[{agent_name.upper()}] [ ] Waiting to start...")
        
        print("="*60)
        print("Live monitoring - refreshes every 1 second (Ctrl+C to interrupt)")
    
    def setup_agent_bridges(self, subtasks: List[Dict]):
        """
        Set up bridges between compatible agents
        :param subtasks: List of subtasks to be executed
        """
        # Find agents that accept bridges
        bridgeable_agents = []
        for subtask in subtasks:
            agent_name = subtask["agent"]
            agent_dir = project_root / "agents" / "available" / agent_name
            agent_config_path = agent_dir / "agent.yaml"
            
            if agent_config_path.exists():
                import yaml
                with open(agent_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                accepts_bridges = config.get("accepts_bridges", False)
            else:
                accepts_bridges = False
            
            if accepts_bridges:
                bridgeable_agents.append(agent_name)
        
        # Create bridges between all compatible agents
        for i, agent1 in enumerate(bridgeable_agents):
            for agent2 in bridgeable_agents[i+1:]:
                bridge_id = f"{agent1}_to_{agent2}"
                self.bridge_manager.create_bridge(bridge_id)
                print(f"[MASTER] Created bridge: {bridge_id}")
    
    def get_clarification_from_user(self, clarification_request: Dict) -> str:
        """
        Get clarification response from the user
        :param clarification_request: The clarification request from a sub-agent
        :return: User's response to the clarification
        """
        print(f"\n[MASTER] Sub-agent needs clarification: {clarification_request.get('question', 'No question provided')}")
        response = input("Your response: ")
        return response
    
    def process_clarifications(self):
        """
        Process any pending clarification requests
        """
        while self.clarification_requests:
            request = self.clarification_requests.pop(0)
            response = self.get_clarification_from_user(request)
            # In a real implementation, we would send this back to the requesting agent
            # For now, we'll just log it
            print(f"[MASTER] Sent response to sub-agent: {response}")
    
    def find_available_agents(self) -> List[Dict]:
        """
        Dynamically discover available agents in the agents/available directory
        :return: List of available agent configurations
        """
        agents_dir = project_root / "agents" / "available"
        available_agents = []
        
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                agent_config_path = agent_dir / "agent.yaml"
                if agent_config_path.exists():
                    # Read agent configuration
                    import yaml
                    with open(agent_config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    available_agents.append({
                        "name": agent_dir.name,
                        "path": agent_dir,
                        "config": config
                    })
                else:
                    # Use default configuration if agent.yaml doesn't exist
                    available_agents.append({
                        "name": agent_dir.name,
                        "path": agent_dir,
                        "config": {
                            "capabilities": ["basic"],
                            "accepts_bridges": False
                        }
                    })
        
        return available_agents
    
    def run_agent(self, agent_name: str, task: Dict, scratchpad_path: Path, 
                  allowed_tools: List[str] = None, 
                  clarification_endpoint: Optional[str] = None) -> Dict:
        """
        Run a specific agent with the given parameters
        :param agent_name: Name of the agent to run
        :param task: Task description for the agent
        :param scratchpad_path: Path to the agent's scratchpad
        :param allowed_tools: List of tools the agent is allowed to use
        :param clarification_endpoint: URL for clarification requests
        :return: Result from the agent
        """
        agent_dir = project_root / "agents" / "available" / agent_name
        
        if not agent_dir.exists():
            return {
                "status": "failed",
                "error": f"Agent {agent_name} not found"
            }
        
        agent_script = agent_dir / "agent.py"
        if not agent_script.exists():
            return {
                "status": "failed",
                "error": f"Agent script {agent_script} not found"
            }
        
        # Prepare command line arguments
        cmd = [
            sys.executable,
            str(agent_script),
            "--task", json.dumps(task),
            "--scratchpad-path", str(scratchpad_path),
            "--max-scratchpad-chars", "8192"
        ]
        
        if allowed_tools:
            cmd.extend(["--allowed-tools", ",".join(allowed_tools)])
        
        if clarification_endpoint:
            cmd.extend(["--clarification-endpoint", clarification_endpoint])
        
        # Run the agent as a subprocess
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5-minute timeout
            )
            
            if result.returncode != 0:
                return {
                    "status": "failed",
                    "error": f"Agent failed with return code {result.returncode}: {result.stderr}"
                }
            
            # Parse the agent's JSON output
            try:
                agent_result = json.loads(result.stdout.strip())
                return agent_result
            except json.JSONDecodeError:
                return {
                    "status": "failed",
                    "error": f"Agent returned invalid JSON: {result.stdout}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "error": "Agent timed out"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Error running agent: {str(e)}"
            }
    
    def decompose_task(self, task_description: str) -> List[Dict]:
        """
        Decompose the main task into subtasks for different agents
        :param task_description: Original task description
        :return: List of subtasks
        """
        # This is a simplified task decomposition
        # In a real implementation, this would be more sophisticated
        subtasks = []
        
        task_lower = task_description.lower()
        
        # Check if this is a development task
        if any(keyword in task_lower for keyword in ["fastapi", "api", "create", "build", "implement", "code", "application", "app", "service", "server", "endpoint", "crud"]):
            subtasks.append({
                "agent": "coder",
                "description": f"Implement the code for: {task_description}",
                "context": {"type": "code_generation"}
            })
        
        # Check if this is a documentation task
        if any(keyword in task_lower for keyword in ["documentation", "readme", "doc", "explain", "write", "describe", "specify", "manual", "guide"]):
            # Add documenter agent if not already in subtasks or if task specifically mentions documentation
            if any(keyword in task_lower for keyword in ["documentation", "readme", "specify", "openapi", "api", "guide"]):
                subtasks.append({
                    "agent": "documenter",
                    "description": f"Create documentation for: {task_description}",
                    "context": {"type": "documentation"}
                })
        
        # Default fallback if no specific agents identified
        if not subtasks:
            subtasks.append({
                "agent": "echo",
                "description": task_description,
                "context": {"type": "simple_response"}
            })
        
        return subtasks
    
    def run(self, task_data: Dict) -> Dict:
        """
        Run the master orchestrator with the given task
        :param task_data: Task data containing description and context
        :return: Final result
        """
        task_description = task_data["description"]
        workdir = Path(task_data["context"]["workdir"])
        
        # Initialize scratchpad for master
        master_scratchpad_path = workdir / "master.scratchpad.md"
        master_scratchpad = Scratchpad(master_scratchpad_path)
        master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Master orchestrator started\n")
        master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Task: {task_description}\n")
        
        # Start clarification server
        port = self.start_clarification_server()
        clarification_endpoint = f"http://localhost:{port}"
        master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Clarification server started on port {port}\n")
        
        # Find available agents
        available_agents = self.find_available_agents()
        master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Found {len(available_agents)} available agents: {[a['name'] for a in available_agents]}\n")
        
        # Start status monitoring
        self.start_status_monitoring()
        
        # Decompose task
        subtasks = self.decompose_task(task_description)
        master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Decomposed task into {len(subtasks)} subtasks: {[s['agent'] for s in subtasks]}\n")
        
        # Create bridges between compatible agents
        self.setup_agent_bridges(subtasks)
        
        # Prepare agent scratchpads for monitoring
        for i, subtask in enumerate(subtasks):
            agent_name = subtask["agent"]
            agent_scratchpad_path = workdir / f"{agent_name}_{i}.scratchpad.md"
            self.agent_scratchpads[agent_name] = agent_scratchpad_path
        
        # Run subtasks
        results = []
        for i, subtask in enumerate(subtasks):
            agent_name = subtask["agent"]
            agent_task = {
                "description": subtask["description"],
                "context": subtask["context"]
            }
            
            # Create scratchpad for this agent
            agent_scratchpad_path = workdir / f"{agent_name}_{i}.scratchpad.md"
            
            master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Running sub-agent: {agent_name}\n")
            
            # Check for clarifications before running agent
            self.process_clarifications()
            
            # Run the agent (this subprocess call will need to be updated to pass bridge info)
            result = self.run_agent(
                agent_name=agent_name,
                task=agent_task,
                scratchpad_path=agent_scratchpad_path,
                allowed_tools=["file_read", "file_write", "shell"],  # Default allowed tools
                clarification_endpoint=clarification_endpoint
            )
            
            results.append(result)
            
            if result["status"] == "needs_clarification":
                # Process clarifications that came in during agent execution
                self.process_clarifications()
                # Re-run the agent with clarification response if provided
                if "clarification_response" in result:
                    result = self.run_agent(
                        agent_name=agent_name,
                        task=agent_task,
                        scratchpad_path=agent_scratchpad_path,
                        allowed_tools=["file_read", "file_write", "shell"],
                        clarification_endpoint=clarification_endpoint
                    )
            
            master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Sub-agent {agent_name} completed with status: {result['status']}\n")
        
        # Process any remaining clarifications
        self.process_clarifications()
        
        # Stop status monitoring
        self.stop_status_monitoring()
        
        # Aggregate results
        all_produced_files = []
        for result in results:
            if "produced_files" in result:
                all_produced_files.extend(result["produced_files"])
        
        # Stop clarification server
        self.stop_clarification_server()
        master_scratchpad.append(f"[{time.strftime('%H:%M:%S')}] Clarification server stopped\n")
        
        # Final display
        os.system('cls' if os.name == 'nt' else 'clear')
        print("="*60)
        print("MSP ORCHESTRATOR - TASK COMPLETED")
        print("="*60)
        print(f"Task: {task_description}")
        print(f"Subtasks completed: {len(subtasks)}")
        print(f"Successful results: {len([r for r in results if r['status'] == 'success'])}")
        print(f"Files produced: {len(all_produced_files)}")
        if all_produced_files:
            print("Files:")
            for f in all_produced_files:
                print(f"  - {f}")
        print("="*60)
        
        return {
            "status": "success",
            "result": {
                "subtask_results": results,
                "summary": f"Processed {len(subtasks)} subtasks with {len([r for r in results if r['status'] == 'success'])} successful completions"
            },
            "produced_files": all_produced_files
        }


def run_master(task_data: Dict, workdir: Path):
    """
    Public function to run the master orchestrator
    :param task_data: Task data containing description and context
    :param workdir: Working directory
    :return: Result from the orchestrator
    """
    orchestrator = MasterOrchestrator(workdir)
    return orchestrator.run(task_data)


def main():
    parser = argparse.ArgumentParser(description="MSP Master Orchestrator")
    parser.add_argument("--task", required=True, help="Task JSON string")
    parser.add_argument("--workdir", default=".", help="Working directory")
    
    args = parser.parse_args()
    
    task_data = json.loads(args.task)
    workdir = Path(args.workdir).resolve()
    
    result = run_master(task_data, workdir)
    
    # Output result as JSON to stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()