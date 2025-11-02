"""
Examples demonstrating x402IQ + MCP integration
Shows different integration variants in action
"""

from mcp_x402iq_adapter import (
    MCPx402IQAdapter,
    MCPx402IQServer,
    MCPx402IQClient
)
import json


def example_variant1_transport_layer():
    """
    Variant 1: x402IQ as Transport Layer for MCP
    Demonstrates wrapping MCP messages in x402IQ protocol
    """
    print("=" * 70)
    print("Example 1: x402IQ as Transport Layer for MCP")
    print("=" * 70)
    
    # Create adapter (acts as MCP server)
    server = MCPx402IQAdapter("mcp_server_1", enable_logging=True)
    
    # Register some tools
    def calculate_sum(a: float, b: float) -> float:
        """Calculate sum of two numbers"""
        return a + b
    
    def get_weather(city: str) -> dict:
        """Get weather for a city (mock)"""
        return {
            'city': city,
            'temperature': 72,
            'condition': 'sunny',
            'humidity': 65
        }
    
    server.register_mcp_tool(
        "calculate_sum",
        "Add two numbers together",
        calculate_sum,
        {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["a", "b"]
        }
    )
    
    server.register_mcp_tool(
        "get_weather",
        "Get current weather for a city",
        get_weather,
        {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    )
    
    # Client creates MCP request
    from x402IQ_protocol import X402IQProtocol
    
    client = X402IQProtocol("mcp_client_1")
    
    # Create MCP request wrapped in x402IQ
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "calculate_sum",
            "arguments": {
                "a": 15,
                "b": 27
            }
        }
    }
    
    # Wrap in x402IQ message
    x402_message = client.create_request(
        destination="mcp_server_1",
        action="mcp_call",
        params={
            "mcp_method": mcp_request["method"],
            "mcp_params": mcp_request["params"],
            "mcp_id": mcp_request["id"],
            "mcp_jsonrpc": mcp_request["jsonrpc"]
        }
    )
    
    print("\n1. Client sends MCP request wrapped in x402IQ:")
    print(f"   Tool: {mcp_request['params']['name']}")
    print(f"   Arguments: {mcp_request['params']['arguments']}")
    print(f"   x402IQ Message ID: {x402_message.header.message_id}")
    print(f"   Checksum: {x402_message.header.checksum[:16]}...")
    
    # Server processes the request
    response = server.handle_mcp_request(x402_message)
    
    if response:
        mcp_response = server._x402iq_to_mcp_response(response)
        print("\n2. Server responds (via x402IQ):")
        print(f"   Success: {mcp_response.get('result', {}).get('content', [{}])[0].get('text', 'N/A')}")
        result_data = json.loads(mcp_response.get('result', {}).get('content', [{}])[0].get('text', '{}'))
        print(f"   Result: {result_data}")
    
    print()


def example_variant2_distributed_backend():
    """
    Variant 2: MCP Server with x402IQ Backend
    Shows distributed tool execution across x402IQ nodes
    """
    print("=" * 70)
    print("Example 2: MCP Server with x402IQ Backend (Distributed Tools)")
    print("=" * 70)
    
    # Create MCP server that can use local and remote tools
    server = MCPx402IQServer("distributed_mcp_server")
    
    # Register a local tool
    def local_format(data: str) -> str:
        """Format data locally"""
        return f"[FORMATTED] {data.upper()} [/FORMATTED]"
    
    server.register_local_tool(
        "local_format",
        "Format text locally",
        local_format,
        {
            "type": "object",
            "properties": {
                "data": {"type": "string"}
            },
            "required": ["data"]
        }
    )
    
    # Register a remote tool (would be on another x402IQ node)
    server.register_remote_tool(
        "remote_analyze",
        "compute_node_1",  # This tool runs on compute_node_1
        "Analyze data on remote compute node",
        {
            "type": "object",
            "properties": {
                "data": {"type": "string"}
            },
            "required": ["data"]
        }
    )
    
    print("\nRegistered tools:")
    print("  - local_format: Runs locally")
    print("  - remote_analyze: Runs on compute_node_1 via x402IQ")
    
    # Handle standard MCP request
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = server.handle_mcp_request(mcp_request)
    print(f"\nMCP tools/list response:")
    print(json.dumps(response, indent=2))
    
    print()


def example_variant3_tool_exposure():
    """
    Variant 3: x402IQ Tools Exposed as MCP Tools
    Shows how x402IQ services can be accessed via MCP
    """
    print("=" * 70)
    print("Example 3: x402IQ Tools Exposed as MCP Tools")
    print("=" * 70)
    
    # Create x402IQ service node
    service_node = X402IQProtocol("data_service")
    
    # Register service that will be exposed as MCP tool
    def data_service_handler(action: str, params: dict) -> dict:
        """x402IQ service handler"""
        if action == "get_stats":
            return {
                "total_requests": 1000,
                "active_users": 42,
                "uptime": "5d 12h 30m"
            }
        elif action == "query_data":
            query = params.get("query", "")
            return {
                "results": [f"Result for: {query}"],
                "count": 1
            }
        else:
            raise ValueError(f"Unknown action: {action}")
    
    # Create MCP bridge that exposes x402IQ services
    bridge = MCPx402IQAdapter("mcp_bridge")
    
    def expose_x402iq_service(tool_name: str, action: str):
        """Expose x402IQ action as MCP tool"""
        def mcp_tool_handler(**kwargs):
            # Call x402IQ service
            request = bridge.protocol.create_request(
                destination="data_service",
                action=action,
                params=kwargs
            )
            # In real implementation, this would be sent over network
            # For now, simulate response
            result = data_service_handler(action, kwargs)
            return result
        
        bridge.register_mcp_tool(
            tool_name,
            f"MCP wrapper for x402IQ service action: {action}",
            mcp_tool_handler
        )
    
    # Expose x402IQ services as MCP tools
    expose_x402iq_service("get_service_stats", "get_stats")
    expose_x402iq_service("query_service_data", "query_data")
    
    print("\nExposed x402IQ services as MCP tools:")
    tools = bridge.list_available_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Now AI assistant can call these via MCP
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_service_stats",
            "arguments": {}
        }
    }
    
    # Create x402IQ message
    from x402IQ_protocol import X402IQProtocol
    client = X402IQProtocol("ai_client")
    
    x402_message = client.create_request(
        destination="mcp_bridge",
        action="mcp_call",
        params={
            "mcp_method": mcp_request["method"],
            "mcp_params": mcp_request["params"],
            "mcp_id": mcp_request["id"],
            "mcp_jsonrpc": mcp_request["jsonrpc"]
        }
    )
    
    print(f"\nAI client calls MCP tool (via x402IQ):")
    print(f"  Tool: get_service_stats")
    print(f"  x402IQ Message ID: {x402_message.header.message_id}")
    
    response = bridge.handle_mcp_request(x402_message)
    if response:
        print(f"  Response: {response}")
    
    print()


