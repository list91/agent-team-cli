#!/usr/bin/env python3
"""
Integration test for subprocess LLM provider

Verifies that all agents (master, coder, documenter) use real subprocess LLM
instead of mock when config.yaml is set to provider: "subprocess"
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.master.master import MasterOrchestrator
from src.fallbacks import get_fallback_config


def test_master_uses_subprocess_provider():
    """Test that master orchestrator uses subprocess provider from config"""
    config = get_fallback_config()

    # Verify config is set to subprocess
    assert config.llm.get("provider") == "subprocess", \
        "config.yaml should have provider: 'subprocess'"

    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        orchestrator = MasterOrchestrator(workdir)

        # Verify master created subprocess LLM client
        from src.llm_client import SubprocessLLMProvider
        assert isinstance(orchestrator.llm_client.provider, SubprocessLLMProvider), \
            "Master should use SubprocessLLMProvider, not MockProvider"

        print(f"[OK] Master orchestrator uses SubprocessLLMProvider")
        print(f"   Command: {orchestrator.llm_client.provider.command}")
        print(f"   Timeout: {orchestrator.llm_client.provider.timeout}")


def test_coder_agent_uses_subprocess_provider():
    """Test that coder agent uses subprocess provider from config"""
    from agents.available.coder.agent import CoderAgent
    from src.llm_client import SubprocessLLMProvider

    config = get_fallback_config()
    assert config.llm.get("provider") == "subprocess"

    with tempfile.TemporaryDirectory() as tmpdir:
        scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
        agent = CoderAgent(scratchpad_path)

        # Verify coder uses subprocess provider
        assert isinstance(agent.llm_client.provider, SubprocessLLMProvider), \
            "Coder should use SubprocessLLMProvider, not MockProvider"

        print(f"[OK] Coder agent uses SubprocessLLMProvider")
        print(f"   Command: {agent.llm_client.provider.command}")


def test_documenter_agent_uses_subprocess_provider():
    """Test that documenter agent uses subprocess provider from config"""
    from agents.available.documenter.agent import DocumenterAgent
    from src.llm_client import SubprocessLLMProvider

    config = get_fallback_config()
    assert config.llm.get("provider") == "subprocess"

    with tempfile.TemporaryDirectory() as tmpdir:
        scratchpad_path = Path(tmpdir) / "documenter.scratchpad.md"
        agent = DocumenterAgent(scratchpad_path)

        # Verify documenter uses subprocess provider
        assert isinstance(agent.llm_client.provider, SubprocessLLMProvider), \
            "Documenter should use SubprocessLLMProvider, not MockProvider"

        print(f"[OK] Documenter agent uses SubprocessLLMProvider")
        print(f"   Command: {agent.llm_client.provider.command}")


@patch('subprocess.Popen')
def test_master_decompose_task_uses_subprocess(mock_popen):
    """Test that master's decompose_task actually calls subprocess LLM"""
    # Mock successful qwen response
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (
        json.dumps({
            "complexity": 5,
            "strategy": "flat_delegation",
            "agents": [
                {
                    "name": "coder",
                    "subtask": "Generate Python code for ML service",
                    "priority": 1,
                    "tools": ["file_write", "shell"]
                },
                {
                    "name": "documenter",
                    "subtask": "Create documentation and README",
                    "priority": 2,
                    "tools": ["file_write"]
                }
            ],
            "bridges": [
                {
                    "from": "coder",
                    "to": "documenter",
                    "type": "api_specification",
                    "purpose": "Share ML service API"
                }
            ],
            "reasoning": "ML service requires code generation and documentation"
        }),
        ""
    )
    mock_popen.return_value = mock_proc

    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        orchestrator = MasterOrchestrator(workdir)

        # Call decompose_task
        task_description = "Create a sentiment analysis ML service with Redis caching"
        subtasks = orchestrator.decompose_task(task_description)

        # Verify subprocess was called
        assert mock_popen.called, "decompose_task should call subprocess.Popen"

        # Verify command structure
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "qwen", f"Should call 'qwen', got '{cmd[0]}'"
        assert cmd[1] == "run", "Should use 'run' subcommand"
        assert "--task" in cmd, "Should pass --task argument"

        # Verify subtasks were created
        assert len(subtasks) == 2
        assert subtasks[0]["agent"] == "coder"
        assert subtasks[1]["agent"] == "documenter"

        print(f"[OK] Master decompose_task called subprocess with:")
        print(f"   Command: {cmd[:3]}...")
        print(f"   Subtasks created: {[s['agent'] for s in subtasks]}")


@patch('subprocess.Popen')
def test_coder_execute_uses_subprocess(mock_popen):
    """Test that coder's execute method calls subprocess LLM for code generation"""
    from agents.available.coder.agent import CoderAgent

    # Mock successful qwen response with code
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (
        '''```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="Sentiment Analysis API")

@app.post("/analyze")
def analyze(text: str):
    return {"sentiment": "positive", "confidence": 0.95}
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```''',
        ""
    )
    mock_popen.return_value = mock_proc

    with tempfile.TemporaryDirectory() as tmpdir:
        scratchpad_path = Path(tmpdir) / "coder.scratchpad.md"
        agent = CoderAgent(scratchpad_path)

        # Execute coder task
        task = {
            "description": "Create sentiment analysis API with FastAPI",
            "context": {"type": "api_service"}
        }
        result = agent.execute(task, allowed_tools=["file_write", "shell"])

        # Verify subprocess was called
        assert mock_popen.called, "Coder execute should call subprocess.Popen"

        # Verify command
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert cmd[0] == "qwen", f"Should call 'qwen', got '{cmd[0]}'"

        # Verify result
        assert result["status"] == "success"
        assert len(result["produced_files"]) > 0

        print(f"[OK] Coder execute called subprocess and generated files:")
        print(f"   Files: {result['produced_files']}")


def test_subprocess_command_format():
    """Verify that subprocess commands follow the expected format"""
    from src.llm_client import SubprocessLLMProvider

    provider = SubprocessLLMProvider(
        command="qwen",
        timeout=300,
        tools="file_read,file_write,shell"
    )

    # This test documents the expected command format
    expected_base_cmd = [
        "qwen",
        "run",
        "--task", "<prompt>",
        "--temperature", "0.7",
        "--max-tokens", "4000",
        "--tools", "file_read,file_write,shell"
    ]

    print(f"[OK] Expected subprocess command format:")
    print(f"   {' '.join(expected_base_cmd)}")

    # Verify provider configuration
    assert provider.command == "qwen"
    assert provider.timeout == 300
    assert "tools" in provider.extra_args


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
