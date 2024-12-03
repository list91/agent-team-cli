import sys
import os
# Установка кодировки для корректной работы в Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import datetime
import threading
import queue
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, QScrollArea, 
                            QFrame, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPalette, QFont
from gradio_client import Client
from nn import sys_prompt
from signal_methods import *

# Подавление предупреждений Gradio
import logging
logging.getLogger('gradio_client').setLevel(logging.ERROR)

class MessageBubble(QFrame):
    def __init__(self, text, timestamp, is_user=True, with_buttons=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        
        # Минималистичная цветовая схема
        self.user_bg = QColor("#f0f0f0")  # Светло-серый
        self.bot_bg = QColor("#ffffff")   # Белый
        self.user_text = QColor("#333333")  # Темно-серый
        self.bot_text = QColor("#2c3e50")   # Темно-синий
        
        # Настройка внешнего вида
        self.setAutoFillBackground(True)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.user_bg.name() if is_user else self.bot_bg.name()};
                border-radius: 10px;
                padding: 8px;
                margin: 5px;
            }}
        """)
        
        # Создание layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Добавление времени (опционально, можно убрать)
        time_label = QLabel(timestamp)
        time_label.setFont(QFont("Arial", 8))
        time_label.setStyleSheet("""
            color: #888888; 
            margin-bottom: 3px;
        """)
        layout.addWidget(time_label, alignment=Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)
        
        # Текстовое поле сообщения
        message_text = QTextEdit()
        message_text.setReadOnly(True)
        message_text.setText(text)
        message_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {self.user_text.name() if is_user else self.bot_text.name()};
                border: none;
                font-size: 12px;
                padding: 0;
            }}
        """)
        
        # Автоматическая подстройка высоты
        message_text.document().documentLayoutChanged.connect(
            lambda: self._adjust_text_height(message_text)
        )
        
        layout.addWidget(message_text)
        
        # Добавление кнопок действий
        if with_buttons and not is_user and "№%;№:?%:;%№*(743__0=" in text:
            between = text.split("№%;№:?%:;%№*(743__0=")[1].split("№%;№:?%:;%№*(743__0=")[0]
            if "run_command" in between:
                command = between.split("run_command('")[1].split("')")[0]
                button_layout = QHBoxLayout()
                button_layout.setSpacing(10)
                
                launch_btn = QPushButton("Запуск")
                launch_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                launch_btn.clicked.connect(lambda: self.handle_launch(command))
                button_layout.addWidget(launch_btn)
                
                cancel_btn = QPushButton("Отмена")
                cancel_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                    }
                """)
                cancel_btn.clicked.connect(lambda: self.handle_cancel(text))
                button_layout.addWidget(cancel_btn)
                
                layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _adjust_text_height(self, text_edit):
        # Динамическая подстройка высоты текстового поля
        doc_height = text_edit.document().size().height()
        text_edit.setFixedHeight(int(doc_height) + 20)  # Небольшой отступ
    
    def handle_launch(self, command):
        print(f"Запуск для сообщения: {command}")
        print(f"Результат запуска: {run_command(command)}")
    
    def handle_cancel(self, message):
        print(f"Отмена для сообщения: {message}")

class ChatWindow(QMainWindow):
    message_processed = pyqtSignal(str, bool, bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Bot")
        self.resize(600, 800)
        
        # Инициализация Gradio клиента
        try:
            self.client = Client("Nymbo/Qwen2.5-Coder-32B-Instruct-Serverless")
        except Exception as e:
            print(f"Ошибка инициализации Gradio клиента: {e}")
            # Показываем диалог с ошибкой
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setText("Ошибка подключения к AI")
            error_dialog.setInformativeText(f"Не удалось установить соединение: {e}")
            error_dialog.setWindowTitle("Ошибка")
            error_dialog.exec()
        
        # Очередь сообщений
        self.message_queue = queue.Queue()
        
        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        
        # Область чата
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Контейнер для сообщений
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()
        
        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)
        
        # Область ввода
        input_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(50)
        self.message_input.textChanged.connect(self.adjust_input_height)
        input_layout.addWidget(self.message_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        
        # Подключение сигнала обработки сообщений
        self.message_processed.connect(self.add_message_bubble)
        
        # Запуск потока обработки сообщений
        self.processing_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.processing_thread.start()
    
    def adjust_input_height(self):
        doc_height = self.message_input.document().size().height()
        # Ограничиваем высоту от 50 до 100 пикселей
        adjusted_height = max(50, min(100, int(doc_height)))
        self.message_input.setFixedHeight(adjusted_height)
    
    def send_message(self):
        message = self.message_input.toPlainText().strip()
        if message:
            # Добавляем сообщение пользователя
            self.add_message_bubble(message, True, False)
            self.message_input.clear()
            
            # Добавляем в очередь
            self.message_queue.put(message)
        
        # Убираем лишний вызов обработчика
        self.message_input.textChanged.disconnect()
        self.message_input.textChanged.connect(self.adjust_input_height)
    
    def add_message_bubble(self, text, is_user, with_buttons):
        # Создание пузырька сообщения
        timestamp = datetime.datetime.now().strftime("%H:%M")
        bubble = MessageBubble(text, timestamp, is_user, with_buttons)
        
        # Добавление в layout
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Прокрутка вниз
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
    
    def show_spinner(self):
        # Скрываем предыдущий спиннер, если он есть
        if hasattr(self, '_spinner_widget'):
            self._spinner_widget.deleteLater()
        
        # Создаем новый виджет спиннера
        self._spinner_widget = QLabel("⌛ Загрузка...")
        self._spinner_widget.setStyleSheet("""
            QLabel {
                color: #888888;
                font-style: italic;
                padding: 5px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        
        # Добавляем спиннер в layout чата
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, self._spinner_widget)
        
        # Прокрутка вниз
        QTimer.singleShot(100, self.scroll_to_bottom)
        
        # Блокировка ввода
        self.message_input.setEnabled(False)
    
    def hide_spinner(self):
        # Удаляем виджет спиннера, если он существует
        if hasattr(self, '_spinner_widget'):
            self._spinner_widget.deleteLater()
            del self._spinner_widget
        
        # Разблокировка ввода
        self.message_input.setEnabled(True)
    
    def _process_messages(self):
        while True:
            try:
                # Получение сообщения из очереди
                message = self.message_queue.get()
                
                # Показываем спиннер в основном потоке
                QTimer.singleShot(0, self.show_spinner)
                
                try:
                    # Получение ответа от AI
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
                    
                    # Скрываем спиннер и отправляем сообщение
                    QTimer.singleShot(0, self.hide_spinner)
                    self.message_processed.emit(result, False, True)
                
                except Exception as e:
                    error_message = f"Ошибка при получении ответа: {str(e)}"
                    print(error_message)
                    
                    if "rate limit exceeded" in str(e).lower():
                        error_message = "Превышен лимит запросов. Попробуйте позже."
                    
                    # Скрываем спиннер и отправляем сообщение об ошибке
                    QTimer.singleShot(0, self.hide_spinner)
                    self.message_processed.emit(error_message, False, False)
            
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in message processing: {e}")
                QTimer.singleShot(0, self.hide_spinner)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())