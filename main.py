import tkinter as tk
from tkinter import ttk
import datetime

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Bot")
        self.root.geometry("600x800")
        
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
        
        send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Bind Enter key to send message
        self.message_entry.bind("<Return>", lambda e: self.send_message())

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
        message_label = tk.Label(
            message_frame,
            text=text,
            wraplength=400,
            justify=tk.LEFT,
            background=self.user_bg if is_user else self.bot_bg,
            foreground=self.user_fg if is_user else self.bot_fg
        )
        message_label.pack(anchor="e" if is_user else "w", padx=10, pady=5)
        
        # Add buttons if needed
        if with_buttons and not is_user:
            button_frame = ttk.Frame(message_frame, style="Bot.TFrame")
            button_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
            
            launch_btn = ttk.Button(button_frame, text="Запуск", command=lambda: self.handle_launch(text))
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
            
            # Simulate bot response
            self.simulate_bot_response(message)

    def simulate_bot_response(self, user_message):
        # Simple bot logic - alternate between simple and button messages
        if len(user_message) % 2 == 0:
            response = f"Это сообщение с кнопками в ответ на: {user_message}"
            self.create_message_bubble(response, is_user=False, with_buttons=True)
        else:
            response = f"Простой ответ на: {user_message}"
            self.create_message_bubble(response, is_user=False)

    def handle_launch(self, message):
        print(f"Запуск для сообщения: {message}")

    def handle_cancel(self, message):
        print(f"Отмена для сообщения: {message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()