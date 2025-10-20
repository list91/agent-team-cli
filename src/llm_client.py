#!/usr/bin/env python3
"""
LLM Client - Universal interface for multiple LLM providers.

Supports OpenAI, Anthropic, Ollama, Subprocess CLI tools, and Mock for testing.
Provides unified API for all agents to generate intelligent responses.
"""
import json
import os
import re
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000) -> str:
        """Generate text completion from prompts"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4, GPT-3.5, etc.)"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000) -> str:
        """Generate completion using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude)"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000) -> str:
        """Generate completion using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")


class OllamaProvider(LLMProvider):
    """Ollama provider for local models"""

    def __init__(self, model: str = "qwen2.5-coder:7b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("Requests package not installed. Run: pip install requests")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000) -> str:
        """Generate completion using Ollama API"""
        try:
            url = f"{self.host}/api/generate"

            # Combine system and user prompts for Ollama
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            response = self.requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")


class SubprocessLLMProvider(LLMProvider):
    """
    Subprocess provider for local LLM CLI tools (like qwen, claude-code, etc.)

    Executes LLM as a subprocess command and captures output.
    Useful for integrating with CLI-based LLM tools.
    """

    def __init__(self, command: str = "qwen", timeout: int = 300, **kwargs):
        """
        Initialize subprocess LLM provider.

        :param command: Base command to execute (e.g., "qwen", "claude")
        :param timeout: Timeout in seconds for subprocess execution
        :param kwargs: Additional command-line arguments
        """
        import subprocess
        self.subprocess = subprocess
        self.command = command
        self.timeout = timeout
        self.extra_args = kwargs

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000) -> str:
        """
        Generate completion by using qwen CLI as an AGENT to create output files.

        qwen CLI is an interactive coding agent (like Claude Code), not a simple LLM API.
        Strategy: Ask qwen to create a response.json file with the answer.

        :param system_prompt: System prompt defining role
        :param user_prompt: User prompt with task
        :param temperature: Sampling temperature
        :param max_tokens: Maximum tokens to generate
        :return: Content of the file created by qwen
        """
        import logging
        import tempfile
        from pathlib import Path
        logger = logging.getLogger(__name__)

        try:
            # УПРОЩЕННЫЙ подход: qwen возвращает JSON в stdout
            # НЕ просим создать файл - это усложняет промпт
            task = f"""{system_prompt}

{user_prompt}

