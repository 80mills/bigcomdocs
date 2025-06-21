"""API tools for the BigCommerce MCP server"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class APITools:
    """Tools for working with BigCommerce API specifications"""
    
    def __init__(self, openapi_parser, search_indexer):
        self.openapi_parser = openapi_parser
        self.search_indexer = search_indexer
    
    async def search_endpoints(self, query: str, method: Optional[str] = None, api_category: Optional[str] = None) -> str:
        """Search for API endpoints across all BigCommerce APIs"""
        try:
            # Use the OpenAPI parser to search endpoints
            results = self.openapi_parser.search_endpoints(query, method, api_category)
            
            if not results:
                return f"No endpoints found matching query: '{query}'"
            
            # Format the results
            output = [f"Found {len(results)} endpoint(s) matching '{query}':\n"]
            
            for result in results[:10]:  # Limit to top 10 results
                output.append(f"## {result['api_name'].upper()} API")
                output.append(f"**{result['method']} {result['path']}**")
                
                if result.get('summary'):
                    output.append(f"Summary: {result['summary']}")
                
                if result.get('description'):
                    # Truncate long descriptions
                    desc = result['description'][:200] + "..." if len(result['description']) > 200 else result['description']
                    output.append(f"Description: {desc}")
                
                if result.get('tags'):
                    output.append(f"Tags: {', '.join(result['tags'])}")
                
                output.append("")  # Empty line for spacing
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error searching endpoints: {e}")
            return f"Error searching endpoints: {str(e)}"
    
    async def get_api_spec(self, api_name: str) -> str:
        """Get complete OpenAPI specification for a specific API"""
        try:
            spec_data = self.openapi_parser.get_spec(api_name)
            
            if not spec_data:
                available_apis = list(self.openapi_parser.specs.keys())
                return f"API '{api_name}' not found. Available APIs: {', '.join(available_apis)}"
            
            spec = spec_data['spec']
            info = spec.get('info', {})
            
            output = [f"# {info.get('title', api_name.title())} API Specification\n"]
            
            if info.get('version'):
                output.append(f"**Version:** {info['version']}")
            
            if info.get('description'):
                output.append(f"**Description:** {info['description']}")
            
            # Server information
            servers = spec.get('servers', [])
            if servers:
                output.append(f"**Base URL:** {servers[0].get('url', 'N/A')}")
            
            # Authentication
            security_schemes = spec.get('components', {}).get('securitySchemes', {})
            if security_schemes:
                output.append(f"**Authentication:** {', '.join(security_schemes.keys())}")
            
            # Endpoints summary
            endpoints = spec_data.get('endpoints', [])
            if endpoints:
                output.append(f"\n## Endpoints ({len(endpoints)} total)")
                
                # Group by tags
                endpoints_by_tag = {}
                for endpoint in endpoints:
                    tags = endpoint.get('tags', ['Untagged'])
                    for tag in tags:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        endpoints_by_tag[tag].append(endpoint)
                
                for tag, tag_endpoints in endpoints_by_tag.items():
                    output.append(f"\n### {tag}")
                    for endpoint in tag_endpoints[:5]:  # Limit per tag
                        output.append(f"- **{endpoint['method']} {endpoint['path']}** - {endpoint.get('summary', 'No summary')}")
                    
                    if len(tag_endpoints) > 5:
                        output.append(f"  ... and {len(tag_endpoints) - 5} more endpoints")
            
            # Schemas summary
            schemas = spec_data.get('schemas', {})
            if schemas:
                output.append(f"\n## Data Models ({len(schemas)} schemas)")
                for schema_name in list(schemas.keys())[:10]:  # Show first 10 schemas
                    output.append(f"- {schema_name}")
                
                if len(schemas) > 10:
                    output.append(f"  ... and {len(schemas) - 10} more schemas")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error getting API spec: {e}")
            return f"Error getting API spec: {str(e)}"
    
    async def get_endpoint_details(self, api_name: str, endpoint_path: str, method: str) -> str:
        """Get detailed information about a specific API endpoint"""
        try:
            endpoint_data = self.openapi_parser.get_endpoint_details(api_name, endpoint_path, method)
            
            if not endpoint_data:
                return f"Endpoint not found: {method} {endpoint_path} in {api_name} API"
            
            output = [f"# {method.upper()} {endpoint_path}\n"]
            output.append(f"**API:** {endpoint_data['api_name'].upper()}")
            
            if endpoint_data.get('summary'):
                output.append(f"**Summary:** {endpoint_data['summary']}")
            
            if endpoint_data.get('description'):
                output.append(f"**Description:** {endpoint_data['description']}")
            
            if endpoint_data.get('operation_id'):
                output.append(f"**Operation ID:** {endpoint_data['operation_id']}")
            
            if endpoint_data.get('tags'):
                output.append(f"**Tags:** {', '.join(endpoint_data['tags'])}")
            
            # Parameters
            parameters = endpoint_data.get('parameters', [])
            if parameters:
                output.append("\n## Parameters")
                for param in parameters:
                    param_type = param.get('in', 'unknown')
                    param_name = param.get('name', 'unnamed')
                    param_desc = param.get('description', 'No description')
                    required = " (required)" if param.get('required') else " (optional)"
                    output.append(f"- **{param_name}** ({param_type}){required}: {param_desc}")
            
            # Request Body
            request_body = endpoint_data.get('request_body')
            if request_body:
                output.append("\n## Request Body")
                if request_body.get('description'):
                    output.append(request_body['description'])
                
                content = request_body.get('content', {})
                for content_type in content.keys():
                    output.append(f"**Content-Type:** {content_type}")
                    break  # Show first content type
            
            # Responses
            responses = endpoint_data.get('responses', {})
            if responses:
                output.append("\n## Responses")
                for status_code, response in responses.items():
                    desc = response.get('description', 'No description')
                    output.append(f"- **{status_code}:** {desc}")
            
            # Security
            security = endpoint_data.get('security', [])
            if security:
                output.append("\n## Authentication")
                for sec in security:
                    for sec_name, scopes in sec.items():
                        scope_text = f" (scopes: {', '.join(scopes)})" if scopes else ""
                        output.append(f"- {sec_name}{scope_text}")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error getting endpoint details: {e}")
            return f"Error getting endpoint details: {str(e)}"
    
    async def list_categories(self) -> str:
        """List all available API categories"""
        try:
            categories = self.openapi_parser.list_api_categories()
            
            if not categories:
                return "No API categories found"
            
            output = [f"# BigCommerce API Categories ({len(categories)} total)\n"]
            
            for category in categories:
                output.append(f"## {category['title']}")
                output.append(f"**Name:** {category['name']}")
                
                if category.get('version'):
                    output.append(f"**Version:** {category['version']}")
                
                output.append(f"**Endpoints:** {category['endpoint_count']}")
                
                if category.get('description'):
                    # Truncate long descriptions
                    desc = category['description'][:150] + "..." if len(category['description']) > 150 else category['description']
                    output.append(f"**Description:** {desc}")
                
                if category.get('tags'):
                    output.append(f"**Tags:** {', '.join(category['tags'][:5])}")  # Show first 5 tags
                
                output.append("")  # Empty line for spacing
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error listing categories: {e}")
            return f"Error listing categories: {str(e)}" 