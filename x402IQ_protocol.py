"""
x402IQ Protocol Implementation
A high-performance protocol implementation for distributed systems
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class ProtocolError(Exception):
    """Base exception for x402IQ protocol errors"""
    pass


class MessageType(Enum):
    """Message types in x402IQ protocol"""
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    NOTIFICATION = "NOTIFICATION"
    ERROR = "ERROR"


@dataclass
class ProtocolHeader:
    """Protocol header structure"""
    version: str
    message_type: MessageType
    message_id: str
    timestamp: float
    source: str
    destination: str
    checksum: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolHeader':
        """Create header from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


@dataclass
class ProtocolMessage:
    """Complete protocol message structure"""
    header: ProtocolHeader
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'header': self.header.to_dict(),
            'payload': self.payload
        }

    def to_json(self) -> str:
        """Serialize message to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolMessage':
        """Create message from dictionary"""
        return cls(
            header=ProtocolHeader.from_dict(data['header']),
            payload=data['payload']
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'ProtocolMessage':
        """Deserialize message from JSON string"""
        return cls.from_dict(json.loads(json_str))


class X402IQProtocol:
    """
    x402IQ Protocol implementation
    
    Features:
    - Secure message transmission with checksums
    - Message type validation
    - Automatic timestamping
    - Request/Response pattern
    - Error handling
    """

    PROTOCOL_VERSION = "1.0"
    CHECKSUM_ALGORITHM = "sha256"

    def __init__(self, node_id: str):
        """
        Initialize protocol instance
        
        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id
        self.message_counter = 0
        self.received_messages: Dict[str, ProtocolMessage] = {}
        self.outstanding_requests: Dict[str, float] = {}

    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        self.message_counter += 1
        timestamp = time.time()
        unique_str = f"{self.node_id}_{self.message_counter}_{timestamp}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _calculate_checksum(self, payload: Dict[str, Any]) -> str:
        """
        Calculate checksum for payload
        
        Args:
            payload: Message payload data
            
        Returns:
            Checksum string
        """
        payload_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_json.encode()).hexdigest()

    def _validate_checksum(self, message: ProtocolMessage) -> bool:
        """
        Validate message checksum
        
        Args:
            message: Protocol message to validate
            
        Returns:
            True if checksum is valid, False otherwise
        """
        calculated = self._calculate_checksum(message.payload)
        return calculated == message.header.checksum

    def create_message(
        self,
        message_type: MessageType,
        destination: str,
        payload: Dict[str, Any]
    ) -> ProtocolMessage:
        """
        Create a new protocol message
        
        Args:
            message_type: Type of message
            destination: Destination node ID
            payload: Message payload data
            
        Returns:
            Complete protocol message
        """
        message_id = self._generate_message_id()
        checksum = self._calculate_checksum(payload)

        header = ProtocolHeader(
            version=self.PROTOCOL_VERSION,
            message_type=message_type,
            message_id=message_id,
            timestamp=time.time(),
            source=self.node_id,
            destination=destination,
            checksum=checksum
        )

        message = ProtocolMessage(header=header, payload=payload)

        # Track requests for timeout handling
        if message_type == MessageType.REQUEST:
            self.outstanding_requests[message_id] = time.time()

        return message

    def create_request(
        self,
        destination: str,
        action: str,
        params: Optional[Dict[str, Any]] = None
    ) -> ProtocolMessage:
        """
        Create a REQUEST message
        
        Args:
            destination: Destination node ID
            action: Action to request
            params: Optional parameters for the action
            
        Returns:
            Protocol message
        """
        payload = {'action': action}
        if params:
            payload['params'] = params

        return self.create_message(MessageType.REQUEST, destination, payload)

    def create_response(
        self,
        request_message: ProtocolMessage,
        result: Any,
        success: bool = True
    ) -> ProtocolMessage:
        """
        Create a RESPONSE message to a REQUEST
        
        Args:
            request_message: Original request message
            result: Response result data
            success: Whether the request was successful
            
        Returns:
            Protocol message
        """
        payload = {
            'success': success,
            'result': result,
            'request_id': request_message.header.message_id
        }

        message = self.create_message(
            MessageType.RESPONSE,
            request_message.header.source,
            payload
        )

        # Remove from outstanding requests if exists
        if request_message.header.message_id in self.outstanding_requests:
            del self.outstanding_requests[request_message.header.message_id]

        return message

    def create_error_response(
        self,
        request_message: ProtocolMessage,
        error_code: str,
        error_message: str
    ) -> ProtocolMessage:
        """
        Create an ERROR response
        
        Args:
            request_message: Original request message
            error_code: Error code
            error_message: Error description
            
        Returns:
            Protocol message
        """
        payload = {
            'success': False,
            'error_code': error_code,
            'error_message': error_message,
            'request_id': request_message.header.message_id
        }

        message = self.create_message(
            MessageType.ERROR,
            request_message.header.source,
            payload
        )

        if request_message.header.message_id in self.outstanding_requests:
            del self.outstanding_requests[request_message.header.message_id]

        return message

    def create_notification(
        self,
        destination: str,
        event: str,
        data: Optional[Dict[str, Any]] = None
    ) -> ProtocolMessage:
        """
        Create a NOTIFICATION message
        
        Args:
            destination: Destination node ID
            event: Event name
            data: Optional event data
            
        Returns:
            Protocol message
        """
        payload = {'event': event}
        if data:
            payload['data'] = data

        return self.create_message(MessageType.NOTIFICATION, destination, payload)

    def receive_message(self, message: ProtocolMessage) -> Tuple[bool, Optional[str]]:
        """
        Receive and validate a protocol message
        
        Args:
            message: Incoming protocol message
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if message is for this node
        if message.header.destination != self.node_id:
            return False, "Message not addressed to this node"

        # Validate checksum
        if not self._validate_checksum(message):
            return False, "Invalid checksum"

        # Check for duplicate message
        if message.header.message_id in self.received_messages:
            return False, "Duplicate message ID"

        # Validate version
        if message.header.version != self.PROTOCOL_VERSION:
            return False, "Protocol version mismatch"

        # Store received message
        self.received_messages[message.header.message_id] = message

        return True, None

    def process_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """
        Process received message and generate response if needed
        
        Args:
            message: Incoming protocol message
            
        Returns:
            Response message if required, None otherwise
        """
        is_valid, error = self.receive_message(message)
        if not is_valid:
            raise ProtocolError(f"Invalid message: {error}")

        # Process based on message type
        if message.header.message_type == MessageType.REQUEST:
            return self._handle_request(message)
        elif message.header.message_type == MessageType.NOTIFICATION:
            self._handle_notification(message)
            return None
        elif message.header.message_type == MessageType.RESPONSE:
            self._handle_response(message)
            return None
        elif message.header.message_type == MessageType.ERROR:
            self._handle_error(message)
            return None

    def _handle_request(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """
        Handle incoming REQUEST message
        
        Args:
            message: Request message
            
        Returns:
            Response message or None
        """
        action = message.payload.get('action', '')
        params = message.payload.get('params', {})

        # Default handler - override in subclass
        return self.create_error_response(
            message,
            'NOT_IMPLEMENTED',
            f'Action "{action}" not implemented'
        )

    def _handle_notification(self, message: ProtocolMessage) -> None:
        """Handle incoming NOTIFICATION message"""
        event = message.payload.get('event', '')
        data = message.payload.get('data', {})
        # Default handler - override in subclass
        print(f"Received notification: {event}")

    def _handle_response(self, message: ProtocolMessage) -> None:
        """Handle incoming RESPONSE message"""
        request_id = message.payload.get('request_id', '')
        success = message.payload.get('success', False)
        result = message.payload.get('result', {})
        # Default handler - override in subclass
        print(f"Received response for request {request_id}: success={success}")

    def _handle_error(self, message: ProtocolMessage) -> None:
        """Handle incoming ERROR message"""
        error_code = message.payload.get('error_code', '')
        error_message = message.payload.get('error_message', '')
        # Default handler - override in subclass
        print(f"Received error: {error_code} - {error_message}")

    def cleanup_old_messages(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old messages from storage
        
        Args:
            max_age_seconds: Maximum age of messages to keep
            
        Returns:
            Number of messages cleaned up
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds

        # Clean received messages
        to_remove = [
            msg_id for msg_id, msg in self.received_messages.items()
            if msg.header.timestamp < cutoff_time
        ]
        for msg_id in to_remove:
            del self.received_messages[msg_id]

        # Clean outstanding requests
        to_remove_requests = [
            req_id for req_id, req_time in self.outstanding_requests.items()
            if req_time < cutoff_time
        ]
        for req_id in to_remove_requests:
            del self.outstanding_requests[req_id]

        return len(to_remove) + len(to_remove_requests)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get protocol statistics
        
        Returns:
            Dictionary with protocol statistics
        """
        return {
            'node_id': self.node_id,
            'total_messages_sent': self.message_counter,
            'messages_received': len(self.received_messages),
            'outstanding_requests': len(self.outstanding_requests),
            'protocol_version': self.PROTOCOL_VERSION
        }


# Example usage
if __name__ == "__main__":
    # Create protocol instances for two nodes
    node_a = X402IQProtocol("node_A")
    node_b = X402IQProtocol("node_B")

    # Node A creates a request
    request = node_a.create_request("node_B", "get_info", {"query": "status"})
    print("Node A creates request:")
    print(request.to_json())
    print()

    # Node B processes the request
    try:
        response = node_b.process_message(request)
        if response:
            print("Node B responds:")
            print(response.to_json())
            print()
    except ProtocolError as e:
        print(f"Protocol error: {e}")
        print()

    # Get statistics
    print("Node A stats:", node_a.get_stats())
    print("Node B stats:", node_b.get_stats())

