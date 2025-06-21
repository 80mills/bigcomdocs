"""Search indexer for BigCommerce documentation"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SearchIndexer:
    """Simple search indexer for BigCommerce documentation"""
    
    def __init__(self):
        self.api_index = {}
        self.doc_index = {}
        self.schema_index = {}
    
    async def build_indexes(self, api_specs: Dict[str, Any], documentation: Dict[str, Any], schemas: Dict[str, Any]):
        """Build search indexes from loaded data"""
        logger.info("Building search indexes...")
        
        # Build API index
        await self._build_api_index(api_specs)
        
        # Build documentation index
        await self._build_doc_index(documentation)
        
        # Build schema index
        await self._build_schema_index(schemas)
        
        logger.info("Search indexes built successfully")
    
    async def _build_api_index(self, api_specs: Dict[str, Any]):
        """Build search index for API specifications"""
        self.api_index = {}
        
        for api_name, api_data in api_specs.items():
            # Index API metadata
            self.api_index[api_name] = {
                'name': api_name,
                'title': api_data['spec'].get('info', {}).get('title', ''),
                'description': api_data['spec'].get('info', {}).get('description', ''),
                'endpoints': api_data.get('endpoints', []),
                'tags': api_data.get('tags', []),
                'schemas': api_data.get('schemas', {})
            }
    
    async def _build_doc_index(self, documentation: Dict[str, Any]):
        """Build search index for documentation"""
        self.doc_index = documentation
    
    async def _build_schema_index(self, schemas: Dict[str, Any]):
        """Build search index for schemas"""
        self.schema_index = schemas
    
    def search_apis(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search API specifications"""
        results = []
        query_lower = query.lower()
        
        for api_name, api_data in self.api_index.items():
            score = 0
            
            # Check API name
            if query_lower in api_name.lower():
                score += 10
            
            # Check title
            if query_lower in api_data.get('title', '').lower():
                score += 8
            
            # Check description
            if query_lower in api_data.get('description', '').lower():
                score += 5
            
            # Check endpoints
            for endpoint in api_data.get('endpoints', []):
                if query_lower in endpoint.get('path', '').lower():
                    score += 7
                if query_lower in endpoint.get('summary', '').lower():
                    score += 6
                if query_lower in endpoint.get('description', '').lower():
                    score += 4
            
            if score > 0:
                results.append({
                    'api_name': api_name,
                    'score': score,
                    'data': api_data
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def search_documentation(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documentation content"""
        results = []
        query_lower = query.lower()
        
        for doc_path, doc_data in self.doc_index.items():
            score = 0
            
            # Check title
            if query_lower in doc_data.get('title', '').lower():
                score += 10
            
            # Check content
            if query_lower in doc_data.get('content', '').lower():
                score += 5
            
            # Check description
            if query_lower in doc_data.get('description', '').lower():
                score += 7
            
            if score > 0:
                results.append({
                    'path': doc_path,
                    'score': score,
                    'data': doc_data
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def search_schemas(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search schema definitions"""
        results = []
        query_lower = query.lower()
        
        for schema_name, schema_data in self.schema_index.items():
            score = 0
            
            # Check schema name
            if query_lower in schema_name.lower():
                score += 10
            
            # Check schema content (basic string search)
            schema_str = json.dumps(schema_data, default=str).lower()
            if query_lower in schema_str:
                score += 3
            
            if score > 0:
                results.append({
                    'name': schema_name,
                    'score': score,
                    'data': schema_data
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit] 