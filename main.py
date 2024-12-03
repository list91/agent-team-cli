import tkinter as tk
from tkinter import ttk
import datetime
import asyncio
import threading
from gradio_client import Client
import queue
from nn import sys_prompt
from signal_methods import *

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat")
        self.root.geometry("600x800")
        
        # Initialize Gradio client
        self.client = Client("Nymbo/Qwen2.5-Coder-32B-Instruct-Serverless")
        
        # Message queue for async processing
        self.message_queue = queue.Queue()
        
        # Configure style
        self.user_bg = "#e3f2fd"
        self.bot_bg = "#f5f5f5"
        self.user_fg = "#60476c"  # Темно-фиолетовый для пользователя
        self.bot_fg = "#2c3e50"   # Темно-синий для бота
        style = ttk.Style()
        style.configure("User.TFrame", background=self.user_bg)
        style.configure("Bot.TFrame", background=self.bot_bg)
        
        # Create main container
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create chat display area
        self.chat_frame = ttk.Frame(main_container)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable canvas for messages
        self.canvas = tk.Canvas(self.chat_frame, background="#ffffff")
        self.scrollbar = ttk.Scrollbar(self.chat_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=580)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind canvas resize to update the scrollable window width
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas.pack(side="left", fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Create input area
        input_frame = ttk.Frame(main_container)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create spinner
        self.spinner_label = ttk.Label(input_frame, text="⌛")
        
        send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Bind Enter key to send message
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Start message processing thread
        self.processing_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.processing_thread.start()

    def show_spinner(self):
        self.spinner_label.pack(side=tk.RIGHT, padx=(5, 5))
        self.message_entry.configure(state="disabled")
        self.root.update()

    def hide_spinner(self):
        self.spinner_label.pack_forget()
        self.message_entry.configure(state="normal")
        self.root.update()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_canvas_configure(self, event):
        # Update the width of the scrollable window when the canvas is resized
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def create_message_bubble(self, text, is_user=True, with_buttons=False):
        # Create message frame
        message_frame = ttk.Frame(
            self.scrollable_frame,
            style="User.TFrame" if is_user else "Bot.TFrame"
        )
        message_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M")
        time_label = tk.Label(
            message_frame,
            text=timestamp,
            font=("Arial", 8),
            background=self.user_bg if is_user else self.bot_bg,
            foreground=self.user_fg if is_user else self.bot_fg
        )
        time_label.pack(anchor="ne" if is_user else "nw", padx=5)
        
        # Add message text
        message_text = tk.Text(
            message_frame,
            wrap=tk.WORD,
            width=50,  # Увеличил ширину
            height=100,  # Начальная высота
            font=("Arial", 10),
            background=self.user_bg if is_user else self.bot_bg,
            foreground=self.user_fg if is_user else self.bot_fg,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            borderwidth=0,
            highlightthickness=0
        )
        
        # Включаем редактирование для вставки текста
        message_text.configure(state="normal")
        message_text.insert("1.0", text)
        
        # Автоматическая настройка высоты
        def adjust_height(event=None):
            lines = text.count('\n') + 1
            message_text.configure(height=lines)
        
        message_text.bind("<Configure>", adjust_height)
        
        # Делаем текст только для чтения
        message_text.configure(state="disabled")
        
        message_text.pack(anchor="e" if is_user else "w", fill=tk.X, expand=True, padx=10, pady=5)
        
        # "№%;№:?%:;%№*(743__0=" in result:
        if with_buttons and not is_user and "№%;№:?%:;%№*(743__0=" in text:
            between = text.split("№%;№:?%:;%№*(743__0=")[1].split("№%;№:?%:;%№*(743__0=")[0]
            if "run_command" in between:
                command = between.split("run_command('")[1].split("')")[0]
                button_frame = ttk.Frame(message_frame, style="Bot.TFrame")
                button_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
                
                launch_btn = ttk.Button(button_frame, text="Запуск", command=lambda: self.handle_launch(command))
                launch_btn.pack(side=tk.LEFT, padx=(0, 5))
                
                cancel_btn = ttk.Button(button_frame, text="Отмена", command=lambda: self.handle_cancel(text))
                cancel_btn.pack(side=tk.LEFT)
        
        # Schedule auto-scroll after all widgets are updated
        self.root.after(10, self._auto_scroll)

    def _auto_scroll(self):
        # Scroll to the bottom of the canvas
        self.canvas.yview_moveto(1.0)

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            # Create user message
            self.create_message_bubble(message, is_user=True)
            self.message_entry.delete(0, tk.END)
            
            # Add message to processing queue
            self.message_queue.put(message)

    def _process_messages(self):
        while True:
            try:
                # Get message from queue
                message = self.message_queue.get()
                
                # Show spinner
                self.root.after(0, self.show_spinner)
                
                # Get AI response
                try:
                    result = self.client.predict(
                        message=message,
                        system_message=sys_prompt,
                        max_tokens=512,
                        temperature=0.7,
                        top_p=0.95,
                        api_name="/chat"
                    )
                    
                    # Вывод в консоль
                    print(f"Запрос: {message}")
                    print(f"Ответ: {result}")
                    
                    # Schedule bot response in main thread
                    self.root.after(0, self.create_message_bubble, result, False, True)
                
                except Exception as e:
                    error_message = f"Ошибка при получении ответа: {str(e)}"
                    print(error_message)
                    
                    # Специальная обработка ошибки rate limit
                    if "rate limit exceeded" in str(e).lower():
                        error_message = "Превышен лимит запросов. Попробуйте позже."
                    
                    self.root.after(0, self.create_message_bubble, error_message, False, False)
                
                finally:
                    # Hide spinner
                    self.root.after(0, self.hide_spinner)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in message processing: {e}")
                self.root.after(0, self.hide_spinner)

    def handle_launch(self, message):
        print(f"Запуск для сообщения: {message}")
        print(f"Результат запуска: {run_command(message)}")

    def handle_cancel(self, message):
        print(f"Отмена для сообщения: {message}")

    def _copy_text(self, event, text_widget):
        try:
            selected_text = text_widget.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass  # Ничего не выбрано
        return "break"

    def _select_all(self, event, text_widget):
        text_widget.tag_add("sel", "1.0", "end")
        return "break"

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()