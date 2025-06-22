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
        # Agentic use case patterns
        self.use_case_patterns = {
            'product_queries': {
                'keywords': ['products', 'catalog', 'items', 'goods', 'merchandise'],
                'apis': ['catalog', 'products_catalog'],
                'endpoints': ['/catalog/products', '/catalog/products/{product_id}'],
                'methods': ['GET'],
                'description': 'Query and retrieve product information'
            },
            'product_updates': {
                'keywords': ['update products', 'modify products', 'edit products', 'change products'],
                'apis': ['catalog', 'products_catalog'],
                'endpoints': ['/catalog/products/{product_id}'],
                'methods': ['PUT', 'PATCH'],
                'description': 'Update existing product information'
            },
            'product_creation': {
                'keywords': ['create products', 'add products', 'new products', 'insert products'],
                'apis': ['catalog', 'products_catalog'],
                'endpoints': ['/catalog/products'],
                'methods': ['POST'],
                'description': 'Create new products in catalog'
            },
            'bulk_product_operations': {
                'keywords': ['bulk', 'batch', 'mass', 'hundreds', 'thousands', 'multiple products'],
                'apis': ['catalog', 'products_catalog'],
                'endpoints': ['/catalog/products/batch'],
                'methods': ['POST', 'PUT'],
                'description': 'Perform operations on multiple products at once'
            },
            'inventory_queries': {
                'keywords': ['inventory', 'stock', 'quantity', 'availability'],
                'apis': ['inventory', 'catalog'],
                'endpoints': ['/catalog/products/{product_id}/inventory', '/inventory'],
                'methods': ['GET'],
                'description': 'Check product inventory levels'
            },
            'inventory_updates': {
                'keywords': ['update inventory', 'adjust stock', 'change quantity', 'modify inventory'],
                'apis': ['inventory', 'catalog'],
                'endpoints': ['/catalog/products/{product_id}/inventory'],
                'methods': ['PUT', 'PATCH'],
                'description': 'Update product inventory levels'
            },
            'bulk_inventory_operations': {
                'keywords': ['bulk inventory', 'batch inventory', 'mass inventory', 'hundreds inventory'],
                'apis': ['inventory'],
                'endpoints': ['/inventory/batch'],
                'methods': ['POST', 'PUT'],
                'description': 'Update inventory for multiple products'
            },
            'order_queries': {
                'keywords': ['orders', 'purchases', 'transactions'],
                'apis': ['orders'],
                'endpoints': ['/orders', '/orders/{order_id}'],
                'methods': ['GET'],
                'description': 'Query order information'
            },
            'order_updates': {
                'keywords': ['update orders', 'modify orders', 'change orders'],
                'apis': ['orders'],
                'endpoints': ['/orders/{order_id}'],
                'methods': ['PUT', 'PATCH'],
                'description': 'Update order status and information'
            },
            'customer_queries': {
                'keywords': ['customers', 'users', 'buyers', 'shoppers'],
                'apis': ['customers'],
                'endpoints': ['/customers', '/customers/{customer_id}'],
                'methods': ['GET'],
                'description': 'Query customer information'
            },
            'customer_updates': {
                'keywords': ['update customers', 'modify customers', 'edit customers'],
                'apis': ['customers'],
                'endpoints': ['/customers/{customer_id}'],
                'methods': ['PUT', 'PATCH'],
                'description': 'Update customer information'
            },
            'category_queries': {
                'keywords': ['categories', 'departments', 'sections'],
                'apis': ['catalog', 'categories_catalog'],
                'endpoints': ['/catalog/categories', '/catalog/categories/{category_id}'],
                'methods': ['GET'],
                'description': 'Query category information'
            },
            'pricing_queries': {
                'keywords': ['pricing', 'prices', 'cost', 'price lists'],
                'apis': ['price_lists', 'catalog'],
                'endpoints': ['/pricelists', '/catalog/products/{product_id}/prices'],
                'methods': ['GET'],
                'description': 'Query pricing information'
            },
            'pricing_updates': {
                'keywords': ['update prices', 'modify prices', 'change prices'],
                'apis': ['price_lists', 'catalog'],
                'endpoints': ['/pricelists/{price_list_id}/records'],
                'methods': ['POST', 'PUT'],
                'description': 'Update product pricing'
            },
            'webhook_setup': {
                'keywords': ['webhooks', 'notifications', 'events', 'callbacks'],
                'apis': ['webhooks'],
                'endpoints': ['/hooks'],
                'methods': ['POST', 'GET'],
                'description': 'Set up webhook notifications'
            },
            'widget_management': {
                'keywords': ['widgets', 'content', 'display', 'frontend'],
                'apis': ['widgets', 'page_widgets'],
                'endpoints': ['/content/widgets', '/content/widget-templates'],
                'methods': ['GET', 'POST', 'PUT', 'DELETE'],
                'description': 'Manage storefront widgets and content'
            }
        }
    
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
    
    async def recommend_api_for_use_case(self, use_case: str, operation_type: Optional[str] = None, scale: Optional[str] = None) -> str:
        """Intelligently recommend the best API for a specific use case"""
        try:
            use_case_lower = use_case.lower()
            matches = []
            for pattern_name, pattern in self.use_case_patterns.items():
                score = 0
                for keyword in pattern['keywords']:
                    if keyword in use_case_lower:
                        score += 1
                if score > 0:
                    matches.append({'pattern': pattern_name, 'pattern_data': pattern, 'score': score})
            matches.sort(key=lambda x: x['score'], reverse=True)
            if not matches:
                return f"No specific API recommendation found for: '{use_case}'. Try searching for specific endpoints or APIs."
            best_match = matches[0]
            pattern = best_match['pattern_data']
            output = [f"# API Recommendation for: {use_case}\n"]
            output.append(f"**Recommended Pattern:** {best_match['pattern']}")
            output.append(f"**Description:** {pattern['description']}")
            is_bulk = any(word in use_case_lower for word in ['bulk', 'batch', 'mass', 'hundreds', 'thousands', 'multiple'])
            if is_bulk:
                output.append("\n## ⚠️ Bulk Operation Detected")
                output.append("For operations on hundreds or thousands of items, consider:")
                output.append("- Using batch endpoints when available")
                output.append("- Implementing rate limiting")
                output.append("- Using webhooks for status updates")
            output.append(f"\n## Recommended APIs")
            for api_name in pattern['apis']:
                api_data = self.openapi_parser.get_spec(api_name)
                if api_data:
                    spec = api_data['spec']
                    info = spec.get('info', {})
                    output.append(f"### {info.get('title', api_name.title())}")
                    output.append(f"**API Name:** {api_name}")
                    if info.get('description'):
                        desc = info['description'][:200] + "..." if len(info['description']) > 200 else info['description']
                        output.append(f"**Description:** {desc}")
                    relevant_endpoints = []
                    for endpoint in api_data.get('endpoints', []):
                        if endpoint['method'] in pattern['methods']:
                            for pattern_endpoint in pattern['endpoints']:
                                if pattern_endpoint in endpoint['path']:
                                    relevant_endpoints.append(endpoint)
                    if relevant_endpoints:
                        output.append(f"**Relevant Endpoints:**")
                        for endpoint in relevant_endpoints[:3]:
                            output.append(f"- **{endpoint['method']} {endpoint['path']}**")
                            if endpoint.get('summary'):
                                output.append(f"  {endpoint['summary']}")
            output.append(f"\n## Performance Considerations")
            if is_bulk:
                output.append("- Use batch endpoints for bulk operations")
                output.append("- Implement pagination for large result sets")
                output.append("- Consider webhooks for real-time updates")
                output.append("- Monitor rate limits (typically 1000 requests/minute)")
            else:
                output.append("- Single item operations are generally fast")
                output.append("- Use appropriate HTTP methods (GET for queries, PUT/PATCH for updates)")
            output.append(f"\n## Authentication")
            output.append("All BigCommerce APIs require authentication:")
            output.append("- **X-Auth-Token** header for REST APIs")
            output.append("- **Store Hash** in URL path")
            output.append("- **Access Token** for OAuth flows")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Error recommending API: {e}")
            return f"Error recommending API: {str(e)}"
    
    async def get_bulk_operation_guide(self, operation_type: str, item_count: Optional[int] = None) -> str:
        """Get specific guidance for bulk operations"""
        try:
            operation_lower = operation_type.lower()
            output = [f"# Bulk Operation Guide: {operation_type}\n"]
            if item_count:
                output.append(f"**Estimated Item Count:** {item_count}")
            if any(word in operation_lower for word in ['product', 'catalog']):
                category = 'products'
                api_name = 'catalog'
                batch_endpoint = '/catalog/products/batch'
            elif any(word in operation_lower for word in ['inventory', 'stock']):
                category = 'inventory'
                api_name = 'inventory'
                batch_endpoint = '/inventory/batch'
            elif any(word in operation_lower for word in ['order']):
                category = 'orders'
                api_name = 'orders'
                batch_endpoint = '/orders/batch'
            elif any(word in operation_lower for word in ['customer']):
                category = 'customers'
                api_name = 'customers'
                batch_endpoint = '/customers/batch'
            else:
                category = 'general'
                api_name = 'general'
                batch_endpoint = None
            output.append(f"**Operation Category:** {category}")
            api_data = self.openapi_parser.get_spec(api_name)
            if api_data:
                output.append(f"\n## Recommended API")
                spec = api_data['spec']
                info = spec.get('info', {})
                output.append(f"**API:** {info.get('title', api_name.title())}")
                if batch_endpoint:
                    output.append(f"**Batch Endpoint:** {batch_endpoint}")
                batch_endpoints = []
                for endpoint in api_data.get('endpoints', []):
                    if 'batch' in endpoint['path'].lower():
                        batch_endpoints.append(endpoint)
                if batch_endpoints:
                    output.append(f"\n## Available Batch Endpoints")
                    for endpoint in batch_endpoints:
                        output.append(f"- **{endpoint['method']} {endpoint['path']}**")
                        if endpoint.get('summary'):
                            output.append(f"  {endpoint['summary']}")
            output.append(f"\n## Performance Recommendations")
            if item_count:
                if item_count > 1000:
                    output.append("⚠️ **Large Operation Detected**")
                    output.append("- Consider breaking into smaller batches (100-500 items)")
                    output.append("- Implement exponential backoff for retries")
                    output.append("- Use webhooks to monitor progress")
                elif item_count > 100:
                    output.append("⚠️ **Medium Operation Detected**")
                    output.append("- Use batch endpoints when available")
                    output.append("- Monitor rate limits")
                else:
                    output.append("✅ **Small Operation**")
                    output.append("- Standard endpoints should work fine")
            output.append(f"\n## Rate Limiting")
            output.append("- **Default Limit:** 1000 requests per minute")
            output.append("- **Burst Limit:** 100 requests per 10 seconds")
            output.append("- **Response Headers:** Check `X-Rate-Limit-*` headers")
            output.append(f"\n## Best Practices")
            output.append("1. **Use Batch Endpoints:** When available, use batch operations")
            output.append("2. **Implement Pagination:** For large result sets")
            output.append("3. **Handle Errors:** Implement proper error handling and retries")
            output.append("4. **Monitor Progress:** Use webhooks or status endpoints")
            output.append("5. **Test First:** Test with small batches before large operations")
            output.append(f"\n## Example Implementation Structure")
            output.append("```python")
            output.append("# Example bulk operation structure")
            output.append("def bulk_operation(items, batch_size=100):")
            output.append("    for i in range(0, len(items), batch_size):")
            output.append("        batch = items[i:i + batch_size]")
            output.append("        response = api_client.batch_operation(batch)")
            output.append("        # Handle response and errors")
            output.append("        time.sleep(0.1)  # Rate limiting")
            output.append("```")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Error getting bulk operation guide: {e}")
            return f"Error getting bulk operation guide: {str(e)}" 