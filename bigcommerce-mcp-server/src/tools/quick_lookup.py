"""Quick lookup tools for fast API query resolution"""

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class QuickLookupTools:
    """Fast lookup tools for common BigCommerce API queries"""
    
    def __init__(self, cache_manager, pattern_matcher):
        self.cache_manager = cache_manager
        self.pattern_matcher = pattern_matcher
        
        # Pre-defined responses for common queries
        self.quick_responses = {
            'inventory_single_product': {
                'title': 'Get Inventory for a Single Product',
                'description': 'To check inventory for a single product, use the Inventory API',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': '/v3/inventory/items',
                        'parameters': 'You can filter by variant_id, product_id, or sku',
                        'example': 'GET /stores/{store_hash}/v3/inventory/items?variant_id=123'
                    }
                ],
                'curl_example': '''curl -X GET \\
  https://api.bigcommerce.com/stores/{store_hash}/v3/inventory/items?variant_id=123 \\
  -H 'X-Auth-Token: {access_token}' \\
  -H 'Accept: application/json' ''',
                'response_fields': [
                    'quantity: Current inventory level',
                    'location_id: Location of the inventory',
                    'warning_level: Low stock warning threshold',
                    'is_in_stock: Boolean indicating if item is in stock'
                ]
            },
            'update_inventory': {
                'title': 'Update Inventory Levels',
                'description': 'To update inventory, use absolute adjustments for best performance',
                'endpoints': [
                    {
                        'method': 'PUT',
                        'path': '/v3/inventory/adjustments/absolute',
                        'description': 'Set inventory to specific quantity (recommended)',
                        'example': 'PUT /stores/{store_hash}/v3/inventory/adjustments/absolute'
                    }
                ],
                'request_body': {
                    'reason': 'Inventory update reason',
                    'items': [
                        {
                            'location_id': 1,
                            'variant_id': 123,
                            'quantity': 50
                        }
                    ]
                },
                'curl_example': '''curl -X PUT \\
  https://api.bigcommerce.com/stores/{store_hash}/v3/inventory/adjustments/absolute \\
  -H 'X-Auth-Token: {access_token}' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "reason": "Stock replenishment",
    "items": [{
      "location_id": 1,
      "variant_id": 123,
      "quantity": 50
    }]
  }' '''
            },
            'get_product': {
                'title': 'Get Product Information',
                'description': 'Retrieve product details using the Catalog API',
                'endpoints': [
                    {
                        'method': 'GET',
                        'path': '/v3/catalog/products/{product_id}',
                        'description': 'Get single product by ID',
                        'example': 'GET /stores/{store_hash}/v3/catalog/products/123'
                    },
                    {
                        'method': 'GET',
                        'path': '/v3/catalog/products',
                        'description': 'List products with filters',
                        'example': 'GET /stores/{store_hash}/v3/catalog/products?sku=ABC123'
                    }
                ],
                'curl_example': '''curl -X GET \\
  https://api.bigcommerce.com/stores/{store_hash}/v3/catalog/products/123 \\
  -H 'X-Auth-Token: {access_token}' \\
  -H 'Accept: application/json' '''
            }
        }
    
    async def initialize(self):
        """Initialize quick lookup patterns"""
        logger.info("Initializing quick lookup tools...")
        # Pre-compile any additional patterns if needed
        pass
    
    async def handle_query(self, query: str) -> str:
        """Handle a natural language query with fast lookup"""
        # Check cache first
        cache_key = f"quick_lookup:{query.lower()}"
        cached_response = await self.cache_manager.get(cache_key)
        if cached_response:
            return cached_response
        
        # Try pattern matching
        match = self.pattern_matcher.match_query(query)
        
        if match and match.get('confidence', 0) > 0.8:
            response = self._generate_response_from_match(match)
        else:
            # Try keyword-based quick lookup
            response = self._keyword_lookup(query)
        
        if response:
            # Cache the response
            await self.cache_manager.set(cache_key, response, ttl=3600)
            return response
        
        # Fallback message
        return self._generate_fallback_response(query)
    
    def _generate_response_from_match(self, match: Dict[str, Any]) -> str:
        """Generate response from pattern match"""
        output = []
        
        output.append(f"# {match['description']}")
        output.append("")
        
        # Add endpoint information
        output.append("## API Endpoint")
        output.append(f"**Method:** {match['method']}")
        output.append(f"**Path:** {match.get('endpoint', 'N/A')}")
        
        if match['category'] == 'inventory' and match['action'] == 'get_single':
            # Special handling for inventory queries
            response_data = self.quick_responses.get('inventory_single_product', {})
            
            output.append("")
            output.append("## Parameters")
            output.append("You can query inventory using one of these parameters:")
            output.append("- `variant_id`: The variant ID")
            output.append("- `product_id`: The product ID (for products without variants)")
            output.append("- `sku`: The product SKU")
            
            output.append("")
            output.append("## Example Request")
            output.append("```bash")
            output.append(response_data.get('curl_example', ''))
            output.append("```")
            
            output.append("")
            output.append("## Response Fields")
            for field in response_data.get('response_fields', []):
                output.append(f"- {field}")
        
        elif match['category'] == 'inventory' and match['action'] == 'update_single':
            response_data = self.quick_responses.get('update_inventory', {})
            
            output.append("")
            output.append("## Request Body")
            output.append("```json")
            output.append(json.dumps(response_data.get('request_body', {}), indent=2))
            output.append("```")
            
            output.append("")
            output.append("## Example Request")
            output.append("```bash")
            output.append(response_data.get('curl_example', ''))
            output.append("```")
        
        elif match['category'] == 'catalog' and match['action'] == 'get_single':
            response_data = self.quick_responses.get('get_product', {})
            
            output.append("")
            output.append("## Example Request")
            output.append("```bash")
            output.append(response_data.get('curl_example', ''))
            output.append("```")
        
        output.append("")
        output.append("## Authentication")
        output.append("All requests require:")
        output.append("- `X-Auth-Token` header with your access token")
        output.append("- Store hash in the URL path")
        
        return "\n".join(output)
    
    def _keyword_lookup(self, query: str) -> Optional[str]:
        """Perform keyword-based quick lookup"""
        query_lower = query.lower()
        
        # Map keywords to quick responses
        if 'inventory' in query_lower and ('single' in query_lower or 'product' in query_lower):
            return self._format_quick_response('inventory_single_product')
        elif 'update' in query_lower and 'inventory' in query_lower:
            return self._format_quick_response('update_inventory')
        elif 'product' in query_lower and any(word in query_lower for word in ['get', 'fetch', 'retrieve']):
            return self._format_quick_response('get_product')
        
        return None
    
    def _format_quick_response(self, response_key: str) -> str:
        """Format a pre-defined quick response"""
        response_data = self.quick_responses.get(response_key)
        if not response_data:
            return ""
        
        output = []
        output.append(f"# {response_data['title']}")
        output.append("")
        output.append(response_data['description'])
        output.append("")
        
        if 'endpoints' in response_data:
            output.append("## Endpoints")
            for endpoint in response_data['endpoints']:
                output.append(f"- **{endpoint['method']} {endpoint['path']}**")
                if 'description' in endpoint:
                    output.append(f"  {endpoint['description']}")
                if 'example' in endpoint:
                    output.append(f"  Example: `{endpoint['example']}`")
                if 'parameters' in endpoint:
                    output.append(f"  {endpoint['parameters']}")
                output.append("")
        
        if 'request_body' in response_data:
            output.append("## Request Body Example")
            output.append("```json")
            output.append(json.dumps(response_data['request_body'], indent=2))
            output.append("```")
            output.append("")
        
        if 'curl_example' in response_data:
            output.append("## Example cURL Request")
            output.append("```bash")
            output.append(response_data['curl_example'])
            output.append("```")
            output.append("")
        
        if 'response_fields' in response_data:
            output.append("## Response Fields")
            for field in response_data['response_fields']:
                output.append(f"- {field}")
            output.append("")
        
        output.append("## Authentication")
        output.append("Remember to include:")
        output.append("- `X-Auth-Token` header with your API access token")
        output.append("- Your store hash in the URL")
        
        return "\n".join(output)
    
    def _generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when no match is found"""
        return f"""# API Query: {query}

I couldn't find a direct match for your query. Here are some suggestions:

## Available Tools
- Use `search_api_endpoints` to search for specific endpoints
- Use `get_api_spec` to get complete API documentation
- Use `get_endpoint_details` for detailed endpoint information

## Common API Categories
- **Catalog**: Products, categories, brands
- **Orders**: Order management and processing
- **Customers**: Customer data and management
- **Inventory**: Stock levels and adjustments
- **Webhooks**: Event notifications

Please try rephrasing your query or use one of the specific tools above."""