#!/usr/bin/env python3
"""
Unit tests for MasterOrchestrator class
"""
import pytest
import tempfile
import json
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.master.master import MasterOrchestrator


class TestMasterOrchestratorInit:
    """Test MasterOrchestrator initialization"""

    def test_init_creates_orchestrator(self):
        """Test orchestrator initializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            assert orchestrator.workdir == workdir
            assert orchestrator.clarification_requests == []
            assert orchestrator.clarification_server is None
            assert orchestrator.running_agents == []
            assert orchestrator.agent_scratchpads == {}

    def test_init_creates_bridge_manager(self):
        """Test orchestrator creates bridge manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            assert orchestrator.bridge_manager is not None
            assert (workdir / "shared").exists()


class TestClarificationServer:
    """Test clarification server functionality"""

    def test_start_clarification_server_returns_port(self):
        """Test starting clarification server returns port number"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            port = orchestrator.start_clarification_server()

            assert isinstance(port, int)
            assert 8000 <= port <= 9000
            assert orchestrator.clarification_server is not None
            assert orchestrator.clarification_thread is not None

            orchestrator.stop_clarification_server()

    def test_stop_clarification_server(self):
        """Test stopping clarification server"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            orchestrator.start_clarification_server()
            orchestrator.stop_clarification_server()

            # Server should be stopped (httpd still exists but is shutdown)
            assert orchestrator.clarification_server is not None

    def test_stop_clarification_server_when_not_started(self):
        """Test stopping server when it wasn't started doesn't error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            # Should not raise error
            orchestrator.stop_clarification_server()


class TestTaskDecomposition:
    """Test task decomposition logic"""

    def test_decompose_fastapi_task_creates_coder_subtask(self):
        """Test FastAPI task creates coder subtask"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Create a FastAPI service with CRUD operations"
            subtasks = orchestrator.decompose_task(task)

            assert len(subtasks) >= 1
            assert any(st["agent"] == "coder" for st in subtasks)

    def test_decompose_api_task_creates_coder_subtask(self):
        """Test API task creates coder subtask"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Build an API server"
            subtasks = orchestrator.decompose_task(task)

            assert len(subtasks) >= 1
            assert any(st["agent"] == "coder" for st in subtasks)

    def test_decompose_documentation_task_creates_documenter_subtask(self):
        """Test documentation task creates documenter subtask"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Create documentation for the API"
            subtasks = orchestrator.decompose_task(task)

            assert len(subtasks) >= 1
            assert any(st["agent"] == "documenter" for st in subtasks)

    def test_decompose_readme_task_creates_documenter_subtask(self):
        """Test README task creates documenter subtask"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Write a README for the project"
            subtasks = orchestrator.decompose_task(task)

            assert len(subtasks) >= 1
            assert any(st["agent"] == "documenter" for st in subtasks)

    def test_decompose_generic_task_creates_echo_subtask(self):
        """Test generic task creates echo subtask as fallback"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Do something generic"
            subtasks = orchestrator.decompose_task(task)

            assert len(subtasks) >= 1
            assert any(st["agent"] == "echo" for st in subtasks)

    def test_decompose_combined_task_creates_multiple_subtasks(self):
        """Test combined task creates multiple subtasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Create a FastAPI service and write documentation"
            subtasks = orchestrator.decompose_task(task)

            assert len(subtasks) >= 2
            agents = [st["agent"] for st in subtasks]
            assert "coder" in agents
            assert "documenter" in agents

    def test_decompose_task_includes_context(self):
        """Test decomposed subtasks include context"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Create a FastAPI service"
            subtasks = orchestrator.decompose_task(task)

            for subtask in subtasks:
                assert "context" in subtask
                assert "type" in subtask["context"]

    def test_decompose_task_includes_description(self):
        """Test decomposed subtasks include description"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = "Create a FastAPI service"
            subtasks = orchestrator.decompose_task(task)

            for subtask in subtasks:
                assert "description" in subtask
                assert len(subtask["description"]) > 0

    def test_decompose_task_is_case_insensitive(self):
        """Test task decomposition is case insensitive"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task_lower = "create a fastapi service"
            task_upper = "CREATE A FASTAPI SERVICE"
            task_mixed = "CrEaTe A FaStApI SeRvIcE"

            subtasks_lower = orchestrator.decompose_task(task_lower)
            subtasks_upper = orchestrator.decompose_task(task_upper)
            subtasks_mixed = orchestrator.decompose_task(task_mixed)

            assert len(subtasks_lower) == len(subtasks_upper) == len(subtasks_mixed)


