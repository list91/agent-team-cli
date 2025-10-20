# Почему qwen CLI не подходит для MSP Orchestrator: Детальный анализ

## TL;DR

**qwen CLI - это интерактивный coding assistant (как Claude Code), а НЕ LLM API.**

Он создан для работы С пользователем в терминале, а не ДЛЯ программных вызовов.

## Конкретные проблемы

### 1. qwen возвращает диалоговые сообщения вместо выполнения задач

#### Что мы хотели:
```bash
qwen -p "Create a file response.json with this JSON: {\"agents\": [...]}" -y
# Ожидали: qwen создаст файл response.json
```

#### Что получили:
```
Понял. Я буду действовать как мастер-оркестратор в MSP-системе.
Что вы хотите, чтобы я сделал?
```

**Проблема**: qwen воспринимает промпт как начало ДИАЛОГА, а не как КОМАНДУ.

#### Реальный вывод qwen (из наших тестов):

```bash
$ qwen -p "Return JSON: {\"test\": \"success\"}" -y
Понял. Я буду действовать как мастер-оркестратор в MSP-системе.
Что вы хотите, чтобы я сделал?

# Файл response.json НЕ СОЗДАН
# JSON в stdout НЕ ВЫВЕДЕН
# qwen ждет следующего сообщения от пользователя
```

### 2. qwen требует VS Code workspace (Directory Mismatch)

#### Ошибка при запуске из temp директории:

```
[ERROR] [IDEClient] Directory mismatch.
Qwen Code is running in a different location than the open workspace in VS Code.
Please run the CLI from one of the following directories:
c:\sts\projects\agents\agent-team-cli
```

**Проблема**: qwen CLI интегрирован с VS Code и требует:
- Открытый VS Code workspace
- Запуск из директории workspace
- Наличие .vscode конфигурации

**Почему это критично**:
- Нельзя запустить qwen из произвольной директории
- Нельзя создать temp workspace для изолированных вызовов
- qwen "знает" где открыт VS Code и проверяет это

### 3. qwen не выполняет задачи в non-interactive режиме

#### Тест с разными подходами:

**Попытка 1: Прямой вызов с -p**
```bash
qwen -p "Create file test.txt with content 'hello'" -y
```
**Результат**: Текст в stdout, файл НЕ создан

**Попытка 2: С --approval-mode yolo**
```bash
qwen -p "Create file test.txt" --approval-mode yolo
```
**Результат**:
```
Cannot use both --yolo (-y) and --approval-mode together.
Use --approval-mode=yolo instead.
```

**Попытка 3: С --approval-mode=yolo (правильный синтаксис)**
```bash
qwen -p "Create file .qwen_temp/response_abc.json with JSON" --approval-mode=yolo
```
**Результат**:
- Process запускается ~30 секунд
- Возвращает exit code 0
- Файл .qwen_temp/response_abc.json НЕ СОЗДАН
- stdout содержит диалоговое сообщение

### 4. Архитектурное несоответствие

#### Как работает qwen CLI (по дизайну):

```
User → Terminal
  ↓
qwen CLI starts interactive session
  ↓
qwen: "What do you want me to do?"
  ↓
User: "Create a FastAPI service"
  ↓
qwen: [Analyzes task]
qwen: "I'll create these files: main.py, Dockerfile, ..."
qwen: "Approve? [y/n]"
  ↓
User: "y"
  ↓
qwen: [Creates files]
qwen: [Shows results]
qwen: "What else?"
  ↓
User: "Add tests"
  ...
```

**Это многошаговый диалог**, а не single-shot API call.

#### Как мы пытались использовать:

```python
# Single-shot API call
response = subprocess.Popen(
    ["qwen", "-p", prompt, "--approval-mode=yolo"],
    stdout=PIPE
).communicate()

# Ожидали: response содержит JSON или файл создан
# Получили: "Что вы хотите, чтобы я сделал?"
```

**Несовместимость**: qwen ожидает stdin stream для продолжения диалога, а мы даем один промпт и ждем результата.

### 5. qwen CLI vs LLM API - фундаментальная разница

