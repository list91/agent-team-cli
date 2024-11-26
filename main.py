import http.client
import json

def query_ollama(prompt):
    conn = http.client.HTTPConnection("localhost", 11434)
    
    payload = json.dumps({
        "model": "llama3.2",  # using your installed model
        "prompt": prompt,
        "stream": True
    })
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        conn.request("POST", "/api/generate", payload, headers)
        response = conn.getresponse()
        
        if response.status == 200:
            while True:
                chunk = response.readline()
                if not chunk:
                    break
                try:
                    data = json.loads(chunk.decode())
                    if 'response' in data:
                        print(data['response'], end='', flush=True)
                    if data.get('done', False):
                        break
                except json.JSONDecodeError:
                    continue
            return "Response completed"
        else:
            return f"Error: {response.status} - {response.reason}"
            
    except Exception as e:
        return f"Connection error: {str(e)}"
    finally:
        conn.close()

# Test the connection
if __name__ == "__main__":
    test_prompt = "I will provide you with text representing the output of a command executed in the console. Your task is to classify this text as follows: if it indicates successful execution of the command, return the number 1. If it indicates an error or failure, return the number 0. Please do not add any additional comments or explanations—just provide the number (1 or 0) in response. Note that the text to classify is enclosed between the markers '>&&63542764hsadnfhsksanjdH'. Here is the text for classification: [>&&63542764hsadnfhsksanjdHC:\\Users\\s_anu\\Downloads\\RPA>C:\\Users\\s_anu\\AppData\\Local\\Programs\\Ollama\\ollama.exe run llama3.2:1b pulling manifest pulling 74701a8c35f6... 100% ▕████████████████████████████████████████████████████████▏ 1.3 GB pulling 966de95ca8a6... 100% ▕████████████████████████████████████████████████████████▏ 1.4 KB pulling fcc5a6bec9da... 100% ▕████████████████████████████████████████████████████████▏ 7.7 KB pulling a70ff7e570d9... 100% ▕████████████████████████████████████████████████████████▏ 6.0 KB pulling 4f659a1e86d7... 100% ▕████████████████████████████████████████████████████████▏  485 B verifying sha256 digest writing manifest removing any unused layers success Error: llama runner process has terminated: exit status 0xc0000409>&&63542764hsadnfhsksanjdH]"
    print("Sending prompt to Ollama...")
    print("\nResponse:")
    print(query_ollama(test_prompt))