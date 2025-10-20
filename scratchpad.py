import os
import sys
from pathlib import Path
from typing import Optional


class Scratchpad:
    """
    A scratchpad for MSP agents that enforces atomic writes and size limits.
    """
    
    def __init__(self, scratchpad_path: Path, max_chars: int = 8192):
        """
        Initialize the scratchpad.
        :param scratchpad_path: Path to the scratchpad file
        :param max_chars: Maximum number of characters to keep (default 8192)
        """
        self.scratchpad_path = scratchpad_path
        self.max_chars = max_chars
        
        # Ensure parent directory exists
        self.scratchpad_path.parent.mkdir(parents=True, exist_ok=True)
        
    def read(self) -> str:
        """
        Read the content of the scratchpad.
        :return: Content of the scratchpad as a string
        """
        if not self.scratchpad_path.exists():
            return ""
        
        with open(self.scratchpad_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def write(self, content: str, append: bool = True):
        """
        Write content to the scratchpad with atomic operations and size limit.
        :param content: Content to write
        :param append: Whether to append to file or overwrite completely
        """
        # Read existing content if appending
        existing_content = ""
        if self.scratchpad_path.exists() and append:
            existing_content = self.read()
        
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
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Rename temp file to final file (atomic operation on most systems)
        temp_path.replace(self.scratchpad_path)
    
    def append(self, content: str):
        """
        Append content to the scratchpad.
        :param content: Content to append
        """
        self.write(content, append=True)
    
    def clear(self):
        """
        Clear the scratchpad content.
        """
        if self.scratchpad_path.exists():
            self.write("", append=False)