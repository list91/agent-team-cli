# Интеграция qwen CLI как LLM-провайдера для MSP Orchestrator

## Проблема

qwen CLI - это интерактивный coding agent (аналог Claude Code), а НЕ простой LLM API:
- Ожидает диалога с пользователем
- Планирует действия и просит подтверждения
- Создает файлы, выполняет команды
- Возвращает результат работы, а не генерированный текст

При попытке использовать qwen как text generator (`qwen -p "prompt" -y`):
- Возвращает: "Понял. Я буду действовать... Что вы хотите, чтобы я сделал?"
- Зависает в ожидании интерактивного ввода
- Не возвращает JSON в stdout

## Решение: Agent-Based подход

Вместо того чтобы заставлять qwen генерировать текст, используем его КАК АГЕНТА:

### Архитектура

```
Master/Coder/Documenter Agent
    ↓
LLMClient.generate(system_prompt, user_prompt)
    ↓
SubprocessLLMProvider (qwen)
    ↓
1. Создать temp directory
2. Попросить qwen создать файл response.json с ответом
3. qwen выполняет задачу: пишет файл
4. Прочитать response.json
5. Вернуть содержимое как "generated" текст
```

### Реализация

#### src/llm_client.py:150-226 - SubprocessLLMProvider.generate()

```python
def generate(self, system_prompt, user_prompt, temperature, max_tokens):
    with tempfile.TemporaryDirectory(prefix="qwen_llm_") as tmpdir:
        output_file = Path(tmpdir) / "response.json"

        # Reformulate as agent task: create a file
        task = f"""{system_prompt}

{user_prompt}

IMPORTANT TASK: Create a file named 'response.json' in the current directory with your complete response.
The file MUST contain ONLY valid JSON with all required fields.
Use file operations to write this file.
After creating the file, your task is complete."""

        # Run qwen with auto-approval of file operations
        cmd = [
            self.command,
            "-p", task,
            "--approval-mode", "yolo"  # Auto-approve все file writes
        ]

        proc = subprocess.Popen(cmd, cwd=tmpdir, ...)
        stdout, stderr = proc.communicate(timeout=self.timeout)

        # Read the file qwen created
        if output_file.exists():
            response = output_file.read_text()
            return response.strip()
        else:
            # Fallback to stdout if file wasn't created
            return stdout.strip()
```

### Преимущества этого подхода

1. **Работа с природой qwen** - используем его как агента, а не боремся с интерактивностью
2. **Надежность** - qwen создает файл, мы просто читаем его
3. **Изоляция** - каждый вызов в отдельной temp директории
4. **Совместимость** - остальная система не изменилась, только SubprocessLLMProvider

## Что было сделано

### 1. Создан SubprocessLLMProvider с agent-based логикой
**Файл**: `src/llm_client.py:128-226`

**Ключевые особенности**:
- Временная директория для каждого вызова
- Переформулирование промпта как task: "создай файл response.json"
- Использование `--approval-mode yolo` для auto-approval
- Чтение результата из файла
- Fallback на stdout если файл не создан

### 2. Улучшен JSON парсинг (на случай fallback)
**Файл**: `src/llm_client.py:496-581`

**Стратегии парсинга**:
1. Code blocks с балансировкой скобок
2. Поиск всех JSON объектов в тексте (balance braces)
3. Скоринг кандидатов (приоритет объектам с `agents`)
4. Fallback: парсинг всей строки

```python
# Скоринг
score = 0
if 'agents' in parsed:
    score += 100  # Критически важное поле
if 'complexity' in parsed:
    score += 10
if 'strategy' in parsed:
    score += 10
```

### 3. Усилен промпт в Master
**Файл**: `agents/master/master.py:462-502`

Добавлена CRITICAL INSTRUCTION:
```
CRITICAL INSTRUCTION: You MUST respond with ONLY a valid JSON object.
Do NOT include any explanatory text, markdown formatting, or additional
commentary before or after the JSON. Your entire response should be parseable as JSON.

Required JSON format:
{...}

Remember: Output ONLY the JSON object, nothing else.
```

### 4. Конфигурация
**Файл**: `config.yaml`

```yaml
llm:
  provider: "subprocess"
  subprocess_command: "C:\\Users\\Дарья\\AppData\\Roaming\\npm\\qwen.cmd"
  subprocess_timeout: 300
  temperature: 0.7
  max_tokens: 4000
```

### 5. Документация

Created:
- `JSON_PARSING_IMPROVEMENTS.md` - детали улучшений парсинга
- `OLLAMA_MIGRATION_GUIDE.md` - альтернатива (если qwen не подойдет)
- `SUBPROCESS_LLM_USAGE.md` - руководство по subprocess provider
- `QWEN_AGENT_INTEGRATION_SUMMARY.md` (этот файл)

## Тестирование

