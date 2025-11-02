"""
MCP-x402IQ Adapter
Translates between Model Context Protocol (MCP) and x402IQ Protocol
Enables AI assistants to access tools via secure x402IQ network
"""

import json
import time
from typing import Dict, Any, Optional, List, Callable
from x402IQ_protocol import (
    X402IQProtocol,
    ProtocolMessage,
    MessageType,
    ProtocolError
)


class MCPx402IQAdapter:
    """
    Adapter that translates MCP protocol to/from x402IQ protocol
    Variant 1: x402IQ as Transport Layer for MCP
    """
    
    def __init__(self, node_id: str, enable_logging: bool = True):
        """
        Initialize MCP-x402IQ adapter
        
        Args:
            node_id: Unique identifier for this adapter node
            enable_logging: Enable logging for debugging
        """
        self.node_id = node_id
        self.protocol = X402IQProtocol(node_id, enable_logging=enable_logging)
        self.mcp_tools: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        
    def register_mcp_tool(
        self,
        tool_name: str,
        description: str,
        tool_handler: Callable,
        parameters_schema: Optional[Dict[str, Any]] = None
    ):
        """
        Register an MCP tool that can be called via x402IQ
        
        Args:
            tool_name: Name of the tool
            description: Description of what the tool does
            tool_handler: Function that executes the tool
            parameters_schema: JSON schema for tool parameters
        """
        self.mcp_tools[tool_name] = {
            'name': tool_name,
            'description': description,
            'handler': tool_handler,
            'parameters': parameters_schema or {}
        }
        
    def _mcp_request_to_x402iq(
        self,
        mcp_request: Dict[str, Any],
        destination: str
    ) -> ProtocolMessage:
        """
        Convert MCP request to x402IQ message
        
        Args:
            mcp_request: MCP-formatted request
            destination: Destination node ID
            
        Returns:
            x402IQ ProtocolMessage
        """
        payload = {
            'mcp_method': mcp_request.get('method', ''),
            'mcp_params': mcp_request.get('params', {}),
            'mcp_id': mcp_request.get('id'),
            'mcp_jsonrpc': mcp_request.get('jsonrpc', '2.0')
        }
        
        return self.protocol.create_request(
            destination=destination,
            action='mcp_call',
            params=payload
        )
    
    def _x402iq_to_mcp_response(
        self,
        x402_message: ProtocolMessage
    ) -> Dict[str, Any]:
        """
        Convert x402IQ response to MCP response format
        
        Args:
            x402_message: x402IQ response message
            
        Returns:
            MCP-formatted response
        """
        payload = x402_message.payload
        
        # Handle error responses
        if x402_message.header.message_type == MessageType.ERROR:
            mcp_response = {
                'jsonrpc': '2.0',
                'id': payload.get('mcp_id'),
                'error': {
                    'code': payload.get('error_code', -32000),
                    'message': payload.get('error_message', 'Unknown error')
                }
            }
        else:
            # Success response
            mcp_response = {
                'jsonrpc': '2.0',
                'id': payload.get('mcp_id'),
                'result': payload.get('result', {})
            }
        
        return mcp_response
    
    def send_mcp_request(
        self,
        destination: str,
        mcp_request: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send MCP request via x402IQ network
        
        Args:
            destination: Target x402IQ node ID
            mcp_request: MCP-formatted request
            timeout: Request timeout in seconds
            
        Returns:
            MCP-formatted response
        """
        # Convert to x402IQ message
        x402_message = self._mcp_request_to_x402iq(mcp_request, destination)
        
        # Store pending request
        request_id = x402_message.header.message_id
        self.pending_requests[request_id] = {
            'mcp_id': mcp_request.get('id'),
            'timestamp': time.time()
        }
        
        # For this example, we'll simulate sending and receiving
        # In real implementation, this would use network transport
        return {'status': 'sent', 'message_id': request_id}
    
    def receive_x402iq_message(
        self,
        message: ProtocolMessage
    ) -> Optional[Dict[str, Any]]:
        """
        Receive and process x402IQ message, convert to MCP if needed
        
        Args:
            message: Incoming x402IQ message
            
        Returns:
            MCP-formatted response if applicable, None otherwise
        """
        try:
            response = self.protocol.process_message(message)
            
            if response:
                # Check if this is an MCP-related message
                if response.payload.get('mcp_id'):
                    return self._x402iq_to_mcp_response(response)
            
            return None
            
        except ProtocolError as e:
            return {
                'jsonrpc': '2.0',
                'id': message.payload.get('mcp_id'),
                'error': {
                    'code': -32603,
                    'message': f'Protocol error: {str(e)}'
                }
            }
    
    def _handle_mcp_tool_call(
        self,
        message: ProtocolMessage
    ) -> ProtocolMessage:
        """
        Handle incoming MCP tool call request
        
        Args:
            message: x402IQ message containing MCP tool call
            
        Returns:
            x402IQ response message
        """
        payload = message.payload.get('params', {})
        mcp_method = payload.get('mcp_method', '')
        mcp_params = payload.get('mcp_params', {})
        mcp_id = payload.get('mcp_id')
        
        # Handle different MCP methods
        if mcp_method == 'tools/list':
            # List available tools
            tools = [
                {
                    'name': tool['name'],
                    'description': tool['description'],
                    'parameters': tool['parameters']
                }
                for tool in self.mcp_tools.values()
            ]
            
            result = {
                'mcp_id': mcp_id,
                'result': {'tools': tools}
            }
            
            return self.protocol.create_response(message, result, success=True)
            
        elif mcp_method == 'tools/call':
            # Call a specific tool
            tool_name = mcp_params.get('name', '')
            tool_args = mcp_params.get('arguments', {})
            
            if tool_name not in self.mcp_tools:
                return self.protocol.create_error_response(
                    message,
                    'TOOL_NOT_FOUND',
                    f'Tool "{tool_name}" not found'
                )
            
            try:
                # Execute tool
                tool_handler = self.mcp_tools[tool_name]['handler']
                tool_result = tool_handler(**tool_args)
                
                result = {
                    'mcp_id': mcp_id,
                    'result': {
                        'content': [
                            {
                                'type': 'text',
                                'text': json.dumps(tool_result)
                            }
                        ]
                    }
                }
                
                return self.protocol.create_response(message, result, success=True)
                
            except Exception as e:
                return self.protocol.create_error_response(
                    message,
                    'TOOL_EXECUTION_ERROR',
                    f'Error executing tool: {str(e)}'
                )
        
        else:
            return self.protocol.create_error_response(
                message,
                'UNKNOWN_METHOD',
                f'Unknown MCP method: {mcp_method}'
            )
    
    def handle_mcp_request(
        self,
        message: ProtocolMessage
    ) -> Optional[ProtocolMessage]:
        """
        Handle incoming x402IQ message that contains MCP request
        
        Args:
            message: x402IQ message with MCP request
            
        Returns:
            x402IQ response message or None
        """
        # Validate message is for this node
        is_valid, error = self.protocol.receive_message(message)
        if not is_valid:
            raise ProtocolError(f"Invalid message: {error}")
        
        # Check if this is an MCP-related request
        action = message.payload.get('action', '')
        if action == 'mcp_call':
            return self._handle_mcp_tool_call(message)
        
        # Default handler
        return self.protocol._handle_request(message)
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered MCP tools
        
        Returns:
            List of tool definitions
        """
        return [
            {
                'name': tool['name'],
                'description': tool['description'],
                'parameters': tool['parameters']
            }
            for tool in self.mcp_tools.values()
        ]


class MCPx402IQServer:
    """
    MCP Server that uses x402IQ for internal tool communication
    Variant 2: MCP Server with x402IQ Backend
    """
    
    def __init__(self, server_id: str):
        """
        Initialize MCP server with x402IQ backend
        
        Args:
            server_id: Unique identifier for this server
        """
        self.server_id = server_id
        self.adapter = MCPx402IQAdapter(server_id)
        self.remote_tools: Dict[str, str] = {}  # tool_name -> x402iq_node_id
        
    def register_local_tool(
        self,
        tool_name: str,
        description: str,
        tool_handler: Callable,
        parameters_schema: Optional[Dict[str, Any]] = None
    ):
        """Register a tool that runs locally"""
        self.adapter.register_mcp_tool(
            tool_name,
            description,
            tool_handler,
            parameters_schema
        )
    
    def register_remote_tool(
        self,
        tool_name: str,
        x402iq_node_id: str,
        description: str,
        parameters_schema: Optional[Dict[str, Any]] = None
    ):
        """
        Register a tool that runs on a remote x402IQ node
        
        Args:
            tool_name: Name of the tool
            x402iq_node_id: x402IQ node ID where tool runs
            description: Tool description
            parameters_schema: Tool parameter schema
        """
        self.remote_tools[tool_name] = x402iq_node_id
        
        # Register as local tool but with remote handler
        def remote_handler(**kwargs):
            return self._call_remote_tool(tool_name, kwargs)
        
        self.adapter.register_mcp_tool(
            tool_name,
            description,
            remote_handler,
            parameters_schema
        )
    
    def _call_remote_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool on a remote x402IQ node
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if tool_name not in self.remote_tools:
            raise ValueError(f"Remote tool {tool_name} not found")
        
        remote_node = self.remote_tools[tool_name]
        
        # Create x402IQ request to remote node
        request = self.adapter.protocol.create_request(
            destination=remote_node,
            action='execute_tool',
            params={
                'tool_name': tool_name,
                'arguments': arguments
            }
        )
        
        # In real implementation, send via network and wait for response
        # For now, return placeholder
        return {'status': 'sent_to_remote', 'node': remote_node}
    
    def handle_mcp_request(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP request (standard MCP format)
        
        Args:
            mcp_request: MCP-formatted request
            
        Returns:
            MCP-formatted response
        """
        # Convert MCP request to internal x402IQ format
        # This allows using x402IQ features even for local tools
        method = mcp_request.get('method', '')
        params = mcp_request.get('params', {})
        request_id = mcp_request.get('id')
        
        # Create internal x402IQ message
        internal_message = self.adapter.protocol.create_request(
            destination=self.server_id,
            action='internal_mcp_call',
            params={
                'mcp_method': method,
                'mcp_params': params,
                'mcp_id': request_id
            }
        )
        
        # Process via adapter
        response = self.adapter.handle_mcp_request(internal_message)
        
        if response:
            return self.adapter._x402iq_to_mcp_response(response)
        else:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32603,
                    'message': 'Internal error'
                }
            }


class MCPx402IQClient:
    """
    MCP Client that communicates via x402IQ network
    Variant 4: MCP Client via x402IQ Network
    """
    
    def __init__(self, client_id: str):
        """
        Initialize MCP client with x402IQ transport
        
        Args:
            client_id: Unique identifier for this client
        """
        self.client_id = client_id
        self.protocol = X402IQProtocol(client_id)
        self.server_nodes: Dict[str, str] = {}  # server_name -> x402iq_node_id
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        
    def register_server(
        self,
        server_name: str,
        x402iq_node_id: str
    ):
        """
        Register an MCP server accessible via x402IQ
        
        Args:
            server_name: Human-readable server name
            x402iq_node_id: x402IQ node ID of the server
        """
        self.server_nodes[server_name] = x402iq_node_id
    
    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call a tool on a remote MCP server via x402IQ
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            timeout: Request timeout
            
        Returns:
            Tool result
        """
        if server_name not in self.server_nodes:
            raise ValueError(f"Server {server_name} not registered")
        
        server_node = self.server_nodes[server_name]
        
        # Create MCP request
        mcp_request = {
            'jsonrpc': '2.0',
            'id': f"{self.client_id}_{int(time.time() * 1000)}",
            'method': 'tools/call',
            'params': {
                'name': tool_name,
                'arguments': arguments
            }
        }
        
        # Wrap in x402IQ message
        x402_message = self.protocol.create_request(
            destination=server_node,
            action='mcp_call',
            params={
                'mcp_request': mcp_request
            }
        )
        
        # Store pending request
        self.pending_requests[x402_message.header.message_id] = {
            'mcp_id': mcp_request['id'],
            'server': server_name,
            'tool': tool_name
        }
        
        # In real implementation, send via network and wait for response
        return {'status': 'sent', 'message_id': x402_message.header.message_id}
    
    def list_tools(
        self,
        server_name: str
    ) -> Dict[str, Any]:
        """
        List available tools on a server
        
        Args:
            server_name: Name of the server
            
        Returns:
            List of available tools
        """
        if server_name not in self.server_nodes:
            raise ValueError(f"Server {server_name} not registered")
        
        server_node = self.server_nodes[server_name]
        
        mcp_request = {
            'jsonrpc': '2.0',
            'id': f"{self.client_id}_{int(time.time() * 1000)}",
            'method': 'tools/list',
            'params': {}
        }
        
        x402_message = self.protocol.create_request(
            destination=server_node,
            action='mcp_call',
            params={'mcp_request': mcp_request}
        )
        
        return {'status': 'sent', 'message_id': x402_message.header.message_id}
    
    def handle_response(self, message: ProtocolMessage) -> Optional[Dict[str, Any]]:
        """
        Handle incoming x402IQ response
        
        Args:
            message: x402IQ response message
            
        Returns:
            MCP-formatted response if applicable
        """
        is_valid, error = self.protocol.receive_message(message)
        if not is_valid:
            return None
        
        if message.header.message_type == MessageType.RESPONSE:
            result = message.payload.get('result', {})
            mcp_response = result.get('mcp_response', {})
            
            if mcp_response:
                return mcp_response
        
        return None

