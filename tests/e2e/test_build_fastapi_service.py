"""
E2E test for the MSP orchestrator - FastAPI service creation
"""
import pytest
import tempfile
import json
import subprocess
import sys
from pathlib import Path


def test_fastapi_service_creation():
    """
    E2E test: Create REST API on FastAPI for task management with documentation and Dockerfile
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
        
        # Check that the expected files were created
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
        
        print("E2E test passed: FastAPI service created successfully!")


if __name__ == "__main__":
    test_fastapi_service_creation()