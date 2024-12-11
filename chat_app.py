import asyncio
import sys
import time
import threading

class ChatBot:
    def __init__(self):
        self.history = []

    def add_user_message(self, message):
        self.history.append(f'User: {message}')
        self.manage_history()

    def manage_history(self):
        # Limit history size
        if len(self.history) > 10:
            self.history.pop(0)

    import re

    async def send_request(self, prompt):
        # Simulate an asynchronous request to an AI model
        await asyncio.sleep(2)  # Simulating network delay
        response = f'Bot: Here is the response to your prompt. Here is a special signal: №%;№:?%:;%№*(743__0=Some important content here and another signal: №%;№:?%:;%№*(743__0='  # Simulated response with signal

        # Use regex to find content between special symbols
        pattern = r'№%;№:?%:;%№\*\(743__0=(.*?)№%;№:?%:;%№\*\(743__0='
        matches = re.findall(pattern, response)

        if matches:
            main_response = response.split('№%;№:?%:;%№*(743__0=')[0].strip()
            extracted_content = matches[0].strip()  # Get the first match
            return main_response + f'\n[Signal Content]: {extracted_content}'  # Return formatted response

        return response

    def display_spinner(self):
        spinner = ['|', '/', '-', '\\']  # Corrected escape character
        for _ in range(10):  # Show spinner for a short duration
            for symbol in spinner:
                sys.stdout.write(f'\rLoading... {symbol}')
                sys.stdout.flush()
                time.sleep(0.1)

    def run_chat(self):
        print("Welcome to the chat!")
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

            # Wait for spinner to finish
            spinner_thread.join()

            # Display bot response
            print(f'\n{response}')

if __name__ == '__main__':
    chat_bot = ChatBot()
    chat_bot.run_chat()
