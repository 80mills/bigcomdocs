# BigCommerce MCP Server - n8n Integration Guide

## Overview
This guide shows you how to connect your n8n instance to the BigCommerce MCP (Model Context Protocol) server to access BigCommerce API documentation, schemas, and tools.

## Prerequisites
- n8n instance running
- BigCommerce MCP server deployed (already done at: `https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app`)

## Available Endpoints

### 1. MCP API Endpoint
- **URL:** `/api/mcp`
- **Method:** POST
- **Purpose:** Handle MCP protocol requests

### 2. SSE (Server-Sent Events) Endpoint
- **URL:** `/api/sse`
- **Method:** GET
- **Purpose:** Real-time connection for n8n to receive live updates
- **Content-Type:** `text/event-stream`

### 3. Health Check Endpoint
- **URL:** `/health`
- **Method:** GET
- **Purpose:** Check server status

## Method 1: Direct HTTP Integration (Recommended)

### Step 1: Create HTTP Request Nodes
In your n8n workflow, add HTTP Request nodes to communicate with the MCP server:

#### Example: List Available Tools
```json
{
  "httpMethod": "POST",
  "url": "https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/mcp",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }
}
```

#### Example: Search Documentation
```json
{
  "httpMethod": "POST",
  "url": "https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/mcp",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "search_documentation",
      "arguments": {
        "query": "API rate limits"
      }
    }
  }
}
```

#### Example: Build HTTP Request
```json
{
  "httpMethod": "POST",
  "url": "https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/mcp",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "build_http_request",
      "arguments": {
        "endpoint": "/catalog/products",
        "method": "GET",
        "params": {
          "limit": 5
        }
      }
    }
  }
}
```

## Method 2: SSE Integration for Real-time Updates

### Step 1: Connect to SSE Endpoint
Use n8n's HTTP Request node to establish an SSE connection:

```json
{
  "httpMethod": "GET",
  "url": "https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/sse",
  "headers": {
    "Accept": "text/event-stream",
    "Cache-Control": "no-cache"
  }
}
```

### Step 2: Handle SSE Events
The SSE endpoint sends the following event types:

#### Connected Event
```json
{
  "event": "connected",
  "data": {
    "message": "SSE connection established",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "server": "BigCommerce MCP Server",
    "version": "1.0.0",
    "endpoint": "/api/sse"
  }
}
```

#### Status Event
```json
{
  "event": "status",
  "data": {
    "status": "ready",
    "availableEndpoints": [
      "/api/mcp",
      "/api/health",
      "/api/sse"
    ],
    "timestamp": "2024-01-15T10:30:00.000Z"
  }
}
```

#### Heartbeat Event (every 30 seconds)
```json
{
  "event": "heartbeat",
  "data": {
    "timestamp": "2024-01-15T10:30:30.000Z",
    "uptime": 1800.5,
    "memory": {
      "rss": 52428800,
      "heapTotal": 20971520,
      "heapUsed": 10485760
    },
    "environment": "production",
    "region": "iad1"
  }
}
```

#### Error Event
```json
{
  "event": "error",
  "data": {
    "error": "Error message",
    "timestamp": "2024-01-15T10:30:00.000Z"
  }
}
```

### Step 3: Process SSE Data in n8n
Use n8n's Code node to parse SSE events:

```javascript
// Parse SSE event data
const eventData = $input.first().json;

if (eventData.event === 'connected') {
  console.log('Connected to MCP server SSE');
} else if (eventData.event === 'status') {
  console.log('Server status:', eventData.data.status);
} else if (eventData.event === 'heartbeat') {
  console.log('Server heartbeat:', eventData.data.uptime);
} else if (eventData.event === 'error') {
  console.error('Server error:', eventData.data.error);
}

return eventData;
```

## Method 3: Using MCP Client Node (Advanced)

### Step 1: Install MCP Client
```bash
npm install -g n8n-nodes-mcp-client
```

