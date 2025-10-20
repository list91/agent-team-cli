# JSON Parsing Improvements

## Проблема

При использовании qwen CLI в качестве subprocess provider, возвращаемый ответ мог содержать дополнительный текст помимо JSON:

```
Analyzing the task...
{
  "complexity": 5,
  "agents": [...]
}
Done!
```

Старый парсер использовал простые регулярные выражения, которые могли:
- Захватывать неполный JSON (non-greedy `.*?` останавливался на первой `}`)
- Не находить JSON среди дополнительного текста
- Не обрабатывать вложенные объекты корректно

## Решение

### 1. Улучшенный `_parse_json_response()` в `src/llm_client.py`

Реализована многоступенчатая стратегия парсинга:

#### Strategy 1: Code blocks с балансировкой скобок
```python
r'```json\s*(\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})\s*```'
```
Использует рекурсивную балансировку `{` и `}` для корректного извлечения вложенных объектов.

#### Strategy 2: Балансировка скобок в тексте
```python
brace_count = 0
for i, char in enumerate(response):
    if char == '{':
        if brace_count == 0:
            start_idx = i
        brace_count += 1
    elif char == '}':
        brace_count -= 1
        if brace_count == 0 and start_idx is not None:
            potential_jsons.append(response[start_idx:i+1])
```
Находит ВСЕ потенциальные JSON объекты в тексте путем подсчета скобок.

#### Strategy 3: Скоринг кандидатов
```python
score = 0
if 'agents' in parsed:
    score += 100  # Критически важное поле
if 'complexity' in parsed:
    score += 10
if 'strategy' in parsed:
    score += 10
```
Выбирает JSON с наибольшим score - приоритет объектам с полем `agents`.

#### Strategy 4: Fallback
Пытается распарсить всю строку как JSON, если предыдущие стратегии не сработали.

### 2. Детальное логирование в `SubprocessLLMProvider`

Добавлено логирование для отладки:

```python
logger.info(f"[SubprocessLLM] Executing command: {cmd[0]} -p <prompt> -y")
logger.info(f"[SubprocessLLM] Raw response length: {len(stdout)} chars")
logger.debug(f"[SubprocessLLM] Raw stdout:\n{stdout}")
logger.info(f"[SubprocessLLM] Stripped response length: {len(result)} chars")
```

Позволяет увидеть:
- Какая команда выполняется
- Сколько символов вернул qwen
- Полный raw output (на уровне DEBUG)

### 3. Усиленный промпт в `master.py`

Добавлена CRITICAL INSTRUCTION для LLM:

```python
CRITICAL INSTRUCTION: You MUST respond with ONLY a valid JSON object.
Do NOT include any explanatory text, markdown formatting, or additional
commentary before or after the JSON. Your entire response should be parseable as JSON.

Required JSON format:
{...}

Remember: Output ONLY the JSON object, nothing else.
```

Это помогает LLM (особенно qwen) понять что нужен только JSON, без дополнительного текста.

## Тестирование

### Unit тест
```python
test_response = '''
Analyzing the task...
{
  "complexity": 5,
  "strategy": "flat_delegation",
  "agents": [{"name": "coder", ...}],
  "bridges": [],
  "reasoning": "This is a complex ML task"
}
Done!
'''

result = client._parse_json_response(test_response)
# ✅ Успешно извлечен JSON
# ✅ score: 120 (100 + 10 + 10)
# ✅ Поле 'agents' присутствует
```

## Преимущества

1. **Робастность** - работает даже если qwen добавляет дополнительный текст
2. **Приоритизация** - выбирает правильный JSON если их несколько
3. **Отладка** - детальное логирование помогает диагностировать проблемы
4. **Совместимость** - работает с любыми subprocess LLM провайдерами

## Измененные файлы

- `src/llm_client.py:496-581` - Метод `_parse_json_response()` с улучшенным парсингом
- `src/llm_client.py:150-219` - SubprocessLLMProvider с логированием
- `agents/master/master.py:462-502` - Промпт с CRITICAL INSTRUCTION

## Использование

Теперь система автоматически обрабатывает различные форматы ответов от LLM:

```python
# ✅ Чистый JSON
{"agents": [...]}

# ✅ JSON в code block
```json
{"agents": [...]}
```

# ✅ JSON с дополнительным текстом
Analysis: ...
{"agents": [...]}
Complete!

# ✅ Несколько JSON объектов (выберет тот, где есть 'agents')
{"status": "ok"}
{"agents": [...], "complexity": 5}
```

## Дальнейшие улучшения

Если qwen продолжает возвращать некорректные ответы, рассмотрите:

1. **Использование Ollama** - более предсказуемый HTTP API
2. **Увеличение строгости промпта** - добавить примеры (few-shot)
3. **Post-processing** - дополнительная очистка вывода qwen
