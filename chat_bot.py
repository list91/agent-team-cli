import asyncio
import sys
import time
import threading
import json
import os
from nn import generate_response

class ChatBot:
    
    def __init__(self):
        self.special_sym = '№%;№:?%:;%№743__0='
        self.filename = "context.json"
        self.default_content = {"history": []}
        self.init_local_context_history()

    def add_user_message(self, message):
        self.append_to_history({"role": "user", "content": message})

    def add_bot_message(self, message):
        self.append_to_history({"role": "assistant", "content": message})

    def append_to_history(self, content):
        self.history['history'].append(content)
        # update the JSON file
        with open(self.filename, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data['history'].append(content)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=4)  # Указываем ensure_ascii=False
            f.truncate()
        self.manage_history() # TODO dodelai ma local i file | I schitai tolko moi msg

    def init_local_context_history(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.default_content, f, ensure_ascii=False)  # Указываем ensure_ascii=False
            self.history = self.default_content
        else:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.history = json.load(f)

    def manage_history(self):
        # Limit history size
        if len(self.history['history']) > 10:
            self.history['history'].pop(0)

    def get_format_signals(self, text):
        if self.special_sym in text:
            count = len([i for i in text.split('\n') if i.startswith(self.special_sym)])
            if count % 2 == 0:
                signal = text.split(self.special_sym)[-2]
                text = text.replace(signal, ' {__SIGNAL__} ')
        return text

    async def send_request(self, prompt):
        # response = f'Bot: Here is the response to your prompt. Here is a special signal: №%;№:?%:;%№743__0=analyze("some_path")№%;№:?%:;%№743__0='  # Simulated response with signal
        result = await asyncio.run(generate_response(prompt, []))
        # generate_response(prompt+"\n"+user_input, [])

        
        # count = len([i for i in result.split('\n') if i.startswith('{__SIGNAL__}')])

        

        # response = result.replace(special_sym, ' {__SIGNAL__} ')
        return self.get_format_signals(result)

    def display_spinner(self):
        spinner = ['|', '/', '-', '\\']  # Исправлен символ
        for _ in range(10):  # Show spinner for a short duration
            for symbol in spinner:
                sys.stdout.write(f'\rLoading... {symbol}')
                sys.stdout.flush()
                time.sleep(0.1)

    def run_chat(self):
        while True:
            user_input = input('You: ')
            self.add_user_message(user_input)

            # Start spinner in a separate thread
            spinner_thread = threading.Thread(target=self.display_spinner)
            spinner_thread.start()

            # Create a prompt from history
            prompt = '\n'.join([msg['content'] for msg in self.history['history']])  # TODO временно пока не сделанна передача контекста нормально

            response = asyncio.run(self.send_request(prompt + '\n' + user_input))
            # response = asyncio.run(generate_response(user_input, self.history['history']))
            self.add_bot_message(response)

            # Wait for spinner to finish
            spinner_thread.join()

            # Display bot response
            print(f'\n{response}')
