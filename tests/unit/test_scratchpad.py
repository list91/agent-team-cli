#!/usr/bin/env python3
"""
Unit tests for Scratchpad class
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scratchpad import Scratchpad


class TestScratchpadInit:
    """Test scratchpad initialization"""

    def test_init_creates_parent_directory(self):
        """Test that scratchpad creates parent directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "subdir" / "test.md"
            scratchpad = Scratchpad(scratch_path)
            assert scratch_path.parent.exists()

    def test_init_with_custom_max_chars(self):
        """Test scratchpad initialization with custom max_chars"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path, max_chars=1024)
            assert scratchpad.max_chars == 1024

    def test_init_with_default_max_chars(self):
        """Test scratchpad initialization with default max_chars"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)
            assert scratchpad.max_chars == 8192


class TestScratchpadRead:
    """Test scratchpad read operations"""

    def test_read_nonexistent_file_returns_empty_string(self):
        """Test reading from nonexistent file returns empty string"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)
            content = scratchpad.read()
            assert content == ""

    def test_read_existing_file_returns_content(self):
        """Test reading from existing file returns correct content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            expected_content = "Test content\nLine 2\n"
            scratch_path.write_text(expected_content, encoding='utf-8')

            scratchpad = Scratchpad(scratch_path)
            content = scratchpad.read()
            assert content == expected_content

    def test_read_unicode_content(self):
        """Test reading unicode content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            expected_content = "Unicode: 你好, привет, مرحبا\n"
            scratch_path.write_text(expected_content, encoding='utf-8')

            scratchpad = Scratchpad(scratch_path)
            content = scratchpad.read()
            assert content == expected_content


class TestScratchpadWrite:
    """Test scratchpad write operations"""

    def test_write_creates_new_file(self):
        """Test write creates new file if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)
            scratchpad.write("Test content\n", append=False)

            assert scratch_path.exists()
            assert scratch_path.read_text(encoding='utf-8') == "Test content\n"

    def test_write_overwrites_existing_file(self):
        """Test write with append=False overwrites existing content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratch_path.write_text("Old content\n", encoding='utf-8')

            scratchpad = Scratchpad(scratch_path)
            scratchpad.write("New content\n", append=False)

            content = scratch_path.read_text(encoding='utf-8')
            assert content == "New content\n"
            assert "Old content" not in content

    def test_write_appends_to_existing_file(self):
        """Test write with append=True appends to existing content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratch_path.write_text("Line 1\n", encoding='utf-8')

            scratchpad = Scratchpad(scratch_path)
            scratchpad.write("Line 2\n", append=True)

            content = scratch_path.read_text(encoding='utf-8')
            assert content == "Line 1\nLine 2\n"

    def test_write_enforces_size_limit(self):
        """Test write enforces max_chars size limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path, max_chars=100)

            # Write content longer than max_chars
            long_content = "X" * 200
            scratchpad.write(long_content, append=False)

            content = scratch_path.read_text(encoding='utf-8')
            assert len(content) == 100
            assert content == "X" * 100

    def test_write_keeps_end_of_content_when_truncating(self):
        """Test write keeps the end of content when truncating"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path, max_chars=10)

            scratchpad.write("0123456789ABCDEF", append=False)

            content = scratch_path.read_text(encoding='utf-8')
            assert content == "6789ABCDEF"

    def test_write_with_unicode(self):
        """Test write with unicode content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)
            unicode_content = "Unicode: 你好 世界\n"

            scratchpad.write(unicode_content, append=False)
            content = scratch_path.read_text(encoding='utf-8')
            assert content == unicode_content


class TestScratchpadAppend:
    """Test scratchpad append operations"""

    def test_append_to_empty_file(self):
        """Test append to empty/nonexistent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)
            scratchpad.append("First line\n")

            content = scratch_path.read_text(encoding='utf-8')
            assert content == "First line\n"

    def test_append_multiple_times(self):
        """Test multiple append operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            scratchpad.append("Line 1\n")
            scratchpad.append("Line 2\n")
            scratchpad.append("Line 3\n")

            content = scratch_path.read_text(encoding='utf-8')
            assert content == "Line 1\nLine 2\nLine 3\n"

    def test_append_enforces_size_limit(self):
        """Test append enforces max_chars size limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path, max_chars=50)

            scratchpad.append("A" * 30)
            scratchpad.append("B" * 30)

            content = scratch_path.read_text(encoding='utf-8')
            assert len(content) == 50
            assert content.startswith("A")
            assert content.endswith("B" * 30)


class TestScratchpadClear:
    """Test scratchpad clear operations"""

    def test_clear_existing_file(self):
        """Test clear empties existing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratch_path.write_text("Some content\n", encoding='utf-8')

            scratchpad = Scratchpad(scratch_path)
            scratchpad.clear()

            content = scratch_path.read_text(encoding='utf-8')
            assert content == ""

    def test_clear_nonexistent_file_no_error(self):
        """Test clear on nonexistent file doesn't raise error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            # Should not raise an error
            scratchpad.clear()


class TestScratchpadAtomicWrites:
    """Test scratchpad atomic write behavior"""

    def test_atomic_write_creates_temp_file(self):
        """Test that atomic write mechanism works correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            scratchpad.write("Content\n", append=False)

            # After write completes, temp file should not exist
            temp_file = scratch_path.with_suffix(scratch_path.suffix + '.tmp')
            assert not temp_file.exists()
            assert scratch_path.exists()

    def test_concurrent_writes_do_not_corrupt(self):
        """Test that multiple quick writes complete successfully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scratch_path = Path(tmpdir) / "test.md"
            scratchpad = Scratchpad(scratch_path)

            # Perform multiple writes in quick succession
            for i in range(10):
                scratchpad.append(f"Line {i}\n")

            content = scratch_path.read_text(encoding='utf-8')
            # All lines should be present
            for i in range(10):
                assert f"Line {i}" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
