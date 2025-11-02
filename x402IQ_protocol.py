"""
x402IQ Protocol Implementation
A high-performance protocol implementation for distributed systems
"""

import base64
import gzip
import hashlib
import json
import logging
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
    compressed: bool = False  # New field for compression support

    def to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProtocolHeader':
        """Create header from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        # Handle optional compressed field for backward compatibility
        if 'compressed' not in data:
            data['compressed'] = False
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
    
    @staticmethod
    def compress_payload(payload: Dict[str, Any]) -> str:
        """
        Compress payload data using gzip
        
        Args:
            payload: Payload dictionary
            
        Returns:
            Base64 encoded compressed string
        """
        json_str = json.dumps(payload)
        compressed = gzip.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    
    @staticmethod
    def decompress_payload(compressed_str: str) -> Dict[str, Any]:
        """
        Decompress payload data using gzip
        
        Args:
            compressed_str: Base64 encoded compressed string
            
        Returns:
            Decompressed payload dictionary
        """
        compressed_bytes = base64.b64decode(compressed_str.encode('utf-8'))
        decompressed = gzip.decompress(compressed_bytes)
        return json.loads(decompressed.decode('utf-8'))


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

    def __init__(self, node_id: str, enable_logging: bool = True, log_level: int = logging.INFO,
                 default_timeout: int = 30):
        """
        Initialize protocol instance
        
        Args:
            node_id: Unique identifier for this node
            enable_logging: Whether to enable logging
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            default_timeout: Default timeout for requests in seconds
        """
        self.node_id = node_id
        self.message_counter = 0
        self.received_messages: Dict[str, ProtocolMessage] = {}
        self.outstanding_requests: Dict[str, float] = {}
        self.default_timeout = default_timeout
        
        # Setup logging
        if enable_logging:
            self.logger = logging.getLogger(f"x402IQ.{node_id}")
            self.logger.setLevel(log_level)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                self.logger.addHandler(handler)
        else:
            self.logger = None

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
        is_valid = calculated == message.header.checksum
        
        if self.logger and not is_valid:
            self.logger.warning(
                f"Invalid checksum for message {message.header.message_id} "
                f"from {message.header.source}"
            )
        
        return is_valid

    def create_message(
        self,
        message_type: MessageType,
        destination: str,
        payload: Dict[str, Any],
        compress: bool = False
    ) -> ProtocolMessage:
        """
        Create a new protocol message
        
        Args:
            message_type: Type of message
            destination: Destination node ID
            payload: Message payload data
            compress: Whether to compress the payload
            
        Returns:
            Complete protocol message
        """
        message_id = self._generate_message_id()
        
        # Compress if requested
        if compress:
            compressed_payload = ProtocolMessage.compress_payload(payload)
            actual_payload = {'_compressed': True, '_data': compressed_payload}
            checksum = self._calculate_checksum(actual_payload)
            header_compressed = True
        else:
            checksum = self._calculate_checksum(payload)
            actual_payload = payload
            header_compressed = False

        header = ProtocolHeader(
            version=self.PROTOCOL_VERSION,
            message_type=message_type,
            message_id=message_id,
            timestamp=time.time(),
            source=self.node_id,
            destination=destination,
            checksum=checksum,
            compressed=header_compressed
        )

        message = ProtocolMessage(header=header, payload=actual_payload)

        # Track requests for timeout handling
        if message_type == MessageType.REQUEST:
            self.outstanding_requests[message_id] = time.time()

        if self.logger:
            self.logger.debug(
                f"Created {message_type.value} message ID {message_id} "
                f"to {destination}{' [compressed]' if compress else ''}"
            )

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
            if self.logger:
                self.logger.debug(
                    f"Rejected message {message.header.message_id} - "
                    f"not addressed to this node"
                )
            return False, "Message not addressed to this node"

        # Validate checksum
        if not self._validate_checksum(message):
            return False, "Invalid checksum"

        # Check for duplicate message
        if message.header.message_id in self.received_messages:
            if self.logger:
                self.logger.warning(
                    f"Duplicate message ID {message.header.message_id} "
                    f"from {message.header.source}"
                )
            return False, "Duplicate message ID"

        # Validate version
        if message.header.version != self.PROTOCOL_VERSION:
            if self.logger:
                self.logger.warning(
                    f"Version mismatch for message {message.header.message_id}: "
                    f"expected {self.PROTOCOL_VERSION}, got {message.header.version}"
                )
            return False, "Protocol version mismatch"

        # Decompress if needed
        if message.payload.get('_compressed'):
            try:
                decompressed = ProtocolMessage.decompress_payload(message.payload['_data'])
                message.payload = decompressed
                if self.logger:
                    self.logger.debug(f"Decompressed message {message.header.message_id}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to decompress message: {e}")
                return False, "Failed to decompress payload"

        # Store received message
        self.received_messages[message.header.message_id] = message

        if self.logger:
            self.logger.debug(
                f"Received {message.header.message_type.value} message "
                f"{message.header.message_id} from {message.header.source}"
            )

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
        
        if self.logger:
            self.logger.error(
                f"Received error from {message.header.source}: "
                f"{error_code} - {error_message}"
            )
        else:
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

    def check_timeout(self, request_id: str, timeout: Optional[int] = None) -> bool:
        """
        Check if a request has timed out
        
        Args:
            request_id: ID of the request to check
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            True if request has timed out, False otherwise
        """
        if request_id not in self.outstanding_requests:
            return False
        
        timeout_seconds = timeout if timeout is not None else self.default_timeout
        elapsed = time.time() - self.outstanding_requests[request_id]
        return elapsed > timeout_seconds
    
    def cleanup_timed_out_requests(self, timeout: Optional[int] = None) -> List[str]:
        """
        Clean up timed out requests
        
        Args:
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            List of timed out request IDs
        """
        timeout_seconds = timeout if timeout is not None else self.default_timeout
        timed_out = []
        current_time = time.time()
        
        for req_id, req_time in list(self.outstanding_requests.items()):
            if current_time - req_time > timeout_seconds:
                timed_out.append(req_id)
                del self.outstanding_requests[req_id]
                
                if self.logger:
                    self.logger.warning(
                        f"Request {req_id} timed out after {timeout_seconds}s"
                    )
        
        return timed_out

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
            'protocol_version': self.PROTOCOL_VERSION,
            'default_timeout': self.default_timeout
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


