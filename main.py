import sys
import os
import threading
import queue
import logging
import subprocess
# Установка кодировки для корректной работы в Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QPushButton, QScrollArea, 
                            QFrame, QLabel, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QObject, QEvent, QProcess
from PyQt6.QtGui import QColor, QPalette, QFont
from gradio_client import Client
from nn import sys_prompt
from signal_methods import *

# Подавление предупреждений Gradio
logging.getLogger('gradio_client').setLevel(logging.ERROR)

class ConsoleOutputWidget(QTextEdit):
    command_finished = pyqtSignal(str)  # Создаем сигнал как класс переменную
    
    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command
        self.full_output = ""  # Для хранения полного вывода
        self.error_output = ""  # Для хранения вывода ошибок
        self.exit_code = None  # Код завершения процесса
        
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                color: #333333;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                padding: 10px;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
        """)
        
        # Добавляем заголовок команды
        self.append(f"$ {command}\n")
        
        # Запускаем команду асинхронно
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.handle_finished)
        
        # Запуск команды
        self.process.start("cmd", ["/c", command])
    
    def process_output(self, output):
        # Обработка дополнительного вывода от ИИ
        self.append(f"\n[ИИ]: {output}")
    
    def handle_stdout(self):
        # Чтение стандартного вывода
        output = bytes(self.process.readAllStandardOutput()).decode('cp866')
        self.full_output += output  # Накапливаем полный вывод
        self.append(output.strip())  # Добавляем без лишних пробелов
        print("handle_stdout", output, output.strip())
    
    def handle_stderr(self):
        # Чтение вывода ошибок
        error = bytes(self.process.readAllStandardError()).decode('cp866')
        self.error_output += error  # Накапливаем вывод ошибок
        self.full_output += error  # Также добавляем в полный вывод
        
        # Стилизация для ошибок
        self.setStyleSheet("""
            QTextEdit {
                background-color: #ffebee;
                color: #d32f2f;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                padding: 10px;
                border: 1px solid #ef5350;
                border-radius: 5px;
            }
        """)
        self.append(f"[ОШИБКА]: {error.strip()}")
    
    def handle_finished(self, exit_code, exit_status):
        # Сохраняем код завершения
        self.exit_code = exit_code
        
        # Добавляем информацию о завершении
        status_color = "#4CAF50" if exit_code == 0 else "#F44336"
        status_text = f"\n<span style='color:{status_color};'>[Процесс завершен. Код выхода: {exit_code}]</span>"
        self.append(status_text)
        
        # Автоматическая прокрутка
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
        # Формируем полный результат выполнения
        result_message = f"Команда: {self.command}\n"
        result_message += f"Код завершения: {exit_code}\n"
        
        if self.full_output:
            result_message += f"Вывод:\n{self.full_output}"
        
        if self.error_output:
            result_message += f"\nОшибки:\n{self.error_output}"
        
        # Отправляем полный вывод в ИИ
        if hasattr(self, 'parent_bubble'):
            self.command_finished.emit(result_message)
    
    def get_console_output(self):
        # Возвращаем результат уже выполненной команды
        result_message = f"Команда: {self.command}\n"
        result_message += f"Код завершения: {self.exit_code}\n"
        
        if self.full_output:
            result_message += f"Вывод:\n{self.full_output}"
        
        if self.error_output:
            result_message += f"\nОшибки:\n{self.error_output}"
        
        return result_message
    
    def get_console_text(self):
        # Метод для получения текста консоли как обычного текста
        return self.toPlainText()

class MessageBubble(QFrame):
    message_processed = pyqtSignal(str)
    
    def __init__(self, text, timestamp, is_user=True, with_buttons=False, command=None, parent=None, message_queue=None):
        super().__init__(parent)
        self.is_user = is_user
        self.command = command
        
        # Создание очереди сообщений
        self.message_queue = message_queue
        
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
        
        # Добавление времени
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
        if with_buttons and not is_user and "run_command" in text:
            between = text.split("run_command('")[1].split("')")[0]
            command = between
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
        # Создаем консольный виджет вывода
        console_output = ConsoleOutputWidget(command)
        console_output.parent_bubble = self  # Добавляем ссылку на родительский пузырь
        
        # Добавляем консольный виджет в родительский layout
        parent_layout = self.parent().layout()
        parent_layout.insertWidget(parent_layout.count() - 1, console_output)
        
        # Подключаем сигнал завершения команды
        console_output.command_finished.connect(self.send_command_result_to_ai)
    
    def handle_cancel(self, message):
        print(f"Отмена для сообщения: {message}")
    
    def send_command_result_to_ai(self, result):
        # Обработка консольного вывода с ИИ
        print("[DEBUG] Результат команды:", result)
        
        # Отправляем результат напрямую в очередь сообщений
        self.message_queue.put((result, False, True))

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
        
        # Добавляем обработку нажатия Enter
        self.message_input.installEventFilter(self)
        
        # Настройка контекстного меню для копирования/вставки
        self.message_input.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.message_input.customContextMenuRequested.connect(self.show_context_menu)
        
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
    
    def eventFilter(self, obj, event):
        # Обработка нажатия Enter в поле ввода
        if obj is self.message_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                # Проверяем, не нажат ли Shift
                modifiers = event.modifiers()
                if modifiers != Qt.KeyboardModifier.ShiftModifier:
                    self.send_message()
                    return True  # Событие обработано
        return super().eventFilter(obj, event)
    
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
        bubble = MessageBubble(text, timestamp, is_user, with_buttons, message_queue=self.message_queue)
        
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
                print(f"ПОЛУЧЕННЫЙ СООБЩЕНИЕ: {message}")
                
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
    
    def show_context_menu(self, pos):
        # Создаем контекстное меню
        context_menu = QMenu(self)
        
        # Действия копирования, вырезания и вставки
        copy_action = context_menu.addAction("Копировать")
        cut_action = context_menu.addAction("Вырезать")
        paste_action = context_menu.addAction("Вставить")
        
        # Добавляем разделитель
        context_menu.addSeparator()
        
        # Действия выделения
        select_all_action = context_menu.addAction("Выделить все")
        
        # Получаем выбранное действие
        action = context_menu.exec(self.message_input.mapToGlobal(pos))
        
        # Обработка действий
        if action == copy_action:
            self.message_input.copy()
        elif action == cut_action:
            self.message_input.cut()
        elif action == paste_action:
            self.message_input.paste()
        elif action == select_all_action:
            self.message_input.selectAll()
    
    def process_command_result(self, result):
        # Обработка результата команды
        print(f"Результат команды: {result}")
        self.message_processed.emit(result, False, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())