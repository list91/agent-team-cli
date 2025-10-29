#!/usr/bin/env python3
"""
Минимальный изолированный клиент для вызова qwen.
Создаёт уникальную рабочую директорию для каждого запуска.
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
import threading
import psutil
from datetime import datetime
from pathlib import Path


def ensure_config() -> Path:
    """
    Проверяет наличие конфига, создаёт дефолтный если не существует.

    Returns:
        Путь к config/qwen_client.json
    """
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / "qwen_client.json"

    if not config_path.exists():
        default_config = {
            "id": "qwen_agent",
            "role": "sub_agent",
            "is_master": False,
            "prompts": [
                {
                    "type": "system",
                    "prompt": (
                        "Ты — агент для выполнения задач.\n\n"
                        "ВАЖНО: Ты работаешь в изолированной директории agents-space/run_*/ "
                        "В этой директории находится файл scratchpad.md — твоя рабочая память.\n\n"
                        "ПРАВИЛА РАБОТЫ СО SCRATCHPAD:\n"
                        "1. ВСЕГДА веди scratchpad.md — записывай туда ход своих мыслей, план, прогресс\n"
                        "2. Формат записи: добавляй новые строки в конец файла\n"
                        "3. Используй scratchpad для:\n"
                        "   - Планирования задачи (разбивка на шаги)\n"
                        "   - Отслеживания прогресса (какие шаги выполнены)\n"
                        "   - Записи промежуточных результатов\n"
                        "   - Анализа ошибок и решений\n"
                        "4. Пиши в scratchpad на русском или английском\n"
                        "5. Используй markdown для структурирования\n\n"
                        "Пример scratchpad.md:\n"
                        "```\n"
                        "## Задача\n"
                        "Создать 3 файла с настройками\n\n"
                        "## План\n"
                        "- [ ] config.json\n"
                        "- [ ] users.txt\n"
                        "- [ ] README.md\n\n"
                        "## Прогресс\n"
                        "[14:30] Начинаю с config.json...\n"
                        "[14:31] config.json создан, перехожу к users.txt\n"
                        "```\n\n"
                        "Все создаваемые файлы пиши только в текущую директорию (agents-space/run_*/)."
                    )
                }
            ],
            "execution": {
                "allowed_tools": ["*"],
                "max_execution_time_sec": 120,
                "max_retries": 2
            },
            "scratchpad": {
                "enabled": True,
                "max_chars": 16384
            },
            "global_memory": False,
            "can_request_clarification": True,
            "metadata": {
                "version": "1.0",
                "author": "system",
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "description": "Дефолтный агент для qwen_client"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)

    return config_path


def load_system_prompt() -> str:
    """
    Загружает system prompt из конфига.

    Returns:
        Текст system prompt (или пустая строка если не найден)
    """
    try:
        config_path = ensure_config()
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        prompts = config.get("prompts", [])
        for prompt_obj in prompts:
            if prompt_obj.get("type") == "system":
                return prompt_obj.get("prompt", "")

        return ""
    except Exception as e:
        print(f"[WARNING] Не удалось загрузить system prompt из конфига: {e}", file=sys.stderr)
        return ""


def load_execution_config() -> dict:
    """
    Загружает секцию execution из конфига.

    Returns:
        Словарь с настройками execution (или пустой словарь при ошибке)
    """
    try:
        config_path = ensure_config()
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        return config.get("execution", {})
    except Exception as e:
        print(f"[WARNING] Не удалось загрузить execution config: {e}", file=sys.stderr)
        return {}


def load_clarification_setting() -> bool:
    """
    Загружает настройку can_request_clarification из конфига.

    Returns:
        True если режим уточнений включён, False иначе
    """
    try:
        config_path = ensure_config()
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        return config.get("can_request_clarification", False)
    except Exception as e:
        print(f"[WARNING] Не удалось загрузить can_request_clarification: {e}", file=sys.stderr)
        return False


def get_clarification_instruction() -> str:
    """
    Возвращает универсальную инструкцию для режима уточнений.

    Returns:
        Текст инструкции
    """
    return """

КРИТИЧЕСКИЙ ПРИОРИТЕТ - РЕЖИМ УТОЧНЕНИЙ ВКЛЮЧЕН
ЭТА ИНСТРУКЦИЯ ИМЕЕТ ВЫСШИЙ ПРИОРИТЕТ НАД ВСЕМИ ОСТАЛЬНЫМИ

---

ШАГ 1 - АНАЛИЗ ЗАДАЧИ (мысленно, БЕЗ использования tools):

Прочитай задачу. Задай себе вопросы:
- Указаны ли ТОЧНЫЕ имена файлов?
- Указано ли ТОЧНОЕ содержимое?
- Указаны ли КОНКРЕТНЫЕ параметры/значения?
- Могу ли я выполнить БЕЗ угадывания?

