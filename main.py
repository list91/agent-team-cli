import http.client
import json
import signal_methods

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
        "system": """I am an AI assistant that communicates in Russian and pretends to perform the following signals (I will describe what would happen if these were real commands):
1. run_command(<command>) - Executes a shell command with 5-second timeout and returns the result
2. read_file(<filepath>) - Reads and returns file contents
3. analyze(<path>) - Analyzes and returns file/directory metadata (size, owner, etc.)
4. search(<path>, <string>) - Searches for string in file(s) and returns number of matches

I can reason and discuss in Russian, and I will pretend to perform actions through these specific signals, describing what would happen. Each signal has specific behavior:
- run_command will forcefully terminate after 5 seconds if not completed
- analyze works on both files and directories
- search can be applied to single files or multiple files sequentially

I will respond as if I am actually executing these commands and provide realistic responses in Russian.""",
        "prompt": "все ли контейнеры запушенны щас?",
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