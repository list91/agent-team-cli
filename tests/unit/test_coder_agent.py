#!/usr/bin/env python3
"""
Unit tests for CoderAgent class
"""
import pytest
import tempfile
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.available.coder.agent import CoderAgent


class TestCoderAgentInit:
    """Test CoderAgent initialization"""

    def test_init_creates_coder_agent(self):
        """Test coder agent initializes correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            assert agent.scratchpad_path == scratchpad_path
            assert agent.max_scratchpad_chars == 8192

    def test_init_with_custom_max_chars(self):
        """Test coder agent with custom max_scratchpad_chars"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path, max_scratchpad_chars=4096)

            assert agent.max_scratchpad_chars == 4096


class TestCoderAgentExecute:
    """Test CoderAgent execute method"""

    def test_execute_with_fastapi_task_generates_main_py(self):
        """Test execute with FastAPI task generates main.py"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service with CRUD operations",
                "context": {"type": "code_generation"}
            }
            allowed_tools = ["file_read", "file_write"]

            result = agent.execute(task, allowed_tools)

            assert result["status"] == "success"
            assert "produced_files" in result
            assert len(result["produced_files"]) > 0

            # Check main.py was created
            main_py = Path(tmpdir) / "main.py"
            assert main_py.exists()

    def test_execute_generates_correct_fastapi_code(self):
        """Test execute generates correct FastAPI code"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {"type": "code_generation"}
            }

            result = agent.execute(task, ["file_write"])

            main_py = Path(tmpdir) / "main.py"
            content = main_py.read_text()

            # Verify FastAPI imports and structure
            assert "from fastapi import FastAPI" in content
            assert "app = FastAPI" in content
            assert "@app.get" in content

    def test_execute_with_docker_task_generates_dockerfile(self):
        """Test execute with Docker keyword generates Dockerfile"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service with Docker container",
                "context": {"type": "code_generation"}
            }

            result = agent.execute(task, ["file_write"])

            assert result["status"] == "success"

            # Check Dockerfile was created
            dockerfile = Path(tmpdir) / "Dockerfile"
            assert dockerfile.exists()

    def test_execute_dockerfile_has_correct_structure(self):
        """Test generated Dockerfile has correct structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create FastAPI with docker",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            dockerfile = Path(tmpdir) / "Dockerfile"
            content = dockerfile.read_text()

            assert "FROM python:" in content
            assert "WORKDIR /app" in content
            assert "EXPOSE 8000" in content
            assert "CMD" in content

    def test_execute_writes_to_scratchpad(self):
        """Test execute writes progress to scratchpad"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            # Check scratchpad exists and has content
            assert scratchpad_path.exists()
            scratchpad_content = scratchpad_path.read_text()
            assert "Coder Agent started" in scratchpad_content
            assert "Task:" in scratchpad_content

    def test_execute_returns_correct_structure(self):
        """Test execute returns correct result structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            assert "status" in result
            assert "result" in result
            assert "produced_files" in result
            assert isinstance(result["produced_files"], list)

    def test_execute_handles_empty_task_description(self):
        """Test execute handles empty task description"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {"description": "", "context": {}}

            result = agent.execute(task, ["file_write"])

            # Should still succeed but not generate files
            assert result["status"] == "success"

    def test_execute_fastapi_generates_crud_endpoints(self):
        """Test generated FastAPI code includes CRUD endpoints"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service with CRUD",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            main_py = Path(tmpdir) / "main.py"
            content = main_py.read_text()

            # Check for CRUD operations
            assert "GET" in content or "@app.get" in content
            assert "POST" in content or "@app.post" in content
            assert "PUT" in content or "@app.put" in content
            assert "DELETE" in content or "@app.delete" in content

    def test_execute_generates_pydantic_models(self):
        """Test generated FastAPI code includes Pydantic models"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            main_py = Path(tmpdir) / "main.py"
            content = main_py.read_text()

            assert "from pydantic import BaseModel" in content
            assert "class Task(BaseModel):" in content

    def test_execute_multiple_times_overwrites_files(self):
        """Test execute can be called multiple times"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            result1 = agent.execute(task, ["file_write"])
            result2 = agent.execute(task, ["file_write"])

            assert result1["status"] == "success"
            assert result2["status"] == "success"

            main_py = Path(tmpdir) / "main.py"
            assert main_py.exists()

    def test_execute_with_bridge_manager_none(self):
        """Test execute works when bridge_manager is None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path, bridge_manager=None)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            assert result["status"] == "success"

    def test_execute_produces_valid_python_syntax(self):
        """Test generated Python code has valid syntax"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            main_py = Path(tmpdir) / "main.py"

            # Try to compile the generated code
            import py_compile
            try:
                py_compile.compile(str(main_py), doraise=True)
                syntax_valid = True
            except py_compile.PyCompileError:
                syntax_valid = False

            assert syntax_valid

    def test_execute_includes_uvicorn_run_command(self):
        """Test generated code includes uvicorn run command"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
            agent = CoderAgent(scratchpad_path)

            task = {
                "description": "Create a FastAPI service",
                "context": {}
            }

            result = agent.execute(task, ["file_write"])

            main_py = Path(tmpdir) / "main.py"
            content = main_py.read_text()

            assert "uvicorn.run" in content or "uvicorn" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
