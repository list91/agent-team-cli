import asyncio
import sys
import time
import threading
import json
import os
from nn import NN
from signals import *
from config import *
from accounts_controller import AccountsController

class ChatBot:
    
    def __init__(self):
        self.NN = NN("")
        self.accounts_controller = AccountsController()
        self.set_active_token()
        self.special_sym = '№%;№:?%:;%№(743__0='
        self.filename = "context.json"
        self.init_local_context_history()

    def set_token_for_nn(self, key):
        self.NN.set_token(key)

    def set_active_token(self):
        self.set_token_for_nn(self.accounts_controller.get_active_token())
        if self.NN.current_token is None:
            print("Токен не найден. Пожалуйста, введите токен:")
            self.NN.current_token = input()

    def add_user_message(self, message):
        self.append_to_history({"role": "user", "content": message})

    def add_bot_message(self, message):
        self.append_to_history({"role": "assistant", "content": message})

    def append_to_history(self, content):
        self.history['history'].append(content)
        with open(self.filename, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data['history'].append(content)
            f.seek(0)  # Переместить указатель в начало файла
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.truncate()  # Удалить лишние данные
        self.manage_history()

    def init_local_context_history(self):
        if not os.path.exists(self.filename):
            self.default_content = {"history": [{"role": "system", "content": system_prompt_ru + "\nТекущий каталог:" + str(run_command("cd"))}]}
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
        return ''.join(q)

    async def send_request(self, prompt):
        try:
            result = await self.NN.generate_response(prompt, self.history['history'])
            if self.NN.accoutn_log["rate_limit"]:
                # помечаю текущий токен как неактуальный
                self.accounts_controller.update_account(
                    self.NN.current_token,
                    self.NN.accoutn_log["future_timestamp"],
                    False,
                    False
                )

                # обновляю активный токен
                self.set_active_token()
                pass
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
                            print(signal_params)
                            res = run_command(signal_params)
                            print(res)
                            self.add_user_message("Результат выполнения run_command:" + str(res))
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
                            self.add_user_message("Результат выполнения search:" + str(res))
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
                            self.add_user_message("Результат выполнения analyze:" + str(res))
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
                            self.add_user_message("Результат выполнения create_file:" + str(res))
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
                            self.add_user_message("Результат выполнения update_file:" + str(res))
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
                            self.add_user_message("Результат выполнения read_file:" + str(res))
                        else:
                            print('Сигнал отменен.')
                    except Exception as e:
                        res = e

                if res is not None:
                    res = str(res)
                    print(res)
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
            self.spinner_thread = threading.Thread(target=self.display_spinner)
            self.spinner_thread.start()
            prompt = self.get_history_prompt()
            await self.send_request({"role": "user", "content": user_input})
            

# Пример использования
if __name__ == "__main__":
    chatbot = ChatBot()
    asyncio.run(chatbot.run_chat())


# из файла qq.txt убери цифры