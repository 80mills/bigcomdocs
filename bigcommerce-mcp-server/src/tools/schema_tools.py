"""Schema tools for the BigCommerce MCP server"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SchemaTools:
    """Tools for working with BigCommerce schemas"""
    
    def __init__(self, schema_parser, search_indexer):
        self.schema_parser = schema_parser
        self.search_indexer = search_indexer
    
    async def get_schema(self, schema_name: str) -> str:
        """Get JSON schema for BigCommerce data models"""
        try:
            schema_data = self.schema_parser.get_schema(schema_name)
            
            if not schema_data:
                available_schemas = list(self.schema_parser.schemas.keys())[:10]
                return f"Schema '{schema_name}' not found. Available schemas: {', '.join(available_schemas)}"
            
            schema = schema_data['schema']
            
            output = [f"# Schema: {schema_name}\n"]
            
            # Schema metadata
            if schema.get('title'):
                output.append(f"**Title:** {schema['title']}")
            
            if schema.get('description'):
                output.append(f"**Description:** {schema['description']}")
            
            if schema.get('type'):
                output.append(f"**Type:** {schema['type']}")
            
            # Properties
            properties = schema.get('properties', {})
            if properties:
                output.append(f"\n## Properties ({len(properties)} total)")
                
                for prop_name, prop_data in properties.items():
                    prop_type = prop_data.get('type', 'unknown')
                    prop_desc = prop_data.get('description', 'No description')
                    required = " (required)" if prop_name in schema.get('required', []) else " (optional)"
                    
                    output.append(f"- **{prop_name}** ({prop_type}){required}: {prop_desc}")
                    
                    # Show enum values if present
                    if prop_data.get('enum'):
                        output.append(f"  Possible values: {', '.join(map(str, prop_data['enum']))}")
            
            # Required fields
            required_fields = schema.get('required', [])
            if required_fields:
                output.append(f"\n## Required Fields")
                for field in required_fields:
                    output.append(f"- {field}")
            
            # Examples
            if schema.get('examples'):
                output.append(f"\n## Examples")
                for i, example in enumerate(schema['examples'][:2]):  # Show first 2 examples
                    output.append(f"\n### Example {i+1}")
                    output.append("```json")
                    output.append(json.dumps(example, indent=2))
                    output.append("```")
            
            # Raw schema (truncated)
            output.append(f"\n## Raw Schema")
            output.append("```json")
            schema_json = json.dumps(schema, indent=2)
            if len(schema_json) > 1000:
                output.append(schema_json[:1000] + "\n  ... (truncated)")
            else:
                output.append(schema_json)
            output.append("```")
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return f"Error getting schema: {str(e)}"
    
    async def search_schemas(self, query: str) -> str:
        """Search for schemas by name or properties"""
        try:
            results = self.schema_parser.search_schemas(query, limit=10)
            
            if not results:
                return f"No schemas found matching query: '{query}'"
            
            output = [f"Found {len(results)} schema(s) matching '{query}':\n"]
            
            for result in results:
                schema_data = result['data']
                schema = schema_data['schema']
                
                output.append(f"## {result['name']}")
                
                if schema.get('title'):
                    output.append(f"**Title:** {schema['title']}")
                
                if schema.get('description'):
                    desc = schema['description'][:150] + "..." if len(schema['description']) > 150 else schema['description']
                    output.append(f"**Description:** {desc}")
                
                if schema.get('type'):
                    output.append(f"**Type:** {schema['type']}")
                
                # Properties count
                properties = schema.get('properties', {})
                if properties:
                    output.append(f"**Properties:** {len(properties)} total")
                    
                    # Show first few property names
                    prop_names = list(properties.keys())[:5]
                    output.append(f"**Sample Properties:** {', '.join(prop_names)}")
                    if len(properties) > 5:
                        output.append(f"  ... and {len(properties) - 5} more")
                
                output.append("")  # Empty line for spacing
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error searching schemas: {e}")
            return f"Error searching schemas: {str(e)}" 