import subprocess
import os
import time
import re

def run_command(command):
    """Executes a shell command with 5-second timeout and returns the result"""
    try:
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        try:
            stdout, stderr = process.communicate(timeout=5)
            return stdout if process.returncode == 0 else stderr
        except subprocess.TimeoutExpired:
            process.kill()
            return "Command timed out after 5 seconds"
    except Exception as e:
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