### Unit тесты
**Файл**: `tests/unit/test_subprocess_llm_client.py`
- ✅ 10/10 тестов проходят
- Моки subprocess вызовов
- Проверка формата команды, таймаутов, ошибок

### Integration тесты
**Файл**: `tests/integration/test_subprocess_provider_integration.py`
- ✅ 6/6 тестов проходят
- Проверка что Master, Coder, Documenter используют subprocess
- Проверка формата команды qwen

### Реальное использование

```bash
# Простая задача
python msp-run.py --task "Создай файл hello.py с функцией print Hello World" --workdir ./output_test

# ML задача с Redis и Docker
python msp-run.py --task "Создай production-ready Python-сервис для анализа тональности..." --workdir ./output_ml
```

## Как это работает (пример)

### 1. Master анализирует задачу

```python
# Master вызывает
analysis = self.llm_client.generate(
    system_prompt="You are a Master Orchestrator in an MSP system...",
    user_prompt="Task: Создай Python API...\nAvailable Agents: coder, documenter...",
    response_format="json"
)
```

### 2. SubprocessLLMProvider запускает qwen

```bash
# Создает /tmp/qwen_llm_xyz/
# Запускает:
C:\...\qwen.cmd \
    -p "You are a Master Orchestrator... IMPORTANT TASK: Create a file named 'response.json'..." \
    --approval-mode yolo

# qwen получает задачу:
# "Проанализируй задачу и создай файл response.json с таким JSON: {agents: [...], complexity: X, ...}"
```

### 3. qwen работает как агент

```
qwen понимает: нужно создать файл response.json
qwen пишет файл с содержимым:
{
  "complexity": 4,
  "strategy": "flat_delegation",
  "agents": [
    {"name": "coder", "subtask": "Create Python API", "priority": 1, "tools": ["file_write", "shell"]},
    {"name": "documenter", "subtask": "Document API", "priority": 2, "tools": ["file_write"]}
  ],
  "bridges": [],
  "reasoning": "API task requires code + docs"
}
```

### 4. SubprocessLLMProvider читает результат

```python
if output_file.exists():
    response = output_file.read_text()  # Читаем JSON созданный qwen
    return response.strip()
```

### 5. Master получает JSON

```python
# response_format="json" → автоматически парсится
analysis = {
    "complexity": 4,
    "agents": [...],
    ...
}

# Master создает subtasks
for agent_spec in analysis['agents']:
    subtasks.append({...})
```

## Ключевые особенности

### ✅ Преимущества

1. **Работает с qwen CLI** - используем его естественным образом (как агента)
2. **Изолированно** - каждый вызов в отдельной temp директории
3. **Надежно** - файл либо создан, либо нет (нет проблем с парсингом stdout)
4. **Универсально** - работает для любых агентов (Master, Coder, Documenter)
5. **Полностью LLM-driven** - никакого hardcode, все через qwen

### ⚠️ Потенциальные проблемы

1. **Скорость** - qwen запускается для каждого вызова (~30-60 сек на задачу)
2. **Надежность qwen** - зависит от того, понимает ли qwen инструкцию "создай файл"
3. **Timeout** - если qwen зависнет, нужен большой timeout (300 сек)

## Альтернативы

Если qwen agent подход не заработает:

### Вариант 1: Ollama (рекомендуется)
```yaml
llm:
  provider: "ollama"
  model: "qwen2.5-coder:7b"  # Та же модель!
  ollama_host: "http://localhost:11434"
```

**Плюсы**: HTTP API, гарантированный JSON, та же модель qwen
**Минусы**: Требует установки Ollama

### Вариант 2: OpenAI/Anthropic
```yaml
llm:
  provider: "openai"  # или "anthropic"
  model: "gpt-4o-mini"  # или "claude-3-5-sonnet"
  api_key: "${OPENAI_API_KEY}"
```

**Плюсы**: Высокое качество, надежно
**Минусы**: Платно

## Статус

✅ **Реализовано**:
- SubprocessLLMProvider с agent-based логикой
- Интеграция во все агенты (Master, Coder, Documenter)
- Улучшенный JSON парсинг
- Unit и integration тесты

🔄 **Тестируется**:
- Реальные вызовы qwen CLI
- Создание файлов qwen-ом
- Парсинг результатов

⏳ **Следующие шаги** (если текущий подход не сработает):
- Переключиться на Ollama с той же моделью qwen2.5-coder
- Или использовать OpenAI/Anthropic API

## Вывод

Система MSP Orchestrator теперь использует qwen CLI КАК АГЕНТА для выполнения LLM задач.
Вместо генерации текста в stdout, qwen создает файлы с результатами, которые мы читаем.

Это соответствует природе qwen как coding agent и должно работать надежнее чем попытки
заставить его вести себя как простой text generator.

Все агенты (Master, Coder, Documenter) используют одну и ту же логику через
`create_llm_client_from_config(config)`, что обеспечивает единообразие и соответствие
требованиям QWEN.md (никакого hardcode, все через LLM).
