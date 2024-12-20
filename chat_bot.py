import asyncio
import sys
import time
import threading
import json
import os
from nn import generate_response
from signals import *

class ChatBot:
    
    def __init__(self):
        self.special_sym = '№%;№:?%:;%№(743__0='
        self.filename = "context.json"
        self.default_content = {"history": []}
        self.init_local_context_history()

    def add_user_message(self, message):
        self.append_to_history({"role": "user", "content": message})

    def add_bot_message(self, message):
        self.append_to_history({"role": "assistant", "content": message})

    def append_to_history(self, content):
        self.history['history'].append(content)
        # Обновление JSON файла
        with open(self.filename, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data['history'].append(content)
            f.seek(0)  # Переместить указатель в начало файла
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.truncate()  # Удалить лишние данные
        self.manage_history()

    def init_local_context_history(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.default_content, f, ensure_ascii=False)
            self.history = self.default_content
        else:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.history = json.load(f)

    def manage_history(self):
        if len(self.history['history']) > 10:
            self.history['history'].pop(0)

    def is_signals(self, text):
        if self.special_sym in text:
            count = text.count(self.special_sym)
            return count % 2 == 0
        return False

    def get_signal_params(self, signal):
        left = None
        right = None
        if "('" in signal and "')" in signal:
            left = signal.index("('")
            right = signal.index("')")
        elif '("' in signal and '")' in signal:
            left = signal.index('("')
            right = signal.index('")')
        else:
            return None
        
        signal_params = signal[left+2:right]
        q = []
        for i in signal_params:
            q.append(i.replace('"', '').replace("'", ""))
        # signal_params = self.get_signal_params(signal)
        return q        

    async def send_request(self, prompt):
        try:
            result = await generate_response(prompt, self.history['history'])
            self.spinner_thread.join()
            self.add_bot_message(result.replace(' {__SIGNAL__} ', self.special_sym))
            print(f'\n{result.replace(' {__SIGNAL__} ', self.special_sym)}')
            if self.is_signals(result):
                signal = result.split(self.special_sym)[-2]
                res = None
                if "run_command" in signal:
                    try:
                        user_input = input('\nВыбери 1 или 0: ')
                        if user_input == '1':
                            signal_params = self.get_signal_params(signal)
                            res = run_command(signal_params)
                            print(res)
                            self.add_user_message("Результат выполнения run_command:", res)
                        else:
                            print('Сигнал отменен.')
                    except Exception as e:
                        res = e

                elif "search" in signal:
                    try:
                        user_input = input('\nВыбери 1 или 0: ')
                        if user_input == '1':
                            signal_params = self.get_signal_params(signal)
                            res = search(signal_params.split(', ')[0], signal_params.split(', ')[1])
                            print(res)
                            self.add_user_message("Результат выполнения search:", res)
                        else:
                            print('Сигнал отменен.')
                    except Exception as e:
                        res = e

                elif "analyze" in signal:
                    try:
                        user_input = input('\nВыбери 1 или 0: ')
                        if user_input == '1':
                            signal_params = self.get_signal_params(signal)
                            res = analyze(signal_params)
                            print(res)
                            self.add_user_message("Результат выполнения analyze:", res)
                        else:
                            print('Сигнал отменен.')
                    except Exception as e:
                        res = e

                elif "create_file" in signal:
                    try:
                        user_input = input('\nВыбери 1 или 0: ')
                        if user_input == '1':
                            signal_params = self.get_signal_params(signal)
                            res = create_file(signal_params.split(', ')[0], signal_params.split(', ')[1])
                            print(res)
                            self.add_user_message("Результат выполнения create_file:", res)
                        else:
                            print('Сигнал отменен.')
                    except Exception as e:
                        res = e

                elif "update_file" in signal:
                    try:
                        user_input = input('\nВыбери 1 или 0: ')
                        if user_input == '1':
                            signal_params = self.get_signal_params(signal)
                            q = signal_params.split(', ')
                            print(q)
                            res = update_file(signal_params.split(', ')[0], signal_params.split(', ')[1])
                            print(res)
                            self.add_user_message("Результат выполнения update_file:", res)
                        else:
                            print('Сигнал отменен.')
                    except Exception as e:
                        res = e

                elif "read_file" in signal:
                    try:
                        user_input = input('\nВыбери 1 или 0: ')
                        if user_input == '1':
                            signal_params = self.get_signal_params(signal)
                            res = read_file(signal_params)
                            print(res)
                            self.add_user_message("Результат выполнения read_file:", res)
                        else:
                            print('Сигнал отменен.')
                    except Exception as e:
                        res = e

                if res is not None:
                    res = str(res)
                    print(res)
                    # prompt = self.get_history_prompt()
                    await self.send_request({"role": "user", "content": "Результат выполнения сигнала:"+ res})
        except Exception as e:
            q = 1
            print(f"Ошибка генерации ответа: {e}")

    def display_spinner(self):
        spinner = ['|', '/', '-', '\\']  # Исправлен символ
        for _ in range(9):
            for symbol in spinner:
                sys.stdout.write(f'\rLoading... {symbol}')
                sys.stdout.flush()
                time.sleep(0.1)

    def get_history_prompt(self):
        return "\n".join([f"{entry['role']}: {entry['content']}" for entry in self.history['history']])

    async def run_chat(self):
        while True:
            user_input = input('You: ')
            self.add_user_message(user_input)

            # Запускаем спиннер в отдельном потоке
            self.spinner_thread = threading.Thread(target=self.display_spinner)
            self.spinner_thread.start()

            # Создаем подсказку из истории
            prompt = self.get_history_prompt()

            await self.send_request({"role": "user", "content": user_input})
            
            # Ждем завершения спиннера
            

# Пример использования
if __name__ == "__main__":
    chatbot = ChatBot()
    asyncio.run(chatbot.run_chat())
