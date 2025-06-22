"""Pattern matcher for quick query routing"""

import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Matches natural language queries to API patterns for fast routing"""
    
    def __init__(self):
        # Define patterns for common queries with their corresponding API info
        self.patterns = {
            # Inventory patterns
            r'(?:check|get|view|query)?\s*inventory\s*(?:for|of)?\s*(?:single|one|a)?\s*product': {
                'category': 'inventory',
                'action': 'get_single',
                'endpoint': '/inventory/items',
                'method': 'GET',
                'params': ['variant_id', 'product_id', 'sku'],
                'description': 'Get inventory for a single product'
            },
            r'(?:update|change|modify|set)?\s*inventory\s*(?:for|of)?\s*(?:single|one|a)?\s*product': {
                'category': 'inventory',
                'action': 'update_single',
                'endpoint': '/inventory/adjustments/absolute',
                'method': 'PUT',
                'description': 'Update inventory for a single product'
            },
            r'(?:bulk|batch|mass)?\s*(?:update|change)?\s*inventory': {
                'category': 'inventory',
                'action': 'bulk_update',
                'endpoint': '/inventory/adjustments/absolute',
                'method': 'PUT',
                'description': 'Bulk update inventory'
            },
            
            # Product patterns
            r'(?:get|fetch|retrieve|find)?\s*product\s*(?:by|with)?\s*(?:id|ID)': {
                'category': 'catalog',
                'action': 'get_single',
                'endpoint': '/catalog/products/{product_id}',
                'method': 'GET',
                'description': 'Get product by ID'
            },
            r'(?:list|get|fetch|show)?\s*(?:all)?\s*products': {
                'category': 'catalog',
                'action': 'list',
                'endpoint': '/catalog/products',
                'method': 'GET',
                'description': 'List all products'
            },
            r'(?:create|add|new)?\s*product': {
                'category': 'catalog',
                'action': 'create',
                'endpoint': '/catalog/products',
                'method': 'POST',
                'description': 'Create a new product'
            },
            r'(?:update|modify|edit|change)?\s*product': {
                'category': 'catalog',
                'action': 'update',
                'endpoint': '/catalog/products/{product_id}',
                'method': 'PUT',
                'description': 'Update a product'
            },
            
            # Order patterns
            r'(?:get|fetch|retrieve|find)?\s*order\s*(?:by|with)?\s*(?:id|ID|number)': {
                'category': 'orders',
                'action': 'get_single',
                'endpoint': '/orders/{order_id}',
                'method': 'GET',
                'description': 'Get order by ID'
            },
            r'(?:list|get|fetch|show)?\s*(?:all)?\s*orders': {
                'category': 'orders',
                'action': 'list',
                'endpoint': '/orders',
                'method': 'GET',
                'description': 'List all orders'
            },
            r'(?:create|place|new)?\s*order': {
                'category': 'orders',
                'action': 'create',
                'endpoint': '/orders',
                'method': 'POST',
                'description': 'Create a new order'
            },
            
            # Customer patterns
            r'(?:get|fetch|retrieve|find)?\s*customer\s*(?:information|info|details|data)': {
                'category': 'customers',
                'action': 'get_single',
                'endpoint': '/customers/{customer_id}',
                'method': 'GET',
                'description': 'Get customer information'
            },
            r'(?:list|get|fetch|show)?\s*(?:all)?\s*customers': {
                'category': 'customers',
                'action': 'list',
                'endpoint': '/customers',
                'method': 'GET',
                'description': 'List all customers'
            },
            
            # Category patterns
            r'(?:get|list|fetch)?\s*(?:product)?\s*categories': {
                'category': 'catalog',
                'action': 'list_categories',
                'endpoint': '/catalog/categories',
                'method': 'GET',
                'description': 'List product categories'
            },
            
            # Webhook patterns
            r'(?:create|setup|configure)?\s*webhook': {
                'category': 'webhooks',
                'action': 'create',
                'endpoint': '/hooks',
                'method': 'POST',
                'description': 'Create a webhook'
            }
        }
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = {
            re.compile(pattern, re.IGNORECASE): info 
            for pattern, info in self.patterns.items()
        }
    
    def match_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Match a natural language query to an API pattern"""
        query = query.strip()
        
        # Try each pattern
        for pattern, info in self.compiled_patterns.items():
            if pattern.search(query):
                logger.debug(f"Matched query '{query}' to pattern: {info['description']}")
                return {
                    **info,
                    'matched_query': query,
                    'confidence': 0.9  # High confidence for direct pattern match
                }
        
        # If no direct match, try keyword matching
        return self._keyword_match(query)
    
    def _keyword_match(self, query: str) -> Optional[Dict[str, Any]]:
        """Fallback keyword matching for queries that don't match patterns"""
        query_lower = query.lower()
        
        # Define keyword mappings
        keyword_mappings = {
            'inventory': {
                'category': 'inventory',
                'endpoints': ['/inventory/items', '/inventory/adjustments/absolute'],
                'confidence': 0.7
            },
            'product': {
                'category': 'catalog',
                'endpoints': ['/catalog/products', '/catalog/products/{product_id}'],
                'confidence': 0.7
            },
            'order': {
                'category': 'orders',
                'endpoints': ['/orders', '/orders/{order_id}'],
                'confidence': 0.7
            },
            'customer': {
                'category': 'customers',
                'endpoints': ['/customers', '/customers/{customer_id}'],
                'confidence': 0.7
            },
            'category': {
                'category': 'catalog',
                'endpoints': ['/catalog/categories'],
                'confidence': 0.7
            },
            'price': {
                'category': 'price_lists',
                'endpoints': ['/pricelists', '/catalog/products/{product_id}/prices'],
                'confidence': 0.6
            },
            'webhook': {
                'category': 'webhooks',
                'endpoints': ['/hooks'],
                'confidence': 0.7
            }
        }
        
        for keyword, mapping in keyword_mappings.items():
            if keyword in query_lower:
                # Determine action based on verb
                action = 'get'
                if any(verb in query_lower for verb in ['create', 'add', 'new']):
                    action = 'create'
                elif any(verb in query_lower for verb in ['update', 'modify', 'change', 'edit']):
                    action = 'update'
                elif any(verb in query_lower for verb in ['delete', 'remove']):
                    action = 'delete'
                elif any(verb in query_lower for verb in ['list', 'all', 'show']):
                    action = 'list'
                
                return {
                    'category': mapping['category'],
                    'action': action,
                    'endpoints': mapping['endpoints'],
                    'confidence': mapping['confidence'],
                    'matched_query': query,
                    'match_type': 'keyword'
                }
        
        return None
    
    def get_common_patterns(self) -> List[Dict[str, Any]]:
        """Get list of common patterns for documentation"""
        return [
            {
                'example': example,
                'description': info['description'],
                'endpoint': info['endpoint'],
                'method': info['method']
            }
            for example, info in self.patterns.items()
        ]