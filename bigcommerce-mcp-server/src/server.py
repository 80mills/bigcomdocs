"""Main BigCommerce MCP Server implementation"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .config import Config
from .parsers.openapi_parser import OpenAPIParser
from .parsers.mdx_parser import MDXParser
from .parsers.schema_parser import SchemaParser
from .indexers.search_indexer import SearchIndexer
from .indexers.content_indexer import ContentIndexer
from .tools.api_tools import APITools
from .tools.documentation_tools import DocumentationTools
from .tools.schema_tools import SchemaTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BigCommerceMCPServer:
    """BigCommerce Model Context Protocol Server"""
    
    def __init__(self, docs_path: Path):
        self.docs_path = docs_path
        self.config = Config()
        self.server = Server("bigcommerce-docs")
        
        # Initialize parsers
        self.openapi_parser = OpenAPIParser(docs_path / "reference")
        self.mdx_parser = MDXParser(docs_path / "docs")
        self.schema_parser = SchemaParser(docs_path / "models")
        
        # Initialize indexers
        self.search_indexer = SearchIndexer()
        self.content_indexer = ContentIndexer()
        
        # Initialize tools
        self.api_tools = APITools(self.openapi_parser, self.search_indexer)
        self.documentation_tools = DocumentationTools(self.mdx_parser, self.search_indexer)
        self.schema_tools = SchemaTools(self.schema_parser, self.search_indexer)
        
        # Store parsed data
        self.api_specs = {}
        self.documentation = {}
        self.schemas = {}
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools"""
            tools = []
            
            # API Tools
            tools.extend([
                Tool(
                    name="search_api_endpoints",
                    description="Search for API endpoints across all BigCommerce APIs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query for endpoints"},
                            "method": {"type": "string", "description": "HTTP method (GET, POST, etc.)", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                            "api_category": {"type": "string", "description": "API category to search within"}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_api_spec",
                    description="Get complete OpenAPI specification for a specific API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_name": {"type": "string", "description": "Name of the API (e.g., 'widgets', 'catalog', 'orders')"}
                        },
                        "required": ["api_name"]
                    }
                ),
                Tool(
                    name="get_endpoint_details",
                    description="Get detailed information about a specific API endpoint",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_name": {"type": "string", "description": "API name"},
                            "endpoint_path": {"type": "string", "description": "Endpoint path"},
                            "method": {"type": "string", "description": "HTTP method"}
                        },
                        "required": ["api_name", "endpoint_path", "method"]
                    }
                ),
                Tool(
                    name="list_api_categories",
                    description="List all available API categories",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="recommend_api_for_use_case",
                    description="Intelligently recommend the best API for a specific use case (e.g., 'querying products', 'updating inventory for hundreds of items')",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "use_case": {"type": "string", "description": "Description of what you want to accomplish"},
                            "operation_type": {"type": "string", "description": "Type of operation (query, update, create, delete)", "enum": ["query", "update", "create", "delete"]},
                            "scale": {"type": "string", "description": "Scale of operation (single, bulk, batch)", "enum": ["single", "bulk", "batch"]}
                        },
                        "required": ["use_case"]
                    }
                ),
                Tool(
                    name="get_bulk_operation_guide",
                    description="Get specific guidance for bulk operations (e.g., updating hundreds of products, managing inventory at scale)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation_type": {"type": "string", "description": "Type of bulk operation (e.g., 'product updates', 'inventory management')"},
                            "item_count": {"type": "integer", "description": "Estimated number of items to process"}
                        },
                        "required": ["operation_type"]
                    }
                )
            ])
            
            # Documentation Tools
            tools.extend([
                Tool(
                    name="search_documentation",
                    description="Search across all BigCommerce documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "section": {"type": "string", "description": "Documentation section to search within"},
                            "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_documentation_section",
                    description="Get specific documentation section content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "section_path": {"type": "string", "description": "Path to documentation section"}
                        },
                        "required": ["section_path"]
                    }
                ),
                Tool(
                    name="list_documentation_topics",
                    description="List available documentation topics and sections",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_code_examples",
                    description="Get code examples for specific use cases",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Topic or API to get examples for"},
                            "language": {"type": "string", "description": "Programming language preference"}
                        },
                        "required": ["topic"]
                    }
                )
            ])
            
            # Schema Tools
            tools.extend([
                Tool(
                    name="get_schema",
                    description="Get JSON schema for BigCommerce data models",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "schema_name": {"type": "string", "description": "Name of the schema"}
                        },
                        "required": ["schema_name"]
                    }
                ),
                Tool(
                    name="search_schemas",
                    description="Search for schemas by name or properties",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query for schemas"}
                        },
                        "required": ["query"]
                    }
                )
            ])
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "search_api_endpoints":
                    result = await self.api_tools.search_endpoints(**arguments)
                elif name == "get_api_spec":
                    result = await self.api_tools.get_api_spec(**arguments)
                elif name == "get_endpoint_details":
                    result = await self.api_tools.get_endpoint_details(**arguments)
                elif name == "list_api_categories":
                    result = await self.api_tools.list_categories()
                elif name == "recommend_api_for_use_case":
                    result = await self.api_tools.recommend_api_for_use_case(**arguments)
                elif name == "get_bulk_operation_guide":
                    result = await self.api_tools.get_bulk_operation_guide(**arguments)
                elif name == "search_documentation":
                    result = await self.documentation_tools.search_documentation(**arguments)
                elif name == "get_documentation_section":
                    result = await self.documentation_tools.get_section(**arguments)
                elif name == "list_documentation_topics":
                    result = await self.documentation_tools.list_topics()
                elif name == "get_code_examples":
                    result = await self.documentation_tools.get_code_examples(**arguments)
                elif name == "get_schema":
                    result = await self.schema_tools.get_schema(**arguments)
                elif name == "search_schemas":
                    result = await self.schema_tools.search_schemas(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                logger.error(f"Error handling tool call {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def initialize(self):
        """Initialize the server by loading and parsing all documentation"""
        logger.info("Initializing BigCommerce MCP Server...")
        
        # Load API specifications
        logger.info("Loading API specifications...")
        self.api_specs = await self.openapi_parser.load_all_specs()
        logger.info(f"Loaded {len(self.api_specs)} API specifications")
        
        # Load documentation
        logger.info("Loading documentation...")
        self.documentation = await self.mdx_parser.load_all_docs()
        logger.info(f"Loaded {len(self.documentation)} documentation files")
        
        # Load schemas
        logger.info("Loading schemas...")
        self.schemas = await self.schema_parser.load_all_schemas()
        logger.info(f"Loaded {len(self.schemas)} schema files")
        
        # Build search indexes
        logger.info("Building search indexes...")
        await self.search_indexer.build_indexes(
            self.api_specs, 
            self.documentation, 
            self.schemas
        )
        
        await self.content_indexer.build_content_index(
            self.api_specs,
            self.documentation,
            self.schemas
        )
        
        logger.info("Server initialization complete!")
    
    async def run(self):
        """Run the MCP server"""
        await self.initialize()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="bigcommerce-docs",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


async def main():
    """Main entry point"""
    import sys
    from pathlib import Path
    
    # Get the docs path (current directory by default)
    docs_path = Path.cwd()
    if len(sys.argv) > 1:
        docs_path = Path(sys.argv[1])
    
    logger.info(f"Starting BigCommerce MCP Server with docs path: {docs_path}")
    
    server = BigCommerceMCPServer(docs_path)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 