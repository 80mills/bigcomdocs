import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { Config } from './config/index.js';
import { OpenAPIParser } from './parsers/openapi-parser.js';
import { MDXParser } from './parsers/mdx-parser.js';
import { SchemaParser } from './parsers/schema-parser.js';
import { APITools } from './tools/api-tools.js';
import { DocumentationTools } from './tools/documentation-tools.js';
import { SchemaTools } from './tools/schema-tools.js';

export class BigCommerceMCPServer {
  public server: Server;
  private config: Config;
  private openApiParser?: OpenAPIParser;
  private mdxParser?: MDXParser;
  private schemaParser?: SchemaParser;
  private apiTools?: APITools;
  private documentationTools?: DocumentationTools;
  private schemaTools?: SchemaTools;
  private initialized = false;

  constructor(basePath?: string) {
    this.config = Config.getInstance(basePath);
    this.server = new Server(
      {
        name: this.config.serverName,
        version: this.config.serverVersion,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private async initializeParsers(): Promise<void> {
    if (this.initialized) return;

    try {
      // Initialize parsers lazily
      this.openApiParser = new OpenAPIParser(this.config.referencePath);
      this.mdxParser = new MDXParser(this.config.docsPath);
      this.schemaParser = new SchemaParser(this.config.modelsPath);

      // Initialize tools
      this.apiTools = new APITools(this.openApiParser);
      this.documentationTools = new DocumentationTools(this.mdxParser);
      this.schemaTools = new SchemaTools(this.schemaParser);

      this.initialized = true;
    } catch (error) {
      console.error('Error initializing parsers:', error);
      throw new Error(`Failed to initialize parsers: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private setupHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          // API Tools
          {
            name: 'search_api_endpoints',
            description: 'Search for API endpoints across all BigCommerce APIs',
            inputSchema: {
              type: 'object',
              properties: {
                query: { type: 'string', description: 'Search query for endpoints' },
                method: { 
                  type: 'string', 
                  description: 'HTTP method (GET, POST, etc.)', 
                  enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] 
                },
                api_category: { type: 'string', description: 'API category to search within' }
              },
              required: ['query']
            }
          },
          {
            name: 'get_api_spec',
            description: 'Get complete OpenAPI specification for a specific API',
            inputSchema: {
              type: 'object',
              properties: {
                api_name: { type: 'string', description: 'Name of the API (e.g., "widgets", "catalog", "orders")' }
              },
              required: ['api_name']
            }
          },
          {
            name: 'get_endpoint_details',
            description: 'Get detailed information about a specific API endpoint',
            inputSchema: {
              type: 'object',
              properties: {
                api_name: { type: 'string', description: 'API name' },
                endpoint_path: { type: 'string', description: 'Endpoint path' },
                method: { type: 'string', description: 'HTTP method' }
              },
              required: ['api_name', 'endpoint_path', 'method']
            }
          },
          {
            name: 'list_api_categories',
            description: 'List all available API categories',
            inputSchema: { type: 'object', properties: {} }
          },
          {
            name: 'recommend_api_for_use_case',
            description: 'Intelligently recommend the best API for a specific use case',
            inputSchema: {
              type: 'object',
              properties: {
                use_case: { type: 'string', description: 'Description of what you want to accomplish' },
                operation_type: { 
                  type: 'string', 
                  description: 'Type of operation (query, update, create, delete)', 
                  enum: ['query', 'update', 'create', 'delete'] 
                },
                scale: { 
                  type: 'string', 
                  description: 'Scale of operation (single, bulk, batch)', 
                  enum: ['single', 'bulk', 'batch'] 
                }
              },
              required: ['use_case']
            }
          },
          {
            name: 'build_http_request',
            description: 'Build a complete HTTP request for BigCommerce API with examples',
            inputSchema: {
              type: 'object',
              properties: {
                api_name: { type: 'string', description: 'Name of the API' },
                endpoint_path: { type: 'string', description: 'API endpoint path' },
                method: { 
                  type: 'string', 
                  description: 'HTTP method', 
                  enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] 
                },
                parameters: { type: 'object', description: 'Query parameters and path parameters' },
                body: { type: 'object', description: 'Request body for POST/PUT/PATCH requests' },
                auth_type: { 
                  type: 'string', 
                  description: 'Authentication type', 
                  enum: ['bearer', 'basic'], 
                  default: 'bearer' 
                }
              },
              required: ['api_name', 'endpoint_path', 'method']
            }
          },

          // Documentation Tools
          {
            name: 'search_documentation',
            description: 'Search across all BigCommerce documentation',
            inputSchema: {
              type: 'object',
              properties: {
                query: { type: 'string', description: 'Search query' },
                section: { type: 'string', description: 'Documentation section to search within' },
                limit: { type: 'integer', description: 'Maximum number of results', default: 10 }
              },
              required: ['query']
            }
          },
          {
            name: 'get_documentation_section',
            description: 'Get specific documentation section content',
            inputSchema: {
              type: 'object',
              properties: {
                section_path: { type: 'string', description: 'Path to documentation section' }
              },
              required: ['section_path']
            }
          },
          {
            name: 'list_documentation_topics',
            description: 'List available documentation topics and sections',
            inputSchema: { type: 'object', properties: {} }
          },
          {
            name: 'get_code_examples',
            description: 'Get code examples for specific use cases',
            inputSchema: {
              type: 'object',
              properties: {
                topic: { type: 'string', description: 'Topic or API to get examples for' },
                language: { type: 'string', description: 'Programming language preference' }
              },
              required: ['topic']
            }
          },

          // Schema Tools
          {
            name: 'get_schema',
            description: 'Get JSON schema for BigCommerce data models',
            inputSchema: {
              type: 'object',
              properties: {
                schema_name: { type: 'string', description: 'Name of the schema' }
              },
              required: ['schema_name']
            }
          },
          {
            name: 'search_schemas',
            description: 'Search for schemas by name or properties',
            inputSchema: {
              type: 'object',
              properties: {
                query: { type: 'string', description: 'Search query for schemas' }
              },
              required: ['query']
            }
          },

          // Health check
          {
            name: 'health_check',
            description: 'Check the health status of the MCP server',
            inputSchema: { type: 'object', properties: {} }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      if (!args) {
        throw new Error('Missing arguments in tool request');
      }

      try {
        // Initialize parsers only when needed
        await this.initializeParsers();

        if (!this.apiTools || !this.documentationTools || !this.schemaTools) {
          throw new Error('Tools not properly initialized');
        }

        let result: string;
        const startTime = Date.now();

        switch (name) {
          // API Tools
          case 'search_api_endpoints':
            result = await this.apiTools.searchEndpoints(
              args.query as string,
              args.method as string,
              args.api_category as string
            );
            break;
          case 'get_api_spec':
            result = await this.apiTools.getApiSpec(args.api_name as string);
            break;
          case 'get_endpoint_details':
            result = await this.apiTools.getEndpointDetails(
              args.api_name as string,
              args.endpoint_path as string,
              args.method as string
            );
            break;
          case 'list_api_categories':
            result = await this.apiTools.listCategories();
            break;
          case 'recommend_api_for_use_case':
            result = await this.apiTools.recommendApiForUseCase(
              args.use_case as string,
              args.operation_type as string,
              args.scale as string
            );
            break;
          case 'build_http_request':
            result = await this.apiTools.buildHttpRequest(
              args.api_name as string,
              args.endpoint_path as string,
              args.method as string,
              args.parameters as Record<string, any>,
              args.body as any,
              args.auth_type as string
            );
            break;

          // Documentation Tools
          case 'search_documentation':
            result = await this.documentationTools.searchDocumentation(
              args.query as string,
              args.section as string,
              args.limit as number
            );
            break;
          case 'get_documentation_section':
            result = await this.documentationTools.getSection(args.section_path as string);
            break;
          case 'list_documentation_topics':
            result = await this.documentationTools.listTopics();
            break;
          case 'get_code_examples':
            result = await this.documentationTools.getCodeExamples(
              args.topic as string,
              args.language as string
            );
            break;

          // Schema Tools
          case 'get_schema':
            result = await this.schemaTools.getSchema(args.schema_name as string);
            break;
          case 'search_schemas':
            result = await this.schemaTools.searchSchemas(args.query as string);
            break;

          // Health check
          case 'health_check':
            result = await this.getHealthStatus();
            break;

          default:
            throw new Error(`Unknown tool: ${name}`);
        }

        const duration = Date.now() - startTime;
        
        // Log performance for monitoring
        if (this.config.environment === 'development' || duration > 5000) {
          console.log(`Tool ${name} executed in ${duration}ms`);
        }

        return {
          content: [
            {
              type: 'text',
              text: result
            }
          ]
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error(`Error executing tool ${name}:`, error);
        
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${errorMessage}`
            }
          ],
          isError: true
        };
      }
    });
  }

  private async getHealthStatus(): Promise<string> {
    try {
      const health = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        environment: this.config.environment,
        initialized: this.initialized,
        cacheStats: this.config.getCacheStats(),
        parsers: {
          openapi: this.openApiParser ? await this.openApiParser.healthCheck() : null,
          // mdx: this.mdxParser ? await this.mdxParser.healthCheck() : null,
          // schema: this.schemaParser ? await this.schemaParser.healthCheck() : null
        }
      };

      return JSON.stringify(health, null, 2);
    } catch (error) {
      return JSON.stringify({
        status: 'unhealthy',
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString()
      }, null, 2);
    }
  }

  async initialize(): Promise<void> {
    console.log('Initializing BigCommerce MCP Server...');
    
    try {
      await this.initializeParsers();
      
      if (!this.config.lazyLoadEnabled) {
        // Load all data eagerly if lazy loading is disabled
        await Promise.all([
          this.openApiParser!.loadAllSpecs(),
          this.mdxParser!.loadAllDocs(),
          this.schemaParser!.loadAllSchemas()
        ]);
      }
      
      console.log('Server initialization complete!');
    } catch (error) {
      console.error('Error during initialization:', error);
      throw error;
    }
  }

  async run(): Promise<void> {
    await this.initialize();
    
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.log('BigCommerce MCP Server running on stdio');
  }

  // Graceful shutdown
  async shutdown(): Promise<void> {
    try {
      // Clear caches
      this.config.clearCache();
      
      // Reset initialization state
      this.initialized = false;
      
      console.log('Server shutdown complete');
    } catch (error) {
      console.error('Error during shutdown:', error);
    }
  }
}

