import http.client
import json

class OllamaClient:
    def __init__(self, model="qwen2.5-coder:32b", host="localhost", port=11434):
        self.model = model
        self.host = host
        self.port = port
        
    def _format_messages(self, messages):
        """Форматирует историю сообщений в единый промпт"""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt += f"{content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        
        prompt += "Assistant: "
        return prompt

    def chat(self, messages):
        try:
            conn = http.client.HTTPConnection(self.host, self.port)
            
            # Форматируем историю сообщений в промпт
            prompt = self._format_messages(messages)
            
            # Подготавливаем данные запроса
            payload = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": True
            })
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Отправляем запрос
            conn.request("POST", "/api/generate", payload, headers)
            res = conn.getresponse()
            
            if res.status != 200:
                raise Exception(f"API request failed with status {res.status}: {res.reason}")
            
            # Обрабатываем потоковый ответ
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
                            accumulated_response += response['response']
                    except json.JSONDecodeError:
                        continue
            
            # Обрабатываем оставшийся буфер
            if buffer.strip():
                try:
                    response = json.loads(buffer)
                    if 'response' in response:
                        accumulated_response += response['response']
                except json.JSONDecodeError:
                    pass
                    
            return accumulated_response
            
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            return None
        finally:
            conn.close()
