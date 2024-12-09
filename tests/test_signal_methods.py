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
        with open('test_signal.txt', 'w', encoding='utf-8') as f:
            f.write("Test signal content\nMultiple lines\nWith different data")
        
        # Создаем временную директорию
        os.makedirs('test_signal_dir', exist_ok=True)
        with open('test_signal_dir/file1.txt', 'w', encoding='utf-8') as f:
            f.write("Signal test file 1")
        with open('test_signal_dir/file2.txt', 'w', encoding='utf-8') as f:
            f.write("Signal test file 2")

    def tearDown(self):
        # Удаляем временные файлы и директории после теста
        os.remove('test_signal.txt')
        os.remove('test_signal_dir/file1.txt')
        os.remove('test_signal_dir/file2.txt')
        os.rmdir('test_signal_dir')

    def test_signal_run_command(self):
        """Тестирование выполнения команды"""
        result = signal_methods.run_command('echo "Signal test command"')
        print(f"Run Command Result: {result}")
        self.assertIn("Signal test command", result)

    def test_signal_read_file(self):
        """Тестирование чтения файла"""
        result = signal_methods.read_file('test_signal.txt')
        print(f"Read File Result: {result}")
        self.assertIn("Test signal content", result)

    def test_signal_analyze_file(self):
        """Тестирование анализа файла"""
        result = signal_methods.analyze('test_signal.txt')
        print(f"Analyze File Result: {result}")
        self.assertEqual(result['type'], 'file')
        self.assertTrue('size' in result)

    def test_signal_analyze_directory(self):
        """Тестирование анализа директории"""
        result = signal_methods.analyze('test_signal_dir')
        print(f"Analyze Directory Result: {result}")
        
        # Проверяем основные ключевые поля
        self.assertEqual(result['type'], 'directory')
        self.assertEqual(result['total_items'], 2)
        
        # Проверяем содержимое директории
        self.assertTrue('contents' in result)
        contents = result['contents']
        
        # Проверяем метаданные каждого файла
        for item in contents:
            print(f"Directory Item: {item}")
            self.assertTrue('name' in item)
            self.assertTrue('type' in item)
            self.assertTrue('modified' in item)
            self.assertTrue('permissions' in item)
            
            # Проверяем, что файлы имеют размер
            if item['type'] == 'file':
                self.assertTrue('size' in item)
                self.assertIsNotNone(item['size'])
        
        # Проверяем общий размер директории
        self.assertTrue('total_size' in result)
        self.assertIsNotNone(result['total_size'])

    def test_signal_search_in_file(self):
        """Тестирование поиска в файле"""
        result = signal_methods.search('test_signal.txt', 'lines')
        print(f"Search in File Result: {result}")
        self.assertEqual(result, 1)

    def test_signal_search_in_directory(self):
        """Тестирование поиска в директории"""
        result = signal_methods.search('test_signal_dir', 'Signal')
        print(f"Search in Directory Result: {result}")
        self.assertEqual(result, 2)

    def test_signal_update_file_replace(self):
        """Тестирование замены содержимого файла"""
        # Выводим исходное содержимое
        print("Original file content:")
        with open('test_signal.txt', 'r') as f:
            print(f.read())
        
        # Обновляем файл
        result = signal_methods.update_file('test_signal.txt', "New content entirely")
        print("Update result:", result)
        
        # Выводим новое содержимое
        print("Updated file content:")
        with open('test_signal.txt', 'r') as f:
            updated_content = f.read()
            print(updated_content)
        
        # Проверяем результат
        self.assertEqual(updated_content, "New content entirely")
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result['status'], 'success')

    def test_signal_update_file_append(self):
        """Тестирование добавления содержимого в конец файла"""
        # Выводим исходное содержимое
        print("Original file content:")
        with open('test_signal.txt', 'r') as f:
            print(f.read())
        
        # Обновляем файл
        result = signal_methods.update_file('test_signal.txt', "\nAppended content", mode='append')
        print("Update result:", result)
        
        # Выводим новое содержимое
        print("Updated file content:")
        with open('test_signal.txt', 'r') as f:
            updated_content = f.read()
            print(updated_content)
        
        # Проверяем результат
        self.assertTrue("Appended content" in updated_content)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result['status'], 'success')

    def test_signal_update_file_prepend(self):
        """Тестирование добавления содержимого в начало файла"""
        # Выводим исходное содержимое
        print("Original file content:")
        with open('test_signal.txt', 'r') as f:
            print(f.read())
        
        # Обновляем файл
        result = signal_methods.update_file('test_signal.txt', "Prepended content\n", mode='prepend')
        print("Update result:", result)
        
        # Выводим новое содержимое
        print("Updated file content:")
        with open('test_signal.txt', 'r') as f:
            updated_content = f.read()
            print(updated_content)
        
        # Проверяем результат
        self.assertTrue(updated_content.startswith("Prepended content"))
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result['status'], 'success')

if __name__ == '__main__':
    # Демонстрация потокового вывода
    print("Streaming ping output:")
    for line in signal_methods.run_command('ping 8.8.8.8', stream=True):
        print(line)
        # Можно добавить условие остановки, например:
        # if some_condition:
        #     break
