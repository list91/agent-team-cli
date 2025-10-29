# qwen_client.py

Минимальный изолированный клиент для вызова `qwen` с реал-тайм мониторингом.

## Быстрый старт

```bash
python qwen_client.py --prompt "создай файл hello.txt с текстом привет мир"
```

## Что создаётся

```
agents-space/
  └── run_20251029_142233_abc123/    ← уникальная папка для каждого запуска
        ├── scratchpad.md            ← краткий лог (старт, финиш, файлы)
        ├── live.log                 ← полный вывод qwen с рассуждениями
        └── [созданные файлы]        ← результаты работы qwen
```

## Мониторинг в реал-тайм

### Вариант 1: Смотри в основном терминале
При запуске сразу видишь диалог qwen:
```bash
python qwen_client.py --prompt "твоя задача"
# → Видишь весь вывод qwen в реал-тайм
```

### Вариант 2: Открой live.log в редакторе
Скрипт выдаёт путь к `live.log` при старте:
```bash
Рабочая директория: C:\...\agents-space\run_20251029_142233_abc123
Live лог: C:\...\agents-space\run_20251029_142233_abc123\live.log
```

Открой этот файл в VSCode/Notepad++/любом редакторе с автообновлением — увидишь вывод в реал-тайм.

### Вариант 3: В другом терминале

**Windows:**
```bash
type agents-space\run_20251029_142233_abc123\live.log
```

**Linux/Mac:**
```bash
cat agents-space/run_20251029_142233_abc123/live.log
```

### Вариант 4: Краткий статус через scratchpad.md

```bash
cat agents-space/run_20251029_142233_abc123/scratchpad.md
```

**Содержит:**
- Время старта
- Команду qwen
- Время завершения
- Созданные файлы
- Ошибки (если были)

## Пример scratchpad.md

```
[2025-10-29T14:22:33] [~] Запуск задачи: "создай 3 файла..."
[2025-10-29T14:22:33] [~] Рабочая директория: C:\...\run_20251029_142233_abc123
[2025-10-29T14:22:33] [~] Выполнение команды: qwen ... --allowed-tools --yolo json
[2025-10-29T14:22:33] [~] Live лог: C:\...\run_20251029_142233_abc123\live.log
[2025-10-29T14:23:20] [X] Успешно выполнено
[2025-10-29T14:23:20] [X] Созданы файлы: config.json, README.md, users.txt
```

Статусы: `[~]` = процесс, `[X]` = успех, `[!]` = ошибка

## Параметры

```bash
python qwen_client.py \
  --prompt "твоя задача"       # обязательный
  --allowed-tools              # по умолчанию включен
  --yolo json                  # формат вывода (по умолчанию json)
```

## Изоляция

Все файлы создаются **только внутри** `agents-space/run_*/` — аппаратная изоляция через `os.chdir()`.

Корень проекта остаётся чистым.

## Очистка старых запусков

```bash
# Удалить всё
rm -rf agents-space/

# Удалить запуски старше 7 дней (Linux/Mac)
find agents-space/ -type d -name "run_*" -mtime +7 -exec rm -rf {} +

# Удалить запуски старше 7 дней (Windows PowerShell)
Get-ChildItem agents-space -Directory -Filter "run_*" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Recurse -Force
```