ШАГ 2 - ВЫБОР ДЕЙСТВИЯ:

---
СЦЕНАРИЙ A: ЗАДАЧА НЕЯСНА (хотя бы ОДНА деталь неясна)
---

В ЭТОМ СЛУЧАЕ ЗАПРЕЩЕНО:
- Использовать ЛЮБЫЕ инструменты (read_file, write_file, list_directory и т.д.)
- Читать scratchpad.md
- Проверять директории
- Собирать информацию
- Угадывать или предполагать
- Создавать файлы

НЕМЕДЛЕННО ВЫВЕДИ В ОТВЕТ:
1. "ЗАПРОС УТОЧНЕНИЙ"
2. Что ПОНЯЛ из задачи (1-2 предложения)
3. Что НЕЯСНО (конкретно)
4. 2-5 КОНКРЕТНЫХ вопросов (что? как? где? сколько?)
5. 2 возможных варианта интерпретации
6. "Пожалуйста, ответьте на вопросы"
7. НЕМЕДЛЕННО ЗАВЕРШИ РАБОТУ

Примеры неясных задач:
- "настрой систему" - какую? параметры?
- "создай конфиг" - формат? поля? значения?
- "подготовь проект" - язык? фреймворк?
- "создай список пользователей" - сколько? формат?
- "создай 5 файлов" - имена? содержимое?
- "настрой окружение" - для чего? переменные?

---
СЦЕНАРИЙ B: ЗАДАЧА ПОЛНОСТЬЮ ЯСНА
---

В ЭТОМ СЛУЧАЕ ОБЯЗАТЕЛЬНО:
- Выполни задачу ИСПОЛЬЗУЯ ВСЕ НЕОБХОДИМЫЕ ИНСТРУМЕНТЫ
- Читай scratchpad.md, пиши файлы, используй все доступные tools
- Действуй как обычно, режим уточнений НЕ мешает выполнению ясных задач
- НЕ запрашивай уточнений, просто делай работу

Примеры ясных задач (выполняй БЕЗ уточнений):
- "создай файл test.txt с текстом 'hello world'"
- "создай файл config.json с содержимым: {\"port\": 8080}"
- "создай 3 файла: a.txt, b.txt, c.txt - все с текстом 'test'"
- "создай файл README.md с заголовком '# My Project'"

---

