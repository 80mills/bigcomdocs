# BigCommerce MCP Server - n8n Integration Guide

## Overview
This guide shows you how to connect your n8n instance to the BigCommerce MCP (Model Context Protocol) server to access BigCommerce API documentation, schemas, and tools.

## Prerequisites
- n8n instance running
- BigCommerce MCP server deployed (already done at: `https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app`)

## Method 1: Direct HTTP Integration (Recommended)

### Step 1: Create HTTP Request Nodes
In your n8n workflow, add HTTP Request nodes to communicate with the MCP server:

#### Example: List Available Tools
```json
{
  "httpMethod": "POST",
  "url": "https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/api/mcp",
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
  "url": "https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/api/mcp",
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
  "url": "https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/api/mcp",
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

### Step 2: Import the Example Workflow
1. In n8n, go to **Workflows** → **Import from file**
2. Select the `n8n-workflow-example.json` file from this repository
3. The workflow will be imported with three connected nodes

## Method 2: Using MCP Client Node (Advanced)

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
  url: 'https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/api/mcp',
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
  url: 'https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/api/mcp',
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

## Error Handling

### Common MCP Errors
- **Method not found**: Check the tool name in the `tools/list` response
- **Invalid arguments**: Verify the arguments match the tool's schema
- **Server error**: Check the MCP server logs

### n8n Error Handling
```javascript
try {
  const response = await $http.post({
    url: 'https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/api/mcp',
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
curl https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/health
```

### 2. Test MCP Endpoint
```bash
curl -X POST https://mcpserverbigcommerce-evi7wq3dp-80mills-projects.vercel.app/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Troubleshooting

### Issues with n8n MCP Client
1. Ensure you're using the correct MCP server URL
2. Check that the MCP server is running and accessible
3. Verify the JSON-RPC format is correct

### Performance Optimization
1. Cache MCP responses when possible
2. Use batch requests for multiple operations
3. Implement retry logic for failed requests

## Support
- **MCP Server Issues**: Check the server logs at the Vercel dashboard
- **n8n Integration**: Refer to n8n documentation for HTTP request nodes
- **BigCommerce API**: Consult the official BigCommerce documentation

## Next Steps
1. Import the example workflow
2. Test with simple queries
3. Build your own workflows using the MCP tools
4. Explore the available documentation and schemas 