#!/usr/bin/env python3
"""
Скрипт для запуска пограничных тестов мастер-агента и создания JSON отчетов
"""
import json
import subprocess
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Тесты из boundary_test_cases.md
TESTS = [
    {
        "id": "001",
        "name": "Неоднозначная задача",
        "category": "A: Граничные случаи задач",
        "prompt": "Составь алгоритм: сделай что-нибудь"
    },
    {
        "id": "002",
        "name": "Противоречивая задача",
        "category": "A: Граничные случаи задач",
        "prompt": "Составь алгоритм: создай файл НО не используй coder агента"
    },
    {
        "id": "003",
        "name": "Задача без глаголов",
        "category": "A: Граничные случаи задач",
        "prompt": "Составь алгоритм: Python FastAPI JWT"
    },
    {
        "id": "004",
        "name": "Задача на английском",
        "category": "A: Граничные случаи задач",
        "prompt": "Составь алгоритм: create REST API with authentication"
    },
    {
        "id": "005",
        "name": "Очень длинная задача",
        "category": "A: Граничные случаи задач",
        "prompt": "Составь алгоритм: мне нужно создать REST API сервер используя FastAPI фреймворк, причем API должен иметь 3 эндпоинта: первый для получения списка пользователей, второй для создания нового пользователя, третий для удаления пользователя, также нужно добавить JWT аутентификацию и rate limiting на 100 запросов в минуту, и обязательно протестировать все это с использованием pytest"
    },
    {
        "id": "006",
        "name": "Прямая команда создания файла",
        "category": "B: Граничные случаи команд",
        "prompt": "создай файл config.json с настройками"
    },
    {
        "id": "007",
        "name": "Прямая команда выполнения кода",
        "category": "B: Граничные случаи команд",
        "prompt": "запусти npm install и покажи результат"
    },
    {
        "id": "008",
        "name": "Императивная команда",
        "category": "B: Граничные случаи команд",
        "prompt": "Сделай!"
    },
    {
        "id": "009",
        "name": "Вопрос вместо команды",
        "category": "B: Граничные случаи команд",
        "prompt": "Как создать REST API?"
    },
    {
        "id": "010",
        "name": "Команда с escape-символами",
        "category": "B: Граничные случаи команд",
        "prompt": "Составь алгоритм: создай файл test\\nwith\\ttabs.txt"
    },
    {
        "id": "011",
        "name": "Прямая делегация",
        "category": "C: Граничные случаи делегации",
        "prompt": "Передай coder: напиши hello world на Python"
    },
    {
        "id": "012",
        "name": "Делегация несуществующему агенту",
        "category": "C: Граничные случаи делегации",
        "prompt": "Передай deployer: задеплой приложение"
    },
    {
        "id": "013",
        "name": "Делегация всей команде",
        "category": "C: Граничные случаи делегации",
        "prompt": "Передай всем агентам: проверьте код"
    },
    {
        "id": "014",
        "name": "Циклическая зависимость",
        "category": "C: Граничные случаи делегации",
        "prompt": "Составь алгоритм: coder создает код, researcher ищет инфо для coder на основе кода, coder дорабатывает"
    },
    {
        "id": "015",
        "name": "Несуществующий тип агента",
        "category": "D: Граничные случаи команды",
        "prompt": "Составь алгоритм: задеплой приложение в production"
    },
    {
        "id": "016",
        "name": "Все агенты одновременно",
        "category": "D: Граничные случаи команды",
        "prompt": "Составь алгоритм: создай, протестируй и задокументируй библиотеку"
    },
    {
        "id": "017",
        "name": "Только один агент",
        "category": "D: Граничные случаи команды",
        "prompt": "Составь алгоритм: посчитай 2+2"
    },
    {
        "id": "018",
        "name": "Очень сложная задача",
        "category": "D: Граничные случаи команды",
        "prompt": "Составь алгоритм: создай нейросеть для распознавания лиц"
    },
    {
        "id": "019",
        "name": "Явное указание workspace",
        "category": "E: Граничные случаи workspace",
        "prompt": "Составь алгоритм: создай файл в /custom/path/file.txt"
    },
    {
        "id": "020",
        "name": "Разные workspace",
        "category": "E: Граничные случаи workspace",
        "prompt": "Составь алгоритм: найди инфо в интернете, создай файл локально, протестируй в docker"
    },
    {
        "id": "021",
        "name": "Последовательность (потом, затем)",
        "category": "F: Граничные случаи зависимостей",
        "prompt": "Составь алгоритм: найди инфо о X, потом о Y, затем о Z"
    },
    {
        "id": "022",
        "name": "Явная зависимость",
        "category": "F: Граничные случаи зависимостей",
        "prompt": "Составь алгоритм: найди лучшую библиотеку, используя результаты напиши код"
    },
    {
        "id": "023",
        "name": "Смешанные зависимости",
        "category": "F: Граничные случаи зависимостей",
        "prompt": "Составь алгоритм: найди инфо о Python, найди инфо о Go, напиши код на Python используя первую инфу"
    },
    {
        "id": "024",
        "name": "Неявная зависимость",
        "category": "F: Граничные случаи зависимостей",
        "prompt": "Составь алгоритм: напиши API, протестируй API"
    },
    {
        "id": "025",
        "name": "Попытка write_file",
        "category": "G: Граничные случаи инструментов",
        "prompt": "используя write_file создай конфиг"
    },
    {
        "id": "026",
        "name": "Попытка run_shell_command",
        "category": "G: Граничные случаи инструментов",
        "prompt": "запусти через run_shell_command команду ls"
    },
    {
        "id": "027",
        "name": "Read-only операции",
        "category": "G: Граничные случаи инструментов",
        "prompt": "Составь алгоритм: прочитай файл config.json и проанализируй его"
    },
    {
        "id": "028",
        "name": "Запрос todo_write",
        "category": "G: Граничные случаи инструментов",
        "prompt": "используя todo_write создай план работы"
    },
    {
        "id": "029",
        "name": "Эмодзи и спецсимволы",
        "category": "H: Граничные случаи форматирования",
        "prompt": "Составь алгоритм: создай файл README.md с описанием 🚀 проекта ⭐"
    },
    {
        "id": "030",
        "name": "Очень короткая задача",
        "category": "H: Граничные случаи форматирования",
        "prompt": "алгоритм: API"
    },
    {
        "id": "031",
        "name": "Цифры и версии",
        "category": "H: Граничные случаи форматирования",
        "prompt": "Составь алгоритм: создай API v2.5.3 с 10 эндпоинтами"
    },
    {
        "id": "034",
        "name": "Пустая команда",
        "category": "J: Экстремальные случаи",
        "prompt": ""
    },
    {
        "id": "035",
        "name": "Только пробелы",
        "category": "J: Экстремальные случаи",
        "prompt": "     "
    },
    {
        "id": "036",
        "name": "SQL инъекция",
        "category": "J: Экстремальные случаи",
        "prompt": "Составь алгоритм: создай файл'; DROP TABLE users; --"
    },
    {
        "id": "037",
        "name": "Длинная команда 1000+ символов",
        "category": "J: Экстремальные случаи",
        "prompt": "Составь алгоритм: " + ("создай очень подробную документацию " * 50)
    },
    {
        "id": "038",
        "name": "Многострочная команда",
        "category": "J: Экстремальные случаи",
        "prompt": """Составь алгоритм:
1. Найди информацию
2. Создай код
3. Протестируй"""
    }
]