### Step 2: Configure MCP Server
Use the `n8n-mcp-config.json` file to configure your MCP server connection.

## Available MCP Tools

### 1. Documentation Tools
- **`search_documentation`**: Search BigCommerce documentation
- **`get_documentation`**: Retrieve specific documentation files
- **`list_documentation`**: List available documentation

### 2. API Tools
- **`build_http_request`**: Build properly formatted HTTP requests
- **`get_api_endpoint`**: Get information about specific API endpoints
- **`validate_request`**: Validate API request parameters

### 3. Schema Tools
- **`get_schema`**: Retrieve API schemas
- **`validate_schema`**: Validate data against schemas
- **`list_schemas`**: List available schemas

## Example Use Cases

### 1. Automated API Request Building
```javascript
// n8n Code node
const mcpResponse = await $http.post({
  url: 'https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/mcp',
  headers: { 'Content-Type': 'application/json' },
  body: {
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'build_http_request',
      arguments: {
        endpoint: '/catalog/products',
        method: 'GET',
        params: { limit: 10 }
      }
    }
  }
});

// Use the built request
const builtRequest = mcpResponse.data.result.content;
```

### 2. Documentation Lookup
```javascript
// Search for specific documentation
const docResponse = await $http.post({
  url: 'https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/mcp',
  headers: { 'Content-Type': 'application/json' },
  body: {
    jsonrpc: '2.0',
    id: 1,
    method: 'tools/call',
    params: {
      name: 'search_documentation',
      arguments: { query: 'webhooks setup' }
    }
  }
});
```

### 3. Real-time Monitoring with SSE
```javascript
// Monitor server health via SSE
const sseResponse = await $http.get({
  url: 'https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/sse',
  headers: { 'Accept': 'text/event-stream' }
});

// Process SSE events
const events = sseResponse.data.split('\n\n');
events.forEach(event => {
  if (event.startsWith('event: heartbeat')) {
    const data = JSON.parse(event.split('data: ')[1]);
    console.log('Server uptime:', data.uptime);
  }
});
```

## Error Handling

### Common MCP Errors
- **Method not found**: Check the tool name in the `tools/list` response
- **Invalid arguments**: Verify the arguments match the tool's schema
- **Server error**: Check the MCP server logs

### n8n Error Handling
```javascript
try {
  const response = await $http.post({
    url: 'https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/mcp',
    headers: { 'Content-Type': 'application/json' },
    body: mcpRequest
  });
  
  if (response.data.error) {
    throw new Error(`MCP Error: ${response.data.error.message}`);
  }
  
  return response.data.result;
} catch (error) {
  console.error('MCP request failed:', error);
  throw error;
}
```

## Testing Your Integration

### 1. Test Health Endpoint
```bash
curl https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/health
```

### 2. Test MCP Endpoint
```bash
curl -X POST https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### 3. Test SSE Endpoint
```bash
curl -N https://mcpserverbigcommerce-3fwmkshgl-80mills-projects.vercel.app/api/sse \
  -H "Accept: text/event-stream"
```

## Troubleshooting

### Issues with n8n MCP Client
1. Ensure you're using the correct MCP server URL
2. Check that the MCP server is running and accessible
3. Verify the JSON-RPC format is correct

### SSE Connection Issues
1. Check that the SSE endpoint is accessible
2. Verify CORS headers are properly set
3. Ensure n8n can handle long-running connections

### Performance Optimization
1. Cache MCP responses when possible
2. Use batch requests for multiple operations
3. Implement retry logic for failed requests
4. Use SSE for real-time monitoring instead of polling

## Support
- **MCP Server Issues**: Check the server logs at the Vercel dashboard
- **n8n Integration**: Refer to n8n documentation for HTTP request nodes
- **BigCommerce API**: Consult the official BigCommerce documentation

## Next Steps
1. Import the example workflow
2. Test with simple queries
3. Build your own workflows using the MCP tools
4. Set up SSE monitoring for real-time updates 