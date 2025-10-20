#!/usr/bin/env python3
"""
Unit tests for TesterAgent class
"""
import pytest
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.available.tester.agent import TesterAgent


class TestTesterAgentInit:
    """Test TesterAgent initialization"""

    def test_init_creates_tester_agent(self):
        """Test tester agent initializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            assert agent.scratchpad_path == scratchpad_path
            assert agent.max_scratchpad_chars == 8192
            assert agent.validation_results == {}


class TestTesterAgentValidation:
    """Test TesterAgent validation functionality"""

    def test_execute_with_valid_python_file_succeeds(self):
        """Test execute with valid Python file succeeds"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            # Create a valid Python file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('Hello, World!')\n")

            task = {
                "description": "Validate Python code",
                "produced_files": [str(test_file)],
                "context_from_producers": {},
                "context": {"validation_level": "standard"}
            }

            result = agent.execute(task, ["file_read", "shell"])

            assert result["status"] == "success"

    def test_execute_with_nonexistent_file_fails(self):
        """Test execute with nonexistent file fails"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            nonexistent_file = Path(tmpdir) / "nonexistent.py"

            task = {
                "description": "Validate code",
                "produced_files": [str(nonexistent_file)],
                "context_from_producers": {},
                "context": {"validation_level": "standard"}
            }

            result = agent.execute(task, ["file_read"])

            assert result["status"] == "failed"
            assert len(result["result"]["issues"]) > 0

    def test_execute_with_empty_file_fails(self):
        """Test execute with empty file reports issue"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            empty_file = Path(tmpdir) / "empty.py"
            empty_file.write_text("")

            task = {
                "description": "Validate code",
                "produced_files": [str(empty_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read"])

            assert result["status"] == "failed"
            assert any("empty" in issue.lower() for issue in result["result"]["issues"])

    def test_execute_calculates_quality_score(self):
        """Test execute calculates quality score correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            valid_file = Path(tmpdir) / "valid.py"
            valid_file.write_text("x = 1\n")

            task = {
                "description": "Validate",
                "produced_files": [str(valid_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read", "shell"])

            assert "quality_score" in result["result"]
            assert 0.0 <= result["result"]["quality_score"] <= 1.0

    def test_execute_suggests_fixes_when_issues_found(self):
        """Test execute suggests fixes when issues are found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            empty_file = Path(tmpdir) / "empty.py"
            empty_file.write_text("")

            task = {
                "description": "Validate",
                "produced_files": [str(empty_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read"])

            assert result["status"] == "failed"
            assert "suggested_fixes" in result["result"]

    def test_execute_validates_dockerfile(self):
        """Test execute validates Dockerfile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            dockerfile = Path(tmpdir) / "Dockerfile"
            dockerfile.write_text("FROM python:3.10\nEXPOSE 8000\nCMD [\"uvicorn\"]")

            task = {
                "description": "Validate container",
                "produced_files": [str(dockerfile)],
                "context_from_producers": {},
                "context": {"validation_level": "standard"}
            }

            result = agent.execute(task, ["file_read"])

            # Should validate without errors
            assert result["status"] == "success"

    def test_execute_validates_fastapi_criteria(self):
        """Test execute validates FastAPI-specific criteria"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            py_file = Path(tmpdir) / "main.py"
            py_file.write_text("from fastapi import FastAPI\napp = FastAPI()\n")

            task = {
                "description": "Create a FastAPI service",
                "produced_files": [str(py_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read", "shell"])

            # Should pass because FastAPI import is present
            assert result["status"] == "success"

    def test_execute_fails_missing_fastapi_import(self):
        """Test execute fails when FastAPI import is missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            py_file = Path(tmpdir) / "main.py"
            py_file.write_text("print('Hello')\n")

            task = {
                "description": "Create a FastAPI service",
                "produced_files": [str(py_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read", "shell"])

            # Should fail because FastAPI import is missing
            assert result["status"] == "failed"

    def test_execute_writes_to_scratchpad(self):
        """Test execute writes to scratchpad"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("x = 1\n")

            task = {
                "description": "Validate",
                "produced_files": [str(test_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read", "shell"])

            assert scratchpad_path.exists()
            content = scratchpad_path.read_text()
            assert "Tester Agent started" in content

    def test_execute_returns_correct_structure(self):
        """Test execute returns correct structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "tester.scratchpad.md"
            agent = TesterAgent(scratchpad_path)

            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("x = 1\n")

            task = {
                "description": "Validate",
                "produced_files": [str(test_file)],
                "context_from_producers": {},
                "context": {}
            }

            result = agent.execute(task, ["file_read"])

            assert "status" in result
            assert "result" in result
            assert "produced_files" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
