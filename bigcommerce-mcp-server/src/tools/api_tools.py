"""API tools for the BigCommerce MCP server - Optimized with caching and API execution"""

import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class APITools:
    """Tools for working with BigCommerce API specifications - Optimized"""
    
    def __init__(self, openapi_parser, search_indexer, cache_manager):
        self.openapi_parser = openapi_parser
        self.search_indexer = search_indexer
        self.cache_manager = cache_manager
        
        # HTTP session for API calls
        self._session = None
        
        # Define common use case patterns for agentic API selection
        self.use_case_patterns = {
            # Product management
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
            
            # Inventory management
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
            
            # Order management
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
            
            # Customer management
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
            
            # Category management
            'category_queries': {
                'keywords': ['categories', 'departments', 'sections'],
                'apis': ['catalog', 'categories_catalog'],
                'endpoints': ['/catalog/categories', '/catalog/categories/{category_id}'],
                'methods': ['GET'],
                'description': 'Query category information'
            },
            
            # Pricing
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
            
            # Webhooks
            'webhook_setup': {
                'keywords': ['webhooks', 'notifications', 'events', 'callbacks'],
                'apis': ['webhooks'],
                'endpoints': ['/hooks'],
                'methods': ['POST', 'GET'],
                'description': 'Set up webhook notifications'
            },
            
            # Widgets and content
            'widget_management': {
                'keywords': ['widgets', 'content', 'display', 'frontend'],
                'apis': ['widgets', 'page_widgets'],
                'endpoints': ['/content/widgets', '/content/widget-templates'],
                'methods': ['GET', 'POST', 'PUT', 'DELETE'],
                'description': 'Manage storefront widgets and content'
            }
        }
        
        # Dropshipping-specific business logic patterns
        self.dropshipping_patterns = {
            'pricing_strategy': {
                'primary': 'MAP',
                'fallback': 'MSRP',
                'cost_plus_minimum': 0.15,
                'map_compliance': True,
                'competitive_factor': 0.95,
                'margin_requirements': {
                    'minimum': 0.10,
                    'target': 0.25,
                    'maximum_discount': 0.30
                }
            },
            'inventory_sync': {
                'update_frequency': 300,  # 5 minutes in seconds
                'buffer_stock': 2,
                'max_quantity_display': 10,
                'stockout_threshold': 1,
                'sync_tolerance': 0.1  # 10% variance tolerance
            },
            'product_management': {
                'auto_enable_disable': True,
                'visibility_rules': {
                    'min_stock': 1,
                    'valid_pricing': True,
                    'supplier_active': True
                },
                'bulk_operation_size': 100,
                'rate_limit_buffer': 0.8  # Use 80% of rate limit
            },
            'order_processing': {
                'auto_status_updates': True,
                'tracking_sync': True,
                'inventory_adjustment': True,
                'notification_triggers': ['order_created', 'payment_received', 'shipped']
            }
        }
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._session:
            await self._session.close()
    
    @property
    def cache_decorator(self):
        """Get cache decorator for methods"""
        return self.cache_manager.cache_key
    
    async def search_endpoints(self, query: str, method: Optional[str] = None, api_category: Optional[str] = None) -> str:
        """Search for API endpoints across all BigCommerce APIs"""
        # Check cache first
        cache_key = f"search_endpoints:{query}:{method}:{api_category}"
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Use the search indexer for fast results
            results = await self.openapi_parser.search_endpoints(query, method, api_category)
            
            if not results:
                response = f"No endpoints found matching query: '{query}'"
            else:
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
                
                response = "\n".join(output)
            
            # Cache the result
            await self.cache_manager.set(cache_key, response, ttl=3600)
            return response
            
        except Exception as e:
            logger.error(f"Error searching endpoints: {e}")
            return f"Error searching endpoints: {str(e)}"
    
    async def get_api_spec(self, api_name: str) -> str:
        """Get complete OpenAPI specification for a specific API"""
        # Check cache first
        cache_key = f"api_spec:{api_name}"
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            spec_data = await self.openapi_parser.get_spec(api_name)
            
            if not spec_data:
                # List available APIs from file map if using lazy loading
                if hasattr(self.openapi_parser, '_file_map'):
                    available_apis = list(self.openapi_parser._file_map.keys())[:10]
                else:
                    available_apis = list(self.openapi_parser.specs.keys())[:10]
                response = f"API '{api_name}' not found. Available APIs: {', '.join(available_apis)}..."
            else:
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
                
                response = "\n".join(output)
            
            # Cache the result
            await self.cache_manager.set(cache_key, response, ttl=7200)
            return response
            
        except Exception as e:
            logger.error(f"Error getting API spec: {e}")
            return f"Error getting API spec: {str(e)}"
    
    async def get_endpoint_details(self, api_name: str, endpoint_path: str, method: str) -> str:
        """Get detailed information about a specific API endpoint"""
        # Check cache
        cache_key = f"endpoint_details:{api_name}:{method}:{endpoint_path}"
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            endpoint_data = await self.openapi_parser.get_endpoint_details(api_name, endpoint_path, method)
            
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
            
            response = "\n".join(output)
            
            # Cache the result
            await self.cache_manager.set(cache_key, response, ttl=7200)
            return response
            
        except Exception as e:
            logger.error(f"Error getting endpoint details: {e}")
            return f"Error getting endpoint details: {str(e)}"
    
    async def execute_api_call(self, store_hash: str, access_token: str, method: str, endpoint: str, 
                              params: Optional[Dict] = None, body: Optional[Dict] = None, 
                              api_version: str = "v3") -> str:
        """Execute a BigCommerce API call"""
        try:
            # Build the URL
            base_url = f"https://api.bigcommerce.com/stores/{store_hash}/{api_version}"
            url = urljoin(base_url, endpoint.lstrip('/'))
            
            # Prepare headers
            headers = {
                'X-Auth-Token': access_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Get session
            session = await self._get_session()
            
            # Make the request
            async with session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=body if body and method.upper() in ['POST', 'PUT', 'PATCH'] else None
            ) as response:
                response_data = await response.text()
                
                # Try to parse as JSON
                try:
                    response_json = json.loads(response_data)
                    response_formatted = json.dumps(response_json, indent=2)
                except:
                    response_formatted = response_data
                
                output = [f"# API Call Result\n"]
                output.append(f"**Method:** {method.upper()}")
                output.append(f"**URL:** {url}")
                output.append(f"**Status:** {response.status} {response.reason}")
                
                output.append("\n## Response Headers")
                for key, value in response.headers.items():
                    if key.lower() in ['x-rate-limit-requests-left', 'x-rate-limit-time-reset-ms', 'content-type']:
                        output.append(f"- **{key}:** {value}")
                
                output.append("\n## Response Body")
                output.append("```json")
                output.append(response_formatted[:2000])  # Limit response size
                if len(response_formatted) > 2000:
                    output.append("... (truncated)")
                output.append("```")
                
                if response.status >= 400:
                    output.append("\n## Error Details")
                    output.append(f"The request failed with status code {response.status}.")
                    if response_json and isinstance(response_json, dict):
                        if 'title' in response_json:
                            output.append(f"**Error:** {response_json['title']}")
                        if 'errors' in response_json:
                            output.append(f"**Details:** {json.dumps(response_json['errors'], indent=2)}")
                
                return "\n".join(output)
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error executing API call: {e}")
            return f"HTTP Error executing API call: {str(e)}"
        except Exception as e:
            logger.error(f"Error executing API call: {e}")
            return f"Error executing API call: {str(e)}"
    
    async def build_http_request(self, api_name: str, endpoint_path: str, method: str, 
                                parameters: Optional[Dict] = None, body: Optional[Dict] = None,
                                store_hash: Optional[str] = None) -> str:
        """Build a complete HTTP request for BigCommerce API"""
        try:
            # Get API spec to understand the endpoint
            api_data = await self.openapi_parser.get_spec(api_name)
            api_version = "v3"  # Default to v3
            
            if api_data:
                # Try to determine API version from spec
                servers = api_data['spec'].get('servers', [])
                if servers and 'v2' in servers[0].get('url', ''):
                    api_version = "v2"
            
            # Build base URL
            store_hash_placeholder = store_hash or "{store_hash}"
            base_url = f"https://api.bigcommerce.com/stores/{store_hash_placeholder}/{api_version}"
            
            # Process path parameters
            processed_path = endpoint_path
            if parameters:
                for param_name, param_value in parameters.items():
                    placeholder = f"{{{param_name}}}"
                    if placeholder in endpoint_path:
                        processed_path = processed_path.replace(placeholder, str(param_value))
            
            full_url = urljoin(base_url, processed_path.lstrip('/'))
            
            output = [f"# HTTP Request Builder\n"]
            output.append(f"## {method.upper()} {processed_path}")
            output.append(f"**API:** {api_name}")
            output.append(f"**Version:** {api_version}")
            
            output.append("\n## cURL Example")
            output.append("```bash")
            curl_cmd = [f"curl -X {method.upper()} \\"]
            curl_cmd.append(f'  "{full_url}" \\')
            curl_cmd.append('  -H "X-Auth-Token: {access_token}" \\')
            curl_cmd.append('  -H "Accept: application/json" \\')
            
            if method.upper() in ['POST', 'PUT', 'PATCH'] and body:
                curl_cmd.append('  -H "Content-Type: application/json" \\')
                curl_cmd.append(f"  -d '{json.dumps(body, separators=(',', ':'))}'")
            else:
                curl_cmd[-1] = curl_cmd[-1].rstrip(' \\')  # Remove trailing backslash
            
            output.extend(curl_cmd)
            output.append("```")
            
            output.append("\n## Python Example")
            output.append("```python")
            output.append("import requests")
            output.append("")
            output.append(f'url = "{full_url}"')
            output.append("headers = {")
            output.append('    "X-Auth-Token": "{access_token}",')
            output.append('    "Accept": "application/json",')
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                output.append('    "Content-Type": "application/json"')
            output.append("}")
            
            if body:
                output.append("")
                output.append("data = " + json.dumps(body, indent=4))
                output.append("")
                output.append(f'response = requests.{method.lower()}(url, headers=headers, json=data)')
            else:
                output.append("")
                output.append(f'response = requests.{method.lower()}(url, headers=headers)')
            
            output.append("print(response.json())")
            output.append("```")
            
            output.append("\n## JavaScript Example")
            output.append("```javascript")
            output.append("const options = {")
            output.append(f'  method: "{method.upper()}",')
            output.append("  headers: {")
            output.append('    "X-Auth-Token": "{access_token}",')
            output.append('    "Accept": "application/json",')
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                output.append('    "Content-Type": "application/json"')
            output.append("  }")
            
            if body:
                output.append(f",  body: JSON.stringify({json.dumps(body, indent=2)})")
            
            output.append("};")
            output.append("")
            output.append(f'fetch("{full_url}", options)')
            output.append("  .then(response => response.json())")
            output.append("  .then(data => console.log(data))")
            output.append("  .catch(error => console.error('Error:', error));")
            output.append("```")
            
            output.append("\n## Required Parameters")
            output.append("- **store_hash**: Your BigCommerce store hash")
            output.append("- **access_token**: Your API access token")
            
            if parameters:
                output.append("\n## Path Parameters")
                for param_name, param_value in parameters.items():
                    output.append(f"- **{param_name}**: {param_value}")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error building HTTP request: {e}")
            return f"Error building HTTP request: {str(e)}"
    
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
    
    async def optimize_pricing_across_channels(self, product_data: dict, map_pricing: dict = None, cost_data: dict = None) -> str:
        """Optimize BigCommerce pricing based on MAP, cost, and dropshipping requirements"""
        try:
            output = [f"# BigCommerce Pricing Optimization\n"]
            
            # Extract product information
            product_id = product_data.get('id', 'unknown')
            current_price = product_data.get('price', 0)
            product_name = product_data.get('name', 'Unknown Product')
            
            output.append(f"**Product:** {product_name} (ID: {product_id})")
            output.append(f"**Current Price:** ${current_price}")
            
            # Analyze pricing strategy
            pricing_strategy = self.dropshipping_patterns['pricing_strategy']
            
            # Determine optimal pricing
            recommended_price = None
            pricing_rationale = []
            
            if map_pricing:
                map_price = map_pricing.get('price', 0)
                if map_price > 0:
                    recommended_price = map_price
                    pricing_rationale.append(f"MAP pricing enforced: ${map_price}")
                    output.append(f"**MAP Price:** ${map_price}")
            
            if cost_data and not recommended_price:
                cost = cost_data.get('cost', 0)
                if cost > 0:
                    min_margin = pricing_strategy['cost_plus_minimum']
                    target_margin = pricing_strategy['margin_requirements']['target']
                    
                    min_price = cost * (1 + min_margin)
                    target_price = cost * (1 + target_margin)
                    
                    recommended_price = target_price
                    pricing_rationale.append(f"Cost-plus pricing: ${cost} + {target_margin*100}% = ${target_price}")
                    output.append(f"**Cost:** ${cost}")
                    output.append(f"**Minimum Price:** ${min_price}")
                    output.append(f"**Target Price:** ${target_price}")
            
            if recommended_price:
                output.append(f"**Recommended Price:** ${recommended_price}")
                
                # Price change analysis
                if abs(recommended_price - current_price) > 0.01:
                    price_change = recommended_price - current_price
                    change_percent = (price_change / current_price) * 100 if current_price > 0 else 0
                    output.append(f"**Price Change:** ${price_change:.2f} ({change_percent:.1f}%)")
                    
                    if abs(change_percent) > 5:
                        output.append("⚠️ **Significant Price Change Detected**")
                else:
                    output.append("✅ **Current pricing is optimal**")
            
            # BigCommerce API recommendations
            output.append(f"\n## Recommended BigCommerce API Actions")
            
            if recommended_price and abs(recommended_price - current_price) > 0.01:
                output.append("### Update Product Price")
                output.append(f"**API:** Catalog API")
                output.append(f"**Endpoint:** PUT /catalog/products/{product_id}")
                output.append("**Payload:**")
                output.append("```json")
                output.append("{")
                output.append(f'  "price": {recommended_price}')
                output.append("}")
                output.append("```")
            
            # Pricing rationale
            if pricing_rationale:
                output.append(f"\n## Pricing Rationale")
                for i, reason in enumerate(pricing_rationale, 1):
                    output.append(f"{i}. {reason}")
            
            # Best practices
            output.append(f"\n## Best Practices")
            output.append("- Always respect MAP pricing when available")
            output.append("- Maintain minimum margin requirements")
            output.append("- Monitor competitor pricing regularly")
            output.append("- Use batch updates for multiple products")
            output.append("- Set up webhooks for price change notifications")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error optimizing pricing: {e}")
            return f"Error optimizing pricing: {str(e)}"
    
    async def sync_inventory_strategy(self, supplier_inventory: dict, current_bc_inventory: dict = None) -> str:
        """Recommend BigCommerce inventory sync strategy for dropshipping"""
        try:
            output = [f"# BigCommerce Inventory Sync Strategy\n"]
            
            sync_config = self.dropshipping_patterns['inventory_sync']
            buffer_stock = sync_config['buffer_stock']
            max_display = sync_config['max_quantity_display']
            
            # Analyze inventory data
            total_products = len(supplier_inventory)
            output.append(f"**Products to Sync:** {total_products}")
            
            sync_actions = []
            products_to_update = []
            products_to_disable = []
            
            for product_id, supplier_data in supplier_inventory.items():
                supplier_qty = supplier_data.get('quantity', 0)
                current_qty = 0
                
                if current_bc_inventory and product_id in current_bc_inventory:
                    current_qty = current_bc_inventory[product_id].get('quantity', 0)
                
                # Determine target quantity for BigCommerce
                if supplier_qty <= 0:
                    target_qty = 0
                    products_to_disable.append(product_id)
                elif supplier_qty <= buffer_stock:
                    target_qty = 1  # Show as available but limited
                else:
                    target_qty = min(supplier_qty - buffer_stock, max_display)
                
                # Check if update is needed
                if target_qty != current_qty:
                    products_to_update.append({
                        'product_id': product_id,
                        'current_qty': current_qty,
                        'target_qty': target_qty,
                        'supplier_qty': supplier_qty
                    })
            
            # Summary statistics
            output.append(f"**Products Needing Updates:** {len(products_to_update)}")
            output.append(f"**Products to Disable:** {len(products_to_disable)}")
            output.append(f"**No Changes Needed:** {total_products - len(products_to_update)}")
            
            # Sync strategy recommendations
            output.append(f"\n## Sync Strategy")
            output.append(f"**Buffer Stock:** {buffer_stock} units (reserved for supplier)")
            output.append(f"**Max Display Quantity:** {max_display} units")
            output.append(f"**Update Frequency:** Every {sync_config['update_frequency']} seconds")
            
            # BigCommerce API recommendations
            if products_to_update:
                output.append(f"\n## Recommended BigCommerce API Actions")
                
                # Batch inventory updates
                if len(products_to_update) > 10:
                    output.append("### Batch Inventory Update")
                    output.append(f"**API:** Catalog API")
                    output.append(f"**Endpoint:** PUT /catalog/products/batch")
                    output.append(f"**Batch Size:** {min(len(products_to_update), 100)} products")
                    output.append("**Payload Structure:**")
                    output.append("```json")
                    output.append("[")
                    for i, update in enumerate(products_to_update[:3]):  # Show first 3 examples
                        output.append("  {")
                        output.append(f'    "id": {update["product_id"]},')
                        output.append(f'    "inventory_level": {update["target_qty"]}')
                        output.append("  }" + ("," if i < 2 else ""))
                    if len(products_to_update) > 3:
                        output.append(f"  // ... {len(products_to_update) - 3} more products")
                    output.append("]")
                    output.append("```")
                else:
                    output.append("### Individual Product Updates")
                    for update in products_to_update[:5]:  # Show first 5
                        output.append(f"**Product {update['product_id']}:**")
                        output.append(f"- Current: {update['current_qty']} → Target: {update['target_qty']}")
                        output.append(f"- API: PUT /catalog/products/{update['product_id']}")
            
            # Product visibility management
            if products_to_disable:
                output.append(f"\n### Product Visibility Management")
                output.append(f"**Products to Hide:** {len(products_to_disable)}")
                output.append(f"**API:** Catalog API")
                output.append(f"**Endpoint:** PUT /catalog/products/batch")
                output.append("**Action:** Set `is_visible: false` for out-of-stock products")
            
            # Performance considerations
            output.append(f"\n## Performance Optimization")
            output.append(f"- Use batch updates for {len(products_to_update)} products")
            output.append(f"- Implement rate limiting (max 80% of API limits)")
            output.append(f"- Consider webhooks for real-time inventory changes")
            output.append(f"- Cache inventory data to reduce API calls")
            
            # Error handling
            output.append(f"\n## Error Handling")
            output.append("- Retry failed updates with exponential backoff")
            output.append("- Log all inventory sync operations")
            output.append("- Alert on repeated sync failures")
            output.append("- Maintain fallback inventory levels")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error creating inventory sync strategy: {e}")
            return f"Error creating inventory sync strategy: {str(e)}"
    
    async def handle_stockout_scenario(self, out_of_stock_products: list, alternative_options: dict = None) -> str:
        """Handle BigCommerce product stockouts in dropshipping scenario"""
        try:
            output = [f"# BigCommerce Stockout Management\n"]
            
            total_stockouts = len(out_of_stock_products)
            output.append(f"**Products Out of Stock:** {total_stockouts}")
            
            # Categorize stockout actions
            products_to_hide = []
            products_to_redirect = []
            products_to_notify = []
            
            for product_id in out_of_stock_products:
                product_data = {'id': product_id}
                
                # Check if alternative suppliers available
                if alternative_options and product_id in alternative_options:
                    alternatives = alternative_options[product_id]
                    if alternatives:
                        products_to_redirect.append({
                            'product_id': product_id,
                            'alternatives': alternatives
                        })
                    else:
                        products_to_hide.append(product_id)
                else:
                    products_to_hide.append(product_id)
                
                products_to_notify.append(product_id)
            
            # Action summary
            output.append(f"**Products to Hide:** {len(products_to_hide)}")
            output.append(f"**Products with Alternatives:** {len(products_to_redirect)}")
            output.append(f"**Notifications Needed:** {len(products_to_notify)}")
            
            # BigCommerce API actions
            output.append(f"\n## Recommended BigCommerce API Actions")
            
            # Hide out-of-stock products
            if products_to_hide:
                output.append("### Hide Out-of-Stock Products")
                output.append(f"**API:** Catalog API")
                output.append(f"**Endpoint:** PUT /catalog/products/batch")
                output.append("**Action:** Set visibility and inventory to zero")
                output.append("**Payload:**")
                output.append("```json")
                output.append("[")
                for i, product_id in enumerate(products_to_hide[:3]):
                    output.append("  {")
                    output.append(f'    "id": {product_id},')
                    output.append('    "is_visible": false,')
                    output.append('    "inventory_level": 0')
                    output.append("  }" + ("," if i < 2 else ""))
                if len(products_to_hide) > 3:
                    output.append(f"  // ... {len(products_to_hide) - 3} more products")
                output.append("]")
                output.append("```")
            
            # Handle products with alternatives
            if products_to_redirect:
                output.append("### Products with Alternative Sources")
                for redirect in products_to_redirect[:3]:
                    product_id = redirect['product_id']
                    alternatives = redirect['alternatives']
                    output.append(f"**Product {product_id}:**")
                    output.append(f"- Alternative suppliers: {len(alternatives)}")
                    output.append(f"- Action: Update supplier reference and restore visibility")
                    output.append(f"- API: PUT /catalog/products/{product_id}")
            
            # Customer notification strategy
            output.append(f"\n## Customer Communication Strategy")
            output.append("### Email Notifications")
            output.append("- Send 'back in stock' notifications when available")
            output.append("- Suggest alternative products where applicable")
            output.append("- Use BigCommerce email templates for consistency")
            
            output.append("### Product Page Updates")
            output.append("- Add 'temporarily unavailable' messaging")
            output.append("- Display estimated restock dates if known")
            output.append("- Show related/alternative products")
            
            # Automation recommendations
            output.append(f"\n## Automation Recommendations")
            output.append("### Webhook Setup")
            output.append("- Monitor inventory changes in real-time")
            output.append("- Trigger immediate stockout handling")
            output.append("- API: POST /hooks (inventory/updated event)")
            
            output.append("### Scheduled Monitoring")
            output.append("- Check supplier inventory every 5 minutes")
            output.append("- Proactively identify potential stockouts")
            output.append("- Maintain inventory buffer to prevent overselling")
            
            # Recovery strategy
            output.append(f"\n## Recovery Strategy")
            output.append("### When Stock Returns")
            output.append("1. Update inventory levels")
            output.append("2. Restore product visibility")
            output.append("3. Send back-in-stock notifications")
            output.append("4. Update related product recommendations")
            
            output.append("### Prevent Future Stockouts")
            output.append("- Implement inventory buffer (2-5 units)")
            output.append("- Set up low-stock alerts")
            output.append("- Diversify supplier sources")
            output.append("- Monitor supplier reliability metrics")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error handling stockout scenario: {e}")
            return f"Error handling stockout scenario: {str(e)}"
    
    async def optimize_order_fulfillment(self, order_data: dict, fulfillment_options: dict = None) -> str:
        """Optimize BigCommerce order processing for dropshipping fulfillment"""
        try:
            output = [f"# BigCommerce Order Fulfillment Optimization\n"]
            
            # Extract order information
            order_id = order_data.get('id', 'unknown')
            order_status = order_data.get('status', 'unknown')
            order_items = order_data.get('products', [])
            customer_info = order_data.get('customer', {})
            
            output.append(f"**Order ID:** {order_id}")
            output.append(f"**Status:** {order_status}")
            output.append(f"**Items:** {len(order_items)}")
            output.append(f"**Customer:** {customer_info.get('email', 'N/A')}")
            
            # Analyze fulfillment requirements
            fulfillment_actions = []
            inventory_updates = []
            status_updates = []
            
            for item in order_items:
                product_id = item.get('product_id')
                quantity = item.get('quantity', 1)
                
                # Determine fulfillment action
                action = {
                    'product_id': product_id,
                    'quantity': quantity,
                    'status': 'pending_fulfillment'
                }
                
                if fulfillment_options and str(product_id) in fulfillment_options:
                    supplier_info = fulfillment_options[str(product_id)]
                    action['supplier'] = supplier_info.get('supplier_name', 'Unknown')
                    action['estimated_ship_date'] = supplier_info.get('ship_date', 'TBD')
                
                fulfillment_actions.append(action)
                
                # Plan inventory adjustment
                inventory_updates.append({
                    'product_id': product_id,
                    'quantity_adjustment': -quantity,
                    'reason': f'Order {order_id} fulfillment'
                })
            
            # BigCommerce API recommendations
            output.append(f"\n## Recommended BigCommerce API Actions")
            
            # Order status update
            output.append("### 1. Update Order Status")
            output.append(f"**API:** Orders API")
            output.append(f"**Endpoint:** PUT /orders/{order_id}")
            output.append("**Action:** Set status to 'Processing' or 'Awaiting Fulfillment'")
            output.append("**Payload:**")
            output.append("```json")
            output.append("{")
            output.append('  "status_id": 2,')  # Processing status
            output.append('  "staff_notes": "Order sent to supplier for fulfillment"')
            output.append("}")
            output.append("```")
            
            # Inventory adjustments
            if inventory_updates:
                output.append("### 2. Adjust Inventory Levels")
                output.append(f"**API:** Catalog API")
                output.append(f"**Endpoint:** PUT /catalog/products/batch")
                output.append("**Action:** Reduce inventory for ordered items")
                output.append("**Payload:**")
                output.append("```json")
                output.append("[")
                for i, update in enumerate(inventory_updates[:3]):
                    output.append("  {")
                    output.append(f'    "id": {update["product_id"]},')
                    output.append(f'    "inventory_tracking": "simple",')
                    output.append(f'    "inventory_level": "current_level{update["quantity_adjustment"]}"')
                    output.append("  }" + ("," if i < 2 else ""))
                if len(inventory_updates) > 3:
                    output.append(f"  // ... {len(inventory_updates) - 3} more products")
                output.append("]")
                output.append("```")
            
            # Customer communication
            output.append("### 3. Customer Communication")
            output.append(f"**API:** Orders API")
            output.append(f"**Endpoint:** POST /orders/{order_id}/messages")
            output.append("**Action:** Send order confirmation with tracking info")
            
            # Fulfillment tracking
            output.append("### 4. Fulfillment Tracking Setup")
            for action in fulfillment_actions[:3]:
                output.append(f"**Product {action['product_id']}:**")
                output.append(f"- Supplier: {action.get('supplier', 'TBD')}")
                output.append(f"- Est. Ship Date: {action.get('estimated_ship_date', 'TBD')}")
                output.append(f"- Quantity: {action['quantity']}")
            
            # Automation workflow
            output.append(f"\n## Automation Workflow")
            output.append("### Immediate Actions (0-5 minutes)")
            output.append("1. Update order status to 'Processing'")
            output.append("2. Adjust product inventory levels")
            output.append("3. Send order details to supplier")
            output.append("4. Create fulfillment tracking record")
            
            output.append("### Follow-up Actions (1-24 hours)")
            output.append("1. Confirm supplier received order")
            output.append("2. Update estimated ship dates")
            output.append("3. Send customer confirmation email")
            output.append("4. Set up tracking number webhook")
            
            output.append("### Ongoing Monitoring")
            output.append("1. Track shipment status")
            output.append("2. Update order with tracking info")
            output.append("3. Handle delivery confirmations")
            output.append("4. Process any returns/exchanges")
            
            # Error handling
            output.append(f"\n## Error Handling")
            output.append("### Common Issues")
            output.append("- Supplier out of stock: Notify customer, offer alternatives")
            output.append("- Payment issues: Hold fulfillment until resolved")
            output.append("- Shipping address problems: Contact customer for correction")
            output.append("- Supplier delays: Update customer with new timeline")
            
            output.append("### Recovery Actions")
            output.append("- Maintain order status history")
            output.append("- Log all supplier communications")
            output.append("- Implement automatic retry mechanisms")
            output.append("- Escalate unresolved issues after 24 hours")
            
            # Performance metrics
            output.append(f"\n## Performance Tracking")
            output.append("### Key Metrics")
            output.append("- Order processing time (target: < 5 minutes)")
            output.append("- Supplier confirmation rate (target: > 95%)")
            output.append("- Shipping accuracy (target: > 98%)")
            output.append("- Customer satisfaction (track via reviews)")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error optimizing order fulfillment: {e}")
            return f"Error optimizing order fulfillment: {str(e)}"
    
    async def generate_api_client_code(self, api_name: str, language: str = "python") -> str:
        """Generate API client code for a specific BigCommerce API"""
        try:
            api_spec = self.openapi_parser.get_spec(api_name)
            if not api_spec:
                return f"API '{api_name}' not found. Available APIs: {', '.join(self.openapi_parser.specs.keys())}"
            
            endpoints = api_spec.get('endpoints', [])
            if not endpoints:
                return f"No endpoints found for API '{api_name}'"
            
            output = [f"# {api_name.upper()} API Client ({language.title()})\n"]
            
            if language.lower() == "python":
                output.extend(self._generate_python_client(api_name, endpoints))
            elif language.lower() == "javascript":
                output.extend(self._generate_javascript_client(api_name, endpoints))
            elif language.lower() == "curl":
                output.extend(self._generate_curl_examples(api_name, endpoints))
            else:
                return f"Unsupported language: {language}. Supported: python, javascript, curl"
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error generating API client code: {e}")
            return f"Error generating API client code: {str(e)}"
    
    def _generate_python_client(self, api_name: str, endpoints: List[Dict]) -> List[str]:
        """Generate Python client code"""
        output = []
        output.append("```python")
        output.append("import requests")
        output.append("from typing import Dict, Any, Optional")
        output.append("")
        output.append("")
        output.append(f"class {api_name.title()}APIClient:")
        output.append("    def __init__(self, store_hash: str, access_token: str):")
        output.append("        self.base_url = f'https://api.bigcommerce.com/stores/{store_hash}'")
        output.append("        self.headers = {")
        output.append("            'Content-Type': 'application/json',")
        output.append("            'Authorization': f'Bearer {access_token}',")
        output.append("            'Accept': 'application/json'")
        output.append("        }")
        output.append("")
        
        for endpoint in endpoints[:10]:  # Limit to first 10 endpoints
            path = endpoint.get('path', '')
            method = endpoint.get('method', 'GET').lower()
            operation_id = endpoint.get('operation_id', '')
            
            if operation_id:
                method_name = operation_id.replace('get', '').replace('post', '').replace('put', '').replace('delete', '')
                method_name = method_name[0].lower() + method_name[1:] if method_name else f"{method}_{path.split('/')[-1]}"
            else:
                method_name = f"{method}_{path.split('/')[-1]}"
            
            output.append(f"    def {method_name}(self, **kwargs) -> Dict[str, Any]:")
            output.append(f"        \"\"\"{endpoint.get('summary', f'{method.upper()} {path}')}\"\"\"")
            output.append(f"        url = f'{{self.base_url}}{path}'")
            
            if method.upper() in ["POST", "PUT", "PATCH"]:
                output.append("        data = kwargs.get('data', {})")
                output.append(f"        response = requests.{method}(url, json=data, headers=self.headers)")
            else:
                output.append("        params = kwargs.get('params', {})")
                output.append(f"        response = requests.{method}(url, params=params, headers=self.headers)")
            
            output.append("        response.raise_for_status()")
            output.append("        return response.json()")
            output.append("")
        
        output.append("")
        output.append("# Usage example:")
        output.append("client = BigCommerceAPIClient('your_store_hash', 'your_access_token')")
        output.append("products = client.get_products()")
        output.append("```")
        
        return output
    
    def _generate_javascript_client(self, api_name: str, endpoints: List[Dict]) -> List[str]:
        """Generate JavaScript client code"""
        output = []
        output.append("```javascript")
        output.append(f"class {api_name.charAt(0).toUpperCase() + api_name.slice(1)}APIClient {{")
        output.append("    constructor(storeHash, accessToken) {")
        output.append("        this.baseUrl = `https://api.bigcommerce.com/stores/${storeHash}`;")
        output.append("        this.headers = {")
        output.append("            'Content-Type': 'application/json',")
        output.append("            'Authorization': `Bearer ${accessToken}`,")
        output.append("            'Accept': 'application/json'")
        output.append("        };")
        output.append("    }")
        output.append("")
        
        for endpoint in endpoints[:10]:  # Limit to first 10 endpoints
            path = endpoint.get('path', '')
            method = endpoint.get('method', 'GET').toLowerCase()
            operation_id = endpoint.get('operation_id', '')
            
            if operation_id:
                method_name = operation_id.replace('get', '').replace('post', '').replace('put', '').replace('delete', '')
                method_name = method_name.charAt(0).toLowerCase() + method_name.slice(1) if method_name else `${method}${path.split('/').pop()}`
            else:
                method_name = `${method}${path.split('/').pop()}`
            
            output.append(f"    async {method_name}(params = {{}}) {{")
            output.append(f"        // {endpoint.get('summary', `${method.toUpperCase()} ${path}`)}")
            output.append(f"        const url = `${{this.baseUrl}}{path}`;")
            
            if method.toUpperCase() in ["POST", "PUT", "PATCH"]:
                output.append("        const response = await fetch(url, {")
                output.append(f"            method: '{method.toUpperCase()}',")
                output.append("            headers: this.headers,")
                output.append("            body: JSON.stringify(params.data || {})")
                output.append("        });")
            else:
                output.append("        const queryString = new URLSearchParams(params.query || {}).toString();")
                output.append("        const fullUrl = queryString ? `${url}?${queryString}` : url;")
                output.append("        const response = await fetch(fullUrl, {")
                output.append("            method: 'GET',")
                output.append("            headers: this.headers")
                output.append("        });")
            
            output.append("        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);")
            output.append("        return await response.json();")
            output.append("    }")
            output.append("")
        
        output.append("}")
        output.append("")
        output.append("// Usage example:")
        output.append("const client = new BigCommerceAPIClient('your_store_hash', 'your_access_token');")
        output.append("const products = await client.getProducts();")
        output.append("```")
        
        return output
    
    def _generate_curl_examples(self, api_name: str, endpoints: List[Dict]) -> List[str]:
        """Generate cURL examples"""
        output = []
        output.append("```bash")
        output.append(f"# {api_name.upper()} API Examples")
        output.append("STORE_HASH='your_store_hash'")
        output.append("ACCESS_TOKEN='your_access_token'")
        output.append("BASE_URL=\"https://api.bigcommerce.com/stores/$STORE_HASH\"")
        output.append("")
        
        for endpoint in endpoints[:5]:  # Limit to first 5 endpoints
            path = endpoint.get('path', '')
            method = endpoint.get('method', 'GET')
            summary = endpoint.get('summary', f'{method} {path}')
            
            output.append(f"# {summary}")
            output.append(f"curl -X {method} \\")
            output.append(f"  \"$BASE_URL{path}\" \\")
            output.append("  -H 'Content-Type: application/json' \\")
            output.append("  -H \"Authorization: Bearer $ACCESS_TOKEN\" \\")
            output.append("  -H 'Accept: application/json'")
            output.append("")
        
        output.append("```")
        
        return output 