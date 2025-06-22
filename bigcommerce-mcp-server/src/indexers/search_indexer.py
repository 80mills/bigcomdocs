"""Search indexer for BigCommerce documentation - Optimized with inverted index"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class SearchIndexer:
    """Optimized search indexer with inverted index for BigCommerce documentation"""
    
    def __init__(self, use_inverted_index: bool = True):
        self.use_inverted_index = use_inverted_index
        
        # Traditional indexes
        self.api_index = {}
        self.doc_index = {}
        self.schema_index = {}
        
        # Inverted indexes for fast search
        self.inverted_api_index = defaultdict(set)  # term -> set of api names
        self.inverted_endpoint_index = defaultdict(set)  # term -> set of (api_name, endpoint_path)
        self.inverted_doc_index = defaultdict(set)  # term -> set of doc paths
        
        # Pre-compiled regex for tokenization
        self._token_pattern = re.compile(r'\b\w+\b')
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into searchable terms"""
        if not text:
            return set()
        # Convert to lowercase and extract words
        tokens = self._token_pattern.findall(text.lower())
        # Also include n-grams for better matching
        tokens.extend([f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1) if i < len(tokens)-1])
        return set(tokens)
    
    async def build_indexes(self, api_specs: Dict[str, Any], documentation: Dict[str, Any], schemas: Dict[str, Any]):
        """Build search indexes from loaded data"""
        logger.info("Building optimized search indexes...")
        
        # Build API index
        await self._build_api_index(api_specs)
        
        # Build documentation index
        await self._build_doc_index(documentation)
        
        # Build schema index
        await self._build_schema_index(schemas)
        
        logger.info(f"Search indexes built successfully. Inverted index contains {len(self.inverted_api_index)} terms")
    
    async def build_api_index(self, api_specs: Dict[str, Any]):
        """Build API index separately (for lazy loading)"""
        await self._build_api_index(api_specs)
    
    async def _build_api_index(self, api_specs: Dict[str, Any]):
        """Build search index for API specifications"""
        self.api_index = {}
        
        for api_name, api_data in api_specs.items():
            # Traditional index
            self.api_index[api_name] = {
                'name': api_name,
                'title': api_data['spec'].get('info', {}).get('title', ''),
                'description': api_data['spec'].get('info', {}).get('description', ''),
                'endpoints': api_data.get('endpoints', []),
                'tags': api_data.get('tags', []),
                'schemas': api_data.get('schemas', {})
            }
            
            if self.use_inverted_index:
                # Build inverted index for API
                searchable_text = ' '.join([
                    api_name,
                    self.api_index[api_name]['title'],
                    self.api_index[api_name]['description']
                ])
                tokens = self._tokenize(searchable_text)
                for token in tokens:
                    self.inverted_api_index[token].add(api_name)
                
                # Build inverted index for endpoints
                for endpoint in api_data.get('endpoints', []):
                    endpoint_text = ' '.join([
                        endpoint.get('path', ''),
                        endpoint.get('summary', ''),
                        endpoint.get('description', ''),
                        ' '.join(endpoint.get('tags', []))
                    ])
                    tokens = self._tokenize(endpoint_text)
                    endpoint_key = (api_name, endpoint.get('path', ''), endpoint.get('method', ''))
                    for token in tokens:
                        self.inverted_endpoint_index[token].add(endpoint_key)
    
    async def _build_doc_index(self, documentation: Dict[str, Any]):
        """Build search index for documentation"""
        self.doc_index = documentation
        
        if self.use_inverted_index:
            for doc_path, doc_data in documentation.items():
                searchable_text = ' '.join([
                    doc_data.get('title', ''),
                    doc_data.get('description', ''),
                    doc_data.get('content', '')[:500]  # Limit content for indexing
                ])
                tokens = self._tokenize(searchable_text)
                for token in tokens:
                    self.inverted_doc_index[token].add(doc_path)
    
    async def _build_schema_index(self, schemas: Dict[str, Any]):
        """Build search index for schemas"""
        self.schema_index = schemas
    
    def search_apis(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search API specifications using inverted index"""
        results = []
        query_tokens = self._tokenize(query)
        
        if self.use_inverted_index and query_tokens:
            # Find APIs that match any query token
            matching_apis = set()
            for token in query_tokens:
                matching_apis.update(self.inverted_api_index.get(token, set()))
            
            # Score and rank results
            for api_name in matching_apis:
                if api_name not in self.api_index:
                    continue
                    
                api_data = self.api_index[api_name]
                score = self._calculate_relevance_score(query_tokens, api_name, api_data)
                
                if score > 0:
                    results.append({
                        'api_name': api_name,
                        'score': score,
                        'data': api_data
                    })
        else:
            # Fallback to traditional search
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
                
                if score > 0:
                    results.append({
                        'api_name': api_name,
                        'score': score,
                        'data': api_data
                    })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def search_endpoints(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search endpoints using inverted index"""
        results = []
        query_tokens = self._tokenize(query)
        
        if self.use_inverted_index and query_tokens:
            # Find endpoints that match any query token
            matching_endpoints = set()
            for token in query_tokens:
                matching_endpoints.update(self.inverted_endpoint_index.get(token, set()))
            
            # Build results
            for api_name, path, method in matching_endpoints:
                if api_name in self.api_index:
                    api_data = self.api_index[api_name]
                    for endpoint in api_data.get('endpoints', []):
                        if endpoint.get('path') == path and endpoint.get('method') == method:
                            results.append({
                                'api_name': api_name,
                                'endpoint': endpoint,
                                'score': len(query_tokens)  # Simple scoring
                            })
                            break
        
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def _calculate_relevance_score(self, query_tokens: Set[str], api_name: str, api_data: Dict[str, Any]) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        
        # Create searchable text
        searchable_text = ' '.join([
            api_name,
            api_data.get('title', ''),
            api_data.get('description', '')
        ]).lower()
        
        # Score based on token matches
        for token in query_tokens:
            if token in api_name.lower():
                score += 10  # High score for API name match
            if token in api_data.get('title', '').lower():
                score += 8
            if token in api_data.get('description', '').lower():
                score += 5
        
        # Bonus for exact phrase match
        if ' '.join(query_tokens) in searchable_text:
            score *= 1.5
        
        return score
    
    def search_documentation(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documentation content using inverted index"""
        results = []
        query_tokens = self._tokenize(query)
        
        if self.use_inverted_index and query_tokens:
            # Find docs that match any query token
            matching_docs = set()
            for token in query_tokens:
                matching_docs.update(self.inverted_doc_index.get(token, set()))
            
            # Score and rank results
            for doc_path in matching_docs:
                if doc_path not in self.doc_index:
                    continue
                    
                doc_data = self.doc_index[doc_path]
                score = self._calculate_doc_relevance_score(query_tokens, doc_data)
                
                if score > 0:
                    results.append({
                        'path': doc_path,
                        'score': score,
                        'data': doc_data
                    })
        else:
            # Fallback to traditional search
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
    
    def _calculate_doc_relevance_score(self, query_tokens: Set[str], doc_data: Dict[str, Any]) -> float:
        """Calculate relevance score for documentation"""
        score = 0.0
        
        # Score based on token matches in different fields
        for token in query_tokens:
            if token in doc_data.get('title', '').lower():
                score += 10
            if token in doc_data.get('description', '').lower():
                score += 7
            if token in doc_data.get('content', '').lower()[:1000]:  # Check first 1000 chars
                score += 5
        
        return score
    
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