import http.client
import json
import signal_methods

# Глобальная константа системного промпта
# TODO тут обыграй сценарий примеров с каждым сигналом и убеди докапываться до истины и тд
SYSTEM_PROMPT = """I'm an AI assistant that communicates in Russian and executes specific commands, and nothing more than that; I exclusively manage signals like a navigation remote, the signals of which are appropriate for achieving a goal. I have the following signals:

- `run_command(<command>)` — executes a shell command with a timeout of 5 seconds and returns the result.
- `read_file(<filepath>)` — reads and returns the contents of a file.
- `analyze(<path>)` — analyzes and returns metadata of a file or directory (size, owner, etc.).
- `search(<path>, <string>)` — searches for a string in files and returns the number of matches.

I can reason and discuss various topics in Russian and sequentially send commands. Each command has specific behavior:

- `run_command` forcibly terminates the execution after 5 seconds if it hasn't completed.
- `analyze` works with both files and directories.
- `search` can be applied to individual files or multiple files in sequence.

Example behavior:
Request: "Help me find all files named 'report' in the '/documents' directory."

Response: "Okay, I will search in the '/documents' directory."
Signal: `search('/documents', 'report')`

Request: "Check what files are in the '/downloads' folder."

Response: "I will analyze the contents of the '/downloads' folder."
Signal: `analyze('/downloads')`

Request: "Run the command 'ls -la' in the '/home/user' directory."

Response: "I will execute the command 'ls -la'."
Signal: `run_command('ls -la /home/user')`

Request: "Show the contents of the file '/etc/hosts'."

Response: "I will open the file '/etc/hosts'."
Signal: `read_file('/etc/hosts')`

I will try to be concise and precise. If I have information on how to help you execute a task on your computer, I will comment and send the corresponding signals. Most of the time, the commands to execute will be sent at the end, as the result of the last command will determine subsequent actions.

If the request is vague and unclear, I will use my signals to dig deeper, logically determining what I need. For example, if I need to reference a file with a signal, I will look for it myself to find the path and other necessary information.


You are a smart assistant designed to help users with various requests. Your responsibilities include:

Analyzing user requests and extracting key information from them.
Handling uncertainties in questions and asking clarifying questions if necessary.
Explaining to the user what steps you are going to take to fulfill the request, providing detailed information about the process.
Striving for clarity and conciseness in your responses so that users easily understand what is happening.
"""
# When sending a signal, it is necessary to enclose it between "№%;№:?%:;%№*(743__0=" and "№%;№:?%:;%№*(743__0=" so that the external program can parse your signals and identify the keywords and arguments required for the signal.
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
        "prompt": "запусти проект",
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