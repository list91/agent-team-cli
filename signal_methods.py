import subprocess
import os
import time
import re
import threading
import queue

def run_command(command, timeout=None, stream=False):
    """
    Выполняет команду в оболочке с расширенной обработкой
    
    :param command: Команда для выполнения
    :param timeout: Время ожидания выполнения команды в секундах (None для бесконечного ожидания)
    :param stream: Если True, возвращает генератор для потокового вывода
    :return: Результат выполнения команды или генератор вывода
    """
    try:
        # Используем cmd.exe для более надежного выполнения команд в Windows
        full_command = f'cmd.exe /c {command}'
        
        if stream:
            # Создаем процесс с потоковым выводом
            process = subprocess.Popen(
                full_command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='cp866',  # Кодировка для корректного отображения кириллицы в Windows
                errors='replace',
                bufsize=1  # Построчный буфер
            )
            
            def stream_output():
                try:
                    # Чтение stdout
                    for line in iter(process.stdout.readline, ''):
                        yield line.strip()
                    
                    # Чтение stderr
                    for line in iter(process.stderr.readline, ''):
                        yield line.strip()
                    
                    # Ожидание завершения процесса
                    process.wait()
                except Exception as e:
                    yield f"Streaming error: {str(e)}"
                finally:
                    process.stdout.close()
                    process.stderr.close()
            
            return stream_output()
        
        else:
            # Стандартное выполнение команды
            process = subprocess.Popen(
                full_command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='cp866',  # Кодировка для корректного отображения кириллицы в Windows
                errors='replace'
            )
            
            try:
                # Ожидаем завершения процесса с таймаутом
                stdout, stderr = process.communicate(timeout=timeout)
                
                # Объединяем stdout и stderr для полной информации
                output = stdout + stderr
                
                # Очищаем вывод от лишних пробелов
                output = output.strip()
                
                # Возвращаем результат или сообщение об ошибке
                if process.returncode == 0:
                    return output
                else:
                    return f"Command error (code {process.returncode}): {output}"
            
            except subprocess.TimeoutExpired:
                # Принудительно завершаем процесс при превышении таймаута
                process.kill()
                return f"Command timed out after {timeout} seconds"
    
    except Exception as e:
        # Обработка непредвиденных ошибок
        return f"Command execution error: {str(e)}"

def read_file(filepath):
    """Reads and returns file contents"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def analyze(path):
    """Analyzes and returns file/directory metadata"""
    try:
        stats = os.stat(path)
        if os.path.isfile(path):
            return {
                "type": "file",
                "size": stats.st_size,
                "owner": stats.st_uid,
                "permissions": oct(stats.st_mode)[-3:],
                "modified": time.ctime(stats.st_mtime)
            }
        elif os.path.isdir(path):
            # Детальный анализ содержимого директории
            items = []
            total_size = 0
            for entry in os.scandir(path):
                try:
                    entry_stats = entry.stat()
                    item_info = {
                        "name": entry.name,
                        "type": "directory" if entry.is_dir() else "file",
                        "size": entry_stats.st_size if not entry.is_dir() else None,
                        "modified": time.ctime(entry_stats.st_mtime),
                        "permissions": oct(entry_stats.st_mode)[-3:]
                    }
                    items.append(item_info)
                    if not entry.is_dir():
                        total_size += entry_stats.st_size
                except Exception as e:
                    # Если не удалось получить информацию о конкретном элементе
                    items.append({
                        "name": entry.name,
                        "error": str(e)
                    })
            
            return {
                "type": "directory",
                "total_items": len(items),
                "total_size": total_size,
                "owner": stats.st_uid,
                "permissions": oct(stats.st_mode)[-3:],
                "modified": time.ctime(stats.st_mtime),
                "contents": items
            }
        else:
            return "Path is neither a file nor a directory"
    except Exception as e:
        return f"Error analyzing path: {str(e)}"

def search(path, search_string):
    """Searches for string in file(s) and returns number of matches"""
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                return len(re.findall(search_string, content, re.IGNORECASE))
        elif os.path.isdir(path):
            total_matches = 0
            for root, _, files in os.walk(path):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            total_matches += len(re.findall(search_string, content, re.IGNORECASE))
                    except:
                        continue
            return total_matches
        else:
            return "Path is neither a file nor a directory"
    except Exception as e:
        return f"Error searching: {str(e)}"

def update_file(filepath, content, mode='replace'):
    """
    Изменяет содержимое файла
    
    :param filepath: Путь к файлу
    :param content: Новое содержимое или изменение
    :param mode: Режим изменения ('replace', 'append', 'prepend')
    :return: Результат операции или ошибка
    """
    try:
        # Читаем текущее содержимое файла
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                original_content = file.read()
        except FileNotFoundError:
            original_content = ''
        
        # Определяем режим изменения
        if mode == 'replace':
            new_content = content
        elif mode == 'append':
            new_content = original_content + content
        elif mode == 'prepend':
            new_content = content + original_content
        else:
            return f"Unsupported mode: {mode}"
        
        # Записываем новое содержимое
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        return {
            'status': 'success', 
            'original_content': original_content,
            'new_content': new_content,
            'changes': len(new_content) - len(original_content)
        }
    except Exception as e:
        return f"Error updating file: {str(e)}"
