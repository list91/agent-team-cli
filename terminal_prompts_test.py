import http.client
import json
import socket

def handle_api_error(response_text):
    """Обработка ошибок API"""
    try:
        error_data = json.loads(response_text)
        if 'error' in error_data:
            if 'rate limit exceeded' in error_data['error'].lower():
                return "Превышен лимит запросов к API. Пожалуйста, подождите примерно час и попробуйте снова."
            return f"Ошибка API: {error_data['error']}"
    except json.JSONDecodeError:
        return f"Неожиданный ответ от сервера: {response_text}"
    return "Неизвестная ошибка API"

def send_prompt_to_llm(prompt):
    """Отправка промпта в LLM с потоковой обработкой"""
    try:
        print("Connecting to localhost:11434...")
        conn = http.client.HTTPConnection("localhost", 11434)
        payload = json.dumps({
            "model": "llama3.2",
            "system": """You are an AI assistant capable of sending signals to execute various actions.

Follow the user's requirements carefully and to the letter. First, think step-by-step and describe your plan for what to build in pseudocode, written out in great detail. Then, output the code in a single code block. Minimize any other prose.""",
            "prompt": prompt,
            "stream": True
        })
        headers = {
            'Content-Type': 'application/json'
        }
        
        print("Sending request...")
        conn.request("POST", "/api/generate", payload, headers)
        print("Getting response...")
        res = conn.getresponse()
        print(f"Response status: {res.status} {res.reason}")
        
        if res.status != 200:
            error_text = res.read().decode('utf-8')
            print(handle_api_error(error_text))
            return None

        accumulated_response = ""
        buffer = ""
        
        while True:
            chunk = res.read(1024)
            if not chunk:
                break
                
            buffer += chunk.decode('utf-8')
            
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line.strip():
                    continue
                    
                try:
                    response = json.loads(line)
                    if 'response' in response:
                        current_text = response['response']
                        print(current_text, end='', flush=True)
                        accumulated_response += current_text
                except json.JSONDecodeError:
                    continue
        
        # Process any remaining buffer content
        if buffer.strip():
            try:
                response = json.loads(buffer)
                if 'response' in response:
                    current_text = response['response']
                    print(current_text, end='', flush=True)
                    accumulated_response += current_text
            except json.JSONDecodeError:
                pass
        
        print("\nComplete response:", accumulated_response)
        return accumulated_response
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

# Словарь промптов с командами
terminal_prompts = {
    1: {
        "prompt": "слушай, как мне узнать сколько места на диске?",
        "expected_command": "df -h",
        "description": "Показать занятость диска"
    },
    2: {
        "prompt": "блин, комп тормозит, какие процессы жрут память?",
        "expected_command": "top",
        "description": "Список активных процессов"
    },
    3: {
        "prompt": "чел, мне нужно посмотреть что в папке, помоги",
        "expected_command": "ls",
        "description": "Содержимое текущей директории"
    },
    4: {
        "prompt": "какую хренотень мне показать в текущей директории?",
        "expected_command": "dir",
        "description": "Содержимое директории (Windows)"
    },
    5: {
        "prompt": "блин, не понимаю как посмотреть ip адрес",
        "expected_command": "ipconfig",
        "description": "Информация о сетевых интерфейсах"
    },
    6: {
        "prompt": "эй, как мне глянуть какие порты заняты?",
        "expected_command": "netstat -tuln",
        "description": "Список открытых портов"
    },
    7: {
        "prompt": "народ, как узнать версию оперативки?",
        "expected_command": "free -h",
        "description": "Информация о памяти"
    },
    8: {
        "prompt": "падажжи, как посмотреть размер файлов в папке?",
        "expected_command": "du -sh *",
        "description": "Размер файлов в текущей директории"
    },
    9: {
        "prompt": "блин, как мне глянуть историю команд?",
        "expected_command": "history",
        "description": "История выполненных команд"
    },
    10: {
        "prompt": "йоу, как посмотреть кто сейчас залогинен в системе?",
        "expected_command": "who",
        "description": "Список залогиненных пользователей"
    }
}

def main():
    print("🔍 Тестирование промптов для терминальных команд:\n")
    
    for num, details in terminal_prompts.items():
        print(f"Промпт #{num}: {details['prompt']}")
        print(f"Предполагаемая команда: {details['expected_command']}")
        print(f"Описание: {details['description']}")
        
        # Отправляем промпт в LLM
        llm_response = send_prompt_to_llm(details['prompt'])
        
        print("\nПолный ответ LLM:")
        if llm_response:
            print(llm_response)
        else:
            print("Не удалось получить ответ")
        
        print("-" * 50 + "\n")

if __name__ == "__main__":
    main()
