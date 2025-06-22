"""Main BigCommerce MCP Server implementation - Optimized Version"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from functools import lru_cache
import time

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server import NotificationOptions
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
from .tools.quick_lookup import QuickLookupTools
from .utils.cache_manager import CacheManager
from .utils.pattern_matcher import PatternMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BigCommerceMCPServer:
    """BigCommerce Model Context Protocol Server - Performance Optimized"""
    
    def __init__(self, docs_path: Path):
        self.docs_path = docs_path
        self.config = Config(docs_path=docs_path)
        self.server = Server("bigcommerce-docs")
        
        # Initialize cache manager
        self.cache_manager = CacheManager()
        
        # Initialize pattern matcher for quick query routing
        self.pattern_matcher = PatternMatcher()
        
        # Initialize parsers with lazy loading
        self.openapi_parser = OpenAPIParser(docs_path / "reference", lazy_load=True)
        self.mdx_parser = MDXParser(docs_path / "docs", lazy_load=True)
        self.schema_parser = SchemaParser(docs_path / "models", lazy_load=True)
        
        # Initialize indexers (will be populated on demand)
        self.search_indexer = SearchIndexer(use_inverted_index=True)
        self.content_indexer = ContentIndexer()
        
        # Initialize tools
        self.quick_lookup = QuickLookupTools(self.cache_manager, self.pattern_matcher)
        self.api_tools = APITools(self.openapi_parser, self.search_indexer, self.cache_manager)
        self.documentation_tools = DocumentationTools(self.mdx_parser, self.search_indexer, self.cache_manager)
        self.schema_tools = SchemaTools(self.schema_parser, self.search_indexer, self.cache_manager)
        
        # Lazy-loaded data stores
        self._api_specs_loaded = False
        self._docs_loaded = False
        self._schemas_loaded = False
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools"""
            tools = []
            
            # Quick Lookup Tools (Priority for common queries)
            tools.extend([
                Tool(
                    name="quick_api_lookup",
                    description="Fast lookup for common API queries (inventory, products, orders)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Natural language query about BigCommerce APIs"}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="call_api",
                    description="Execute a BigCommerce API call with authentication",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "store_hash": {"type": "string", "description": "BigCommerce store hash"},
                            "access_token": {"type": "string", "description": "API access token"},
                            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                            "endpoint": {"type": "string", "description": "API endpoint path"},
                            "params": {"type": "object", "description": "Query parameters"},
                            "body": {"type": "object", "description": "Request body for POST/PUT/PATCH"},
                            "api_version": {"type": "string", "description": "API version (v2 or v3)", "default": "v3"}
                        },
                        "required": ["store_hash", "access_token", "method", "endpoint"]
                    }
                )
            ])
            
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
                    name="build_http_request",
                    description="Build a complete HTTP request for BigCommerce API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_name": {"type": "string", "description": "Name of the API"},
                            "endpoint_path": {"type": "string", "description": "API endpoint path"},
                            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                            "parameters": {"type": "object", "description": "Query and path parameters"},
                            "body": {"type": "object", "description": "Request body"},
                            "store_hash": {"type": "string", "description": "Store hash for the request"}
                        },
                        "required": ["api_name", "endpoint_path", "method"]
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
                            "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
                        },
                        "required": ["query"]
                    }
                )
            ])
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls with performance optimization"""
            start_time = time.time()
            
            try:
                # Quick lookup for common queries (bypasses heavy search)
                if name == "quick_api_lookup":
                    result = await self.quick_lookup.handle_query(**arguments)
                
                # API execution
                elif name == "call_api":
                    result = await self.api_tools.execute_api_call(**arguments)
                
                # Standard API tools
                elif name == "search_api_endpoints":
                    # Only load API specs if needed
                    await self._ensure_api_specs_loaded()
                    result = await self.api_tools.search_endpoints(**arguments)
                
                elif name == "get_api_spec":
                    # Load only the requested API spec
                    result = await self.api_tools.get_api_spec(**arguments)
                
                elif name == "get_endpoint_details":
                    result = await self.api_tools.get_endpoint_details(**arguments)
                
                elif name == "build_http_request":
                    result = await self.api_tools.build_http_request(**arguments)
                
                # Documentation tools
                elif name == "search_documentation":
                    await self._ensure_docs_loaded()
                    result = await self.documentation_tools.search_documentation(**arguments)
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                elapsed = time.time() - start_time
                logger.info(f"Tool {name} completed in {elapsed:.2f}s")
                
                return [TextContent(type="text", text=result)]
                
            except Exception as e:
                logger.error(f"Error handling tool call {name}: {e}")
                elapsed = time.time() - start_time
                return [TextContent(type="text", text=f"Error: {str(e)} (took {elapsed:.2f}s)")]
    
    async def _ensure_api_specs_loaded(self):
        """Lazy load API specifications only when needed"""
        if not self._api_specs_loaded:
            logger.info("Loading API specifications on demand...")
            
            # Load only essential API specs first
            essential_apis = ['inventory', 'catalog', 'orders', 'customers']
            for api in essential_apis:
                await self.openapi_parser.load_spec(api)
            
            # Build initial index
            await self.search_indexer.build_api_index(self.openapi_parser.specs)
            self._api_specs_loaded = True
    
    async def _ensure_docs_loaded(self):
        """Lazy load documentation only when needed"""
        if not self._docs_loaded:
            logger.info("Loading documentation on demand...")
            # Load docs progressively
            await self.mdx_parser.load_essential_docs()
            self._docs_loaded = True
    
    async def initialize(self):
        """Minimal initialization - load only what's immediately needed"""
        logger.info("Initializing BigCommerce MCP Server (Optimized)...")
        
        # Load quick lookup patterns
        await self.quick_lookup.initialize()
        
        # Pre-cache common queries
        await self._precache_common_queries()
        
        logger.info("Server initialization complete! (Minimal startup)")
    
    async def _precache_common_queries(self):
        """Pre-cache responses for the most common queries"""
        common_queries = [
            "inventory single product",
            "get product by id",
            "update inventory",
            "create order",
            "list products",
            "customer information"
        ]
        
        for query in common_queries:
            await self.quick_lookup.handle_query(query)
    
    async def run(self):
        """Run the MCP server"""
        await self.initialize()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="bigcommerce-docs",
                    server_version="2.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
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
    
    logger.info(f"Starting BigCommerce MCP Server (Optimized) with docs path: {docs_path}")
    
    server = BigCommerceMCPServer(docs_path)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 