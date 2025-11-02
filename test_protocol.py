"""
Comprehensive test suite for x402IQ Protocol
"""

import unittest
import time
from x402IQ_protocol import (
    X402IQProtocol,
    MessageType,
    ProtocolMessage,
    ProtocolHeader,
    ProtocolError
)


class TestProtocolBasics(unittest.TestCase):
    """Test basic protocol functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.node_a = X402IQProtocol("node_A")
        self.node_b = X402IQProtocol("node_B")

    def test_protocol_initialization(self):
        """Test protocol initialization"""
        self.assertEqual(self.node_a.node_id, "node_A")
        self.assertEqual(self.node_a.message_counter, 0)
        self.assertEqual(len(self.node_a.received_messages), 0)

    def test_message_creation(self):
        """Test basic message creation"""
        message = self.node_a.create_message(
            MessageType.REQUEST,
            "node_B",
            {"test": "data"}
        )
        self.assertIsInstance(message, ProtocolMessage)
        self.assertEqual(message.header.source, "node_A")
        self.assertEqual(message.header.destination, "node_B")
        self.assertEqual(message.header.message_type, MessageType.REQUEST)
        self.assertIsNotNone(message.header.message_id)
        self.assertIsNotNone(message.header.checksum)

    def test_checksum_calculation(self):
        """Test checksum calculation and validation"""
        payload = {"key": "value"}
        checksum = self.node_a._calculate_checksum(payload)
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)  # SHA256 hex length

        # Same payload should give same checksum
        checksum2 = self.node_a._calculate_checksum(payload)
        self.assertEqual(checksum, checksum2)

    def test_checksum_validation(self):
        """Test checksum validation"""
        message = self.node_a.create_message(
            MessageType.REQUEST,
            "node_B",
            {"test": "data"}
        )
        self.assertTrue(self.node_a._validate_checksum(message))

        # Tampered message should fail validation
        message.payload["test"] = "modified"
        self.assertFalse(self.node_a._validate_checksum(message))


class TestMessageTypes(unittest.TestCase):
    """Test different message types"""

    def setUp(self):
        """Set up test fixtures"""
        self.node_a = X402IQProtocol("node_A")
        self.node_b = X402IQProtocol("node_B")

    def test_create_request(self):
        """Test REQUEST message creation"""
        request = self.node_a.create_request(
            destination="node_B",
            action="get_data",
            params={"key": "value"}
        )
        self.assertEqual(request.header.message_type, MessageType.REQUEST)
        self.assertEqual(request.payload["action"], "get_data")
        self.assertEqual(request.payload["params"]["key"], "value")

    def test_create_response(self):
        """Test RESPONSE message creation"""
        request = self.node_a.create_request("node_B", "test", {})
        response = self.node_a.create_response(request, {"status": "ok"}, True)

        self.assertEqual(response.header.message_type, MessageType.RESPONSE)
        self.assertEqual(response.payload["success"], True)
        self.assertEqual(response.payload["result"]["status"], "ok")
        self.assertEqual(response.payload["request_id"], request.header.message_id)

    def test_create_error_response(self):
        """Test ERROR message creation"""
        request = self.node_a.create_request("node_B", "test", {})
        error = self.node_a.create_error_response(
            request,
            "TEST_ERROR",
            "Test error message"
        )

        self.assertEqual(error.header.message_type, MessageType.ERROR)
        self.assertEqual(error.payload["success"], False)
        self.assertEqual(error.payload["error_code"], "TEST_ERROR")
        self.assertEqual(error.payload["error_message"], "Test error message")

    def test_create_notification(self):
        """Test NOTIFICATION message creation"""
        notification = self.node_a.create_notification(
            destination="node_B",
            event="test_event",
            data={"info": "test"}
        )

        self.assertEqual(notification.header.message_type, MessageType.NOTIFICATION)
        self.assertEqual(notification.payload["event"], "test_event")
        self.assertEqual(notification.payload["data"]["info"], "test")


class TestMessageSerialization(unittest.TestCase):
    """Test message serialization/deserialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.node = X402IQProtocol("test_node")

    def test_json_serialization(self):
        """Test JSON serialization"""
        message = self.node.create_notification(
            destination="target",
            event="test",
            data={"key": "value"}
        )

        json_str = message.to_json()
        self.assertIsInstance(json_str, str)
        self.assertIn("header", json_str)
        self.assertIn("payload", json_str)

        # Deserialize
        deserialized = ProtocolMessage.from_json(json_str)
        self.assertEqual(deserialized.payload["event"], "test")
        self.assertEqual(deserialized.header.destination, "target")

    def test_dict_serialization(self):
        """Test dictionary serialization"""
        message = self.node.create_notification("target", "test", {})
        message_dict = message.to_dict()

        self.assertIsInstance(message_dict, dict)
        self.assertIn("header", message_dict)
        self.assertIn("payload", message_dict)

        # Deserialize
        deserialized = ProtocolMessage.from_dict(message_dict)
        self.assertEqual(deserialized.payload["event"], "test")