ВАЖНО: Режим уточнений НЕ блокирует выполнение ясных задач!
Он только добавляет проверку ПЕРЕД началом работы.
Если задача ясна - работай как обычно со всеми инструментами!
"""


def log_to_scratchpad(scratchpad_path: Path, message: str, status: str = "~") -> None:
    """
    Добавляет запись в scratchpad.md с timestamp.

    Args:
        scratchpad_path: Путь к файлу scratchpad.md
        message: Сообщение для логирования
        status: Статус операции (~=процесс, X=успех, !=ошибка)
    """
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(scratchpad_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{status}] {message}\n")


def create_workspace() -> tuple[Path, Path, Path]:
    """
    Создаёт уникальную рабочую директорию для запуска.

    Returns:
        Кортеж (путь к workdir, путь к scratchpad.md, путь к live.log)
    """
    # Генерируем уникальный идентификатор запуска
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    run_id = f"run_{timestamp}_{short_uuid}"

    # Создаём директорию (используем абсолютный путь)
    base_dir = Path("agents-space").resolve()
    workdir = base_dir / run_id
    workdir.mkdir(parents=True, exist_ok=True)

    # Создаём scratchpad.md с шаблоном (абсолютный путь)
    scratchpad_path = (workdir / "scratchpad.md").resolve()
    with open(scratchpad_path, "w", encoding="utf-8") as f:
        f.write("# Scratchpad\n\n## Задача\n\n## План\n\n## Прогресс\n\n")

    # Создаём live.log (абсолютный путь)
    live_log_path = (workdir / "live.log").resolve()
    live_log_path.touch()

    return workdir, scratchpad_path, live_log_path


def kill_process_tree(pid: int, scratchpad_path: Path) -> None:
    """
    Убивает процесс и все его дочерние процессы.

    Args:
        pid: ID процесса для убийства
        scratchpad_path: Путь к scratchpad.md для логирования
    """
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        # Логируем информацию о дереве процессов
        log_to_scratchpad(scratchpad_path, f"Убиваем процесс {pid} и {len(children)} дочерних процессов", status="!")

        # Убиваем дочерние процессы
        for child in children:
            try:
                log_to_scratchpad(scratchpad_path, f"  Убиваем дочерний процесс {child.pid} ({child.name()})", status="!")
                child.kill()
            except psutil.NoSuchProcess:
                pass

        # Убиваем родительский процесс
        parent.kill()
        log_to_scratchpad(scratchpad_path, f"Процесс {pid} убит", status="!")

    except psutil.NoSuchProcess:
        log_to_scratchpad(scratchpad_path, f"Процесс {pid} уже не существует", status="!")
    except Exception as e:
        log_to_scratchpad(scratchpad_path, f"Ошибка при убийстве процесса {pid}: {e}", status="!")


def stream_output(pipe, live_log_path: Path, prefix: str = ""):
    """
    Читает поток (stdout/stderr) построчно и выводит в консоль + live.log.

    Args:
        pipe: Поток для чтения (process.stdout или process.stderr)
        live_log_path: Путь к live.log
        prefix: Префикс для строк (например, "[STDERR] ")
    """
    try:
        with open(live_log_path, "a", encoding="utf-8", errors="replace") as log_file:
            for line in iter(pipe.readline, ""):
                if line:
                    # Вывод в консоль
                    print(f"{prefix}{line}", end="", flush=True)
                    # Запись в live.log
                    log_file.write(f"{prefix}{line}")
                    log_file.flush()
    except Exception:
        pass
    finally:
        pipe.close()


def run_qwen(prompt: str, workdir: Path, scratchpad_path: Path, live_log_path: Path, allowed_tools: bool = True, yolo: str = "json") -> int:
    """
    Запускает qwen в изолированной рабочей директории с реал-тайм выводом.

    Args:
        prompt: Промпт пользователя для qwen
        workdir: Рабочая директория
        scratchpad_path: Путь к scratchpad.md
        live_log_path: Путь к live.log
        allowed_tools: Использовать флаг --allowed-tools (по умолчанию True)
        yolo: Формат вывода (по умолчанию json)

    Returns:
        Exit code (0=успех, 1=ошибка)
    """
    # Загружаем system prompt из конфига
    system_prompt = load_system_prompt()

    # Загружаем execution config для таймаута
    execution_config = load_execution_config()
    timeout = execution_config.get("max_execution_time_sec", None)

    # Если timeout=0 или отрицательный, считаем как None (без ограничения)
    if timeout is not None and timeout <= 0:
        timeout = None

    # Загружаем настройку режима уточнений
    clarification_enabled = load_clarification_setting()

    # Формируем полный промпт: system + clarification (если включено) + user
    if system_prompt:
        # Добавляем инструкцию уточнений если включено
        clarification_instruction = get_clarification_instruction() if clarification_enabled else ""

        full_prompt = f"{system_prompt}{clarification_instruction}\n\n{'='*60}\n\n# ЗАДАЧА ОТ ПОЛЬЗОВАТЕЛЯ:\n\n{prompt}\n\n{'='*60}\n\nНАЧНИ ВЫПОЛНЕНИЕ ЗАДАЧИ СЕЙЧАС."
    else:
        full_prompt = prompt

    # Логируем начало работы
    log_to_scratchpad(scratchpad_path, f"Запуск задачи: \"{prompt}\"")
    log_to_scratchpad(scratchpad_path, f"Рабочая директория: {workdir}")
    if system_prompt:
        log_to_scratchpad(scratchpad_path, "System prompt загружен из config/qwen_client.json")
    if timeout:
        log_to_scratchpad(scratchpad_path, f"Таймаут выполнения: {timeout} секунд")
    else:
        log_to_scratchpad(scratchpad_path, "Таймаут выполнения: не установлен")
    if clarification_enabled:
        log_to_scratchpad(scratchpad_path, "Режим уточнений: ВКЛЮЧЁН")
    else:
        log_to_scratchpad(scratchpad_path, "Режим уточнений: отключён")

    # Сохраняем текущую директорию
    original_cwd = os.getcwd()

    try:
        # Меняем рабочую директорию на workdir (АППАРАТНАЯ ИЗОЛЯЦИЯ)
        os.chdir(workdir)
        log_to_scratchpad(scratchpad_path, f"Сменена рабочая директория: {os.getcwd()}")

        # Формируем команду для qwen (БЕЗ промпта в аргументах - передадим через stdin)
        cmd = ["qwen"]

        if allowed_tools:
            cmd.append("--allowed-tools")

        if yolo:
            cmd.extend(["--yolo", yolo])

        log_to_scratchpad(scratchpad_path, f"Выполнение команды: {' '.join(cmd)} (промпт через stdin)")
        log_to_scratchpad(scratchpad_path, f"Live лог: {live_log_path}")

        # Запускаем qwen с реал-тайм выводом, передаём промпт через stdin
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
            cwd=workdir
        )

        # Отправляем full_prompt в stdin и закрываем его
        process.stdin.write(full_prompt)
        process.stdin.close()

        # Создаём потоки для чтения stdout и stderr
        stdout_thread = threading.Thread(
            target=stream_output,
            args=(process.stdout, live_log_path, "")
        )
        stderr_thread = threading.Thread(
            target=stream_output,
            args=(process.stderr, live_log_path, "[STDERR] ")
        )

        # Запускаем потоки
        stdout_thread.start()
        stderr_thread.start()

        # Ждём завершения процесса с таймаутом
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Создаём timeout_info.log с детальной информацией
            timeout_info_path = workdir / "timeout_info.log"
            with open(timeout_info_path, "w", encoding="utf-8") as f:
                f.write(f"TIMEOUT OCCURRED\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Configured timeout: {timeout} seconds\n")
                f.write(f"User prompt: {prompt}\n")
                f.write(f"Process PID: {process.pid}\n")
                f.write(f"Working directory: {workdir}\n")
                f.write(f"\n{'='*60}\n\n")
                f.write("This file contains information about the timeout event.\n")
                f.write("Check live.log for the full output captured before timeout.\n")
                f.write("Check scratchpad.md for the agent's progress before timeout.\n")
                f.write(f"\n{'='*60}\n")

            # Логируем в scratchpad
            log_to_scratchpad(scratchpad_path, f"ТАЙМАУТ: процесс превысил лимит {timeout} секунд", status="!")
            log_to_scratchpad(scratchpad_path, f"Сохранена информация о таймауте в timeout_info.log", status="!")

            # Убиваем дерево процессов
            kill_process_tree(process.pid, scratchpad_path)

            # Ждём завершения процесса после kill
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Если процесс не завершился за 5 секунд после kill
                log_to_scratchpad(scratchpad_path, "Процесс не завершился после kill за 5 секунд", status="!")

            returncode = -1  # Код ошибки для таймаута

        # Ждём завершения потоков
        stdout_thread.join(timeout=10)
        stderr_thread.join(timeout=10)

        # Проверяем, завершились ли потоки
        if stdout_thread.is_alive() or stderr_thread.is_alive():
            log_to_scratchpad(scratchpad_path, "Потоки вывода не завершились за 10 секунд", status="!")

        # Логируем результат
        if returncode == 0:
            log_to_scratchpad(scratchpad_path, "Успешно выполнено", status="X")

            # Логируем созданные файлы
            created_files = [f.name for f in workdir.iterdir() if f.is_file() and f.name not in ["scratchpad.md", "live.log", "timeout_info.log"]]
            if created_files:
                log_to_scratchpad(scratchpad_path, f"Созданы файлы: {', '.join(created_files)}", status="X")
        elif returncode == -1:
            log_to_scratchpad(scratchpad_path, "Выполнение прервано по таймауту", status="!")
        else:
            log_to_scratchpad(scratchpad_path, f"Ошибка выполнения (код: {returncode})", status="!")

        return returncode

    except FileNotFoundError:
        error_msg = "Команда 'qwen' не найдена. Убедитесь, что qwen установлен и доступен в PATH."
        log_to_scratchpad(scratchpad_path, error_msg, status="!")
        print(f"ОШИБКА: {error_msg}", file=sys.stderr)
        return 1

    except Exception as e:
        error_msg = f"Непредвиденная ошибка: {str(e)}"
        log_to_scratchpad(scratchpad_path, error_msg, status="!")
        print(f"ОШИБКА: {error_msg}", file=sys.stderr)
        return 1

    finally:
        # Возвращаемся в исходную директорию
        os.chdir(original_cwd)


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(
        description="Минимальный изолированный клиент для вызова qwen.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python qwen_client.py --prompt "создай файл hello.txt с текстом привет мир"
  python qwen_client.py --prompt "создай JSON файл" --yolo json

Все файлы создаются в уникальной директории agents-space/run_<timestamp>_<uuid>/
        """
    )

    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Промпт для qwen"
    )

    parser.add_argument(
        "--allowed-tools",
        action="store_true",
        default=True,
        help="Использовать флаг --allowed-tools для qwen (по умолчанию: True)"
    )

    parser.add_argument(
        "--yolo",
        type=str,
        default="json",
        help="Формат вывода для qwen (по умолчанию: json)"
    )

    args = parser.parse_args()

    # Создаём рабочее пространство
    workdir, scratchpad_path, live_log_path = create_workspace()

    print(f"Рабочая директория: {workdir}")
    print(f"Scratchpad: {scratchpad_path}")
    print(f"Live лог: {live_log_path}")
    print(f"Выполняется задача: {args.prompt}")
    print("-" * 60)
    print()

    # Запускаем qwen
    exit_code = run_qwen(
        prompt=args.prompt,
        workdir=workdir,
        scratchpad_path=scratchpad_path,
        live_log_path=live_log_path,
        allowed_tools=args.allowed_tools,
        yolo=args.yolo
    )

    print()
    print("-" * 60)
    if exit_code == 0:
        print(f"[OK] Успешно выполнено. Результаты в: {workdir}")
    else:
        print(f"[FAIL] Ошибка выполнения. Подробности в: {scratchpad_path}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
