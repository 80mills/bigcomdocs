"""Parser for JSON schema files"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SchemaParser:
    """Parser for JSON schema files"""
    
    def __init__(self, models_path: Path):
        self.models_path = models_path
        self.schemas = {}
    
    async def load_all_schemas(self) -> Dict[str, Any]:
        """Load all JSON schema files"""
        schemas = {}
        
        if not self.models_path.exists():
            logger.warning(f"Models path does not exist: {self.models_path}")
            return schemas
        
        # Find all JSON and YAML schema files
        schema_files = (
            list(self.models_path.glob("**/*.json")) + 
            list(self.models_path.glob("**/*.yml")) + 
            list(self.models_path.glob("**/*.yaml"))
        )
        
        for schema_file in schema_files:
            try:
                schema_data = await self._load_schema_file(schema_file)
                if schema_data:
                    schema_name = self._extract_schema_name(schema_file)
                    schemas[schema_name] = {
                        'file_path': str(schema_file),
                        'schema': schema_data,
                        'name': schema_name
                    }
                    logger.info(f"Loaded schema: {schema_name}")
                
            except Exception as e:
                logger.error(f"Error loading schema file {schema_file}: {e}")
        
        self.schemas = schemas
        return schemas
    
    async def _load_schema_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single schema file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_path.suffix.lower() == '.json':
                    return json.load(file)
                else:
                    return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error reading schema file {file_path}: {e}")
            return None
    
    def _extract_schema_name(self, file_path: Path) -> str:
        """Extract schema name from file path"""
        # Remove file extension and use relative path
        relative_path = file_path.relative_to(self.models_path)
        return str(relative_path.with_suffix(''))
    
    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific schema"""
        return self.schemas.get(schema_name)
    
    def search_schemas(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search schemas by name or content"""
        results = []
        query_lower = query.lower()
        
        for schema_name, schema_data in self.schemas.items():
            score = 0
            
            # Check schema name
            if query_lower in schema_name.lower():
                score += 10
            
            # Check schema content (basic string search)
            schema_str = json.dumps(schema_data['schema'], default=str).lower()
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