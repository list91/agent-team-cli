#!/usr/bin/env python3
"""
Master Orchestrator - MSP Orchestrator main component.

Coordinates multiple sub-agents to complete complex tasks through task decomposition,
agent execution, result validation, and feedback loops.
"""
# Standard library imports
import argparse
import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from scratchpad import Scratchpad
from bridge import BridgeManager

try:
    from src.config_loader import config
    from src.utils import get_timestamp
except ImportError:
    # Fallback if config loader not available
    class FallbackConfig:
        @property
        def max_scratchpad_chars(self):
            return 8192
        @property
        def allowed_tools(self):
            return ["file_read", "file_write", "shell"]
        @property
        def agent_timeout(self):
            return 300
        @property
        def port_range(self):
            return (8000, 9000)
    config = FallbackConfig()
    def get_timestamp():
        return time.strftime('%H:%M:%S')


# Task keyword mapping for agent selection
TASK_KEYWORDS = {
    'coder': {
        'keywords': ['fastapi', 'api', 'create', 'build', 'implement', 'code',
                     'application', 'app', 'service', 'server', 'endpoint', 'crud', 'docker'],
        'priority': 1,
        'context_type': 'code_generation'
    },
    'documenter': {
        'keywords': ['documentation', 'readme', 'doc', 'explain', 'write',
                     'describe', 'specify', 'manual', 'guide', 'openapi'],
        'priority': 2,
        'context_type': 'documentation'
    },
    'tester': {
        'keywords': ['test', 'validate', 'check', 'verify'],
        'priority': 3,
        'context_type': 'testing'
    }
}


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
        self.clarification_server = None
        self.clarification_thread = None
        self.running_agents = []
        self.status_monitor_thread = None
        self.monitoring = False
        self.agent_scratchpads = {}
        self.bridge_manager = BridgeManager(workdir / "shared")
    
    def start_clarification_server(self) -> int:
        """
        Start an HTTP server for receiving clarification requests from sub-agents.

        :return: Port number the server is running on
        :raises OSError: If no port is available after max attempts
        """
        port = self._find_available_port()

        self.clarification_server = socketserver.TCPServer(("", port), ClarificationHandler)
        self.clarification_server.clarification_requests = self.clarification_requests

        # Start server in a thread
        try:
            self.clarification_thread = threading.Thread(target=self.clarification_server.serve_forever, daemon=True)
            self.clarification_thread.start()
        except Exception as e:
            # Clean up if thread start fails
            if self.clarification_server:
                self.clarification_server.server_close()
            raise RuntimeError(f"Failed to start clarification server thread: {str(e)}")

        return port

    def _find_available_port(self, start_port: Optional[int] = None, max_attempts: int = 100) -> int:
        """
        Find an available port by trying sequentially.

        :param start_port: Starting port number (defaults to config.port_range[0])
        :param max_attempts: Maximum number of ports to try
        :return: Available port number
        :raises OSError: If no port is available in the range
        """
        import socket

        min_port, max_port = config.port_range
        start = start_port if start_port is not None else min_port

        for port in range(start, min(start + max_attempts, max_port + 1)):
            try:
                # Try to bind to port to verify it's available
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    test_socket.bind(('', port))
                    return port
            except OSError:
                # Port in use, try next
                continue

        raise OSError(f"No available ports in range {start}-{min(start + max_attempts, max_port)}")
    
    def stop_clarification_server(self):
        """
        Stop the HTTP clarification server.
        """
        if self.clarification_server:
            self.clarification_server.shutdown()
            self.clarification_server.server_close()
    
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
        Internal loop for monitoring agent status and outputting to console.
        """
        # Get refresh interval from config, default to 2 seconds
        refresh_interval = getattr(config, 'status_refresh_seconds', 2)

        while self.monitoring:
            self._update_status_display()
            time.sleep(refresh_interval)
    
    def _update_status_display(self):
        """
        Update the console display with current status of all agents.
        """
        # Only display if enabled in config
        if not getattr(config, 'enable_status_display', True):
            return

        # Clear the console (works on Windows and Unix-like systems)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("="*60)
        print("MSP ORCHESTRATOR - LIVE STATUS")
        print("="*60)
        
        # Show master status
        master_scratchpad_path = self.workdir / "master.scratchpad.md"
        if master_scratchpad_path.exists():
            try:
                with open(master_scratchpad_path, 'r', encoding='utf-8') as f:
                    master_content = f.read()
                    last_lines = master_content.split('\n')[-3:] if master_content else []
                    print(f"[MASTER] Status: Active")
                    for line in last_lines:
                        if line.strip():
                            print(f"         {line.strip()}")
            except (IOError, PermissionError, UnicodeDecodeError) as e:
                print(f"[MASTER] Status: Error reading scratchpad")
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
        
        refresh_interval = getattr(config, 'status_refresh_seconds', 2)
        print("="*60)
        print(f"Live monitoring - refreshes every {refresh_interval} second(s) (Ctrl+C to interrupt)")
    
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
                try:
                    import yaml
                    with open(agent_config_path, 'r', encoding='utf-8') as f:
                        agent_cfg = yaml.safe_load(f)
                    accepts_bridges = agent_cfg.get("accepts_bridges", False) if agent_cfg else False
                except (IOError, PermissionError, yaml.YAMLError, ImportError) as e:
                    # If we can't read config, assume no bridges
                    accepts_bridges = False
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

        try:
            agent_dirs = list(agents_dir.iterdir())
        except (IOError, PermissionError) as e:
            # If we can't read agents directory, return empty list
            import logging
            logging.warning(f"Could not read agents directory {agents_dir}: {e}")
            return available_agents

        for agent_dir in agent_dirs:
            try:
                if not agent_dir.is_dir():
                    continue

                agent_config_path = agent_dir / "agent.yaml"
                if agent_config_path.exists():
                    # Read agent configuration
                    try:
                        import yaml
                        with open(agent_config_path, 'r', encoding='utf-8') as f:
                            agent_cfg = yaml.safe_load(f)
                        available_agents.append({
                            "name": agent_dir.name,
                            "path": agent_dir,
                            "config": agent_cfg if agent_cfg else {"capabilities": ["basic"], "accepts_bridges": False}
                        })
                    except (IOError, PermissionError, yaml.YAMLError, ImportError) as e:
                        # If we can't read config, use defaults
                        import logging
                        logging.warning(f"Could not read config for agent {agent_dir.name}: {e}")
                        available_agents.append({
                            "name": agent_dir.name,
                            "path": agent_dir,
                            "config": {
                                "capabilities": ["basic"],
                                "accepts_bridges": False
                            }
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
            except Exception as e:
                # Skip agents we can't process
                import logging
                logging.warning(f"Error processing agent directory {agent_dir}: {e}")
                continue

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
        :raises TypeError: If task is None
        :raises KeyError: If task is missing required fields
        """
        # Validate inputs
        if task is None:
            raise TypeError("Task cannot be None")
        if not isinstance(task, dict):
            raise TypeError("Task must be a dictionary")

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
            "--max-scratchpad-chars", str(config.max_scratchpad_chars)
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
                timeout=config.agent_timeout
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
        Decompose the main task into subtasks for different agents using keyword mapping.

        :param task_description: Original task description
        :return: List of subtasks with agent assignments
        """
        subtasks = []
        task_lower = task_description.lower()
        matched_agents = []

        # Find all matching agents based on keywords
        for agent_name, agent_config in TASK_KEYWORDS.items():
            if any(keyword in task_lower for keyword in agent_config['keywords']):
                matched_agents.append((agent_name, agent_config))

        # Sort by priority and create subtasks
        matched_agents.sort(key=lambda x: x[1]['priority'])

        for agent_name, agent_config in matched_agents:
            action = self._get_agent_action_verb(agent_name)
            subtasks.append({
                "agent": agent_name,
                "description": f"{action} {task_description}",
                "context": {"type": agent_config['context_type']}
            })

        # Default fallback if no specific agents identified
        if not subtasks:
            subtasks.append({
                "agent": "echo",
                "description": task_description,
                "context": {"type": "simple_response"}
            })

        return subtasks

    def _get_agent_action_verb(self, agent_name: str) -> str:
        """
        Get appropriate action verb for agent type.

        :param agent_name: Name of the agent
        :return: Action verb for task description
        """
        action_verbs = {
            'coder': 'Implement the code for:',
            'documenter': 'Create documentation for:',
            'tester': 'Validate and test:',
            'echo': 'Process:'
        }
        return action_verbs.get(agent_name, 'Process:')
    
    def run(self, task_data: Dict) -> Dict:
        """
        Main orchestration workflow - coordinates agents to complete complex tasks.

        :param task_data: Task data containing description and context
        :return: Final result with status and produced files
        """
        try:
            task_description = task_data["description"]
            workdir = Path(task_data["context"]["workdir"])

            master_scratchpad = self._initialize_workspace(workdir, task_description)
            clarification_endpoint = self._start_services(master_scratchpad)
            subtasks = self._decompose_and_plan(task_description, master_scratchpad)
            results = self._execute_subtasks(subtasks, workdir, master_scratchpad, clarification_endpoint)
            validation = self._validate_results(task_description, results, workdir, master_scratchpad, clarification_endpoint)

            if not validation["passed"]:
                results = self._handle_failures(validation, subtasks, workdir, master_scratchpad, clarification_endpoint, results)

            return self._finalize_results(task_description, subtasks, results, workdir, master_scratchpad)
        finally:
            self._cleanup_resources()

    def _initialize_workspace(self, workdir: Path, task_description: str) -> Scratchpad:
        """
        Initialize workspace, scratchpads, and monitoring.

        :param workdir: Working directory for the orchestration
        :param task_description: Description of the task
        :return: Master scratchpad instance
        """
        master_scratchpad_path = workdir / "master.scratchpad.md"
        master_scratchpad = Scratchpad(master_scratchpad_path)
        master_scratchpad.append(f"[{get_timestamp()}] Master orchestrator started\n")
        master_scratchpad.append(f"[{get_timestamp()}] Task: {task_description}\n")
        return master_scratchpad

    def _start_services(self, master_scratchpad: Scratchpad) -> str:
        """
        Start clarification server and status monitoring.

        :param master_scratchpad: Master scratchpad for logging
        :return: Clarification endpoint URL
        """
        port = self.start_clarification_server()
        clarification_endpoint = f"http://localhost:{port}"
        master_scratchpad.append(f"[{get_timestamp()}] Clarification server started on port {port}\n")

        available_agents = self.find_available_agents()
        master_scratchpad.append(f"[{get_timestamp()}] Found {len(available_agents)} available agents: {[a['name'] for a in available_agents]}\n")

        self.start_status_monitoring()
        return clarification_endpoint

    def _decompose_and_plan(self, task_description: str, master_scratchpad: Scratchpad) -> List[Dict]:
        """
        Decompose task into subtasks and set up agent bridges.

        :param task_description: High-level task description
        :param master_scratchpad: Master scratchpad for logging
        :return: List of subtasks
        """
        subtasks = self.decompose_task(task_description)
        master_scratchpad.append(f"[{get_timestamp()}] Decomposed task into {len(subtasks)} subtasks: {[s['agent'] for s in subtasks]}\n")

        self.setup_agent_bridges(subtasks)
        return subtasks

    def _execute_subtasks(self, subtasks: List[Dict], workdir: Path,
                         master_scratchpad: Scratchpad, clarification_endpoint: str) -> List[Dict]:
        """
        Execute all subtasks and collect results.

        :param subtasks: List of subtasks to execute
        :param workdir: Working directory
        :param master_scratchpad: Master scratchpad for logging
        :param clarification_endpoint: Clarification endpoint URL
        :return: List of results from all subtasks
        """
        results = []

        for subtask_index, subtask in enumerate(subtasks):
            agent_name = subtask["agent"]
            agent_scratchpad_path = workdir / f"{agent_name}_{subtask_index}.scratchpad.md"
            self.agent_scratchpads[agent_name] = agent_scratchpad_path

            agent_task = {
                "description": subtask["description"],
                "context": subtask["context"]
            }

            master_scratchpad.append(f"[{get_timestamp()}] Running sub-agent: {agent_name}\n")
            self.process_clarifications()

            result = self.run_agent(
                agent_name=agent_name,
                task=agent_task,
                scratchpad_path=agent_scratchpad_path,
                allowed_tools=["file_read", "file_write", "shell"],
                clarification_endpoint=clarification_endpoint
            )

            results.append(result)

            if result["status"] == "needs_clarification":
                self.process_clarifications()
                if "clarification_response" in result:
                    result = self.run_agent(
                        agent_name=agent_name,
                        task=agent_task,
                        scratchpad_path=agent_scratchpad_path,
                        allowed_tools=["file_read", "file_write", "shell"],
                        clarification_endpoint=clarification_endpoint
                    )
                    results[-1] = result

            master_scratchpad.append(f"[{get_timestamp()}] Sub-agent {agent_name} completed with status: {result['status']}\n")

        return results

    def _validate_results(self, task_description: str, results: List[Dict], workdir: Path,
                         master_scratchpad: Scratchpad, clarification_endpoint: str) -> Dict:
        """
        Run tester agent to validate results.

        :param task_description: Original task description
        :param results: Results from subtasks
        :param workdir: Working directory
        :param master_scratchpad: Master scratchpad for logging
        :param clarification_endpoint: Clarification endpoint URL
        :return: Validation result with 'passed' boolean and 'tester_result'
        """
        all_produced_files = []
        for result in results:
            if "produced_files" in result:
                all_produced_files.extend(result["produced_files"])

        tester_needed = len([r for r in results if r['status'] == 'success']) > 0
        if not tester_needed or not all_produced_files:
            return {"passed": True, "tester_result": None}

        master_scratchpad.append(f"[{get_timestamp()}] Running tester agent to validate results...\n")

        tester_task = {
            "description": task_description,
            "produced_files": all_produced_files,
            "context_from_producers": {},
            "context": {"validation_level": "standard"}
        }

        tester_scratchpad_path = workdir / "tester.scratchpad.md"
        tester_result = self.run_agent(
            agent_name="tester",
            task=tester_task,
            scratchpad_path=tester_scratchpad_path,
            allowed_tools=["file_read", "shell"],
            clarification_endpoint=clarification_endpoint
        )

        master_scratchpad.append(f"[{get_timestamp()}] Tester agent completed with status: {tester_result['status']}\n")

        passed = tester_result.get("status") != "failed"
        return {"passed": passed, "tester_result": tester_result}

    def _handle_failures(self, validation: Dict, subtasks: List[Dict], workdir: Path,
                        master_scratchpad: Scratchpad, clarification_endpoint: str,
                        results: List[Dict]) -> List[Dict]:
        """
        Handle tester failures by rerunning agents with feedback.

        :param validation: Validation result from tester
        :param subtasks: Original subtasks
        :param workdir: Working directory
        :param master_scratchpad: Master scratchpad for logging
        :param clarification_endpoint: Clarification endpoint URL
        :param results: Current results list
        :return: Updated results list after reruns
        """
        tester_result = validation["tester_result"]
        issues = tester_result.get("result", {}).get("issues", [])
        suggested_fixes = tester_result.get("result", {}).get("suggested_fixes", [])

        master_scratchpad.append(f"[{get_timestamp()}] Tester found {len(issues)} issues. Suggested fixes: {len(suggested_fixes)}\n")

        for fix in suggested_fixes:
            agent_to_fix = fix.get('agent', 'unknown')
            suggestion = fix.get('suggestion', 'no details')
            master_scratchpad.append(f"[{get_timestamp()}] Suggested fix for {agent_to_fix}: {suggestion}\n")

            for subtask_index, subtask in enumerate(subtasks):
                if subtask['agent'] == agent_to_fix:
                    master_scratchpad.append(f"[{get_timestamp()}] Rerunning {agent_to_fix} with feedback...\n")

                    updated_task = {
                        "description": subtask["description"],
                        "context": subtask["context"],
                        "feedback_from_tester": suggestion
                    }

                    rerun_scratchpad_path = workdir / f"{agent_to_fix}_rerun_{subtask_index}.scratchpad.md"

                    rerun_result = self.run_agent(
                        agent_name=agent_to_fix,
                        task=updated_task,
                        scratchpad_path=rerun_scratchpad_path,
                        allowed_tools=["file_read", "file_write", "shell"],
                        clarification_endpoint=clarification_endpoint
                    )

                    for result_index, result in enumerate(results):
                        if result_index < len(subtasks) and subtasks[result_index]["agent"] == agent_to_fix:
                            results[result_index] = rerun_result
                            break

                    master_scratchpad.append(f"[{get_timestamp()}] Rerun of {agent_to_fix} completed with status: {rerun_result['status']}\n")

        results = self._run_final_validation(task_description, results, workdir, master_scratchpad, clarification_endpoint)
        return results

    def _run_final_validation(self, task_description: str, results: List[Dict], workdir: Path,
                             master_scratchpad: Scratchpad, clarification_endpoint: str) -> List[Dict]:
        """
        Run final tester validation after fixes.

        :param task_description: Original task description
        :param results: Results after reruns
        :param workdir: Working directory
        :param master_scratchpad: Master scratchpad for logging
        :param clarification_endpoint: Clarification endpoint URL
        :return: Updated results list with final tester result
        """
        master_scratchpad.append(f"[{get_timestamp()}] Running tester again after fixes...\n")

        rerun_produced_files = []
        for result in results:
            if "produced_files" in result:
                rerun_produced_files.extend(result["produced_files"])

        if not rerun_produced_files:
            return results

        final_tester_task = {
            "description": task_description,
            "produced_files": rerun_produced_files,
            "context_from_producers": {},
            "context": {"validation_level": "standard"}
        }

        final_tester_scratchpad_path = workdir / "final_tester.scratchpad.md"

        final_tester_result = self.run_agent(
            agent_name="tester",
            task=final_tester_task,
            scratchpad_path=final_tester_scratchpad_path,
            allowed_tools=["file_read", "shell"],
            clarification_endpoint=clarification_endpoint
        )

        master_scratchpad.append(f"[{get_timestamp()}] Final tester validation completed with status: {final_tester_result['status']}\n")
        results.append(final_tester_result)

        return results

    def _finalize_results(self, task_description: str, subtasks: List[Dict],
                         results: List[Dict], workdir: Path, master_scratchpad: Scratchpad) -> Dict:
        """
        Aggregate and format final results, display summary.

        :param task_description: Original task description
        :param subtasks: List of subtasks
        :param results: All results from agents
        :param workdir: Working directory
        :param master_scratchpad: Master scratchpad for logging
        :return: Final aggregated result dictionary
        """
        self.process_clarifications()

        all_produced_files = []
        for result in results:
            if "produced_files" in result:
                all_produced_files.extend(result["produced_files"])

        master_scratchpad.append(f"[{get_timestamp()}] Orchestration completed\n")

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
            for produced_file in all_produced_files:
                print(f"  - {produced_file}")
        print("="*60)

        return {
            "status": "success",
            "result": {
                "subtask_results": results,
                "summary": f"Processed {len(subtasks)} subtasks with {len([r for r in results if r['status'] == 'success'])} successful completions"
            },
            "produced_files": all_produced_files
        }

    def _cleanup_resources(self):
        """
        Cleanup resources including servers and monitoring threads.
        """
        self.stop_status_monitoring()
        self.stop_clarification_server()


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