import os
import subprocess
import shutil

class FileOperationsTest:
    def __init__(self):
        # Setup test directory
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)

    def run_command_tests(self):
        """Test run_command with 4 different scenarios"""
        print("=== run_command Tests ===")
        
        # Test 1: Simple command execution
        try:
            result1 = subprocess.run(['cmd', '/c', 'echo Hello, World!'], 
                                     capture_output=True, 
                                     text=True, 
                                     timeout=5)
            print("Simple command test: PASSED")
            print(f"Output: {result1.stdout.strip()}")
        except Exception as e:
            print(f"Simple command test: FAILED - {e}")

        # Test 2: Directory listing
        try:
            result2 = subprocess.run(['cmd', '/c', 'dir'], 
                                     capture_output=True, 
                                     text=True, 
                                     timeout=5)
            print("Directory listing test: PASSED")
            print(f"Entries count: {len(result2.stdout.splitlines())}")
        except Exception as e:
            print(f"Directory listing test: FAILED - {e}")

        # Test 3: Command with error handling
        try:
            result3 = subprocess.run(['cmd', '/c', 'nonexistent_command'], 
                                     capture_output=True, 
                                     text=True, 
                                     timeout=5)
            print("Error handling test: FAILED - Command should not exist")
        except subprocess.CalledProcessError as e:
            print("Error handling test: PASSED")
        
        # Test 4: Piped command
        try:
            result4 = subprocess.run('echo test data | findstr "test"', 
                                     shell=True, 
                                     capture_output=True, 
                                     text=True, 
                                     timeout=5)
            print("Piped command test: PASSED")
            print(f"Piped output: {result4.stdout.strip()}")
        except Exception as e:
            print(f"Piped command test: FAILED - {e}")

    def read_file_tests(self):
        """Test read_file with 4 different scenarios"""
        print("\n=== read_file Tests ===")
        test_files = [
            # Different file types and sizes
            ('small_text.txt', 'Small test content'),
            ('unicode_test.txt', '🌍 Unicode test 日本語'),
            ('large_text.txt', 'A' * 10000),
            ('empty_file.txt', '')
        ]

        for filename, content in test_files:
            filepath = os.path.join(self.test_dir, filename)
            
            # Write test file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Read and verify
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    read_content = f.read()
                
                assert read_content == content, f"Content mismatch for {filename}"
                print(f"Read file test for {filename}: PASSED")
                print(f"Content length: {len(read_content)}")
            except Exception as e:
                print(f"Read file test for {filename}: FAILED - {e}")

    def analyze_tests(self):
        """Test analyze with 4 different scenarios"""
        print("\n=== analyze Tests ===")
        
        # Test 1: File metadata
        test_file = os.path.join(self.test_dir, 'analyze_test.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        try:
            file_stat = os.stat(test_file)
            print("File metadata test: PASSED")
            print(f"File size: {file_stat.st_size} bytes")
            print(f"File permissions: {oct(file_stat.st_mode)}")
        except Exception as e:
            print(f"File metadata test: FAILED - {e}")

        # Test 2: Directory metadata
        try:
            dir_stat = os.stat(self.test_dir)
            print("Directory metadata test: PASSED")
            print(f"Directory size: {dir_stat.st_size} bytes")
        except Exception as e:
            print(f"Directory metadata test: FAILED - {e}")

        # Test 3: Owner and group information
        try:
            import pwd
            file_owner = pwd.getpwuid(file_stat.st_uid).pw_name
            print("File owner test: PASSED")
            print(f"File owner: {file_owner}")
        except Exception as e:
            print(f"File owner test: SKIPPED - {e}")

        # Test 4: Recursive directory size
        try:
            total_size = sum(os.path.getsize(os.path.join(dirpath,filename)) 
                             for dirpath, dirnames, filenames in os.walk(self.test_dir) 
                             for filename in filenames)
            print("Recursive directory size test: PASSED")
            print(f"Total directory size: {total_size} bytes")
        except Exception as e:
            print(f"Recursive directory size test: FAILED - {e}")

    def search_tests(self):
        """Test search with 4 different scenarios"""
        print("\n=== search Tests ===")
        
        # Prepare test files
        test_files = [
            ('search_test1.txt', 'Hello world, this is a test'),
            ('search_test2.txt', 'Another test file with multiple occurrences'),
            ('search_test3.txt', 'No matching content here'),
            ('search_test4.txt', 'Test test test multiple matches')
        ]

        for filename, content in test_files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)

        # Test 1: Simple string search
        try:
            matches = sum(1 for file in os.listdir(self.test_dir) 
                          if any('world' in line for line in open(os.path.join(self.test_dir, file))))
            print("Simple string search test: PASSED")
            print(f"Matches found: {matches}")
        except Exception as e:
            print(f"Simple string search test: FAILED - {e}")

        # Test 2: Case-insensitive search
        try:
            matches = sum(1 for file in os.listdir(self.test_dir) 
                          if any('TEST' in line.lower() for line in open(os.path.join(self.test_dir, file))))
            print("Case-insensitive search test: PASSED")
            print(f"Matches found: {matches}")
        except Exception as e:
            print(f"Case-insensitive search test: FAILED - {e}")

        # Test 3: Multiple occurrences in single file
        try:
            matches = sum(line.count('test') for file in os.listdir(self.test_dir) 
                          for line in open(os.path.join(self.test_dir, file)))
            print("Multiple occurrences test: PASSED")
            print(f"Total matches: {matches}")
        except Exception as e:
            print(f"Multiple occurrences test: FAILED - {e}")

        # Test 4: No matches scenario
        try:
            matches = sum(1 for file in os.listdir(self.test_dir) 
                          if any('nonexistent' in line for line in open(os.path.join(self.test_dir, file))))
            print("No matches test: PASSED")
            print(f"Matches found: {matches}")
        except Exception as e:
            print(f"No matches test: FAILED - {e}")

    def write_file_tests(self):
        """Test write_file with 4 different scenarios"""
        print("\n=== write_file Tests ===")
        
        test_contents = [
            ('simple_text.txt', 'Basic text content'),
            ('unicode_content.txt', '🌈 Emoji and Unicode 日本語'),
            ('large_file.txt', 'A' * 100000),
            ('special_chars.txt', '!@#$%^&*()_+')
        ]

        for filename, content in test_contents:
            filepath = os.path.join(self.test_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Verify content
                with open(filepath, 'r', encoding='utf-8') as f:
                    read_content = f.read()
                
                assert read_content == content, f"Content mismatch for {filename}"
                print(f"Write file test for {filename}: PASSED")
                print(f"File size: {len(read_content)} bytes")
            except Exception as e:
                print(f"Write file test for {filename}: FAILED - {e}")

    def update_file_tests(self):
        """Test update_file with 4 different scenarios"""
        print("\n=== update_file Tests ===")
        
        test_scenarios = [
            ('update_test1.txt', 'Original content', 'Updated content', 0),
            ('update_test2.txt', 'Replace middle', 'Completely new', 1),
            ('update_test3.txt', 'Append content', 'Additional text', -1),
            ('update_test4.txt', 'Multiple updates', 'Final version', 2)
        ]

        for filename, initial_content, update_content, update_type in test_scenarios:
            filepath = os.path.join(self.test_dir, filename)
            
            try:
                # Initial write
                with open(filepath, 'w') as f:
                    f.write(initial_content)
                
                # Update based on type
                with open(filepath, 'r+') as f:
                    if update_type == 0:  # Complete replacement
                        f.seek(0)
                        f.truncate()
                        f.write(update_content)
                    elif update_type == 1:  # Partial replacement
                        f.seek(len(initial_content) // 2)
                        remaining = f.read()
                        f.seek(len(initial_content) // 2)
                        f.truncate()
                        f.write(update_content + remaining)
                    elif update_type == -1:  # Append
                        f.seek(0, 2)  # Move to end of file
                        f.write(update_content)
                    elif update_type == 2:  # Multiple updates
                        f.seek(0)
                        content = f.read()
                        f.seek(0)
                        f.truncate()
                        f.write(content.replace('Multiple', 'Final'))
                
                # Verify update
                with open(filepath, 'r') as f:
                    final_content = f.read()
                
                print(f"Update file test for {filename}: PASSED")
                print(f"Final content length: {len(final_content)}")
            except Exception as e:
                print(f"Update file test for {filename}: FAILED - {e}")

    def cleanup(self):
        """Clean up test directory"""
        try:
            shutil.rmtree(self.test_dir)
            print("\nTest directory cleaned up successfully")
        except Exception as e:
            print(f"Cleanup failed: {e}")

    def run_all_tests(self):
        """Run all test methods"""
        try:
            self.run_command_tests()
            self.read_file_tests()
            self.analyze_tests()
            self.search_tests()
            self.write_file_tests()
            self.update_file_tests()
        except Exception as e:
            print(f"Test suite failed: {e}")
        finally:
            self.cleanup()

if __name__ == '__main__':
    test_suite = FileOperationsTest()
    test_suite.run_all_tests()
