from gradio_client import Client
from config import *
import asyncio
from openai import OpenAI


# client = Client("DHEIVER/chat-Llama-3.3-70B")

async def generate_response_old(message, history):
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

client = OpenAI(api_key=openai_token)

async def generate_response(message, history):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history + [message], # TODO тут мессадж это словарь
            # messages=[{"role": "system", "content": system_prompt_ru}] + history + [{"role": "user", "content": message}],
            store=True,
            # messages=[
            #     {"role": "system", "content": system_prompt_ru},
            #     {"role": "user", "content": message}
            # ],
            # stream=True,
        )
        result = completion.choices[0].message.content
        return result
    except Exception as e:
        return f"Ошибка генерации ответа: {e}"

# print(asyncio.run(generate_response({"role": "user", "content": "какая версия докера?"}, [])))        

# from openai import OpenAI

# client = OpenAI(
#   api_key="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"
# )

# completion = client.chat.completions.create(
#   model="gpt-4o-mini",
#   store=True,
#   messages=[
#     {"role": "user", "content": "write a haiku about ai"}
#   ]
# )

# print(completion.choices[0].message);


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


# from openai import OpenAI


# completion = client.chat.completions.create(
#   model="gpt-4o-mini",
#   store=True,
#   messages=[
#     {"role": "system", "content": system_prompt_ru},
#     {"role": "user", "content": "сколько контейнеров щас работает?"}
#   ]
# )

# print(completion.choices[0].message);
