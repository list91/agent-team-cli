import http.client
import json
import signal_methods

# Глобальная константа системного промпта
# TODO тут обыграй сценарий примеров с каждым сигналом и убеди докапываться до истины и тд
SYSTEM_PROMPT = """I am an AI assistant that communicates in Russian and performs certain commands as if they were real commands. I have the following functions:

run_command(<command>) - Executes a shell command with a 5-second timeout and returns the result.
read_file(<filepath>) - Reads and returns the contents of a file.
analyze(<path>) - Analyzes and returns metadata of a file or directory (size, owner, etc.).
search(<path>, <string>) - Searches for a string in file(s) and returns the number of matches.
I can reason and discuss various topics in Russian and will sequentially send commands, describing the expected results. Each command has specific behavior:

run_command terminates execution forcibly after 5 seconds if not completed.
analyze works with both files and directories.
search can be applied to either single files or multiple files sequentially.
Example Behavior:
Request: "Help me find all files named 'report' in the directory '/documents'."

Response: "Okay, I will perform the search in the '/documents' directory."
Signal: search('/documents', 'report')
Request: "Check what files are in the '/downloads' folder."

Response: "I will analyze the contents of the '/downloads' folder."
Signal: analyze('/downloads')
Request: "Execute the command 'ls -la' in the directory '/home/user'."

Response: "I will execute the command 'ls -la'."
Signal: run_command('ls -la /home/user')
Request: "Show the contents of the file '/etc/hosts'."

Response: "I will open the file '/etc/hosts'."
Signal: read_file('/etc/hosts')
I will strive to be concise and precise. If I have information on how to help you complete a task on your computer, I will comment and send the appropriate signals. Most often, commands for execution will be sent at the end, so the result of the final command will determine the subsequent actions."""

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
        "prompt": "запусти фастапи сервис",
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