Respond with ONLY valid JSON. No explanations, no markdown, just JSON."""

            # qwen требует работы в project directory (VS Code workspace)
            project_root = Path.cwd()

            # Use qwen with approval-mode=yolo (auto-approve file operations if needed)
            cmd = [
                self.command,
                "-p", task,
                "--approval-mode", "yolo"
            ]

            logger.info(f"[SubprocessLLM/qwen] Starting qwen")

            # Execute qwen from project root
            proc = self.subprocess.Popen(
                cmd,
                cwd=project_root,  # ← ВАЖНО: запускаем из project root
                stdout=self.subprocess.PIPE,
                stderr=self.subprocess.PIPE,
                text=True,
                encoding='utf-8',  # ← FIX: Windows cp1251 -> UTF-8
                errors='replace'   # ← Replace undecodable chars instead of crash
            )

            # Wait for qwen to finish
            stdout, stderr = proc.communicate(timeout=self.timeout)

            logger.info(f"[SubprocessLLM/qwen] stdout length: {len(stdout)} chars")
            logger.info(f"[SubprocessLLM/qwen] First 500 chars of stdout:\n{stdout[:500]}")
            if stderr:
                logger.debug(f"[SubprocessLLM/qwen] stderr: {stderr[:500]}")

            # Parse stdout directly
            if stdout:
                logger.info(f"[SubprocessLLM/qwen] ✅ Got response, returning to parser")
                return stdout.strip()
            else:
                raise RuntimeError(f"qwen returned no output (stderr: {stderr[:200]})")

        except self.subprocess.TimeoutExpired:
            proc.kill()
            raise RuntimeError(f"qwen agent timed out after {self.timeout} seconds")
        except FileNotFoundError:
            raise RuntimeError(f"qwen command '{self.command}' not found. Ensure it's installed and in PATH.")
        except Exception as e:
            raise RuntimeError(f"qwen agent error: {str(e)}")


class MockProvider(LLMProvider):
    """Mock provider for testing - returns predefined responses"""

    def __init__(self):
        self.call_count = 0
        self.last_prompts = []

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000) -> str:
        """Generate mock completion for testing"""
        self.call_count += 1
        self.last_prompts.append({"system": system_prompt, "user": user_prompt})

        # Smart mock responses based on prompt content
        user_lower = user_prompt.lower()

        # Task decomposition mock
        if "какие агенты нужны" in user_lower or "which agents" in user_lower:
            return json.dumps({
                "agents": ["coder", "documenter", "tester"],
                "complexity": 4,
                "strategy": "flat_delegation",
                "bridges": [
                    {"from": "coder", "to": "documenter", "type": "api_spec"}
                ],
                "reasoning": "FastAPI task requires code generation, documentation, and testing"
            }, ensure_ascii=False)

        # Documentation generation mock (check BEFORE code generation!)
        elif "comprehensive documentation" in user_lower or ("documentation" in user_lower and "generate" in user_lower):
            return '''```markdown
# README.md

# Task Management API

REST API for managing tasks with FastAPI.

## Features

- Create, read, update, delete tasks
- RESTful API design
- OpenAPI documentation
- Docker support

## Installation

    pip install fastapi uvicorn pydantic

## Usage

Run the server:

    python main.py

Or with Docker:

    docker build -t task-api .
    docker run -p 8000:8000 task-api

## API Endpoints

- GET / - Root endpoint
- GET /tasks - Get all tasks
- POST /tasks - Create new task
- GET /tasks/{task_id} - Get specific task
- PUT /tasks/{task_id} - Update task
- DELETE /tasks/{task_id} - Delete task

## OpenAPI Documentation

Visit http://localhost:8000/docs for interactive API documentation.
```

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: Task Management API
  version: 1.0.0
  description: A simple API for managing tasks
paths:
  /:
    get:
      summary: Root endpoint
      responses:
        '200':
          description: Welcome message
  /tasks:
    get:
      summary: Get all tasks
      responses:
        '200':
          description: List of tasks
    post:
      summary: Create new task
      responses:
        '200':
          description: Task created
```'''

        # Code generation mock
        elif "сгенерируй" in user_lower or ("generate" in user_lower and "code" in user_lower) or ("python" in user_lower and "generate" in user_lower):
            if "fastapi" in user_lower or "api" in user_lower or "service" in user_lower:
                return '''```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Task Management API", version="1.0.0")

# Pydantic models
class Task(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    completed: bool = False

class TaskCreate(BaseModel):
    title: str
    description: str

# In-memory storage
tasks_db = []
next_id = 1

@app.get("/")
def root():
    return {"message": "Welcome to Task Management API"}

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return tasks_db

@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    global next_id
    new_task = Task(id=next_id, title=task.title, description=task.description)
    tasks_db.append(new_task)
    next_id += 1
    return new_task

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    for task in tasks_db:
        if task.id == task_id:
            return task
    return {"error": "Task not found"}

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: Task):
    for i, task in enumerate(tasks_db):
        if task.id == task_id:
            tasks_db[i] = task_update
            return task_update
    return {"error": "Task not found"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    global tasks_db
    tasks_db = [t for t in tasks_db if t.id != task_id]
    return {"message": f"Task {task_id} deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn pydantic

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```'''
            else:
                return '''```python
# Generated Python code
def process_task():
    """Process the given task"""
    return {"status": "success", "message": "Task processed"}
```'''

        # Default response
        else:
            return json.dumps({
                "status": "success",
                "message": "Task analyzed and processed",
                "details": "Mock LLM response for testing"
            }, ensure_ascii=False)


class LLMClient:
    """
    Universal LLM client that works with multiple providers.

    Usage:
        client = LLMClient(provider="openai", model="gpt-4")
        response = client.generate(system_prompt="You are...", user_prompt="Do...")
    """

    def __init__(self, provider: str = "mock", model: Optional[str] = None,
                 api_key: Optional[str] = None, **kwargs):
        """
        Initialize LLM client with specified provider.

        :param provider: Provider name ("openai", "anthropic", "ollama", "subprocess", "mock")
        :param model: Model name (provider-specific)
        :param api_key: API key (for OpenAI/Anthropic)
        :param kwargs: Additional provider-specific arguments
        """
        self.provider_name = provider.lower()

        # Auto-detect API keys from environment if not provided
        if api_key is None:
            if self.provider_name == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider_name == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")

        # Initialize appropriate provider
        if self.provider_name == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass api_key parameter")
            self.provider = OpenAIProvider(api_key, model or "gpt-4")

        elif self.provider_name == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env var or pass api_key parameter")
            self.provider = AnthropicProvider(api_key, model or "claude-3-5-sonnet-20241022")

        elif self.provider_name == "ollama":
            host = kwargs.get("host", "http://localhost:11434")
            self.provider = OllamaProvider(model or "qwen2.5-coder:7b", host)

        elif self.provider_name == "subprocess":
            command = kwargs.get("command", model or "qwen")
            timeout = kwargs.get("timeout", 300)
            # Pass remaining kwargs as extra CLI arguments
            extra_kwargs = {k: v for k, v in kwargs.items() if k not in ["command", "timeout"]}
            self.provider = SubprocessLLMProvider(command=command, timeout=timeout, **extra_kwargs)

        elif self.provider_name == "mock":
            self.provider = MockProvider()

        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'openai', 'anthropic', 'ollama', 'subprocess', or 'mock'")

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
                 max_tokens: int = 4000, response_format: str = "text") -> Any:
        """
        Generate text using the configured LLM provider.

        :param system_prompt: System prompt defining agent role
        :param user_prompt: User prompt with task details
        :param temperature: Sampling temperature (0.0-1.0)
        :param max_tokens: Maximum tokens to generate
        :param response_format: Expected format ("text" or "json")
        :return: Generated text or parsed JSON
        """
        raw_response = self.provider.generate(system_prompt, user_prompt, temperature, max_tokens)

        if response_format == "json":
            return self._parse_json_response(raw_response)

        return raw_response

    def _parse_json_response(self, response: str) -> Dict:
        """
        Extract and parse JSON from LLM response with robust parsing.
        Handles code blocks, plain JSON, and extra text around JSON.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"[JSONParser] Parsing response of length {len(response)}")

        # Strategy 1: Try code blocks with balanced braces
        code_block_patterns = [
            r'```json\s*(\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})\s*```',  # ```json {...} ```
            r'```\s*(\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})\s*```',      # ``` {...} ```
        ]

        for pattern in code_block_patterns:
            matches = re.finditer(pattern, response, re.DOTALL)
            for match in matches:
                json_str = match.group(1)
                try:
                    parsed = json.loads(json_str)
                    logger.debug(f"[JSONParser] Successfully parsed from code block")
                    return parsed
                except json.JSONDecodeError:
                    continue

        # Strategy 2: Find all potential JSON objects by balancing braces
        potential_jsons = []
        brace_count = 0
        start_idx = None

        for i, char in enumerate(response):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx is not None:
                    potential_jsons.append(response[start_idx:i+1])
                    start_idx = None

        logger.debug(f"[JSONParser] Found {len(potential_jsons)} potential JSON objects")

        # Strategy 3: Try parsing each potential JSON, prefer ones with 'agents' field
        candidates = []
        for json_str in potential_jsons:
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    # Score based on expected fields
                    score = 0
                    if 'agents' in parsed:
                        score += 100
                    if 'complexity' in parsed:
                        score += 10
                    if 'strategy' in parsed:
                        score += 10
                    candidates.append((score, parsed))
                    logger.debug(f"[JSONParser] Valid JSON found (score: {score}, keys: {list(parsed.keys())})")
            except json.JSONDecodeError:
                continue

        # Return highest scoring candidate
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_json = candidates[0]
            logger.info(f"[JSONParser] Selected JSON with score {best_score}")
            return best_json

        # Strategy 4: Try parsing entire response as JSON
        try:
            parsed = json.loads(response.strip())
            logger.debug(f"[JSONParser] Parsed entire response as JSON")
            return parsed
        except json.JSONDecodeError:
            pass

        # Fallback: return error structure
        logger.warning(f"[JSONParser] Failed to extract valid JSON from response")
        logger.debug(f"[JSONParser] Raw response:\n{response[:500]}")
        return {
            "error": "Failed to parse JSON from LLM response",
            "raw_response": response[:1000]  # Truncate for logging
        }


