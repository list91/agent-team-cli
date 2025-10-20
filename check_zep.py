# Проверим, как на самом деле выглядит библиотека zep_python
import inspect
import zep_python

# Проверим основные атрибуты
print("Атрибуты zep_python:")
for attr in dir(zep_python):
    if not attr.startswith('_'):
        print(f"  {attr}")

# Попробуем импортировать основные классы
try:
    from zep_python import AsyncZepClient, ZepClient
    print(f"\nУспешно импортированы: AsyncZepClient, ZepClient")
except ImportError as e:
    print(f"\nНе удалось импортировать клиенты: {e}")

# Проверим содержимое подмодулей
print(f"\nСодержимое zep_python.core:")
try:
    from zep_python import core
    for attr in dir(core):
        if not attr.startswith('_'):
            print(f"  {attr}")
except ImportError as e:
    print(f"Ошибка при импорте core: {e}")

print(f"\nСодержимое zep_python.memory:")
try:
    from zep_python import memory
    for attr in dir(memory):
        if not attr.startswith('_'):
            print(f"  {attr}")
except ImportError as e:
    print(f"Ошибка при импорте memory: {e}")

print(f"\nСодержимое zep_python.user:")
try:
    from zep_python import user
    for attr in dir(user):
        if not attr.startswith('_'):
            print(f"  {attr}")
except ImportError as e:
    print(f"Ошибка при импорте user: {e}")