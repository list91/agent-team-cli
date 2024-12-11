import asyncio
import sys
import time
import threading
import json
import os

class ChatBot:
    
    def __init__(self):
        self.filename = "context.json"
        self.default_content = {"history": []}
        self.init_local_context_history()
        

    def add_user_message(self, message):
        self.append_to_history({"User": message})

    def add_bot_message(self, message):
        self.append_to_history({"Assistent": message})

    def append_to_history(self, content):
        self.history['history'].append(content)
        # update the JSON file
        with open(self.filename, 'r+') as f:
            data = json.load(f)
            data['history'].append(content)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
        self.manage_history() # TODO dodelai ma local i file | I schitai tolko moi msg

    def init_local_context_history(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                # Use json.dump to write the dictionary to the file
                json.dump(self.default_content, f)
            self.history = self.default_content
        else:
            with open(self.filename, 'r') as f:
                # Use json.load to read the JSON file back into a dictionary
                self.history = json.load(f)

    def manage_history(self):
        # Limit history size
        if len(self.history) > 10:
            self.history.pop(0)

    async def send_request(self, prompt):
        await asyncio.sleep(2)
        response = f'Bot: Here is the response to your prompt. Here is a special signal: №%;№:?%:;%№743__0=Some important content here and another signal: №%;№:?%:;%№743__0='  # Simulated response with signal
        special_sym = '№%;№:?%:;%№743__0='
        response = response.replace(special_sym, ' __SIGNAL__ ')
        return response

    def display_spinner(self):
        spinner = ['|', '/', '-', '\\']  # Corrected escape character
        for _ in range(10):  # Show spinner for a short duration
            for symbol in spinner:
                sys.stdout.write(f'\rLoading... {symbol}')
                sys.stdout.flush()
                time.sleep(0.1)

    def run_chat(self):
        # print("Welcome to the chat!")
        while True:
            user_input = input('You: ')
            self.add_user_message(user_input)

            # Start spinner in a separate thread
            spinner_thread = threading.Thread(target=self.display_spinner)
            spinner_thread.start()

            # Create a prompt from history
            prompt = '\n'.join(self.history)

            # Send request asynchronously
            response = asyncio.run(self.send_request(prompt))
            self.add_bot_message(response)

            # Wait for spinner to finish
            spinner_thread.join()

            # Display bot response
            print(f'\n{response}')