// For Vercel deployment
export default async function handler(req: any, res: any) {
  // Set appropriate headers for serverless
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate');
  
  if (req.method === 'POST') {
    try {
      const server = new BigCommerceMCPServer();
      
      // Initialize for serverless
      await server.initialize();
      
      // Handle MCP request - simplified for HTTP deployment
      let response;
      
      // For HTTP deployment, we'll handle direct tool calls
      // rather than full MCP protocol
      response = { 
        success: true, 
        message: 'BigCommerce MCP Server is running',
        timestamp: new Date().toISOString(),
        version: server['config'].serverVersion,
        note: 'Use individual tool endpoints for direct access'
      };
      
      res.status(200).json(response);
    } catch (error) {
      console.error('Handler error:', error);
      res.status(500).json({ 
        error: error instanceof Error ? error.message : 'Internal server error',
        timestamp: new Date().toISOString()
      });
    }
  } else if (req.method === 'GET') {
    // Health check endpoint
    res.status(200).json({ 
      status: 'healthy',
      server: 'BigCommerce MCP Server',
      version: '1.0.0',
      timestamp: new Date().toISOString()
    });
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}

// For direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new BigCommerceMCPServer();
  
  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully...');
    await server.shutdown();
    process.exit(0);
  });
  
  process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    await server.shutdown();
    process.exit(0);
  });
  
  server.run().catch(console.error);
} 