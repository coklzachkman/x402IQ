"""
Example usage of x402IQ Protocol
Demonstrates basic protocol operations and communication patterns
"""

from x402IQ_protocol import X402IQProtocol, MessageType, ProtocolMessage, ProtocolError


def example_basic_communication():
    """Example: Basic request/response communication"""
    print("=" * 60)
    print("Example 1: Basic Request/Response Communication")
    print("=" * 60)
    
    # Create two nodes
    client = X402IQProtocol("client_node")
    server = X402IQProtocol("server_node")
    
    # Client creates a request
    request = client.create_request(
        destination="server_node",
        action="get_data",
        params={"user_id": "12345"}
    )
    
    print(f"\nClient sends request:")
    print(f"  Action: {request.payload['action']}")
    print(f"  Message ID: {request.header.message_id}")
    print(f"  Timestamp: {request.header.timestamp}")
    
    # Server processes the request
    try:
        response = server.process_message(request)
        if response:
            print(f"\nServer responds:")
            print(f"  Success: {response.payload['success']}")
            print(f"  Request ID: {response.payload['request_id']}")
    except ProtocolError as e:
        print(f"Error: {e}")
    
    print()


def example_error_handling():
    """Example: Error handling and invalid messages"""
    print("=" * 60)
    print("Example 2: Error Handling")
    print("=" * 60)
    
    node_a = X402IQProtocol("node_A")
    node_b = X402IQProtocol("node_B")
    
    # Create a request
    request = node_a.create_request(
        destination="node_B",
        action="unknown_action",
        params={}
    )
    
    # Process - will return error response
    try:
        response = node_b.process_message(request)
        if response and response.header.message_type == MessageType.ERROR:
            print(f"\nReceived error response:")
            print(f"  Error Code: {response.payload['error_code']}")
            print(f"  Error Message: {response.payload['error_message']}")
    except ProtocolError as e:
        print(f"Protocol Error: {e}")
    
    print()


def example_json_serialization():
    """Example: JSON serialization and transmission"""
    print("=" * 60)
    print("Example 3: JSON Serialization")
    print("=" * 60)
    
    sender = X402IQProtocol("sender")
    receiver = X402IQProtocol("receiver")
    
    # Create a notification
    notification = sender.create_notification(
        destination="receiver",
        event="system_update",
        data={"version": "2.0", "features": ["A", "B", "C"]}
    )
    
    # Serialize to JSON
    json_data = notification.to_json()
    print(f"\nSerialized message (JSON):")
    print(json_data)
    
    # Deserialize from JSON
    received_message = ProtocolMessage.from_json(json_data)
    
    # Process message
    try:
        receiver.process_message(received_message)
        print("\nMessage successfully received and processed!")
    except ProtocolError as e:
        print(f"Error: {e}")
    
    print()


def example_custom_protocol():
    """Example: Custom protocol with specific handlers"""
    print("=" * 60)
    print("Example 4: Custom Protocol Implementation")
    print("=" * 60)
    
    class ServerProtocol(X402IQProtocol):
        """Custom protocol with specific request handlers"""
        
        def __init__(self, node_id):
            super().__init__(node_id)
            self.data_store = {
                "user_1": {"name": "Alice", "score": 100},
                "user_2": {"name": "Bob", "score": 85}
            }
        
        def _handle_request(self, message: ProtocolMessage) -> ProtocolMessage:
            """Handle specific actions"""
            action = message.payload.get('action', '')
            params = message.payload.get('params', {})
            
            if action == 'get_user':
                user_id = params.get('user_id')
                if user_id in self.data_store:
                    return self.create_response(
                        message,
                        {"user": self.data_store[user_id]},
                        success=True
                    )
                else:
                    return self.create_error_response(
                        message,
                        "USER_NOT_FOUND",
                        f"User {user_id} not found"
                    )
            
            elif action == 'update_score':
                user_id = params.get('user_id')
                new_score = params.get('score')
                if user_id in self.data_store:
                    self.data_store[user_id]['score'] = new_score
                    return self.create_response(
                        message,
                        {"status": "updated", "user_id": user_id},
                        success=True
                    )
                else:
                    return self.create_error_response(
                        message,
                        "USER_NOT_FOUND",
                        f"User {user_id} not found"
                    )
            
            else:
                return self.create_error_response(
                    message,
                    'UNKNOWN_ACTION',
                    f'Unknown action: {action}'
                )
    
    # Create protocol instances
    client = X402IQProtocol("client")
    server = ServerProtocol("server")
    
    # Request user data
    request1 = client.create_request(
        destination="server",
        action="get_user",
        params={"user_id": "user_1"}
    )
    
    response1 = server.process_message(request1)
    print(f"\nGet user request:")
    print(f"  Success: {response1.payload['success']}")
    print(f"  Result: {response1.payload['result']}")
    
    # Update user score
    request2 = client.create_request(
        destination="server",
        action="update_score",
        params={"user_id": "user_1", "score": 120}
    )
    
    response2 = server.process_message(request2)
    print(f"\nUpdate score request:")
    print(f"  Success: {response2.payload['success']}")
    print(f"  Result: {response2.payload['result']}")
    
    # Request updated user data
    request3 = client.create_request(
        destination="server",
        action="get_user",
        params={"user_id": "user_1"}
    )
    
    response3 = server.process_message(request3)
    print(f"\nGet user again:")
    print(f"  Success: {response3.payload['success']}")
    print(f"  Result: {response3.payload['result']}")
    
    print()


def example_statistics():
    """Example: Protocol statistics"""
    print("=" * 60)
    print("Example 5: Protocol Statistics")
    print("=" * 60)
    
    node = X402IQProtocol("monitored_node")
    
    # Send some messages
    for i in range(5):
        node.create_notification(
            destination="target_node",
            event="heartbeat",
            data={"sequence": i}
        )
    
    # Get statistics
    stats = node.get_stats()
    print(f"\nProtocol Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()


def example_checksum_validation():
    """Example: Checksum validation"""
    print("=" * 60)
    print("Example 6: Checksum Validation")
    print("=" * 60)
    
    sender = X402IQProtocol("sender")
    receiver = X402IQProtocol("receiver")
    
    # Create a message
    message = sender.create_notification(
        destination="receiver",
        event="test_event",
        data={"value": "original"}
    )
    
    # Valid message
    is_valid, error = receiver.receive_message(message)
    print(f"\nOriginal message validation:")
    print(f"  Valid: {is_valid}")
    if error:
        print(f"  Error: {error}")
    
    # Tampered message
    tampered_message = message
    tampered_message.payload['data']['value'] = 'modified'
    is_valid, error = receiver.receive_message(tampered_message)
    print(f"\nTampered message validation:")
    print(f"  Valid: {is_valid}")
    if error:
        print(f"  Error: {error}")
    
    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("x402IQ Protocol - Usage Examples")
    print("=" * 60 + "\n")
    
    example_basic_communication()
    example_error_handling()
    example_json_serialization()
    example_custom_protocol()
    example_statistics()
    example_checksum_validation()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

