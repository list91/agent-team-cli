#!/usr/bin/env python3
"""
Unit tests for Bridge and BridgeManager classes
"""
import pytest
import tempfile
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from bridge import Bridge, BridgeManager


class TestBridgeInit:
    """Test Bridge initialization"""

    def test_bridge_creates_shared_directory(self):
        """Test that bridge creates shared directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)
            expected_dir = shared_dir / "test_bridge"
            assert expected_dir.exists()
            assert expected_dir.is_dir()


class TestBridgeSendMessage:
    """Test Bridge send_message functionality"""

    def test_send_message_creates_file(self):
        """Test send_message creates a JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "test_type", {"key": "value"})

            # Check that a file was created
            bridge_dir = shared_dir / "test_bridge"
            json_files = list(bridge_dir.glob("*.json"))
            assert len(json_files) == 1

    def test_send_message_contains_correct_data(self):
        """Test send_message file contains correct data structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            test_data = {"key": "value", "number": 42}
            bridge.send_message("agent1", "test_type", test_data)

            # Read the created file
            bridge_dir = shared_dir / "test_bridge"
            json_files = list(bridge_dir.glob("*.json"))
            assert len(json_files) == 1

            import json
            with open(json_files[0], 'r') as f:
                message = json.load(f)

            assert message["sender"] == "agent1"
            assert message["type"] == "test_type"
            assert message["data"] == test_data
            assert "timestamp" in message

    def test_send_multiple_messages(self):
        """Test sending multiple messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "type1", {"msg": 1})
            time.sleep(0.01)  # Small delay to ensure different timestamps
            bridge.send_message("agent2", "type2", {"msg": 2})
            time.sleep(0.01)
            bridge.send_message("agent1", "type1", {"msg": 3})

            bridge_dir = shared_dir / "test_bridge"
            json_files = list(bridge_dir.glob("*.json"))
            assert len(json_files) == 3


class TestBridgeGetMessages:
    """Test Bridge get_messages functionality"""

    def test_get_all_messages(self):
        """Test get_messages returns all messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "type1", {"msg": 1})
            time.sleep(0.01)
            bridge.send_message("agent2", "type2", {"msg": 2})

            messages = bridge.get_messages()
            assert len(messages) == 2

    def test_get_messages_filtered_by_type(self):
        """Test get_messages with message_type filter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "typeA", {"msg": 1})
            time.sleep(0.01)
            bridge.send_message("agent2", "typeB", {"msg": 2})
            time.sleep(0.01)
            bridge.send_message("agent3", "typeA", {"msg": 3})

            messages = bridge.get_messages(message_type="typeA")
            assert len(messages) == 2
            assert all(msg["type"] == "typeA" for msg in messages)

    def test_get_messages_sorted_by_timestamp(self):
        """Test get_messages returns messages sorted by timestamp"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "type1", {"msg": 1})
            time.sleep(0.01)
            bridge.send_message("agent2", "type1", {"msg": 2})
            time.sleep(0.01)
            bridge.send_message("agent3", "type1", {"msg": 3})

            messages = bridge.get_messages()
            assert len(messages) == 3
            assert messages[0]["data"]["msg"] == 1
            assert messages[1]["data"]["msg"] == 2
            assert messages[2]["data"]["msg"] == 3

    def test_get_messages_with_since_filter(self):
        """Test get_messages with since timestamp filter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "type1", {"msg": 1})
            time.sleep(0.01)
            cutoff_time = time.time()  # Use float timestamp for precision
            time.sleep(0.01)
            bridge.send_message("agent2", "type1", {"msg": 2})
            bridge.send_message("agent3", "type1", {"msg": 3})

            messages = bridge.get_messages(since=cutoff_time)
            # Should only get messages 2 and 3
            assert len(messages) >= 2
            assert all(msg["data"]["msg"] >= 2 for msg in messages)

    def test_get_messages_empty_bridge(self):
        """Test get_messages on empty bridge returns empty list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            messages = bridge.get_messages()
            assert messages == []


class TestBridgeGetLatestMessage:
    """Test Bridge get_latest_message functionality"""

    def test_get_latest_message_returns_most_recent(self):
        """Test get_latest_message returns the most recent message of type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "test", {"version": 1})
            time.sleep(0.01)
            bridge.send_message("agent2", "test", {"version": 2})
            time.sleep(0.01)
            bridge.send_message("agent3", "test", {"version": 3})

            latest = bridge.get_latest_message("test")
            assert latest is not None
            assert latest["data"]["version"] == 3

    def test_get_latest_message_filters_by_type(self):
        """Test get_latest_message filters by message type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "typeA", {"value": "A1"})
            time.sleep(0.01)
            bridge.send_message("agent2", "typeB", {"value": "B1"})
            time.sleep(0.01)
            bridge.send_message("agent3", "typeA", {"value": "A2"})

            latest_a = bridge.get_latest_message("typeA")
            latest_b = bridge.get_latest_message("typeB")

            assert latest_a["data"]["value"] == "A2"
            assert latest_b["data"]["value"] == "B1"

    def test_get_latest_message_nonexistent_type_returns_none(self):
        """Test get_latest_message returns None for nonexistent type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir)
            bridge = Bridge("test_bridge", shared_dir)

            bridge.send_message("agent1", "typeA", {"value": 1})

            latest = bridge.get_latest_message("typeB")
            assert latest is None


class TestBridgeManager:
    """Test BridgeManager functionality"""

    def test_bridge_manager_creates_shared_directory(self):
        """Test BridgeManager creates shared directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir) / "shared"
            manager = BridgeManager(shared_dir)
            assert shared_dir.exists()

    def test_create_bridge(self):
        """Test BridgeManager creates bridges"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir) / "shared"
            manager = BridgeManager(shared_dir)

            bridge = manager.create_bridge("bridge1")
            assert bridge is not None
            assert bridge.bridge_id == "bridge1"

    def test_create_bridge_is_idempotent(self):
        """Test creating same bridge twice returns same instance"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir) / "shared"
            manager = BridgeManager(shared_dir)

            bridge1 = manager.create_bridge("bridge1")
            bridge2 = manager.create_bridge("bridge1")
            assert bridge1 is bridge2

    def test_get_existing_bridge(self):
        """Test getting an existing bridge"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir) / "shared"
            manager = BridgeManager(shared_dir)

            created_bridge = manager.create_bridge("bridge1")
            retrieved_bridge = manager.get_bridge("bridge1")

            assert retrieved_bridge is not None
            assert retrieved_bridge is created_bridge

    def test_get_nonexistent_bridge_returns_none(self):
        """Test getting nonexistent bridge returns None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir) / "shared"
            manager = BridgeManager(shared_dir)

            bridge = manager.get_bridge("nonexistent")
            assert bridge is None

    def test_list_bridges(self):
        """Test listing all bridges"""
        with tempfile.TemporaryDirectory() as tmpdir:
            shared_dir = Path(tmpdir) / "shared"
            manager = BridgeManager(shared_dir)

            manager.create_bridge("bridge1")
            manager.create_bridge("bridge2")
            manager.create_bridge("bridge3")

            bridges = manager.list_bridges()
            assert len(bridges) == 3
            assert "bridge1" in bridges
            assert "bridge2" in bridges
            assert "bridge3" in bridges


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
