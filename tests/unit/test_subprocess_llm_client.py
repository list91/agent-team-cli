#!/usr/bin/env python3
"""
Unit tests for SubprocessLLMProvider

Tests the subprocess-based LLM client that calls CLI tools like qwen.
"""
import sys
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.llm_client import SubprocessLLMProvider, LLMClient


def test_subprocess_provider_initialization():
    """Test SubprocessLLMProvider initialization"""
    provider = SubprocessLLMProvider(command="qwen", timeout=60)
    assert provider.command == "qwen"
    assert provider.timeout == 60
    assert provider.subprocess is not None


def test_subprocess_provider_with_kwargs():
    """Test SubprocessLLMProvider with extra kwargs"""
    provider = SubprocessLLMProvider(
        command="qwen",
        timeout=120,
        tools="file_read,file_write",
        verbose=True
    )
    assert provider.command == "qwen"
    assert provider.timeout == 120
    assert "tools" in provider.extra_args
    assert provider.extra_args["tools"] == "file_read,file_write"
    assert provider.extra_args["verbose"] is True


@patch('subprocess.Popen')
def test_subprocess_provider_generate_success(mock_popen):
    """Test successful generation via subprocess"""
    # Mock subprocess
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (
        "This is a generated response from the LLM",
        ""
    )
    mock_popen.return_value = mock_proc

    provider = SubprocessLLMProvider(command="qwen")
    result = provider.generate(
        system_prompt="You are a helpful assistant",
        user_prompt="Write a hello world program"
    )

    assert result == "This is a generated response from the LLM"
    mock_popen.assert_called_once()

    # Verify command structure
    call_args = mock_popen.call_args
    cmd = call_args[0][0]
    assert cmd[0] == "qwen"
    assert cmd[1] == "run"
    assert "--task" in cmd
    assert "--temperature" in cmd
    assert "--max-tokens" in cmd


@patch('subprocess.Popen')
def test_subprocess_provider_with_extra_args(mock_popen):
    """Test subprocess provider with extra CLI arguments"""
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = ("Response", "")
    mock_popen.return_value = mock_proc

    provider = SubprocessLLMProvider(
        command="qwen",
        tools="file_read,shell",
        verbose=True
    )
    result = provider.generate(
        system_prompt="You are a coder",
        user_prompt="Generate code"
    )

    # Verify extra args were added to command
    call_args = mock_popen.call_args
    cmd = call_args[0][0]
    assert "--tools" in cmd
    assert "file_read,shell" in cmd
    assert "--verbose" in cmd


@patch('subprocess.Popen')
def test_subprocess_provider_failure(mock_popen):
    """Test subprocess provider handling failure"""
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.communicate.return_value = (
        "",
        "Error: command failed"
    )
    mock_popen.return_value = mock_proc

    provider = SubprocessLLMProvider(command="qwen")

    try:
        result = provider.generate(
            system_prompt="System",
            user_prompt="User"
        )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "Subprocess LLM failed with code 1" in str(e)
        assert "Error: command failed" in str(e)


@patch('subprocess.Popen')
def test_subprocess_provider_timeout(mock_popen):
    """Test subprocess provider timeout handling"""
    mock_proc = MagicMock()
    mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd=["qwen"], timeout=10)
    mock_popen.return_value = mock_proc

    provider = SubprocessLLMProvider(command="qwen", timeout=10)

    try:
        result = provider.generate(
            system_prompt="System",
            user_prompt="User"
        )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "timed out after 10 seconds" in str(e)


@patch('subprocess.Popen')
def test_subprocess_provider_not_found(mock_popen):
    """Test subprocess provider when command not found"""
    mock_popen.side_effect = FileNotFoundError()

    provider = SubprocessLLMProvider(command="nonexistent_llm")

    try:
        result = provider.generate(
            system_prompt="System",
            user_prompt="User"
        )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not found" in str(e)
        assert "nonexistent_llm" in str(e)


def test_llm_client_subprocess_provider():
    """Test LLMClient with subprocess provider"""
    client = LLMClient(
        provider="subprocess",
        model="qwen",
        timeout=60,
        tools="file_read,file_write"
    )

    assert client.provider_name == "subprocess"
    assert isinstance(client.provider, SubprocessLLMProvider)
    assert client.provider.command == "qwen"
    assert client.provider.timeout == 60


def test_llm_client_subprocess_with_custom_command():
    """Test LLMClient with custom subprocess command"""
    client = LLMClient(
        provider="subprocess",
        command="custom-llm",
        timeout=120
    )

    assert client.provider.command == "custom-llm"
    assert client.provider.timeout == 120


@patch('subprocess.Popen')
def test_llm_client_subprocess_generate(mock_popen):
    """Test end-to-end generation through LLMClient"""
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (
        '{"result": "success", "code": "print(\'hello\')"}',
        ""
    )
    mock_popen.return_value = mock_proc

    client = LLMClient(provider="subprocess", model="qwen")
    result = client.generate(
        system_prompt="You are a Python expert",
        user_prompt="Generate hello world code",
        response_format="json"
    )

    assert isinstance(result, dict)
    assert "result" in result or "code" in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
