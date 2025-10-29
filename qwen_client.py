#!/usr/bin/env python3
"""
Минимальный изолированный клиент для вызова qwen.
Создаёт уникальную рабочую директорию для каждого запуска.
"""

import argparse
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


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


def create_workspace() -> tuple[Path, Path]:
    """
    Создаёт уникальную рабочую директорию для запуска.

    Returns:
        Кортеж (путь к workdir, путь к scratchpad.md)
    """
    # Генерируем уникальный идентификатор запуска
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    run_id = f"run_{timestamp}_{short_uuid}"

    # Создаём директорию (используем абсолютный путь)
    base_dir = Path("agents-space").resolve()
    workdir = base_dir / run_id
    workdir.mkdir(parents=True, exist_ok=True)

    # Создаём scratchpad.md (абсолютный путь)
    scratchpad_path = (workdir / "scratchpad.md").resolve()
    scratchpad_path.touch()

    return workdir, scratchpad_path


def run_qwen(prompt: str, workdir: Path, scratchpad_path: Path, allowed_tools: bool = True, yolo: str = "json") -> int:
    """
    Запускает qwen в изолированной рабочей директории.

    Args:
        prompt: Промпт для qwen
        workdir: Рабочая директория
        scratchpad_path: Путь к scratchpad.md
        allowed_tools: Использовать флаг --allowed-tools (по умолчанию True)
        yolo: Формат вывода (по умолчанию json)

    Returns:
        Exit code (0=успех, 1=ошибка)
    """
    # Логируем начало работы
    log_to_scratchpad(scratchpad_path, f"Запуск задачи: \"{prompt}\"")
    log_to_scratchpad(scratchpad_path, f"Рабочая директория: {workdir}")

    # Сохраняем текущую директорию
    original_cwd = os.getcwd()

    try:
        # Меняем рабочую директорию на workdir (АППАРАТНАЯ ИЗОЛЯЦИЯ)
        os.chdir(workdir)
        log_to_scratchpad(scratchpad_path, f"Сменена рабочая директория: {os.getcwd()}")

        # Формируем команду для qwen
        cmd = ["qwen", prompt]

        if allowed_tools:
            cmd.append("--allowed-tools")

        if yolo:
            cmd.extend(["--yolo", yolo])

        log_to_scratchpad(scratchpad_path, f"Выполнение команды: {' '.join(cmd)}")

        # Запускаем qwen (shell=True для Windows .cmd)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            shell=True
        )

        # Логируем результат
        if result.returncode == 0:
            log_to_scratchpad(scratchpad_path, "Успешно выполнено", status="X")

            # Логируем созданные файлы
            created_files = [f.name for f in workdir.iterdir() if f.is_file() and f.name != "scratchpad.md"]
            if created_files:
                log_to_scratchpad(scratchpad_path, f"Созданы файлы: {', '.join(created_files)}", status="X")

            # Логируем stdout если есть
            if result.stdout:
                log_to_scratchpad(scratchpad_path, f"Вывод:\n{result.stdout}")
        else:
            log_to_scratchpad(scratchpad_path, f"Ошибка выполнения (код: {result.returncode})", status="!")

            # Логируем stderr
            if result.stderr:
                log_to_scratchpad(scratchpad_path, f"Ошибка:\n{result.stderr}", status="!")

        return result.returncode

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
    workdir, scratchpad_path = create_workspace()

    print(f"Рабочая директория: {workdir}")
    print(f"Scratchpad: {scratchpad_path}")
    print(f"Выполняется задача: {args.prompt}")
    print("-" * 60)

    # Запускаем qwen
    exit_code = run_qwen(
        prompt=args.prompt,
        workdir=workdir,
        scratchpad_path=scratchpad_path,
        allowed_tools=args.allowed_tools,
        yolo=args.yolo
    )

    print("-" * 60)
    if exit_code == 0:
        print(f"[OK] Успешно выполнено. Результаты в: {workdir}")
    else:
        print(f"[FAIL] Ошибка выполнения. Подробности в: {scratchpad_path}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