def example_variant4_client_via_network():
    """
    Variant 4: MCP Client via x402IQ Network
    Shows MCP client accessing multiple servers through x402IQ network
    """
    print("=" * 70)
    print("Example 4: MCP Client via x402IQ Network")
    print("=" * 70)
    
    # Create MCP client
    client = MCPx402IQClient("ai_assistant_client")
    
    # Register multiple MCP servers accessible via x402IQ
    client.register_server("weather_service", "weather_node_1")
    client.register_server("data_service", "data_node_1")
    client.register_server("compute_service", "compute_node_1")
    
    print("\nRegistered MCP servers:")
    for name, node_id in client.server_nodes.items():
        print(f"  - {name}: x402IQ node {node_id}")
    
    # Call tools on different servers
    print("\nCalling tools across network:")
    
    # Call weather tool
    result1 = client.call_tool(
        "weather_service",
        "get_weather",
        {"city": "San Francisco"},
        timeout=10
    )
    print(f"  1. Weather service: {result1['status']}")
    
    # Call data tool
    result2 = client.list_tools("data_service")
    print(f"  2. Data service tools: {result2['status']}")
    
    # Call compute tool
    result3 = client.call_tool(
        "compute_service",
        "calculate",
        {"expression": "2 + 2"},
        timeout=5
    )
    print(f"  3. Compute service: {result3['status']}")
    
    print()


def example_security_benefits():
    """
    Demonstrate security benefits of x402IQ + MCP integration
    """
    print("=" * 70)
    print("Example 5: Security Benefits of x402IQ + MCP")
    print("=" * 70)
    
    adapter = MCPx402IQAdapter("secure_server")
    
    def sensitive_operation(user_id: str, action: str) -> dict:
        """A sensitive operation that benefits from x402IQ security"""
        return {
            "user_id": user_id,
            "action": action,
            "status": "completed",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    
    adapter.register_mcp_tool(
        "sensitive_operation",
        "Perform sensitive operation with security guarantees",
        sensitive_operation
    )
    
    from x402IQ_protocol import X402IQProtocol
    client = X402IQProtocol("trusted_client")
    
    # Create secure request
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "sensitive_operation",
            "arguments": {
                "user_id": "user123",
                "action": "transfer_funds"
            }
        }
    }
    
    x402_message = client.create_request(
        destination="secure_server",
        action="mcp_call",
        params={
            "mcp_method": mcp_request["method"],
            "mcp_params": mcp_request["params"],
            "mcp_id": mcp_request["id"],
            "mcp_jsonrpc": mcp_request["jsonrpc"]
        },
        compress=False  # Can enable compression for large payloads
    )
    
    print("\nSecure MCP request via x402IQ:")
    print(f"  Message ID: {x402_message.header.message_id}")
    print(f"  Checksum: {x402_message.header.checksum}")
    print(f"  Timestamp: {x402_message.header.timestamp}")
    print(f"  Source: {x402_message.header.source}")
    print(f"  Destination: {x402_message.header.destination}")
    
    # Validate checksum
    is_valid, error = adapter.protocol.receive_message(x402_message)
    print(f"\n  Checksum Validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Demonstrate tamper detection
    tampered_message = x402_message
    tampered_message.payload['params']['mcp_params']['arguments']['action'] = 'malicious_action'
    is_valid_tampered, _ = adapter.protocol.receive_message(tampered_message)
    print(f"  Tampered Message: {'✓ Valid' if is_valid_tampered else '✗ Invalid (detected!)'}")
    
    print()


def main():
    """Run all MCP integration examples"""
    print("\n" + "=" * 70)
    print("x402IQ + MCP Integration Examples")
    print("=" * 70 + "\n")
    
    example_variant1_transport_layer()
    example_variant2_distributed_backend()
    example_variant3_tool_exposure()
    example_variant4_client_via_network()
    example_security_benefits()
    
    print("=" * 70)
    print("All MCP integration examples completed!")
    print("=" * 70 + "\n")
    print("\nIntegration Variants Summary:")
    print("  1. x402IQ as Transport: Secure, reliable MCP message delivery")
    print("  2. Distributed Backend: Tools across multiple x402IQ nodes")
    print("  3. Tool Exposure: x402IQ services accessible via MCP")
    print("  4. Client Network: AI assistants with network-aware tool selection")
    print("  5. Security Benefits: Checksums, deduplication, timeouts")


if __name__ == "__main__":
    main()

