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
                            QHBoxLayout, QLabel, QPushButton, QScrollArea, 
                            QFrame, QMessageBox, QMenu, QSizePolicy, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QObject, QEvent, QProcess
from PyQt6.QtGui import QColor, QPalette, QFont
from gradio_client import Client
from nn import sys_prompt  # Импортируем системный промпт
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
        self.user_bg = QColor("#FBCEB1")
        self.bot_bg = QColor("#60A5A9")
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
        if "\nКонсольный вывод:\n" in text:
            message_text = QTextEdit()
            message_text.setReadOnly(True)
            
            # Разделяем обычный текст и консольный вывод
            parts = text.split("\nКонсольный вывод:\n")
            normal_text = parts[0]
            console_text = parts[1]
            
            # Форматируем текст с разным стилем для консольного вывода
            formatted_text = f"{normal_text}\n\n"
            message_text.setText(formatted_text)
            
            # Создаем консольный блок
            console_block = QTextEdit()
            console_block.setReadOnly(True)
            console_block.setText(console_text)
            console_block.setStyleSheet("""
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
            
            # Отключаем полосы прокрутки для основного текста
            message_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            message_text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # Отключаем полосы прокрутки для консольного блока
            console_block.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            console_block.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # Устанавливаем политику размера
            message_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            console_block.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
            # Основной стиль сообщения
            message_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: transparent;
                    color: {self.user_text.name() if is_user else self.bot_text.name()};
                    border: none;
                    font-size: 12px;
                    padding: 5px;
                    margin: 0;
                }}
            """)
            
            # Создаем layout для сообщения
            message_layout = QVBoxLayout()
            message_layout.setSpacing(10)
            message_layout.addWidget(message_text)
            message_layout.addWidget(console_block)
            
            # Создаем контейнер для сообщения
            message_container = QWidget()
            message_container.setLayout(message_layout)
            
            # Автоматическая подстройка высоты для обоих виджетов
            message_text.document().documentLayoutChanged.connect(
                lambda: self._adjust_text_height(message_text)
            )
            console_block.document().documentLayoutChanged.connect(
                lambda: self._adjust_text_height(console_block)
            )
            
            layout.addWidget(message_container)
            return
        else:
            message_text = QLabel()
            message_text.setWordWrap(True)
            message_text.setTextFormat(Qt.TextFormat.RichText)
            message_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            # Проверяем наличие команды в тексте
            if "№%;№:?%:;%№*(743__0=" in text:
                parts = text.split("№%;№:?%:;%№*(743__0=")
                formatted_text = ""
                for i, part in enumerate(parts):
                    if i % 2 == 0:  # Обычный текст
                        formatted_text += f'<span style="margin-left: 8px;">{part}</span>'
                    else:  # Команда
                        # Извлекаем команду из текста, если она в формате run_command('command')
                        command_text = part
                        if "run_command('" in part and "')" in part:
                            try:
                                command_text = part.split("run_command('")[1].split("')")[0]
                            except IndexError:
                                pass
                        elif "analyze('" in part and "')" in part:
                            try:
                                command_text = part.split("analyze('")[1].split("')")[0]
                                print("@"*10)
                                print(analyze(command_text))

                            except IndexError:
                                pass  # Если что-то пошло не так, оставляем исходный текст
                        formatted_text += f'<div style="background-color: #BABABA; border: 1px solid #808080; border-radius: 4px; padding: 8px 12px; margin: 4px 0; font-family: Consolas, monospace; color: #000000; display: inline-block; font-weight: 500; line-height: 1.2; margin-left: 8px;">{command_text}</div>'
                message_text.setText(formatted_text)
            else:
                message_text.setText(text)
            
            # Устанавливаем политику размера
            message_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
            message_text.setStyleSheet(f"""
                QLabel {{
                    background-color: transparent;
                    color: {self.user_text.name() if is_user else self.bot_text.name()};
                    font-size: 12px;
                    padding: 5px;
                    margin: 0;
                    min-height: 20px;
                }}
            """)
        
        layout.addWidget(message_text)
        
        # Добавление кнопок действий
        if "№%;№:?%:;%№*(743__0=" in text:
            if "analyze('" in text and "')" in text:
                try:
                    command_text = text.split("analyze('")[1].split("')")[0]
                    print("@"*10)
                    print(analyze(command_text))

                except IndexError:
                    pass
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
        """Динамическая подстройка высоты текстового поля для консольного вывода"""
        # Получаем размер документа
        doc = text_edit.document()
        doc.setTextWidth(text_edit.width())
        
        # Устанавливаем высоту с учетом отступов
        margins = text_edit.contentsMargins()
        height = doc.size().height() + margins.top() + margins.bottom()
        text_edit.setMinimumHeight(int(height))
        text_edit.setMaximumHeight(int(height))
    
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
        # Извлекаем команду из сообщения
        command = message.split("run_command('")[1].split("')")[0]
        cancel_message = f"Пользователь отказался выполнять команду: {command}"
        
        # Отправляем сообщение в очередь для обработки ИИ
        if self.message_queue:
            self.message_queue.put((cancel_message, True, False))
    
    def send_command_result_to_ai(self, result):
        # Обработка консольного вывода с ИИ
        print("[DEBUG] Результат команды:", result)
        
        # Отправляем результат напрямую в очередь сообщений
        self.message_queue.put((result, False, True))

