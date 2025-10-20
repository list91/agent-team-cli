"""
Bridge/Messaging System for MSP agents
Enables communication between agents via shared contexts
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import time


class Bridge:
    """
    Bridge for enabling communication between agents
    """
    
    def __init__(self, bridge_id: str, shared_dir: Path):
        """
        Initialize a bridge between agents
        :param bridge_id: Unique identifier for this bridge
        :param shared_dir: Directory where shared data will be stored
        """
        self.bridge_id = bridge_id
        self.shared_dir = shared_dir / bridge_id
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        
    def send_message(self, sender: str, message_type: str, data: Any):
        """
        Send a message to other agents via the shared context.

        :param sender: Name of the sending agent
        :param message_type: Type of message (e.g., 'specification', 'code', 'result')
        :param data: Message data to share
        :raises ValueError: If sender or message_type is None/empty
        :raises IOError: If message cannot be written
        :raises PermissionError: If insufficient permissions
        """
        # Validate inputs
        if not sender or sender is None:
            raise ValueError("Sender cannot be None or empty")
        if not message_type or message_type is None:
            raise ValueError("Message type cannot be None or empty")

        with self.lock:
            # Create a timestamped message file with microsecond precision
            timestamp = time.time()  # Float with microsecond precision
            # Use timestamp in filename with microseconds to ensure uniqueness
            timestamp_str = f"{int(timestamp)}_{int((timestamp % 1) * 1000000)}"
            msg_filename = f"{sender}_{message_type}_{timestamp_str}.json"
            msg_path = self.shared_dir / msg_filename

            message = {
                "sender": sender,
                "type": message_type,
                "timestamp": timestamp,
                "data": data
            }

            try:
                with open(msg_path, 'w', encoding='utf-8') as f:
                    json.dump(message, f, indent=2)
            except PermissionError as e:
                # Re-raise PermissionError with context
                raise PermissionError(f"Failed to send message to bridge {self.bridge_id}: {str(e)}")
            except (IOError, OSError) as e:
                raise IOError(f"Failed to send message to bridge {self.bridge_id}: {str(e)}")
            except (TypeError, ValueError) as e:
                raise ValueError(f"Failed to serialize message data: {str(e)}")
    
    def get_messages(self, message_type: str = None, since: float = 0) -> list:
        """
        Get messages from the shared context.

        :param message_type: Optional filter for message type
        :param since: Optional filter for messages after timestamp (exclusive)
        :return: List of messages sorted by timestamp
        """
        messages = []

        try:
            msg_files = list(self.shared_dir.glob("*.json"))
        except (IOError, PermissionError) as e:
            # If we can't read the directory, return empty list
            import logging
            logging.warning(f"Could not read bridge directory {self.shared_dir}: {e}")
            return messages

        for msg_file in msg_files:
            try:
                with open(msg_file, 'r', encoding='utf-8') as f:
                    msg = json.load(f)

                # Validate message structure
                if not isinstance(msg, dict) or 'timestamp' not in msg or 'type' not in msg:
                    import logging
                    logging.warning(f"Malformed message file {msg_file}, skipping")
                    continue

                # Filter by timestamp (strictly greater than since)
                if msg['timestamp'] > since:
                    if message_type is None or msg['type'] == message_type:
                        messages.append(msg)
            except (IOError, PermissionError, OSError) as e:
                # Skip files we can't read
                import logging
                logging.warning(f"Could not read message file {msg_file}: {e}")
                continue
            except (json.JSONDecodeError, ValueError) as e:
                # Skip malformed JSON files
                import logging
                logging.warning(f"Malformed JSON in {msg_file}: {e}")
                continue
            except (KeyError, TypeError) as e:
                # Skip messages with missing fields
                import logging
                logging.warning(f"Invalid message structure in {msg_file}: {e}")
                continue

        # Sort by timestamp
        try:
            messages.sort(key=lambda x: x['timestamp'])
        except (KeyError, TypeError):
            # If sorting fails, return unsorted
            pass

        return messages
    
    def get_latest_message(self, message_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent message of a specific type
        :param message_type: Type of message to retrieve
        :return: Latest message or None if not found
        """
        messages = self.get_messages(message_type=message_type)
        return messages[-1] if messages else None


class BridgeManager:
    """
    Manages multiple bridges between agents
    """
    
    def __init__(self, shared_dir: Path):
        """
        Initialize the bridge manager
        :param shared_dir: Base directory for all shared contexts
        """
        self.shared_dir = shared_dir
        self.bridges: Dict[str, Bridge] = {}
        self.shared_dir.mkdir(parents=True, exist_ok=True)
    
    def create_bridge(self, bridge_id: str) -> Bridge:
        """
        Create a new bridge with the given ID
        :param bridge_id: Unique identifier for the bridge
        :return: Bridge instance
        """
        if bridge_id not in self.bridges:
            self.bridges[bridge_id] = Bridge(bridge_id, self.shared_dir)
        return self.bridges[bridge_id]
    
    def get_bridge(self, bridge_id: str) -> Optional[Bridge]:
        """
        Get an existing bridge by ID
        :param bridge_id: ID of the bridge to retrieve
        :return: Bridge instance or None if not found
        """
        return self.bridges.get(bridge_id)
    
    def list_bridges(self) -> list:
        """
        List all bridge IDs
        :return: List of bridge IDs
        """
        return list(self.bridges.keys())