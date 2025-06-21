"""Documentation tools for the BigCommerce MCP server"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DocumentationTools:
    """Tools for working with BigCommerce documentation"""
    
    def __init__(self, mdx_parser, search_indexer):
        self.mdx_parser = mdx_parser
        self.search_indexer = search_indexer
    
    async def search_documentation(self, query: str, section: Optional[str] = None, limit: int = 10) -> str:
        """Search across all BigCommerce documentation"""
        try:
            results = self.mdx_parser.search_documentation(query, limit)
            
            if not results:
                return f"No documentation found matching query: '{query}'"
            
            output = [f"Found {len(results)} documentation result(s) matching '{query}':\n"]
            
            for result in results:
                doc_data = result['data']
                output.append(f"## {doc_data.get('title', result['path'])}")
                output.append(f"**Path:** {result['path']}")
                
                if doc_data.get('description'):
                    output.append(f"**Description:** {doc_data['description']}")
                
                if doc_data.get('keywords'):
                    output.append(f"**Keywords:** {', '.join(doc_data['keywords'])}")
                
                # Show snippet of content
                content = doc_data.get('content', '')
                if content:
                    # Find the query in content and show surrounding context
                    query_pos = content.lower().find(query.lower())
                    if query_pos != -1:
                        start = max(0, query_pos - 100)
                        end = min(len(content), query_pos + 200)
                        snippet = content[start:end].strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(content):
                            snippet = snippet + "..."
                        output.append(f"**Snippet:** {snippet}")
                
                output.append("")  # Empty line for spacing
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error searching documentation: {e}")
            return f"Error searching documentation: {str(e)}"
    
    async def get_section(self, section_path: str) -> str:
        """Get specific documentation section content"""
        try:
            doc_data = self.mdx_parser.get_documentation(section_path)
            
            if not doc_data:
                available_docs = list(self.mdx_parser.documentation.keys())[:10]
                return f"Documentation section '{section_path}' not found. Available sections: {', '.join(available_docs)}"
            
            output = [f"# {doc_data.get('title', section_path)}\n"]
            
            if doc_data.get('description'):
                output.append(f"**Description:** {doc_data['description']}")
            
            if doc_data.get('keywords'):
                output.append(f"**Keywords:** {', '.join(doc_data['keywords'])}")
            
            # Show table of contents
            headings = doc_data.get('headings', [])
            if headings:
                output.append("\n## Table of Contents")
                for heading in headings:
                    indent = "  " * (heading['level'] - 1)
                    output.append(f"{indent}- {heading['text']}")
            
            # Show code blocks if any
            code_blocks = doc_data.get('code_blocks', [])
            if code_blocks:
                output.append(f"\n## Code Examples ({len(code_blocks)} found)")
                for i, block in enumerate(code_blocks[:3]):  # Show first 3
                    output.append(f"\n### Example {i+1} ({block['language']})")
                    output.append(f"```{block['language']}")
                    output.append(block['code'][:500] + "..." if len(block['code']) > 500 else block['code'])
                    output.append("```")
            
            # Show content (truncated)
            content = doc_data.get('content', '')
            if content:
                output.append("\n## Content")
                if len(content) > 1000:
                    output.append(content[:1000] + "...")
                    output.append(f"\n*Content truncated. Full content is {len(content)} characters.*")
                else:
                    output.append(content)
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error getting documentation section: {e}")
            return f"Error getting documentation section: {str(e)}"
    
    async def list_topics(self) -> str:
        """List available documentation topics and sections"""
        try:
            topics = self.mdx_parser.list_topics()
            
            if not topics:
                return "No documentation topics found"
            
            output = [f"# BigCommerce Documentation Topics ({len(topics)} total)\n"]
            
            # Group by top-level directory
            topics_by_category = {}
            for topic in topics:
                parts = topic['path'].split('/')
                category = parts[0] if len(parts) > 1 else 'root'
                if category not in topics_by_category:
                    topics_by_category[category] = []
                topics_by_category[category].append(topic)
            
            for category, category_topics in topics_by_category.items():
                output.append(f"## {category.title()} ({len(category_topics)} topics)")
                
                for topic in category_topics[:10]:  # Limit per category
                    output.append(f"- **{topic['title']}** (`{topic['path']}`)")
                    if topic.get('description'):
                        desc = topic['description'][:100] + "..." if len(topic['description']) > 100 else topic['description']
                        output.append(f"  {desc}")
                
                if len(category_topics) > 10:
                    output.append(f"  ... and {len(category_topics) - 10} more topics")
                
                output.append("")  # Empty line
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error listing topics: {e}")
            return f"Error listing topics: {str(e)}"
    
    async def get_code_examples(self, topic: str, language: Optional[str] = None) -> str:
        """Get code examples for specific use cases"""
        try:
            # Search for documentation related to the topic
            search_results = self.mdx_parser.search_documentation(topic, limit=5)
            
            if not search_results:
                return f"No code examples found for topic: '{topic}'"
            
            output = [f"# Code Examples for '{topic}'\n"]
            
            all_code_blocks = []
            
            for result in search_results:
                doc_data = result['data']
                code_blocks = doc_data.get('code_blocks', [])
                
                for block in code_blocks:
                    # Filter by language if specified
                    if language and block['language'].lower() != language.lower():
                        continue
                    
                    all_code_blocks.append({
                        'language': block['language'],
                        'code': block['code'],
                        'source': doc_data.get('title', result['path'])
                    })
            
            if not all_code_blocks:
                return f"No code examples found for topic: '{topic}'" + (f" in language: {language}" if language else "")
            
            # Group by language
            examples_by_lang = {}
            for block in all_code_blocks:
                lang = block['language']
                if lang not in examples_by_lang:
                    examples_by_lang[lang] = []
                examples_by_lang[lang].append(block)
            
            for lang, examples in examples_by_lang.items():
                output.append(f"## {lang.upper()} Examples")
                
                for i, example in enumerate(examples[:3]):  # Limit per language
                    output.append(f"\n### Example {i+1} (from {example['source']})")
                    output.append(f"```{example['language']}")
                    output.append(example['code'])
                    output.append("```")
                
                if len(examples) > 3:
                    output.append(f"\n*... and {len(examples) - 3} more {lang} examples*")
                
                output.append("")  # Empty line
            
            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Error getting code examples: {e}")
            return f"Error getting code examples: {str(e)}" 