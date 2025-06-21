"""Parser for MDX documentation files"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class MDXParser:
    """Parser for MDX documentation files"""
    
    def __init__(self, docs_path: Path):
        self.docs_path = docs_path
        self.documentation = {}
    
    async def load_all_docs(self) -> Dict[str, Any]:
        """Load all MDX documentation files"""
        docs = {}
        
        if not self.docs_path.exists():
            logger.warning(f"Documentation path does not exist: {self.docs_path}")
            return docs
        
        # Find all MDX files
        mdx_files = list(self.docs_path.glob("**/*.mdx")) + list(self.docs_path.glob("**/*.md"))
        
        for mdx_file in mdx_files:
            try:
                doc_data = await self._load_doc_file(mdx_file)
                if doc_data:
                    relative_path = str(mdx_file.relative_to(self.docs_path))
                    docs[relative_path] = doc_data
                    logger.info(f"Loaded documentation: {relative_path}")
                
            except Exception as e:
                logger.error(f"Error loading documentation file {mdx_file}: {e}")
        
        self.documentation = docs
        return docs
    
    async def _load_doc_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a single MDX documentation file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extract frontmatter (basic implementation)
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    content = parts[2].strip()
                    
                    # Parse basic YAML frontmatter
                    for line in frontmatter_text.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip().strip('"\'')
            
            # Extract title from frontmatter or first h1
            title = frontmatter.get('title', '')
            if not title:
                title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1)
            
            # Extract headings for structure
            headings = []
            for match in re.finditer(r'^(#{1,6})\s+(.+)', content, re.MULTILINE):
                level = len(match.group(1))
                heading_text = match.group(2)
                headings.append({
                    'level': level,
                    'text': heading_text,
                    'line': content[:match.start()].count('\n') + 1
                })
            
            # Extract code blocks
            code_blocks = []
            for match in re.finditer(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL):
                language = match.group(1) or 'text'
                code = match.group(2)
                code_blocks.append({
                    'language': language,
                    'code': code
                })
            
            return {
                'title': title,
                'content': content,
                'frontmatter': frontmatter,
                'headings': headings,
                'code_blocks': code_blocks,
                'file_path': str(file_path),
                'description': frontmatter.get('description', ''),
                'keywords': frontmatter.get('keywords', '').split(',') if frontmatter.get('keywords') else []
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def get_documentation(self, doc_path: str) -> Optional[Dict[str, Any]]:
        """Get a specific documentation file"""
        return self.documentation.get(doc_path)
    
    def search_documentation(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documentation content"""
        results = []
        query_lower = query.lower()
        
        for doc_path, doc_data in self.documentation.items():
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
            
            # Check keywords
            for keyword in doc_data.get('keywords', []):
                if query_lower in keyword.lower():
                    score += 8
            
            if score > 0:
                results.append({
                    'path': doc_path,
                    'score': score,
                    'data': doc_data
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def list_topics(self) -> List[Dict[str, Any]]:
        """List all documentation topics"""
        topics = []
        
        for doc_path, doc_data in self.documentation.items():
            topic = {
                'path': doc_path,
                'title': doc_data.get('title', doc_path),
                'description': doc_data.get('description', ''),
                'keywords': doc_data.get('keywords', []),
                'headings_count': len(doc_data.get('headings', []))
            }
            topics.append(topic)
        
        return sorted(topics, key=lambda x: x['path']) 