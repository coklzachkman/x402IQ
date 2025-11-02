# MCP Integration Quick Start Guide

This guide shows you how to quickly get started with x402IQ + MCP integration.

## Prerequisites

- Python 3.8+
- x402IQ Protocol installed
- Understanding of MCP (Model Context Protocol) basics

## Quick Start: Variant 1 (Transport Layer)

This is the simplest integration - wrapping MCP messages in x402IQ for secure transport.

### Step 1: Create an MCP Server with x402IQ Transport

```python
from mcp_x402iq_adapter import MCPx402IQAdapter

# Create adapter (acts as MCP server)
server = MCPx402IQAdapter("my_mcp_server")

# Register a tool
def my_tool(value: str) -> str:
    return f"Processed: {value}"

server.register_mcp_tool(
    "my_tool",
    "A simple tool",
    my_tool,
    {
        "type": "object",
        "properties": {
            "value": {"type": "string"}
        },
        "required": ["value"]
    }
)
```

### Step 2: Client Sends Request

```python
from x402IQ_protocol import X402IQProtocol

client = X402IQProtocol("client_1")

# Create MCP request
mcp_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "my_tool",
        "arguments": {"value": "hello"}
    }
}

# Wrap in x402IQ message
x402_message = client.create_request(
    destination="my_mcp_server",
    action="mcp_call",
    params={
        "mcp_method": mcp_request["method"],
        "mcp_params": mcp_request["params"],
        "mcp_id": mcp_request["id"],
        "mcp_jsonrpc": mcp_request["jsonrpc"]
    }
)
```

### Step 3: Server Processes Request

```python
# Server receives and processes
response = server.handle_mcp_request(x402_message)

if response:
    mcp_response = server._x402iq_to_mcp_response(response)
    print(f"Result: {mcp_response}")
```

## Quick Start: Distributed Tools (Variant 2)

Create an MCP server that can use tools across multiple x402IQ nodes.

```python
from mcp_x402iq_adapter import MCPx402IQServer

# Create distributed server
server = MCPx402IQServer("distributed_server")

# Local tool
def local_format(text: str) -> str:
    return text.upper()

server.register_local_tool(
    "format",
    "Format text locally",
    local_format
)

# Remote tool (on another x402IQ node)
server.register_remote_tool(
    "analyze",
    "compute_node_1",  # x402IQ node ID
    "Analyze data remotely",
    {"type": "object", "properties": {"data": {"type": "string"}}}
)

# Handle MCP request
mcp_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}

response = server.handle_mcp_request(mcp_request)
```

## Quick Start: MCP Client (Variant 4)

Create an MCP client that accesses servers via x402IQ network.

```python
from mcp_x402iq_adapter import MCPx402IQClient

# Create client
client = MCPx402IQClient("ai_client")

# Register servers
client.register_server("weather_api", "weather_node")
client.register_server("data_api", "data_node")

# Call tools
result = client.call_tool(
    "weather_api",
    "get_weather",
    {"city": "New York"},
    timeout=10
)

# List available tools
tools = client.list_tools("weather_api")
```

## Running Examples

Run the full examples:

```bash
python examples/mcp_integration_example.py
```

This demonstrates all integration variants with working code.

## Key Benefits

### Security
- All MCP messages have SHA-256 checksums
- Automatic tamper detection
- Message integrity verification

### Reliability
- Timeout management for tool calls
- Message deduplication
- Automatic cleanup of stale requests

### Scalability
- Distribute tools across multiple nodes
- Load balancing capabilities
- Compression for large responses

### Observability
- Built-in logging
- Statistics tracking
- Message audit trail

## Next Steps

1. Read `MCP_INTEGRATION_PROPOSAL.md` for detailed architecture
2. Explore `examples/mcp_integration_example.py` for complete examples
3. Customize adapters for your specific use case
4. Integrate with your AI assistant (Claude, ChatGPT, etc.)

## Common Use Cases

### Use Case 1: Secure AI Tool Execution
AI assistant needs to call tools securely across network.

**Solution**: Use Variant 1 (Transport Layer) - wrap MCP in x402IQ.

### Use Case 2: Distributed AI Pipeline
AI workflow requires tools on multiple servers.

**Solution**: Use Variant 2 (Distributed Backend) - MCP server with remote tools.

### Use Case 3: AI Orchestration
AI assistant manages microservices.

**Solution**: Use Variant 3 (Tool Exposure) - expose x402IQ services as MCP tools.

### Use Case 4: Multi-Server AI Access
AI assistant needs tools from multiple providers.

**Solution**: Use Variant 4 (Client Network) - MCP client with multiple servers.

## Troubleshooting

### Issue: Tool not found
- Check tool registration with `server.list_available_tools()`
- Verify tool name matches exactly
- Check x402IQ node IDs for remote tools

### Issue: Timeout errors
- Increase timeout parameter
- Check network connectivity
- Verify remote node is accessible

### Issue: Checksum validation fails
- Ensure message wasn't modified in transit
- Check payload serialization
- Verify x402IQ protocol version compatibility

## Integration with Real AI Assistants

To integrate with Claude or ChatGPT:

1. **Create MCP Server**: Use `MCPx402IQServer` as your MCP server
2. **Expose Tools**: Register your tools using `register_local_tool()` or `register_remote_tool()`
3. **Configure AI Assistant**: Point AI assistant to your MCP server endpoint
4. **Use x402IQ Transport**: All communication automatically uses x402IQ protocol

## Support

For questions or issues:
- Check `MCP_INTEGRATION_PROPOSAL.md` for architecture details
- Review example code in `examples/mcp_integration_example.py`
- Open an issue on GitHub

