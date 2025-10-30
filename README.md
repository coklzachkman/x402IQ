# x402IQ Protocol

A high-performance, secure protocol implementation for distributed systems and network communication.

## Overview

x402IQ is a robust protocol designed for reliable message transmission and transaction in distributed networks. It provides secure communication with built-in checksum validation, automatic message tracking, and comprehensive error handling.

## Features

- **Secure Message Transmission**: SHA-256 checksum validation for data integrity
- **Multiple Message Types**: Request, Response, Notification, and Error messages
- **Automatic Timestamping**: Built-in timestamps for message ordering and tracking
- **Request/Response Pattern**: Full support for synchronous and asynchronous communication
- **Message Deduplication**: Automatic detection and prevention of duplicate messages
- **Protocol Versioning**: Version validation for compatibility checking
- **Cleanup Management**: Automatic cleanup of old messages and outstanding requests
- **Statistics**: Built-in protocol statistics and monitoring

## Installation

### Requirements

- Python 3.8 or higher
- No external dependencies required (uses only Python standard library)

### Setup

1. Clone or download this repository:
```bash
git clone https://github.com/yourusername/x402IQ.git
cd x402IQ
```

2. The protocol is ready to use! No additional installation steps required.

## Quick Start

### Basic Usage

```python
from x402IQ_protocol import X402IQProtocol, MessageType

# Create protocol instances
node_a = X402IQProtocol("node_A")
node_b = X402IQProtocol("node_B")

# Node A creates a request
request = node_a.create_request(
    destination="node_B",
    action="get_data",
    params={"key": "value"}
)

# Convert to JSON for transmission
json_message = request.to_json()

# Node B receives and processes the message
message = ProtocolMessage.from_json(json_message)
response = node_b.process_message(message)

# Convert response to JSON
json_response = response.to_json()
```

### Message Types

#### Request Message
```python
request = node_a.create_request(
    destination="node_B",
    action="perform_action",
    params={"param1": "value1"}
)
```

#### Response Message
```python
response = node_b.create_response(
    request_message=request,
    result={"status": "success", "data": [...]},
    success=True
)
```

#### Error Response
```python
error = node_b.create_error_response(
    request_message=request,
    error_code="INVALID_PARAMS",
    error_message="Parameter validation failed"
)
```

#### Notification Message
```python
notification = node_a.create_notification(
    destination="node_B",
    event="system_update",
    data={"version": "2.0"}
)
```

### Custom Handlers

Extend the `X402IQProtocol` class to implement custom message handlers:

```python
from x402IQ_protocol import X402IQProtocol, ProtocolMessage

class CustomProtocol(X402IQProtocol):
    def _handle_request(self, message: ProtocolMessage) -> ProtocolMessage:
        action = message.payload.get('action', '')
        params = message.payload.get('params', {})
        
        if action == 'get_status':
            result = {"status": "online", "uptime": 12345}
            return self.create_response(message, result, success=True)
        elif action == 'process_data':
            # Process data
            processed = self.process(params.get('data'))
            return self.create_response(message, {"result": processed}, success=True)
        else:
            return self.create_error_response(
                message,
                'UNKNOWN_ACTION',
                f'Unknown action: {action}'
            )
```

## Protocol Structure

### Message Format

Each protocol message consists of a header and payload:

```json
{
  "header": {
    "version": "1.0",
    "message_type": "REQUEST",
    "message_id": "abc123...",
    "timestamp": 1234567890.123,
    "source": "node_A",
    "destination": "node_B",
    "checksum": "sha256_hash..."
  },
  "payload": {
    "action": "get_data",
    "params": {
      "key": "value"
    }
  }
}
```

### Checksum Calculation

The protocol uses SHA-256 to calculate checksums for payload data:
- Ensures message integrity during transmission
- Automatically validated on message receipt
- Rejects messages with invalid checksums

### Message IDs

Each message receives a unique ID generated from:
- Node ID
- Message counter
- Timestamp

This ensures global uniqueness and prevents collisions.

## API Reference

### Class: X402IQProtocol

#### Methods

- `create_message(message_type, destination, payload)` - Create a new protocol message
- `create_request(destination, action, params)` - Create a REQUEST message
- `create_response(request_message, result, success)` - Create a RESPONSE message
- `create_error_response(request_message, error_code, error_message)` - Create an ERROR message
- `create_notification(destination, event, data)` - Create a NOTIFICATION message
- `receive_message(message)` - Validate and store received message
- `process_message(message)` - Process message and return response
- `cleanup_old_messages(max_age_seconds)` - Remove old messages from storage
- `get_stats()` - Get protocol statistics

### Class: ProtocolMessage

#### Methods

- `to_dict()` - Convert message to dictionary
- `to_json()` - Serialize message to JSON string
- `from_dict(data)` - Create message from dictionary
- `from_json(json_str)` - Deserialize message from JSON string

## Error Handling

The protocol includes comprehensive error handling:

```python
try:
    response = node.process_message(incoming_message)
except ProtocolError as e:
    print(f"Protocol error: {e}")
```

Common errors:
- Invalid checksums
- Duplicate message IDs
- Version mismatches
- Invalid message formats

## Statistics and Monitoring

Get protocol statistics:

```python
stats = node.get_stats()
print(stats)
# {
#   'node_id': 'node_A',
#   'total_messages_sent': 42,
#   'messages_received': 38,
#   'outstanding_requests': 4,
#   'protocol_version': '1.0'
# }
```

## Message Cleanup

Automatically clean up old messages:

```python
# Remove messages older than 1 hour
cleaned = node.cleanup_old_messages(max_age_seconds=3600)
print(f"Cleaned up {cleaned} old messages")
```

## Use Cases

- **Microservices Communication**: Inter-service messaging in distributed systems
- **IoT Networks**: Device-to-device communication
- **Blockchain Nodes**: Peer-to-peer network protocols
- **Message Queues**: Reliable message delivery systems
- **Distributed Computing**: Task coordination and synchronization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Contact the maintainers

## Version History

- **1.0.0** - Initial release
  - Core protocol implementation
  - Request/Response pattern
  - Checksum validation
  - Message tracking
  - Statistics and monitoring

## Acknowledgments

Built with the goal of providing a simple, secure, and reliable protocol for distributed systems.
