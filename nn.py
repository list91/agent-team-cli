from ollama_client import OllamaClient
from signal_methods import *
import http.client
import json
import re
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_client_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys_prompt = """You are a Russian-speaking AI assistant that can execute commands and provide assistance. You have access to one signal:

run_command(<command>) - executes a shell command with a 5-second timeout and returns the result.

When sending a signal, you must enclose it between №%;№:?%:;%№*(743__0= and №%;№:?%:;%№*(743__0= markers so the external program can parse your signals.

Important rules:
1. Always communicate in Russian
2. If you need to execute a command, end your response with the signal
3. Be concise and clear in your responses
4. Format signals exactly as shown: №%;№:?%:;%№*(743__0=run_command('command')№%;№:?%:;%№*(743__0="""

class AIClient:
    def __init__(self):
        self.conversation_history = []
        
    def add_message(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        
    def get_response(self, user_input):
        # Обработка различных типов входных данных
        if isinstance(user_input, tuple):
            user_input = str(user_input)
        
        # Добавляем системный промпт в начало истории, если она пуста
        if not self.conversation_history:
            self.add_message("system", sys_prompt)
            
        # Добавляем сообщение пользователя
        self.add_message("user", user_input)
        
        try:
            # Получаем ответ от модели
            response = self.get_ai_response(user_input)
            
            if response:
                # Проверяем наличие сигнала выполнения команды
                if "№%;№:?%:;%№*(743__0=" in response:
                    # Извлекаем команду между маркерами
                    match = re.search(r'№%;№:?%:;%№\*\(743__0=(.*?)№%;№:?%:;%№\*\(743__0=', response)
                    if match:
                        command = match.group(1)
                        # Выполняем команду и получаем полный результат
                        cmd_result = run_command(command)
                        
                        # Форматируем результат для более понятного вывода
                        formatted_result = f"""
Выполнена команда: {command}

Полный вывод команды:
{cmd_result[0]}

Код завершения: {cmd_result[1]}
Успешность выполнения: {'Успешно' if cmd_result[1] == 0 else 'Ошибка'}
"""
                        # Логируем полную информацию о результате команды
                        logger.debug(f"Результат команды: {cmd_result}")
                        
                        # Создаем полный текст для передачи в ИИ
                        full_command_context = f"""
Пользователь запросил выполнить команду: {command}

{formatted_result}

Прошу проанализировать результат выполнения команды и дать пояснения."""
                        
                        # Логируем полный контекст, который будет передан
                        logger.debug(f"Полный контекст для ИИ:\n{full_command_context}")
                        
                        # Добавляем результат к ответу
                        response += f"\n\nРезультат выполнения команды:\n{formatted_result}"
                
                # Добавляем ответ в историю
                self.add_message("assistant", response)
                return response
            else:
                return "Извините, произошла ошибка при получении ответа от модели."
                
        except Exception as e:
            logger.error(f"Ошибка при получении ответа: {e}")
            return f"Произошла ошибка: {str(e)}"
            
    def reset_conversation(self):
        self.conversation_history = []
        
    def get_ai_response(self, prompt):
        try:
            # Обработка различных типов входных данных
            if isinstance(prompt, tuple):
                prompt = str(prompt)
            
            # Логируем входящий промпт
            logger.debug(f"Входящий промпт: {prompt}")
            
            print("Connecting to localhost:11434...")
            conn = http.client.HTTPConnection("localhost", 11434)
            
            # Для Windows-совместимой команды используем альтернативный вариант подсчета
            if "docker ps" in prompt and "wc -l" in prompt:
                prompt += "\n\nВажно: в Windows используй команду 'docker ps -q | find /c /v \"\"' вместо 'docker ps | wc -l'"
            
            payload = json.dumps({
                "model": "qwen2.5-coder",
                "system": sys_prompt,
                "prompt": prompt,
                "stream": True
            })
            
            # Логируем полный payload
            logger.debug(f"Payload для запроса:\n{payload}")
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            print("Sending request...")
            conn.request("POST", "/api/generate", payload, headers)
            print("Getting response...")
            res = conn.getresponse()
            print(f"Response status: {res.status} {res.reason}")
            
            # Логируем статус ответа
            logger.debug(f"Статус ответа: {res.status} {res.reason}")
            
            accumulated_response = ""
            buffer = b""
            
            while True:
                chunk = res.read(1024)
                if not chunk:
                    break
                    
                buffer += chunk
                
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if not line.strip():
                        continue
                    
                    try:
                        # Декодируем строку с указанием кодировки
                        line_str = line.decode('utf-8', errors='replace')
                        response = json.loads(line_str)
                        if 'response' in response:
                            current_text = response['response']
                            print(current_text, end='', flush=True)
                            accumulated_response += current_text
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.error(f"Ошибка декодирования: {e}")
                        continue
            
            # Process any remaining buffer content
            if buffer.strip():
                try:
                    # Декодируем оставшийся буфер
                    buffer_str = buffer.decode('utf-8', errors='replace')
                    response = json.loads(buffer_str)
                    if 'response' in response:
                        current_text = response['response']
                        print(current_text, end='', flush=True)
                        accumulated_response += current_text
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"Ошибка финального декодирования: {e}")
            
            print("\nComplete response:", accumulated_response)
            
            # Логируем полный накопленный ответ
            logger.debug(f"Полный ответ от модели:\n{accumulated_response}")
            
            return accumulated_response
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            return None

# client = AIClient()
# result = client.get_response(message)
# print(result)

# print(run_command("docker ps"))

# if "№%;№:?%:;%№*(743__0=" in result:
#     between = result.split("№%;№:?%:;%№*(743__0=")[1].split("№%;№:?%:;%№*(743__0=")[0]
#     if "run_command" in between: 
#         command = between.split("run_command('")[1].split("')")[0]
#         print(run_command(command))
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = ChatApp(root)
#     root.mainloop()