class TestAgentDiscovery:
    """Test agent discovery functionality"""

    def test_find_available_agents_returns_list(self):
        """Test find_available_agents returns a list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            agents = orchestrator.find_available_agents()
            assert isinstance(agents, list)

    def test_find_available_agents_includes_coder(self):
        """Test find_available_agents includes coder agent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            agents = orchestrator.find_available_agents()
            agent_names = [a["name"] for a in agents]
            assert "coder" in agent_names

    def test_find_available_agents_includes_tester(self):
        """Test find_available_agents includes tester agent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            agents = orchestrator.find_available_agents()
            agent_names = [a["name"] for a in agents]
            assert "tester" in agent_names

    def test_find_available_agents_includes_config(self):
        """Test find_available_agents includes agent config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            agents = orchestrator.find_available_agents()
            for agent in agents:
                assert "name" in agent
                assert "path" in agent
                assert "config" in agent


class TestRunAgent:
    """Test run_agent functionality"""

    def test_run_agent_with_nonexistent_agent_returns_error(self):
        """Test running nonexistent agent returns error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test task"}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent(
                "nonexistent_agent",
                task,
                scratchpad_path
            )

            assert result["status"] == "failed"
            assert "not found" in result["error"]

    @patch('subprocess.run')
    def test_run_agent_calls_subprocess(self, mock_run):
        """Test run_agent calls subprocess with correct arguments"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"status": "success", "result": {}, "produced_files": []}),
            stderr=""
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test task", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent(
                "coder",
                task,
                scratchpad_path,
                allowed_tools=["file_read", "file_write"]
            )

            # Verify subprocess was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]

            # Check command structure
            assert "--task" in call_args
            assert "--scratchpad-path" in call_args
            assert "--allowed-tools" in call_args

    @patch('subprocess.run')
    def test_run_agent_includes_clarification_endpoint(self, mock_run):
        """Test run_agent includes clarification endpoint"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"status": "success", "result": {}, "produced_files": []}),
            stderr=""
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test task", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent(
                "coder",
                task,
                scratchpad_path,
                clarification_endpoint="http://localhost:8000"
            )

            # Verify clarification endpoint was passed
            call_args = mock_run.call_args[0][0]
            assert "--clarification-endpoint" in call_args
            assert "http://localhost:8000" in call_args

    @patch('subprocess.run')
    def test_run_agent_handles_subprocess_failure(self, mock_run):
        """Test run_agent handles subprocess failure"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error occurred"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test task", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"
            assert "failed with return code" in result["error"]

    @patch('subprocess.run')
    def test_run_agent_handles_invalid_json_output(self, mock_run):
        """Test run_agent handles invalid JSON from agent"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Not valid JSON",
            stderr=""
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test task", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"
            assert "invalid JSON" in result["error"]

    @patch('subprocess.run')
    def test_run_agent_handles_timeout(self, mock_run):
        """Test run_agent handles subprocess timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test task", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"
            assert "timed out" in result["error"]


class TestClarificationHandling:
    """Test clarification handling"""

    def test_get_clarification_from_user(self):
        """Test get_clarification_from_user prompts correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            request = {"question": "Test question?"}

            with patch('builtins.input', return_value="Test answer"):
                response = orchestrator.get_clarification_from_user(request)

            assert response == "Test answer"

    def test_process_clarifications_empty_list(self):
        """Test process_clarifications with empty list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            # Should not raise error
            orchestrator.process_clarifications()


class TestBridgeSetup:
    """Test bridge setup between agents"""

    @patch('builtins.open', create=True)
    @patch('pathlib.Path.exists')
    def test_setup_agent_bridges_creates_bridges(self, mock_exists, mock_open):
        """Test setup_agent_bridges creates bridges for compatible agents"""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '''
accepts_bridges: true
capabilities: ["coding"]
'''

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            subtasks = [
                {"agent": "coder", "description": "Code task"},
                {"agent": "documenter", "description": "Doc task"}
            ]

            # Should not raise error
            orchestrator.setup_agent_bridges(subtasks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