class ChatWindow(QMainWindow):
    message_processed = pyqtSignal(str, bool, bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LlamaDevAssist")
        
        # Инициализируем AI клиент
        self.ai_client = None
        
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

        # Инициализация тестовых сообщений
        self.initialize_test_messages()
        
        # Инициализация AI клиента
        self.init_ai_client()
        
        # Добавляем список для хранения истории чата
        self.chat_history = []
    
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
                    result = self.get_ai_response(message)
                    
                    # Вывод в консоль
                    print(f"Запрос: {message}")
                    print(f"Ответ: {result}")

                    if "№%;№:?%:;%№*(743__0=" in result:
                        if "analyze(" in result:
                            try:
                                command_text = result.split("analyze(")[1].split(")")[0]
                                print("@"*10)
                                print(analyze(command_text))

                            except IndexError:
                                pass
                    
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

    def initialize_test_messages(self):
        """Инициализация тестовых сообщений в чате"""
        test_messages = [
            ("""Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.""", True),
            
            ("""Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit.""", False),
            
            ("""At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga.""", True),
            
            ("""Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non recusandae.""", False),
            
            ("""Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus.""", True),
            
            ("""Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem.\n\nКонсольный вывод:\n$ python --version\nPython 3.9.0\n\n$ pip list\nPackage      Version\n------------ -------\npyqt6        6.4.0\nrequests     2.26.0\npython-dotenv 0.19.0\nnumpy        1.21.2\npandas       1.3.3\nscipy        1.7.1\n\n$ python\n>>> import numpy as np\n>>> arr = np.array([1, 2, 3, 4, 5])\n>>> print(f"Mean: {arr.mean()}, Sum: {arr.sum()}")\nMean: 3.0, Sum: 15\n""", False)
        ]

        for text, is_user in test_messages:
            self.message_processed.emit(text, is_user, False)

    def init_ai_client(self):
        self.ai_client = create_llama_client(
            model_url="DHEIVER/chat-Llama-3.3-70B", 
            # Системный промпт будет использоваться по умолчанию из nn.py
        )

    def get_ai_response(self, message):
        if not self.ai_client:
            return "Клиент не инициализирован"
        
        try:
            # Передаем историю чата в generate_response
            result = generate_response(
                self.ai_client, 
                message, 
                chat_history=self.chat_history,  # Передаем текущую историю чата
                max_tokens=2048, 
                temperature=0.7, 
                top_p=0.95, 
                language="en"
            )
            
            # Извлекаем текст ответа из кортежа
            if isinstance(result, tuple):
                result = result[0][1]['content'] if result[0] else "Пустой ответ"
            
            # Обновляем историю чата
            self.chat_history.extend([
                {'role': 'user', 'content': message},
                {'role': 'assistant', 'content': result}
            ])
            
            # Ограничиваем размер истории чата (например, последними 10 сообщениями)
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            return result
        except Exception as e:
            return f"Ошибка генерации ответа: {e}"

def create_llama_client(
    model_url="DHEIVER/chat-Llama-3.3-70B", 
    system_message=sys_prompt  # Используем системный промпт по умолчанию
):
    """
    Создает клиент для взаимодействия с LLM через Gradio
    
    :param model_url: URL модели в Hugging Face Spaces
    :param system_message: Системное сообщение для настройки поведения модели
    :return: Клиент Gradio
    """
    try:
        client = Client(model_url)
        return {
            'client': client,
            'system_message': system_message
        }
    except Exception as e:
        print(f"Ошибка создания клиента: {e}")
        return None

def generate_response(
    client_config, 
    message, 
    chat_history=None, 
    max_tokens=2048, 
    temperature=0.7, 
    top_p=0.95, 
    language="en"
):
    """
    Генерирует ответ от LLM
    
    :param client_config: Конфигурация клиента от create_llama_client
    :param message: Текущее сообщение пользователя
    :param chat_history: История чата
    :param max_tokens: Максимальная длина ответа
    :param temperature: Креативность ответа
    :param top_p: Параметр top-p сэмплирования
    :param language: Язык ответа
    :return: Сгенерированный ответ
    """
    if not client_config:
        return "Клиент не инициализирован"
    
    try:
        # Преобразуем историю чата в формат, совместимый с Gradio
        formatted_history = []
        if chat_history:
            for entry in chat_history:
                formatted_history.append(entry)
        
        result = client_config['client'].predict(
            message=message,
            chat_history=formatted_history,
            system_message=client_config['system_message'],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            language=language,
            api_name="/respond"
        )
        
        # Извлекаем текст ответа из кортежа
        if isinstance(result, tuple):
            result = result[0][1]['content'] if result[0] else "Пустой ответ"
        return result
    except Exception as e:
        return f"Ошибка генерации ответа: {e}"

def print_analyze_result(result):
    """
    Красиво выводит результат анализа файла или директории в консоль
    
    :param result: Результат функции analyze()
    """
    if isinstance(result, str):
        print(f"❌ Ошибка: {result}")
        return
    
    # Стили для вывода
    BOLD = "\033[1m"
    RESET = "\033[0m"
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    
    print(f"\n{BOLD}🔍 Результат анализа:{RESET}")
    print(f"{GREEN}Тип:{RESET} {result.get('type', 'Неизвестно')}")
    
    if result.get('type') == 'file':
        print(f"{GREEN}Размер:{RESET} {result.get('size', 0)} байт")
        print(f"{GREEN}Владелец:{RESET} {result.get('owner', 'Неизвестно')}")
        print(f"{GREEN}Права доступа:{RESET} {result.get('permissions', 'Неизвестно')}")
        print(f"{GREEN}Последнее изменение:{RESET} {result.get('modified', 'Неизвестно')}")
    
    elif result.get('type') == 'directory':
        print(f"{GREEN}Всего элементов:{RESET} {result.get('total_items', 0)}")
        print(f"{GREEN}Общий размер:{RESET} {result.get('total_size', 0)} байт")
        print(f"{GREEN}Владелец:{RESET} {result.get('owner', 'Неизвестно')}")
        print(f"{GREEN}Права доступа:{RESET} {result.get('permissions', 'Неизвестно')}")
        print(f"{GREEN}Последнее изменение:{RESET} {result.get('modified', 'Неизвестно')}")
        
        print(f"\n{BOLD}Содержимое директории:{RESET}")
        for item in result.get('contents', []):
            item_type = "📁" if item.get('type') == 'directory' else "📄"
            print(f"{item_type} {BLUE}{item.get('name', 'Неизвестно')}{RESET}")
            if item.get('size') is not None:
                print(f"   Размер: {item.get('size', 0)} байт")
            print(f"   Права: {item.get('permissions', 'Неизвестно')}")
            print(f"   Изменен: {item.get('modified', 'Неизвестно')}")
            print()

# Пример использования
# print_analyze_result(analyze('/path/to/file_or_directory'))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())