import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set cache headers for health checks
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    res.status(405).json({ 
      error: 'Method not allowed',
      allowed: ['GET'],
      timestamp: new Date().toISOString()
    });
    return;
  }

  const startTime = Date.now();

  try {
    const healthData = {
      status: 'healthy',
      service: 'BigCommerce MCP Server',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      responseTime: Date.now() - startTime,
      environment: process.env.NODE_ENV || 'development',
      region: process.env.VERCEL_REGION || 'unknown',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      deployment: {
        vercel: process.env.VERCEL === '1',
        deploymentId: process.env.VERCEL_GIT_COMMIT_SHA?.substring(0, 8) || 'unknown'
      }
    };

    res.status(200).json(healthData);
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
      responseTime: Date.now() - startTime
    });
  }
} 