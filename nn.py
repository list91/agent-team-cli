from gradio_client import Client
from config import *
import asyncio
client = Client("DHEIVER/chat-Llama-3.3-70B")

def generate_response(
    message, 
    chat_history=None, 
    max_tokens=2048, 
    temperature=0.7, 
    top_p=0.95, 
    language="en"
):
    # if not client_config:
    #     return "Клиент не инициализирован"
    client_config = {
                        'client': client,
                        'system_message': system_prompt_ru
                    }
    try:
        result = client_config['client'].predict(
            message=message,
            chat_history=[
                {
                    'role': 'user',
                    'metadata': None,
                    'content': "привет, зебру зовут Бэн",
                    'options': None
                },
                {
                    'role': 'assistant',
                    'metadata': None,
                    'metadata': None,
                    'content': "привет, окей",
                    'options': None
                }
            ],
            system_message=client_config['system_message'],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            language=language,
            api_name="/respond"
        )
        # Извлекаем текст ответа из кортежа
        if isinstance(result, tuple):
            result = result[0][1]['content'] if result[0] else "Пустой ответ"
        return result
    except Exception as e:
        return f"Ошибка генерации ответа: {e}"


# result = generate_response("удали последние 2 строки из файла маинПай")
# print(result)

async def generate_response(message, history):
    try:
        result = client.predict(
            message=message,
            chat_history=history,
            system_message=system_prompt_ru,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.95,
            language="en",
            api_name="/respond"
        )
        
        if isinstance(result, tuple):
            result = result[0][1]['content'] if result[0] else "Пустой ответ"
        
        return result
    except Exception as e:
        return f"Ошибка генерации ответа: {e}"
        
# q = asyncio.run(generate_response("напомни как ее зовут?", [
#                 {
#                     'role': 'dsad',
#                     # 'metadata': None,
#                     'content': "привет, зебру зовут Бэн",
#                     # 'options': None
#                 },
#                 {
#                     'role': 'aawssd',
#                     # 'metadata': None,
#                     'content': "привет, окей",
#                     # 'options': None
#                 }
#             ],))
# print(q)

"""
Dict(role: str, metadata: None, content: str, options: None)
"""

