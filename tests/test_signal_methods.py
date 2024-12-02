import unittest
import os
import sys
import re

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import signal_methods

class TestSignalMethods(unittest.TestCase):
    def setUp(self):
        # Создаем временный файл для тестирования
        with open('test_file.txt', 'w') as f:
            f.write("Hello world! This is a test file.\nAnother line with hello.")
        
        # Создаем временную директорию
        os.makedirs('test_dir', exist_ok=True)
        with open('test_dir/test1.txt', 'w') as f:
            f.write("Test content in file 1")
        with open('test_dir/test2.txt', 'w') as f:
            f.write("Test content in file 2")

    def tearDown(self):
        # Удаляем временные файлы и директории после теста
        os.remove('test_file.txt')
        os.remove('test_dir/test1.txt')
        os.remove('test_dir/test2.txt')
        os.rmdir('test_dir')

    def test_run_command_basic(self):
        """Базовый тест выполнения простой команды"""
        result = signal_methods.run_command('echo "Test command"')
        self.assertIn("Test command", result)

    def test_run_command_complex(self):
        """Тест выполнения более сложной команды"""
        result = signal_methods.run_command('dir')
        self.assertTrue(len(result) > 0, "Команда dir должна вернуть непустой результат")
        self.assertFalse("Error" in result, "Команда dir не должна содержать ошибок")

    def test_run_command_with_pipes(self):
        """Тест команды с использованием pipe"""
        result = signal_methods.run_command('echo "test string" | findstr "test"')
        self.assertIn("test string", result)

    def test_run_command_error_handling(self):
        """Тест обработки ошибочной команды"""
        result = signal_methods.run_command('nonexistent_command')
        self.assertTrue(
            "не является" in result or 
            "not recognized" in result or 
            "Command execution error" in result, 
            f"Неожиданный результат: {result}"
        )

    def test_run_command_with_special_chars(self):
        """Тест команды со специальными символами"""
        result = signal_methods.run_command('echo "Hello, World!"')
        self.assertIn("Hello, World!", result)

    def test_run_command_long_output(self):
        """Тест команды с длинным выводом"""
        result = signal_methods.run_command('systeminfo')
        self.assertTrue(len(result) > 100, "Команда systeminfo должна вернуть развернутую информацию")

    def test_run_command_timeout(self):
        """Расширенный тест на таймаут"""
        result = signal_methods.run_command('ping -n 10 127.0.0.1 > nul')
        self.assertIn("Command timed out", result)

    def test_run_command_environment_vars(self):
        """Тест выполнения команды с переменными окружения"""
        result = signal_methods.run_command('echo %COMPUTERNAME%')
        self.assertTrue(len(result.strip()) > 0, "Должно быть возвращено имя компьютера")

    def test_run_command_powershell(self):
        """Тест выполнения команды через PowerShell"""
        result = signal_methods.run_command('powershell "(Get-Date).ToString(\'dd.MM.yyyy HH:mm:ss\')"')
        # Проверяем, что возвращена дата
        date_pattern = r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}'
        self.assertTrue(re.search(date_pattern, result), 
                        f"Должна быть возвращена корректная дата. Получен результат: {result}")

    def test_run_command_network(self):
        """Тест сетевой команды"""
        result = signal_methods.run_command('ipconfig')
        self.assertTrue(
            "IPv4" in result or 
            "Ethernet" in result or 
            "Адаптер" in result, 
            f"Команда ipconfig должна вернуть информацию о сети. Получен результат: {result}"
        )

    def test_read_file(self):
        # Тестируем чтение файла
        result = signal_methods.read_file('test_file.txt')
        self.assertIn("Hello world!", result)

    def test_analyze_file(self):
        # Тестируем анализ файла
        result = signal_methods.analyze('test_file.txt')
        self.assertEqual(result['type'], 'file')
        self.assertTrue('size' in result)
        self.assertTrue('owner' in result)

    def test_analyze_directory(self):
        # Тестируем анализ директории
        result = signal_methods.analyze('test_dir')
        self.assertEqual(result['type'], 'directory')
        self.assertEqual(result['items_count'], 2)

    def test_search_in_file(self):
        # Тестируем поиск в файле
        result = signal_methods.search('test_file.txt', 'hello')
        self.assertEqual(result, 2)

    def test_search_in_directory(self):
        # Тестируем поиск в директории
        result = signal_methods.search('test_dir', 'Test content')
        self.assertEqual(result, 2)

if __name__ == '__main__':
    unittest.main()