def parse_algorithm_output(output: str) -> Dict[str, Any]:
    """Парсит выход мастер-агента и извлекает структурированную информацию"""

    # Секции алгоритма
    sections = {
        "1": "АНАЛИЗ КОМАНДЫ",
        "2": "ВЫБОР АГЕНТОВ",
        "3": "ДЕТАЛЬНЫЙ ПОШАГОВЫЙ АЛГОРИТМ",
        "4": "ЗАВИСИМОСТИ",
        "5": "ОЖИДАЕМЫЙ РЕЗУЛЬТАТ"
    }

    sections_found = []
    for num, title in sections.items():
        if title in output or f"## {num}." in output:
            sections_found.append(f"section_{num}_{title.lower().replace(' ', '_')}")

    # Извлечение агентов
    agents_pattern = r'- (\w+):'
    agents_mentioned = list(set(re.findall(agents_pattern, output)))

    # Извлечение выбранных агентов (с маркером [X])
    selected_pattern = r'- \[X\] (\w+)'
    agents_selected = list(set(re.findall(selected_pattern, output)))

    # Подсчет шагов
    steps_pattern = r'### ШАГ (\d+):'
    steps = re.findall(steps_pattern, output)
    steps_count = len(steps)

    # Извлечение зависимостей
    dependencies_section = ""
    dep_match = re.search(r'## 4\. ЗАВИСИМОСТИ(.*?)(?=## 5\.|$)', output, re.DOTALL)
    if dep_match:
        dependencies_section = dep_match.group(1).strip()

    # Поиск запрещенных инструментов
    forbidden_tools = ['write_file', 'save_file', 'create_file',
                      'run_shell_command', 'execute_command', 'bash', 'shell']
    forbidden_found = []
    for tool in forbidden_tools:
        if tool in output.lower():
            forbidden_found.append(tool)

    # Проверка запроса уточнений
    clarification_keywords = [
        'запрос уточнений',
        'нужно уточнить',
        'уточните',
        'какие именно',
        'не указано',
        'требуется дополнительная информация',
        'что неясно',
        'конкретные вопросы'
    ]
    clarification_requested = any(kw in output.lower() for kw in clarification_keywords)

    # Извлечение workspace
    workspace_pattern = r'\*\*Workspace:\*\* (\S+)'
    workspace_mentioned = list(set(re.findall(workspace_pattern, output)))

    return {
        "sections_found": sections_found,
        "agents_mentioned": agents_mentioned,
        "agents_selected": agents_selected,
        "steps_count": steps_count,
        "dependencies_text": dependencies_section,
        "workspace_mentioned": workspace_mentioned,
        "forbidden_tools_found": forbidden_found,
        "clarification_requested": clarification_requested
    }


