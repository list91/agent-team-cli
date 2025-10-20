import os
from pathlib import Path
from typing import Union
import tempfile

def safe_file_writer(file_path: str, content: str, session_id: str) -> str:
    """
    Safely writes content to a file, enforcing that it's within the session's workspace.
    
    Args:
        file_path: The path where to write the file
        content: The content to write
        session_id: The session ID for isolation
        
    Returns:
        A message indicating success or failure
    """
    try:
        # Construct the allowed base path for this session
        base_path = Path(f"./workspace/{session_id}").resolve()
        
        # Normalize the target file path
        target_path = Path(file_path).resolve()
        
        # Ensure the target path is within the allowed base path
        if not str(target_path).startswith(str(base_path)):
            return f"ERROR: Path '{file_path}' is not within the allowed workspace for session '{session_id}'"
        
        # Create the directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content to the file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote to file: {file_path}"
        
    except Exception as e:
        return f"ERROR: Failed to write to file '{file_path}': {str(e)}"


def safe_file_reader(file_path: str, session_id: str) -> str:
    """
    Safely reads content from a file, enforcing that it's within the session's workspace.
    
    Args:
        file_path: The path of the file to read
        session_id: The session ID for isolation
        
    Returns:
        The file content or an error message
    """
    try:
        # Construct the allowed base path for this session
        base_path = Path(f"./workspace/{session_id}").resolve()
        
        # Normalize the target file path
        target_path = Path(file_path).resolve()
        
        # Ensure the target path is within the allowed base path
        if not str(target_path).startswith(str(base_path)):
            return f"ERROR: Path '{file_path}' is not within the allowed workspace for session '{session_id}'"
        
        # Read the content from the file
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        return f"ERROR: Failed to read file '{file_path}': {str(e)}"


def list_session_files(session_id: str) -> list:
    """
    Lists all files in the session's workspace directory.
    
    Args:
        session_id: The session ID for isolation
        
    Returns:
        A list of file paths
    """
    try:
        workspace_path = Path(f"./workspace/{session_id}")
        
        if not workspace_path.exists():
            return []
        
        files = []
        for file_path in workspace_path.rglob('*'):
            if file_path.is_file():
                files.append(str(file_path.relative_to(workspace_path)))
        
        return files
        
    except Exception as e:
        return [f"ERROR: Failed to list files: {str(e)}"]