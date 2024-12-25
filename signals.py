import subprocess
import os
import time
import re
import json


# рун_коммнад - внутри доп оболочки выполняет команду, как только кончит так его вывод добавляем в конекст...отдаем ИИ и ждем ответа
# анализ - логика которая принимает путь и возвращает метаданные файла или директории (размер, владелец и т. д.), вывод добавляем в конекст...отдаем ИИ и ждем ответа
# чтение_файла - принимает путь к файлу и возвращает содержимое, вывод добавляем в конекст...отдаем ИИ и ждем ответа
# серч - принимает путь и строку, динамически ищет и вернет число совпадений, вывод добавляем в конекст...отдаем ИИ и ждем ответа
# создать_файл - принимает путь, строку, строку; создаст файл с заданным содержимым, именем, в заданном месте, вернет успех?, вывод добавляем в конекст...отдаем ИИ и ждем ответа
# редачить_файл? - экспериментально

def run_command(command):
    try:
        res = ""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory)
        while True:
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                break
            if output:
                res += output.decode('cp866').strip() + '\n'  # Декодируем строку в cp866
                print(res.strip())

        rc = process.poll()
        if rc != 0:
            error_output = process.stderr.read()
            try:
                print(f'Error: {error_output.decode("cp866")}')
            except UnicodeDecodeError:
                print(f'Error: {error_output.decode("utf-8", errors="replace")}')
                
        return res
    except Exception as e:
        return f'Error: {e}'

def analyze(path):
    try:
        if os.path.isfile(path):
            stat = os.stat(path)
            metadata = {
                'name': os.path.basename(path),
                'size': stat.st_size,
                'owner': stat.st_uid,
                'group': stat.st_gid,
                'permissions': oct(stat.st_mode & 0o777),
                'created': time.ctime(stat.st_ctime),
                'modified': time.ctime(stat.st_mtime),
                'accessed': time.ctime(stat.st_atime),
            }
            return metadata
        elif os.path.isdir(path):
            metadata_list = []
            for name in os.listdir(path):
                file_path = os.path.join(path, name)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    metadata = {
                        'name': name,
                        'size': stat.st_size,
                        'owner': stat.st_uid,
                        'group': stat.st_gid,
                        'permissions': oct(stat.st_mode & 0o777),
                        'created': time.ctime(stat.st_ctime),
                        'modified': time.ctime(stat.st_mtime),
                        'accessed': time.ctime(stat.st_atime),
                    }
                    metadata_list.append(metadata)
            return json.dumps(metadata_list, ensure_ascii=False)
        else:
            raise ValueError(f'{path} is not a valid path')
    except Exception as e:
        return f'Error: {e}'

def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f'Error: {e}'

def search(path, pattern):
    try:
        count = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                print(f'Checking: {file_path}')  # Debug line
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if re.search(pattern, line, re.IGNORECASE):
                                # print(f'Match found: {line.strip()}')
                                count += 1
                except Exception as e:
                    print(f'Error: {e}')
        return str(count)
    except Exception as e:
        return f'Error: {e}'

def create_file(path, content):
    try:
        print(f'Attempting to create file at: {path}')
        
        if not path:
            return 'Error: Path is empty.'
        
        dir_name = os.path.dirname(path)
        
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)

        with open(path, 'w', encoding='utf-8') as f:  # Убедитесь, что используете кодировку
            f.write(content)

        return 'Success'
    except Exception as e:
        return f'Error: {e}'

def update_file(path, content):
    try:
        content = content.replace('\\n', '\n')
        full_path = os.path.abspath(path)  # Получаем полный путь к файлу
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))
        if not os.path.exists(full_path):
            return f'File {full_path} does not exist'
        with open(full_path, 'w', encoding='utf-8') as f:  # Указываем кодировку UTF-8
            f.write(content)
        return 'Success'
    except Exception as e:
        return f'Error: {e}'

# print(create_file('qq1.txt', 'привет'))

# print(update_file("qq.txt", "выфв"))
# print(update_file('qq.txt', 'ee\ndfsdf\ngd\fg\n\nh\nfgh\ngdf\nh\n\n\ngfh\nfg\nh\ngfhgfh\n\nfghh\n\n\nsees\nfgr\nfv\nr\n\nrf\nfdgdfg\n\nfdgdfg\ng'))

# print(update_file('C:\\Users\\s_anu\\projects\\LlamaDevAssist\\qq.txt', '''see\\n\\ndfsdf\\ngd\\nfg\\n\\n\\nh\\nfgh\\ngdf\\nh\\n\\n\\n\\ngfh\\nfg\\nh\\ngfhgfh\\n\\nfghh\\n\\n\\nsees\\nfgr\\nfv\\nr\\n\\nrf\\nfdgdfg\\n\\nfdgdfg\\ng'''))

# Replace with the directory containing .gitignore
# print(search(r"C:\Users\s_anu\Downloads\RPA\proxy-pilot\venv", "see"))

# print(read_file(r"C:\Users\s_anu\Downloads\RPA\proxy-pilot\venv\.gitignore"))
# print(analyze("."))
# print(analyze("C:/Users/s_anu/projects/LlamaDevAssist"))
# q = run_command("dir")
# print(q)
# q = run_command("cd")
# print("qqq",q, "qqq")