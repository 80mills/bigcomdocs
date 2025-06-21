"""Parser for OpenAPI specification files"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OpenAPIParser:
    """Parser for OpenAPI specification files"""
    
    def __init__(self, reference_path: Path):
        self.reference_path = reference_path
        self.specs = {}
    
    async def load_all_specs(self) -> Dict[str, Any]:
        """Load all OpenAPI specification files"""
        specs = {}
        
        if not self.reference_path.exists():
            logger.warning(f"Reference path does not exist: {self.reference_path}")
            return specs
        
        # Find all YAML files
        yaml_files = list(self.reference_path.glob("**/*.yml")) + list(self.reference_path.glob("**/*.yaml"))
        
        for yaml_file in yaml_files:
            try:
                api_name = self._extract_api_name(yaml_file)
                spec_data = await self._load_spec_file(yaml_file)
                
                if spec_data:
                    specs[api_name] = {
                        'file_path': str(yaml_file),
                        'spec': spec_data,
                        'endpoints': self._extract_endpoints(spec_data),
                        'schemas': self._extract_schemas(spec_data),
                        'tags': self._extract_tags(spec_data)
                    }
                    logger.info(f"Loaded API spec: {api_name}")
                
            except Exception as e:
                logger.error(f"Error loading spec file {yaml_file}: {e}")
        
        self.specs = specs
        return specs
    
    async def _load_spec_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single OpenAPI spec file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _extract_api_name(self, file_path: Path) -> str:
        """Extract API name from file path"""
        # Remove file extension and convert to lowercase
        name = file_path.stem.lower()
        
        # Remove version suffixes
        for version in ['.v3', '.v2', '.sf']:
            name = name.replace(version, '')
        
        return name
    
    def _extract_endpoints(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract endpoint information from OpenAPI spec"""
        endpoints = []
        
        paths = spec.get('paths', {})
        for path, path_data in paths.items():
            for method, operation in path_data.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'operation_id': operation.get('operationId'),
                        'summary': operation.get('summary'),
                        'description': operation.get('description'),
                        'tags': operation.get('tags', []),
                        'parameters': operation.get('parameters', []),
                        'request_body': operation.get('requestBody'),
                        'responses': operation.get('responses', {}),
                        'security': operation.get('security', [])
                    }
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_schemas(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract schema definitions from OpenAPI spec"""
        components = spec.get('components', {})
        return components.get('schemas', {})
    
    def _extract_tags(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tags from OpenAPI spec"""
        return spec.get('tags', [])
    
    def get_spec(self, api_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific API specification"""
        return self.specs.get(api_name.lower())
    
    def search_endpoints(self, query: str, method: Optional[str] = None, api_category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for endpoints matching the query"""
        results = []
        
        for api_name, api_data in self.specs.items():
            # Filter by API category if specified
            if api_category and api_category.lower() not in api_name.lower():
                continue
            
            endpoints = api_data.get('endpoints', [])
            for endpoint in endpoints:
                # Filter by method if specified
                if method and endpoint['method'].upper() != method.upper():
                    continue
                
                # Search in various fields
                searchable_text = ' '.join([
                    endpoint.get('path', ''),
                    endpoint.get('summary', ''),
                    endpoint.get('description', ''),
                    endpoint.get('operation_id', ''),
                    ' '.join(endpoint.get('tags', []))
                ]).lower()
                
                if query.lower() in searchable_text:
                    result = endpoint.copy()
                    result['api_name'] = api_name
                    results.append(result)
        
        return results
    
    def get_endpoint_details(self, api_name: str, endpoint_path: str, method: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific endpoint"""
        api_data = self.get_spec(api_name)
        if not api_data:
            return None
        
        endpoints = api_data.get('endpoints', [])
        for endpoint in endpoints:
            if (endpoint['path'] == endpoint_path and 
                endpoint['method'].upper() == method.upper()):
                result = endpoint.copy()
                result['api_name'] = api_name
                result['full_spec'] = api_data['spec']
                return result
        
        return None
    
    def list_api_categories(self) -> List[Dict[str, Any]]:
        """List all available API categories"""
        categories = []
        
        for api_name, api_data in self.specs.items():
            spec = api_data['spec']
            info = spec.get('info', {})
            
            category = {
                'name': api_name,
                'title': info.get('title', api_name.title()),
                'description': info.get('description', ''),
                'version': info.get('version', ''),
                'endpoint_count': len(api_data.get('endpoints', [])),
                'tags': [tag.get('name', '') for tag in api_data.get('tags', [])]
            }
            categories.append(category)
        
        return sorted(categories, key=lambda x: x['name']) 