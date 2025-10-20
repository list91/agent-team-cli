"""
Updated E2E test for the MSP orchestrator - FastAPI service creation with tester validation
"""
import pytest
import tempfile
import json
import subprocess
import sys
from pathlib import Path


def test_fastapi_service_creation_with_tester():
    """
    E2E test: Create REST API on FastAPI for task management with documentation and Dockerfile.
    This test verifies the integration with the tester agent.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)
        
        # Define the task
        task = {
            "description": "Create REST API on FastAPI for managing tasks with CRUD operations, "
                           "OpenAPI documentation, Dockerfile. Server should listen on port 8000. "
                           "No authentication needed.",
            "context": {
                "workdir": str(workdir)
            }
        }
        
        # Run the MSP orchestrator
        result = subprocess.run([
            sys.executable, 
            str(Path(__file__).parent.parent.parent / "msp-run.py"),
            "--task", json.dumps(task["description"]),
            "--workdir", str(workdir)
        ], capture_output=True, text=True, timeout=120)
        
        # Check that the command executed successfully
        assert result.returncode == 0, f"MSP orchestrator failed: {result.stderr}"
        
        # Check that the expected files were created in the workdir
        expected_files = [
            workdir / "main.py",
            workdir / "Dockerfile", 
            workdir / "README.md",
            workdir / "openapi.yaml"
        ]
        
        for file_path in expected_files:
            assert file_path.exists(), f"Expected file {file_path} was not created"
        
        # Verify content of main.py contains FastAPI elements
        main_py_content = (workdir / "main.py").read_text()
        assert "from fastapi import FastAPI" in main_py_content
        assert "uvicorn.run" in main_py_content
        assert "port=8000" in main_py_content  # Check that port 8000 is used
        
        # Verify Dockerfile content
        dockerfile_content = (workdir / "Dockerfile").read_text()
        assert "EXPOSE 8000" in dockerfile_content
        assert "CMD [" in dockerfile_content
        
        # Verify README contains expected sections
        readme_content = (workdir / "README.md").read_text()
        assert "Task Management API" in readme_content
        assert "FastAPI" in readme_content
        
        # Check that tester.scratchpad.md was created, indicating tester ran
        tester_scratchpad = workdir / "tester.scratchpad.md"
        assert tester_scratchpad.exists(), "Tester scratchpad was not created, indicating tester didn't run"
        
        # Read tester output to verify it passed validation
        tester_content = tester_scratchpad.read_text()
        assert "Quality score: 1.0" in tester_content or "Quality score:" in tester_content, \
               f"Tester did not pass validation. Content: {tester_content}"
        assert "Validation completed" in tester_content
        
        print("E2E test passed: FastAPI service created and validated by tester!")


def test_simple_api_creation_with_tester():
    """
    E2E test: Simple API task that should be validated by tester
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workdir = Path(temp_dir)
        
        # Define a simple API task that will trigger the coder agent
        task = {
            "description": "Create a simple FastAPI application with a hello endpoint",
            "context": {
                "workdir": str(workdir)
            }
        }
        
        # Run the MSP orchestrator
        result = subprocess.run([
            sys.executable, 
            str(Path(__file__).parent.parent.parent / "msp-run.py"),
            "--task", json.dumps(task["description"]),
            "--workdir", str(workdir)
        ], capture_output=True, text=True, timeout=120)
        
        # Check that the command executed successfully
        assert result.returncode == 0, f"MSP orchestrator failed: {result.stderr}"
        
        # Check that tester ran by looking for tester scratchpad
        tester_scratchpad = workdir / "tester.scratchpad.md"
        assert tester_scratchpad.exists(), "Tester scratchpad was not created"
        
        print("E2E test passed: Simple API task validated by tester!")


if __name__ == "__main__":
    test_fastapi_service_creation_with_tester()
    test_simple_api_creation_with_tester()
    print("All E2E tests passed!")