| Характеристика | LLM API (OpenAI, Anthropic, Ollama) | qwen CLI |
|---------------|--------------------------------------|----------|
| **Назначение** | Генерация текста по промпту | Интерактивный coding assistant |
| **Вызов** | HTTP POST /v1/chat/completions | Terminal interactive session |
| **Ввод** | Single prompt → Single response | Continuous dialogue |
| **Вывод** | JSON/text в response body | Terminal UI с вопросами/ответами |
| **Действия** | Только генерация текста | Создание файлов, выполнение команд |
| **Approval** | N/A | Требует подтверждения действий |
| **Session** | Stateless | Stateful (помнит контекст) |
| **Subprocess** | ✅ Подходит (ollama serve) | ❌ Не подходит |

### 6. Конкретный пример: что возвращает qwen

#### Наш промпт для Master Orchestrator:

```python
task = """You are a Master Orchestrator in an MSP system.

Analyze this task and determine which agents are needed.

Task: Создай простой Python REST API с одним endpoint /hello

Available Agents:
- coder: basic file operations, code generation
- documenter: documentation writing
- echo: basic task execution
- tester: testing and validation

CRITICAL INSTRUCTION: Create a file named '.qwen_temp/response_abc123.json'
with your complete response. The file MUST contain ONLY valid JSON.

Required JSON format:
{
  "complexity": 4,
  "strategy": "flat_delegation",
  "agents": [
    {"name": "coder", "subtask": "...", "priority": 1, "tools": ["file_write"]}
  ],
  "bridges": [],
  "reasoning": "..."
}
"""
```

#### Что вернул qwen (реальный stdout):

```
Понял. Я буду действовать как мастер-оркестратор в MSP-системе.
Что вы хотите, чтобы я сделал?
```

**Длина**: 167 символов
**JSON объектов найдено**: 0
**Файлов создано**: 0

#### Почему так происходит:

1. qwen читает промпт
2. qwen "понимает" что ему дали роль (Master Orchestrator)
3. qwen переходит в режим ожидания следующей инструкции
4. qwen НЕ выполняет инструкцию "Create a file", потому что:
   - Это часть ПРОМПТА, а не КОМАНДА пользователя
   - qwen различает "system prompt" и "user instruction"
   - В интерактивном режиме он ждет четкой команды после установки роли

### 7. Почему --approval-mode=yolo не помогает

#### Что делает --approval-mode=yolo:

```javascript
// Из исходников qwen CLI (концептуально):
if (approvalMode === 'yolo') {
  // Auto-approve all TOOL CALLS
  when (agent.planAction()) {
    if (action.type === 'file_write' || action.type === 'shell_exec') {
      return 'approved'; // Без запроса у пользователя
    }
  }
}
```

**НО**: qwen должен СНАЧАЛА понять что нужно ДЕЙСТВИЕ, а не ответ.

#### В нашем случае:

```python
qwen -p "Create file response.json" --approval-mode=yolo
```

qwen воспринимает это как:
1. User: "Create file response.json"
2. qwen: "OK, I understand you want me to create a file"
3. qwen: "What should I do next?" ← ждет продолжения диалога

qwen НЕ ПЕРЕХОДИТ к действию, потому что:
- Недостаточно контекста (где создавать? какое содержимое?)
- В интерактивном режиме он бы спросил уточняющие вопросы
- В non-interactive режиме он просто останавливается

### 8. Proof: qwen работает ТОЛЬКО в интерактивном режиме

#### Успешное использование qwen (как задумано):

```bash
$ qwen
# qwen запускается в интерактивном режиме

> Create a Python file hello.py with a function that prints "Hello World"

# qwen:
# I'll create hello.py with the following content:
# [показывает код]
# Approve? [y/n]

> y

# qwen:
# ✓ Created hello.py
# What else can I help you with?

> exit
```

**Это работает**, потому что:
- qwen контролирует весь диалог
- qwen задает уточняющие вопросы
- qwen получает подтверждения
- qwen видит контекст всей сессии

#### Наша попытка (не работает):

```bash
$ qwen -p "Create hello.py" --approval-mode=yolo
# qwen:
# Понял. Что вы хотите, чтобы я сделал?
# [exit code 0, файл не создан]
```

**Это не работает**, потому что:
- qwen не имеет интерактивного контекста
- qwen не может задать уточняющие вопросы
- qwen не знает что делать дальше
- qwen завершается с "успехом" (exit 0), но ничего не сделав

