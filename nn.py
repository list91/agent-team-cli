# -*- coding: utf-8 -*-

from gradio_client import Client
from config import *
import asyncio
import re
import asyncio
from openai import OpenAI
import re
import asyncio
from datetime import datetime, timedelta

class NN():
    def __init__(self, key):
        self.set_token(key)
        self.system_prompt = system_prompt_ru
    
    def set_token(self, key):
        self.current_token = key
        self.client = OpenAI(api_key=self.current_token)
        self.accoutn_log_clear()

    def accoutn_log_clear(self):
        self.accoutn_log = {"rate_limit": False, "future_timestamp": 0, "is_locked": None}

    async def generate_response(self, message, history):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": self.system_prompt}] + history + [message],
                store=True,
            )
            result = completion.choices[0].message.content
            return result
        except Exception as e:
            print(self.handle_error(e))
            return e
        
    def handle_error(self, error):
        if "Rate limit reached" in str(error):
            time_remaining = self.extract_time_remaining(str(error))
            return f"Ошибка генерации ответа: {str(error)}. Ожидание: {time_remaining}"
        if 'account_deactivated' in str(error):
            self.account_deactivated()
            return f"Ошибка генерации ответа: {str(error)}. Деактивируем аккаунт"
        return f"Ошибка генерации ответа: {str(error)}"

    def account_deactivated(self):
        self.accoutn_log["is_locked"] = True

    def extract_time_remaining(self, error_message):
        match = re.search(r'Please try again in (\d+h)?(\d+m)?(\d+s)?', error_message)
        if match:
            hours = int(match.group(1)[:-1]) if match.group(1) else 0
            minutes = int(match.group(2)[:-1]) if match.group(2) else 0
            seconds = int(match.group(3)[:-1]) if match.group(3) else 0
            
            # Calculate total seconds
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Calculate the future timestamp in global seconds
            current_time = datetime.fromisoformat('2024-12-23T16:50:35+07:00')
            current_timestamp = int(current_time.timestamp())
            future_timestamp = current_timestamp + total_seconds
            
            self.accoutn_log["rate_limit"] = True
            self.accoutn_log["future_timestamp"] = future_timestamp
            # print(f"Текущее время (timestamp): {current_timestamp}")
            # print(f"Время ожидания (секунды): {total_seconds}")
            # print(f"Будет доступно (timestamp): {future_timestamp}")
            
            # return f"{hours}h {minutes}m {seconds}s"
        return "Неизвестно"

# Пример использования
# openai_token_wait1_to_24_12_2024 = "ваш_токен"  # Замените на ваш токен
# response = asyncio.run(NN(openai_token_wait1_to_24_12_2024).generate_response({"role": "user", "content": "какая версия докера?"}, []))
# print(response)
