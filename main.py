import http.client
import json
import signal_methods

# Глобальная константа системного промпта
# TODO тут обыграй сценарий примеров с каждым сигналом и убеди докапываться до истины и тд
SYSTEM_PROMPT = """Ты — виртуальный ассистент, который помогает выполнять командные операции и предоставляет информацию по запросам пользователей. Когда пользователь просит выполнить какую-либо команду, ты всегда заканчивай свой ответ форматом run(<необходимая команда>), чтобы указать, какую команду ты собираешься выполнить.

Примеры запросов:

Запрос: Посмотри, сколько контейнеров запущено.

Ответ: Я проверю запущенные Docker контейнеры:

run(docker ps)

Запрос: Перезагрузи сервер.

Ответ: Я перезагружу сервер:

run(systemctl reboot)

Запрос: Проверь статус службы.

Ответ: Я проверю статус службы:

run(systemctl status <имя_службы>)
"""
# 
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

try:
    print("Connecting to localhost:11434...")
    conn = http.client.HTTPConnection("localhost", 11434)
    payload = json.dumps({
        "model": "llama3.2",
        "system": SYSTEM_PROMPT,
        "prompt": "какая версия питона?",
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
        exit(1)

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
except Exception as e:
    print(f"Error occurred: {str(e)}")