def create_llm_client_from_config(config) -> LLMClient:
    """
    Create LLM client from configuration object.

    :param config: Configuration object with llm settings
    :return: Configured LLMClient instance
    """
    llm_config = getattr(config, "llm", {})

    if isinstance(llm_config, dict):
        provider = llm_config.get("provider", "mock")
        model = llm_config.get("model")
        api_key = llm_config.get("api_key")
        temperature = llm_config.get("temperature", 0.7)
        max_tokens = llm_config.get("max_tokens", 4000)

        # Handle ${ENV_VAR} syntax in API key
        if api_key and api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.getenv(env_var)

        # Collect provider-specific kwargs
        kwargs = {}

        # Ollama settings
        if provider == "ollama":
            kwargs["host"] = llm_config.get("ollama_host", "http://localhost:11434")

        # Subprocess settings
        elif provider == "subprocess":
            kwargs["command"] = llm_config.get("subprocess_command", model or "qwen")
            kwargs["timeout"] = llm_config.get("subprocess_timeout", 300)
            # Add extra args from config
            extra_args = llm_config.get("subprocess_extra_args", {})
            if extra_args:
                kwargs.update(extra_args)

    else:
        # Fallback to mock if config not properly structured
        provider = "mock"
        model = None
        api_key = None
        kwargs = {}

    return LLMClient(provider=provider, model=model, api_key=api_key, **kwargs)
