# Subprocess LLM Provider - Usage Guide

## Overview

The Subprocess LLM Provider allows MSP Orchestrator to use **local CLI-based LLM tools** (like `qwen`, `claude-code`, etc.) instead of HTTP APIs. This provides:

- **True LLM-driven orchestration** without mocked responses
- **Privacy** - all processing happens locally
- **Flexibility** - use any CLI tool that follows the standard interface
- **No API keys or rate limits**

## Supported CLI Tools

- **qwen** - Qwen/Alibaba Cloud LLM CLI
- **claude-code** - Anthropic Claude for coding
- **Any custom CLI tool** that accepts:
  - `run --task <prompt> --temperature <t> --max-tokens <n>`

## Installation

### 1. Install qwen CLI (recommended)

```bash
# Install qwen CLI tool
pip install qwen-cli

# Or download from official repo
# https://github.com/QwenLM/Qwen-CLI
```

### 2. Verify installation

```bash
# Test qwen is accessible
qwen --version

# Try a simple generation
qwen run --task "Write hello world in Python"
```

## Configuration

### Option 1: Update config.yaml

```yaml
llm:
  provider: "subprocess"
  model: null  # Not used for subprocess
  subprocess_command: "qwen"
  subprocess_timeout: 300
  subprocess_extra_args:
    tools: "file_read,file_write,shell"
```

### Option 2: Copy example config

```bash
# Copy the example configuration
cp config.subprocess-example.yaml config.yaml

# Edit as needed
nano config.yaml
```

## Usage Examples

### Example 1: Simple Web API

```bash
python msp-run.py --task "Create a REST API with FastAPI for managing tasks (CRUD operations). Include Dockerfile and documentation." --workdir ./output-api
```

### Example 2: ML Service (Your Original Request!)

```bash
python msp-run.py --task "Создай production-ready Python-сервис для анализа тональности отзывов. Он должен:
- принимать JSON с текстом через POST /analyze
- использовать модель distilbert-base-uncased-finetuned-sst-2-english
- кэшировать результаты в Redis (порт 6379)
- логировать всё в формате JSON
- иметь Dockerfile, OpenAPI-документацию и unit-тесты
Проверь, что всё работает: запусти контейнер, отправь тестовый запрос, убедись, что Redis используется.
Если что-то не так — исправь и протестируй снова" --workdir ./output-ml-service
```

### Example 3: DevOps Pipeline

```bash
python msp-run.py --task "Create a CI/CD pipeline with:
- GitHub Actions workflow
- Docker build and push
- Kubernetes deployment manifests
- Helm chart
- Monitoring with Prometheus
Include complete README with setup instructions" --workdir ./output-devops
```

## How It Works

1. **Master Orchestrator** receives your task
2. **LLM analyzes** task via subprocess call to `qwen`
3. **Master decomposes** task into subtasks (coder, documenter, tester, etc.)
4. **Each agent** calls LLM via subprocess for their specific work
5. **Agents coordinate** via bridges (inter-agent communication)
6. **Results are validated** by tester agent
7. **Final output** is produced in workdir

## Architecture

```
User Task
    ↓
Master Orchestrator (uses LLM via subprocess)
    ↓ decomposes
    ├─ Coder Agent (uses LLM via subprocess)
    │   → generates code
    │   → sends to Documenter via bridge
    ├─ Documenter Agent (uses LLM via subprocess)
    │   → generates docs
    │   → receives code context from Coder
    └─ Tester Agent (validates output)
        → checks syntax, runs tests
        → provides feedback for fixes
```

## Advanced Configuration

### Custom CLI Tool

```yaml
llm:
  provider: "subprocess"
  subprocess_command: "my-custom-llm"  # Your CLI tool
  subprocess_timeout: 600  # 10 minutes for complex tasks
  subprocess_extra_args:
    model: "custom-model-v2"
    temperature: 0.8
    context_window: 8000
```

### Debugging

Enable verbose logging:

```yaml
log_level: DEBUG
subprocess_extra_args:
  verbose: true
  debug: true
```

## Comparison: Subprocess vs Other Providers

| Provider | Use Case | Pros | Cons |
|----------|----------|------|------|
| **subprocess** | Local LLM CLI tools | Privacy, no rate limits, flexible | Requires CLI tool installed |
| **ollama** | Ollama local models | HTTP API, multiple models | Requires Ollama server running |
| **openai** | OpenAI GPT models | Best quality, widely supported | Costs money, API key needed |
| **anthropic** | Claude models | High quality, long context | Costs money, API key needed |
| **mock** | Testing only | No setup, fast | Not real LLM, hardcoded responses |

## Troubleshooting

### Command not found

```bash
# Error: qwen command not found
# Solution: Add qwen to PATH or use full path
subprocess_command: "/usr/local/bin/qwen"
```

### Timeout errors

```bash
# Error: Subprocess LLM timed out
# Solution: Increase timeout for complex tasks
subprocess_timeout: 600  # 10 minutes
```

### Invalid JSON responses

Some CLI tools may not return JSON by default. Ensure your tool:
- Returns structured output
- Follows expected format
- Can be parsed by MSP system

## Performance Tips

1. **Use SSD for workdir** - faster file I/O for agents
2. **Increase timeout for complex tasks** - ML services, large codebases
3. **Enable caching** in your CLI tool if supported
4. **Monitor resource usage** - qwen may use significant RAM/CPU

## Real vs Mock LLM

### With Mock (default)
- Fast testing
- Predictable results
- **Limited to FastAPI-style tasks**
- **Not truly universal**

### With Subprocess (qwen)
- **True LLM intelligence**
- **Adapts to any task type** (web, ML, DevOps, data science)
- **Dynamic code generation** (not templates)
- **Context-aware responses**
- Slower (LLM inference time)

## Next Steps

1. Install qwen CLI
2. Copy config example: `cp config.subprocess-example.yaml config.yaml`
3. Test with simple task: `python msp-run.py --task "Write hello world Python script" --workdir ./test`
4. Try complex task (ML service, microservices, etc.)
5. Monitor output in workdir and agent scratchpads

## FAQ

**Q: Can I use GPT-4 via subprocess?**
A: Yes, if you create a CLI wrapper for OpenAI API. Or use `provider: "openai"` directly.

**Q: Is subprocess slower than HTTP API?**
A: Slightly, due to process startup overhead. For heavy tasks (>1min LLM time), overhead is negligible.

**Q: Can multiple agents run in parallel?**
A: Yes! Master spawns agents as subprocess, they run concurrently.

**Q: What if my CLI tool has different arguments?**
A: Customize in `SubprocessLLMProvider` class in `src/llm_client.py:166-171`

## Support

- Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Docs: [QWEN.md](./QWEN.md) - Full system specification
- Tests: `pytest tests/unit/test_subprocess_llm_client.py -v`
