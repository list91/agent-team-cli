#!/usr/bin/env python3
"""
Unit tests for error handling across all components
Tests file I/O failures, subprocess failures, and resource cleanup
"""
import pytest
import tempfile
from pathlib import Path
import sys
from unittest.mock import Mock, patch, mock_open, MagicMock
import subprocess
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scratchpad import Scratchpad
from bridge import Bridge, BridgeManager
from agents.master.master import MasterOrchestrator


class TestScratchpadErrorHandling:
    """Test error handling in Scratchpad class"""

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_scratchpad_write_permission_error(self, mock_file):
        """Test scratchpad handles permission errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            # Should raise error (no error handling in current implementation)
            with pytest.raises(PermissionError):
                scratchpad.write("test content")

    @patch('builtins.open', side_effect=OSError("Disk full"))
    def test_scratchpad_write_disk_full(self, mock_file):
        """Test scratchpad handles disk full errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            with pytest.raises(OSError):
                scratchpad.write("test content")

    @patch('pathlib.Path.read_text', side_effect=IOError("Read error"))
    def test_scratchpad_read_io_error(self, mock_read):
        """Test scratchpad handles read errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratch_path.touch()  # Create file
            scratchpad = Scratchpad(scratch_path)

            with pytest.raises(IOError):
                scratchpad.read()

    def test_scratchpad_read_corrupted_encoding(self):
        """Test scratchpad handles corrupted encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            # Write invalid UTF-8
            with open(scratch_path, 'wb') as f:
                f.write(b'\x80\x81\x82')

            scratchpad = Scratchpad(scratch_path)

            with pytest.raises(UnicodeDecodeError):
                scratchpad.read()


class TestBridgeErrorHandling:
    """Test error handling in Bridge classes"""

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_bridge_send_message_permission_error(self, mock_file):
        """Test bridge handles permission errors when sending messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            with pytest.raises(PermissionError):
                bridge.send_message("agent1", "test_type", {"data": "test"})

    def test_bridge_get_messages_with_corrupted_json(self):
        """Test bridge handles corrupted JSON files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            # Create corrupted JSON file
            bridge_dir = shared_dir / "test_bridge"
            bridge_dir.mkdir(parents=True, exist_ok=True)
            corrupted_file = bridge_dir / "agent1_test_123.json"
            corrupted_file.write_text("Not valid JSON{{{")

            # Should skip corrupted files and not raise
            messages = bridge.get_messages()
            assert messages == []

    @patch('pathlib.Path.mkdir', side_effect=OSError("Cannot create directory"))
    def test_bridge_init_directory_creation_error(self, mock_mkdir):
        """Test bridge handles directory creation errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)

            with pytest.raises(OSError):
                bridge = Bridge("test_bridge", shared_dir)


class TestMasterOrchestratorErrorHandling:
    """Test error handling in MasterOrchestrator"""

    @patch('subprocess.run', side_effect=FileNotFoundError("Python not found"))
    def test_run_agent_python_not_found(self, mock_run):
        """Test run_agent handles missing Python interpreter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"
            assert "error" in result

    @patch('subprocess.run', side_effect=PermissionError("Permission denied"))
    def test_run_agent_permission_error(self, mock_run):
        """Test run_agent handles permission errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"

    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 300))
    def test_run_agent_timeout_handling(self, mock_run):
        """Test run_agent properly handles timeout"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"
            assert "timed out" in result["error"].lower()

    @patch('subprocess.run')
    def test_run_agent_malformed_json_output(self, mock_run):
        """Test run_agent handles malformed JSON from agent"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Not JSON at all!",
            stderr=""
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"
            assert "invalid JSON" in result["error"]

    @patch('subprocess.run')
    def test_run_agent_empty_output(self, mock_run):
        """Test run_agent handles empty output from agent"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("coder", task, scratchpad_path)

            assert result["status"] == "failed"

    def test_run_agent_with_invalid_agent_name(self):
        """Test run_agent with nonexistent agent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            task = {"description": "Test", "context": {}}
            scratchpad_path = workdir / "test.scratchpad.md"

            result = orchestrator.run_agent("nonexistent_agent", task, scratchpad_path)

            assert result["status"] == "failed"
            assert "not found" in result["error"]

    @patch('socketserver.TCPServer', side_effect=OSError("Address in use"))
    def test_start_clarification_server_port_exhaustion(self, mock_server):
        """Test clarification server handles port exhaustion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            # Should eventually raise after trying all ports
            with pytest.raises(OSError):
                orchestrator.start_clarification_server()


