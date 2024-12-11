import subprocess
import os
import time
import re
# рун_коммнад - внутри доп оболочки выполняет команду, как только кончит так его вывод добавляем в конекст...отдаем ИИ и ждем ответа
# анализ - логика которая принимает путь и возвращает метаданные файла или директории (размер, владелец и т. д.), вывод добавляем в конекст...отдаем ИИ и ждем ответа
# чтение_файла - принимает путь к файлу и возвращает содержимое, вывод добавляем в конекст...отдаем ИИ и ждем ответа
# серч - принимает путь и строку, динамически ищет и вернет число совпадений, вывод добавляем в конекст...отдаем ИИ и ждем ответа
# создать_файл - принимает путь, строку, строку; создаст файл с заданным содержимым, именем, в заданном месте, вернет успех?, вывод добавляем в конекст...отдаем ИИ и ждем ответа
# редачить_файл? - экспериментально

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode('cp866')
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    if rc != 0:
        print(f'Error: {process.stderr.read().decode("utf-8")}')

def analyze(path):
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
        return metadata_list
    else:
        raise ValueError(f'{path} is not a valid path')

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def search(path, pattern):
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
    return count

# создать_файл TODO

# Replace with the directory containing .gitignore
print(search(r"C:\Users\s_anu\Downloads\RPA\proxy-pilot\venv", "see"))

# print(read_file(r"C:\Users\s_anu\Downloads\RPA\proxy-pilot\venv\.gitignore"))
# print(analyze(r"C:\Users\s_anu\Downloads\RPA\proxy-pilot\venv\.gitignore"))
# run_command("dir")
# run_command("ping 8.8.8.8")