### 9. Технические ограничения qwen CLI

#### Из документации qwen:

```
Usage: qwen [options] [command]

Qwen Code - Launch an interactive CLI, use -p/--prompt for non-interactive mode
```

**Ключевое слово**: "for non-interactive mode"

#### Что означает "non-interactive mode" для qwen:

```bash
# Interactive mode (по умолчанию):
qwen
# → Запускает сессию, ждет команд

# Non-interactive mode с -p:
qwen -p "task description"
# → Выполняет ОДНО действие и выходит
```

**НО**: "одно действие" для qwen это:
- Прочитать промпт
- Вывести первый ответ
- Выйти

А НЕ:
- Прочитать промпт
- Выполнить все инструкции
- Создать файлы
- Вернуть результат

### 10. Сравнение с Claude Code CLI (аналог)

qwen CLI основан на той же архитектуре что и Claude Code. Вот как работает Claude Code:

```bash
# Интерактивно (работает):
$ claude
> Create a FastAPI service
# Claude создает файлы, показывает progress

# Non-interactive (НЕ работает как API):
$ claude -p "Create a FastAPI service"
# Claude: "I'll help you create a FastAPI service. Let me start..."
# [exit, ничего не создано, потому что нет интерактивности]
```

**То же самое с qwen** - он coding assistant, не API.

### 11. Почему Ollama работает, а qwen нет

#### Ollama (HTTP API):

```bash
# Архитектура Ollama:
ollama serve  # Запускает HTTP server
  ↓
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Return JSON: {...}",
  "stream": false
}'
  ↓
Response: {"response": "{\"test\": \"success\"}"}
```

**Это LLM API**:
- Stateless
- Single request → Single response
- Только генерация текста
- Подходит для программных вызовов

#### qwen CLI (Interactive Agent):

```bash
# Архитектура qwen:
qwen  # Запускает interactive session
  ↓
User input → qwen analyzes → qwen asks questions → User confirms → qwen acts
  ↑_______________________________________________________________|
```

**Это Interactive Agent**:
- Stateful session
- Continuous dialogue
- Создание файлов, выполнение команд
- НЕ подходит для subprocess API calls

## Заключение: Почему qwen CLI не подходит

### Технические причины:

1. **Архитектура**: qwen = interactive agent, не LLM API
2. **Диалоговая модель**: ожидает continuous input/output, не single-shot
3. **VS Code integration**: требует workspace, не работает в isolation
4. **Action approval**: даже с --approval-mode=yolo не выполняет действия в non-interactive mode
5. **Output format**: возвращает диалоговые сообщения, не structured data

### Что мы пытались сделать (и почему не сработало):

```python
# Наша попытка:
llm_response = qwen_cli("-p", "Return JSON: {...}")

# Почему не работает:
# 1. qwen читает промпт как НАЧАЛО диалога, не как КОМАНДУ
# 2. qwen возвращает "Что делать дальше?", не JSON
# 3. qwen НЕ создает файлы без интерактивного подтверждения
# 4. qwen НЕ может работать как API
```

### Правильное решение:

```yaml
# Используйте Ollama с той же моделью:
llm:
  provider: "ollama"
  model: "qwen2.5-coder:7b"  # ← ТА ЖЕ модель, но через HTTP API
  ollama_host: "http://localhost:11434"
```

**Ollama дает**:
- ✅ Та же модель qwen2.5-coder
- ✅ HTTP API для subprocess вызовов
- ✅ Structured JSON output
- ✅ Stateless single-shot calls
- ✅ Нет требований к VS Code workspace
- ✅ В 2-3 раза быстрее
- ✅ Гарантированная совместимость с MSP Orchestrator

## Итоговый вердикт

**qwen CLI технически невозможно использовать как LLM provider для MSP Orchestrator**, потому что:

1. Это НЕ LLM API, это interactive coding assistant
2. Требует интерактивного диалога, не работает в single-shot режиме
3. Возвращает диалоговые сообщения, не structured output
4. Не создает файлы в non-interactive mode даже с --approval-mode=yolo
5. Привязан к VS Code workspace

**Рекомендация**: Используйте Ollama с моделью qwen2.5-coder - это официальный способ запустить qwen как LLM API.
