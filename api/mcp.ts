import type { VercelRequest, VercelResponse } from '@vercel/node';
import { BigCommerceMCPServer } from '../src/index.js';

// Global server instance for reuse across invocations
let serverInstance: BigCommerceMCPServer | null = null;
let lastInitialized = 0;
const INITIALIZATION_TTL = 5 * 60 * 1000; // 5 minutes

async function getServerInstance(): Promise<BigCommerceMCPServer> {
  const now = Date.now();
  
  // Reuse existing instance if it's still fresh
  if (serverInstance && (now - lastInitialized) < INITIALIZATION_TTL) {
    return serverInstance;
  }
  
  // Create new instance
  console.log('Creating new server instance...');
  serverInstance = new BigCommerceMCPServer();
  
  try {
    await serverInstance.initialize();
    lastInitialized = now;
    console.log('Server instance initialized successfully');
    return serverInstance;
  } catch (error) {
    console.error('Failed to initialize server:', error);
    serverInstance = null;
    throw error;
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const startTime = Date.now();
  
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  // Set cache headers for static responses
  if (req.method === 'GET') {
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
  }

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    if (req.method === 'POST') {
      // Handle MCP requests
      const server = await getServerInstance();
      
      if (!req.body) {
        res.status(400).json({ 
          error: 'Request body is required',
          timestamp: new Date().toISOString()
        });
        return;
      }

      let response;
      
      if (req.body.method && req.body.params) {
        // Standard MCP request
        try {
          response = await server.server.request(req.body);
        } catch (mcpError) {
          console.error('MCP request error:', mcpError);
          res.status(400).json({
            error: 'Invalid MCP request',
            details: mcpError instanceof Error ? mcpError.message : String(mcpError),
            timestamp: new Date().toISOString()
          });
          return;
        }
      } else {
        // Custom request format for testing
        response = { 
          success: true, 
          message: 'BigCommerce MCP Server is running',
          timestamp: new Date().toISOString(),
          responseTime: Date.now() - startTime
        };
      }
      
      res.status(200).json(response);
      
    } else if (req.method === 'GET') {
      // Health check and info endpoint
      const healthData = {
        status: 'healthy',
        server: 'BigCommerce MCP Server',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        responseTime: Date.now() - startTime,
        environment: process.env.NODE_ENV || 'development',
        region: process.env.VERCEL_REGION || 'unknown',
        serverInstanceAge: serverInstance ? Date.now() - lastInitialized : 0
      };
      
      // Include detailed health check if requested
      if (req.query.detailed === 'true') {
        try {
          const server = await getServerInstance();
          const healthStatus = await server['getHealthStatus']();
          healthData['detailed'] = JSON.parse(healthStatus);
        } catch (error) {
          healthData['detailed'] = {
            error: 'Failed to get detailed health status',
            message: error instanceof Error ? error.message : String(error)
          };
        }
      }
      
      res.status(200).json(healthData);
      
    } else {
      res.status(405).json({ 
        error: 'Method not allowed',
        allowed: ['GET', 'POST', 'OPTIONS'],
        timestamp: new Date().toISOString()
      });
    }
    
  } catch (error) {
    console.error('Handler error:', error);
    
    const statusCode = error instanceof Error && error.message.includes('timeout') ? 504 : 500;
    
    res.status(statusCode).json({ 
      error: error instanceof Error ? error.message : 'Internal server error',
      timestamp: new Date().toISOString(),
      responseTime: Date.now() - startTime
    });
  }
} 