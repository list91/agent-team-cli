import unittest
import os
import sys

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

    def test_run_command(self):
        # Тестируем выполнение простой команды
        result = signal_methods.run_command('echo "Test command"')
        self.assertIn("Test command", result)

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

    def test_run_command_timeout(self):
        # Тестируем таймаут команды
        result = signal_methods.run_command('ping -n 10 127.0.0.1 > nul')
        self.assertIn("Command timed out", result)

if __name__ == '__main__':
    unittest.main()