def run_single_test(test: Dict[str, str], output_dir: Path) -> Dict[str, Any]:
    """Запускает один тест и возвращает результат"""

    print(f"[TEST {test['id']}] {test['name']}...", end=" ")

    start_time = datetime.now()

    # Запуск qwen_client.py (из корневой директории проекта)
    script_path = Path(__file__).parent.parent / 'qwen_client.py'
    cmd = ['python', str(script_path), '--prompt', test['prompt']]

    try:
        # Используем cp1251 для Windows или UTF-8 с обработкой ошибок
        import sys
        import platform

        if platform.system() == 'Windows':
            # Windows использует cp1251 для кириллицы
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace',  # Заменять неподдерживаемые символы
                timeout=120
            )
        else:
            # Unix-системы обычно используют UTF-8
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120
            )

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        status = "completed" if result.returncode == 0 else "error"

        # Парсинг вывода
        parsed = parse_algorithm_output(result.stdout)

        # Извлечение workspace path из stdout
        workspace_match = re.search(r'Рабочая директория: (.+)', result.stdout)
        workspace_path = workspace_match.group(1) if workspace_match else ""

        report = {
            "test_id": test['id'],
            "test_name": test['name'],
            "timestamp": start_time.isoformat(),
            "input": {
                "prompt": test['prompt'],
                "category": test['category']
            },
            "execution": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": duration_ms,
                "status": status,
                "exit_code": result.returncode,
                "errors": result.stderr.split('\n') if result.stderr else []
            },
            "output": {
                "full_text": result.stdout,
                "stderr": result.stderr,
                "workspace_path": workspace_path
            },
            "parsed_algorithm": parsed
        }

        print(f"[OK] {duration_ms}ms")

    except subprocess.TimeoutExpired:
        end_time = datetime.now()
        duration_ms = 120000

        report = {
            "test_id": test['id'],
            "test_name": test['name'],
            "timestamp": start_time.isoformat(),
            "input": {
                "prompt": test['prompt'],
                "category": test['category']
            },
            "execution": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": duration_ms,
                "status": "timeout",
                "exit_code": -1,
                "errors": ["Timeout after 120 seconds"]
            },
            "output": {
                "full_text": "",
                "stderr": "Timeout",
                "workspace_path": ""
            },
            "parsed_algorithm": {
                "sections_found": [],
                "agents_mentioned": [],
                "agents_selected": [],
                "steps_count": 0,
                "dependencies_text": "",
                "workspace_mentioned": [],
                "forbidden_tools_found": [],
                "clarification_requested": False
            }
        }

        print("[TIMEOUT]")

    except Exception as e:
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        report = {
            "test_id": test['id'],
            "test_name": test['name'],
            "timestamp": start_time.isoformat(),
            "input": {
                "prompt": test['prompt'],
                "category": test['category']
            },
            "execution": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": duration_ms,
                "status": "exception",
                "exit_code": -1,
                "errors": [str(e)]
            },
            "output": {
                "full_text": "",
                "stderr": str(e),
                "workspace_path": ""
            },
            "parsed_algorithm": {
                "sections_found": [],
                "agents_mentioned": [],
                "agents_selected": [],
                "steps_count": 0,
                "dependencies_text": "",
                "workspace_mentioned": [],
                "forbidden_tools_found": [],
                "clarification_requested": False
            }
        }

        print(f"[ERROR] {e}")

    # Сохранение отчета
    report_file = output_dir / f"test_{test['id']}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def run_all_tests(test_subset: List[Dict] = None):
    """Запускает все тесты или подмножество"""

    # Создание директории для отчетов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reports") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"ЗАПУСК ТЕСТОВ МАСТЕР-АГЕНТА")
    print(f"{'='*70}")
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Директория отчетов: {output_dir}")
    print(f"{'='*70}\n")

    tests_to_run = test_subset if test_subset else TESTS

    results = []
    for test in tests_to_run:
        result = run_single_test(test, output_dir)
        results.append(result)
        time.sleep(1)  # Небольшая задержка между тестами

    # Создание сводного отчета
    summary = {
        "test_run_timestamp": timestamp,
        "total_tests": len(results),
        "completed": sum(1 for r in results if r['execution']['status'] == 'completed'),
        "errors": sum(1 for r in results if r['execution']['status'] == 'error'),
        "timeouts": sum(1 for r in results if r['execution']['status'] == 'timeout'),
        "total_duration_ms": sum(r['execution']['duration_ms'] for r in results),
        "tests": [
            {
                "id": r['test_id'],
                "name": r['test_name'],
                "status": r['execution']['status'],
                "duration_ms": r['execution']['duration_ms']
            }
            for r in results
        ]
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Вывод статистики
    print(f"\n{'='*70}")
    print(f"РЕЗУЛЬТАТЫ")
    print(f"{'='*70}")
    print(f"Всего тестов: {summary['total_tests']}")
    print(f"[OK] Завершено: {summary['completed']}")
    print(f"[ERR] Ошибки: {summary['errors']}")
    print(f"[TMO] Таймауты: {summary['timeouts']}")
    print(f"Общее время: {summary['total_duration_ms']/1000:.1f}s")
    print(f"\nОтчеты сохранены в: {output_dir}")
    print(f"{'='*70}\n")

    return output_dir


if __name__ == "__main__":
    import sys

    # Можно запустить все тесты или первые N
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
        print(f"Запуск первых {n} тестов...")
        run_all_tests(TESTS[:n])
    else:
        print("Запуск ВСЕХ тестов...")
        run_all_tests()
