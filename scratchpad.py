import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.config_loader import config
except ImportError:
    # Fallback if config loader not available
    class FallbackConfig:
        @property
        def max_scratchpad_chars(self):
            return 8192
    config = FallbackConfig()


class Scratchpad:
    """
    A scratchpad for MSP agents that enforces atomic writes and size limits.
    """

    def __init__(self, scratchpad_path: Path, max_chars: int = None):
        """
        Initialize the scratchpad.
        :param scratchpad_path: Path to the scratchpad file
        :param max_chars: Maximum number of characters to keep (default from config)
        """
        self.scratchpad_path = scratchpad_path
        self.max_chars = max_chars if max_chars is not None else config.max_scratchpad_chars
        
        # Ensure parent directory exists
        self.scratchpad_path.parent.mkdir(parents=True, exist_ok=True)
        
    def read(self) -> str:
        """
        Read the content of the scratchpad.
        :return: Content of the scratchpad as a string
        :raises IOError: If file cannot be read
        :raises UnicodeDecodeError: If file contains invalid UTF-8
        """
        if not self.scratchpad_path.exists():
            return ""

        try:
            with open(self.scratchpad_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, PermissionError) as e:
            raise IOError(f"Failed to read scratchpad at {self.scratchpad_path}: {str(e)}")
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                e.encoding, e.object, e.start, e.end,
                f"Failed to decode scratchpad at {self.scratchpad_path}: {e.reason}"
            )
    
    def write(self, content: str, append: bool = True):
        """
        Write content to the scratchpad with atomic operations and size limit.
        :param content: Content to write
        :param append: Whether to append to file or overwrite completely
        :raises IOError: If file cannot be written
        :raises PermissionError: If insufficient permissions
        :raises OSError: If disk is full or other OS errors
        """
        # Validate input
        if content is None:
            raise ValueError("Content cannot be None")

        # Read existing content if appending
        existing_content = ""
        if self.scratchpad_path.exists() and append:
            try:
                existing_content = self.read()
            except (IOError, UnicodeDecodeError) as e:
                # If we can't read the existing file, log and start fresh
                import logging
                logging.warning(f"Could not read existing scratchpad, starting fresh: {e}")
                existing_content = ""

        # Combine content
        if append:
            new_content = existing_content + content
        else:
            new_content = content

        # Apply size limit - keep the end of the content
        if len(new_content) > self.max_chars:
            new_content = new_content[-self.max_chars:]

        # Atomic write - write to temp file first, then rename
        temp_path = self.scratchpad_path.with_suffix(self.scratchpad_path.suffix + '.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except (IOError, PermissionError, OSError) as e:
            # Clean up temp file if it was created
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise type(e)(f"Failed to write scratchpad at {self.scratchpad_path}: {str(e)}")

        try:
            # Rename temp file to final file (atomic operation on most systems)
            temp_path.replace(self.scratchpad_path)
        except (IOError, PermissionError, OSError) as e:
            # Clean up temp file if rename failed
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise type(e)(f"Failed to finalize scratchpad write at {self.scratchpad_path}: {str(e)}")
    
    def append(self, content: str):
        """
        Append content to the scratchpad.
        :param content: Content to append
        """
        self.write(content, append=True)
    
    def clear(self):
        """
        Clear the scratchpad content.
        :raises IOError: If file cannot be cleared
        """
        if self.scratchpad_path.exists():
            try:
                self.write("", append=False)
            except (IOError, PermissionError, OSError) as e:
                raise IOError(f"Failed to clear scratchpad at {self.scratchpad_path}: {str(e)}")