class TestMessageValidation(unittest.TestCase):
    """Test message validation logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.node_a = X402IQProtocol("node_A")
        self.node_b = X402IQProtocol("node_B")

    def test_valid_message_receipt(self):
        """Test valid message receipt"""
        message = self.node_a.create_notification("node_B", "test", {})
        is_valid, error = self.node_b.receive_message(message)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_wrong_destination_rejection(self):
        """Test rejection of message with wrong destination"""
        message = self.node_a.create_notification("node_C", "test", {})
        is_valid, error = self.node_b.receive_message(message)

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_invalid_checksum_rejection(self):
        """Test rejection of message with invalid checksum"""
        message = self.node_a.create_notification("node_B", "test", {})
        message.payload["tampered"] = True  # Tamper with payload
        is_valid, error = self.node_b.receive_message(message)

        self.assertFalse(is_valid)
        self.assertEqual(error, "Invalid checksum")

    def test_duplicate_message_rejection(self):
        """Test rejection of duplicate messages"""
        message = self.node_a.create_notification("node_B", "test", {})
        is_valid, error = self.node_b.receive_message(message)
        self.assertTrue(is_valid)

        # Try to receive same message again
        is_valid2, error2 = self.node_b.receive_message(message)
        self.assertFalse(is_valid2)
        self.assertEqual(error2, "Duplicate message ID")

    def test_version_mismatch_rejection(self):
        """Test rejection of message with wrong version"""
        message = self.node_a.create_notification("node_B", "test", {})
        message.header.version = "2.0"  # Wrong version
        is_valid, error = self.node_b.receive_message(message)

        self.assertFalse(is_valid)
        self.assertEqual(error, "Protocol version mismatch")


class TestMessageProcessing(unittest.TestCase):
    """Test message processing"""

    def setUp(self):
        """Set up test fixtures"""
        self.node_a = X402IQProtocol("node_A")
        self.node_b = X402IQProtocol("node_B")

    def test_process_request(self):
        """Test processing a request message"""
        request = self.node_a.create_request("node_B", "test_action", {})
        response = self.node_b.process_message(request)

        self.assertIsInstance(response, ProtocolMessage)
        self.assertEqual(response.header.message_type, MessageType.ERROR)
        self.assertEqual(response.payload["error_code"], "NOT_IMPLEMENTED")

    def test_process_notification(self):
        """Test processing a notification message"""
        notification = self.node_a.create_notification("node_B", "test_event", {})
        response = self.node_b.process_message(notification)

        self.assertIsNone(response)  # Notifications don't return responses

    def test_invalid_message_error(self):
        """Test error handling for invalid messages"""
        message = self.node_a.create_notification("wrong_node", "test", {})
        
        with self.assertRaises(ProtocolError):
            self.node_b.process_message(message)


class TestCustomProtocol(unittest.TestCase):
    """Test custom protocol implementations"""

    def test_custom_request_handler(self):
        """Test custom request handler"""
        class CustomProtocol(X402IQProtocol):
            def _handle_request(self, message):
                return self.create_response(
                    message,
                    {"custom": "response"},
                    True
                )

        node = CustomProtocol("custom_node")
        request = self.create_request_inline("custom_node", "test", {})
        response = node.process_message(request)

        self.assertEqual(response.payload["success"], True)
        self.assertEqual(response.payload["result"]["custom"], "response")

    def create_request_inline(self, destination, action, params):
        """Helper to create a request for testing"""
        node_a = X402IQProtocol("test_client")
        return node_a.create_request(destination, action, params)


class TestStatistics(unittest.TestCase):
    """Test protocol statistics"""

    def setUp(self):
        """Set up test fixtures"""
        self.node = X402IQProtocol("stats_node")

    def test_empty_stats(self):
        """Test statistics for empty node"""
        stats = self.node.get_stats()
        
        self.assertEqual(stats["node_id"], "stats_node")
        self.assertEqual(stats["total_messages_sent"], 0)
        self.assertEqual(stats["messages_received"], 0)
        self.assertEqual(stats["outstanding_requests"], 0)

    def test_stats_after_messages(self):
        """Test statistics after sending messages"""
        # Send some messages
        self.node.create_notification("target", "event1", {})
        self.node.create_request("target", "action1", {})
        self.node.create_notification("target", "event2", {})

        stats = self.node.get_stats()
        self.assertEqual(stats["total_messages_sent"], 3)
        self.assertEqual(stats["outstanding_requests"], 1)  # Request tracked


class TestCleanup(unittest.TestCase):
    """Test message cleanup functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.node = X402IQProtocol("cleanup_node")

    def test_cleanup_empty(self):
        """Test cleanup on empty node"""
        cleaned = self.node.cleanup_old_messages(3600)
        self.assertEqual(cleaned, 0)

    def test_cleanup_old_messages(self):
        """Test cleanup of old messages"""
        # Create and receive some messages
        msg1 = self.node.create_notification("target", "test1", {})
        time.sleep(0.01)  # Small delay to ensure different timestamps
        self.node.receive_message(msg1)

        msg2 = self.node.create_notification("target", "test2", {})
        self.node.receive_message(msg2)

        # Cleanup old messages (very aggressive - 0 seconds)
        cleaned = self.node.cleanup_old_messages(max_age_seconds=0)
        self.assertGreater(cleaned, 0)

        stats = self.node.get_stats()
        self.assertEqual(stats["messages_received"], 0)


class TestOutstandingRequests(unittest.TestCase):
    """Test outstanding request tracking"""

    def setUp(self):
        """Set up test fixtures"""
        self.node_a = X402IQProtocol("node_A")
        self.node_b = X402IQProtocol("node_B")

    def test_request_tracking(self):
        """Test that requests are tracked"""
        request = self.node_a.create_request("node_B", "test", {})
        
        stats = self.node_a.get_stats()
        self.assertEqual(stats["outstanding_requests"], 1)

        # Simulate response
        response = self.node_a.create_response(request, {}, True)
        stats = self.node_a.get_stats()
        self.assertEqual(stats["outstanding_requests"], 0)


if __name__ == "__main__":
    unittest.main()