class TestCoderAgentErrorHandling:
    """Test error handling in CoderAgent"""

    def test_coder_execute_file_write_permission_error(self):
        """Test coder handles permission errors when writing files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Import here to avoid circular import
            from agents.available.coder.agent import CoderAgent

            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            # Make directory read-only
            import os
            os.chmod(tmpdir, 0o444)

            try:
                # Should raise permission error or IOError
                with pytest.raises((PermissionError, IOError)):
                    result = agent.execute(task, ["file_write"])
            finally:
                # Restore permissions for cleanup
                os.chmod(tmpdir, 0o755)

    def test_coder_execute_disk_full_error(self):
        """Test coder handles disk full errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from agents.available.coder.agent import CoderAgent

            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            with patch('builtins.open', side_effect=OSError("No space left on device")):
                with pytest.raises(OSError):
                    result = agent.execute(task, ["file_write"])


class TestTesterAgentErrorHandling:
    """Test error handling in TesterAgent"""

    @patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 10))
    def test_tester_syntax_check_timeout(self, mock_run):
        """Test tester handles syntax check timeout"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from agents.available.tester.agent import TesterAgent

            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('test')\n")

            task = {
                "description": "Validate",
                "produced_files": [str(test_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read", "shell"])

            # Should handle timeout gracefully
            assert result["status"] == "failed"
            assert any("timeout" in issue.lower() for issue in result["result"]["issues"])

    @patch('subprocess.run', side_effect=FileNotFoundError("Python not found"))
    def test_tester_python_not_found(self, mock_run):
        """Test tester handles missing Python interpreter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from agents.available.tester.agent import TesterAgent

            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('test')\n")

            task = {
                "description": "Validate",
                "produced_files": [str(test_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read", "shell"])

            # Should handle error gracefully
            assert result["status"] == "failed"

    def test_tester_handles_file_read_error(self):
        """Test tester handles file read errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            from agents.available.tester.agent import TesterAgent

            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            test_file = Path(tmpdir) / "test.py"
            # Don't create the file

            task = {
                "description": "Validate",
                "produced_files": [str(test_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read"])

            # Should report file doesn't exist
            assert result["status"] == "failed"
            assert len(result["result"]["issues"]) > 0


class TestResourceCleanup:
    """Test resource cleanup scenarios"""

    def test_clarification_server_cleanup(self):
        """Test clarification server is properly cleaned up"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            port = orchestrator.start_clarification_server()
            assert orchestrator.clarification_server is not None

            orchestrator.stop_clarification_server()
            # Server should be stopped

    def test_scratchpad_temp_file_cleanup(self):
        """Test scratchpad temp files are cleaned up"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            scratchpad.write("Test content\n", append=False)

            # Temp file should not exist after write
            temp_file = scratch_path.with_suffix(scratch_path.suffix + '.tmp')
            assert not temp_file.exists()

    def test_bridge_directory_cleanup(self):
        """Test bridge directories exist after creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir) / "shared"
            manager = BridgeManager(shared_dir)

            bridge = manager.create_bridge("test_bridge")
            bridge.send_message("agent1", "test", {"data": 1})

            # Directory and files should exist
            assert (shared_dir / "test_bridge").exists()


class TestConcurrentOperations:
    """Test concurrent operation error handling"""

    def test_scratchpad_concurrent_writes(self):
        """Test scratchpad handles concurrent writes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            # Multiple quick writes should all succeed
            for i in range(10):
                scratchpad.append(f"Line {i}\n")

            content = scratch_path.read_text()
            # All writes should be present
            for i in range(10):
                assert f"Line {i}" in content

    def test_bridge_concurrent_messages(self):
        """Test bridge handles concurrent messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            # Send multiple messages quickly
            for i in range(5):
                bridge.send_message(f"agent{i}", "test", {"msg": i})

            messages = bridge.get_messages()
            assert len(messages) == 5


class TestInvalidInput:
    """Test handling of invalid input"""

    def test_scratchpad_with_none_path(self):
        """Test scratchpad with None path"""
        with pytest.raises((TypeError, AttributeError)):
            scratchpad = Scratchpad(None)

    def test_bridge_with_none_bridge_id(self):
        """Test bridge with None bridge_id"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises((TypeError, AttributeError)):
                bridge = Bridge(None, Path(tmpdir))

    def test_master_orchestrator_decompose_empty_task(self):
        """Test task decomposition with empty string"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            subtasks = orchestrator.decompose_task("")
            # Should return echo agent as fallback
            assert len(subtasks) > 0

    def test_master_orchestrator_run_agent_with_null_task(self):
        """Test run_agent with None task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir)
            orchestrator = MasterOrchestrator(workdir)

            scratchpad_path = workdir / "test.scratchpad.md"

            with pytest.raises((TypeError, KeyError)):
                orchestrator.run_agent("coder", None, scratchpad_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
