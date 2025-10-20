#!/usr/bin/env python3
"""
Unit tests for DocumenterAgent class
"""
import pytest
import tempfile
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.available.documenter.agent import DocumenterAgent


class TestDocumenterAgentInit:
    """Test DocumenterAgent initialization"""

    def test_init_creates_documenter_agent(self):
        """Test documenter agent initializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            assert agent.scratchpad_path == scratchpad_path
            assert agent.max_scratchpad_chars == 8192


class TestDocumenterAgentExecute:
    """Test DocumenterAgent execute method"""

    def test_execute_with_fastapi_task_generates_readme(self):
        """Test execute with FastAPI task generates README.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Create documentation for FastAPI service",
                "context": {"type": "documentation"}
            }

            result = agent.execute(task, ["file_write"])

            assert result["status"] == "success"
            assert "produced_files" in result

            readme = Path(tmpdir) / "README.md"
            assert readme.exists()

    def test_execute_readme_contains_correct_content(self):
        """Test generated README contains correct content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Create documentation for FastAPI API",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            readme = Path(tmpdir) / "README.md"
            content = readme.read_text()

            assert "# Task Management API" in content
            assert "FastAPI" in content
            assert "Endpoints" in content

    def test_execute_with_api_task_generates_documentation(self):
        """Test execute with API keyword generates documentation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Document the API endpoints",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            assert result["status"] == "success"
            assert len(result["produced_files"]) > 0

    def test_execute_writes_to_scratchpad(self):
        """Test execute writes progress to scratchpad"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Create API documentation",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            assert scratchpad_path.exists()
            scratchpad_content = scratchpad_path.read_text()
            assert "Documenter Agent started" in scratchpad_content
            assert "Task:" in scratchpad_content

    def test_execute_returns_correct_structure(self):
        """Test execute returns correct result structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Create documentation",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            assert "status" in result
            assert "result" in result
            assert "produced_files" in result

    def test_execute_readme_includes_installation_instructions(self):
        """Test generated README includes installation instructions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Document FastAPI application",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            readme = Path(tmpdir) / "README.md"
            content = readme.read_text()

            assert "Installation" in content or "install" in content.lower()
            assert "pip install" in content.lower()

    def test_execute_readme_includes_docker_instructions(self):
        """Test generated README includes Docker instructions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Document FastAPI service",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            readme = Path(tmpdir) / "README.md"
            content = readme.read_text()

            assert "Docker" in content or "docker" in content

    def test_execute_readme_lists_endpoints(self):
        """Test generated README lists API endpoints"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path)

            task = {
                "description": "Document API endpoints",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            readme = Path(tmpdir) / "README.md"
            content = readme.read_text()

            # Check for endpoint patterns
            assert "GET" in content or "POST" in content

    def test_execute_with_bridge_manager_none(self):
        """Test execute works when bridge_manager is None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
            agent = DocumenterAgent(scratchpad_path, bridge_manager=None)

            task = {
                "description": "Create API documentation",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            assert result["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
