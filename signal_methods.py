import subprocess
import os
import time
import re

def run_command(command, timeout=5):
    """
    Выполняет команду в оболочке с расширенной обработкой
    
    :param command: Команда для выполнения
    :param timeout: Время ожидания выполнения команды в секундах
    :return: Результат выполнения команды или сообщение об ошибке
    """
    try:
        # Используем cmd.exe для более надежного выполнения команд в Windows
        full_command = f'cmd.exe /c {command}'
        
        # Создаем процесс с перенаправлением вывода
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
            return "Command timed out after {} seconds".format(timeout)
    
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
            items = len(os.listdir(path))
            return {
                "type": "directory",
                "items_count": items,
                "owner": stats.st_uid,
                "permissions": oct(stats.st_mode)[-3:],
                "modified": time.ctime(stats.st_mtime)
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
