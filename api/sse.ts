import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Only allow GET requests for SSE
  if (req.method !== 'GET') {
    res.status(405).json({ 
      error: 'Method not allowed',
      allowed: ['GET', 'OPTIONS'],
      timestamp: new Date().toISOString()
    });
    return;
  }

  try {
    // Send initial connection event
    res.write(`event: connected\ndata: ${JSON.stringify({
      message: 'SSE connection established',
      timestamp: new Date().toISOString(),
      server: 'BigCommerce MCP Server',
      version: '1.0.0',
      endpoint: '/api/sse'
    })}\n\n`);

    // Send server status event
    res.write(`event: status\ndata: ${JSON.stringify({
      status: 'ready',
      availableEndpoints: [
        '/api/mcp',
        '/api/health',
        '/api/sse'
      ],
      timestamp: new Date().toISOString()
    })}\n\n`);

    // Send periodic heartbeat events
    const heartbeatInterval = setInterval(() => {
      res.write(`event: heartbeat\ndata: ${JSON.stringify({
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        environment: process.env.NODE_ENV || 'development',
        region: process.env.VERCEL_REGION || 'unknown'
      })}\n\n`);
    }, 30000); // Every 30 seconds

    // Handle client disconnect
    req.on('close', () => {
      console.log('SSE client disconnected');
      clearInterval(heartbeatInterval);
    });

    // Handle server shutdown
    req.on('aborted', () => {
      console.log('SSE connection aborted');
      clearInterval(heartbeatInterval);
    });

    // Keep connection alive
    req.on('error', (error) => {
      console.error('SSE connection error:', error);
      clearInterval(heartbeatInterval);
    });

  } catch (error) {
    console.error('SSE handler error:', error);
    
    // Send error event
    res.write(`event: error\ndata: ${JSON.stringify({
      error: error instanceof Error ? error.message : 'Internal server error',
      timestamp: new Date().toISOString()
    })}\n\n`);
    
    res.end();
  }
} 