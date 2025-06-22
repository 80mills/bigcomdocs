"""Parser for MDX documentation files - Optimized with lazy loading"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class MDXParser:
    """Parser for MDX documentation files with lazy loading"""
    
    def __init__(self, docs_path: Path, lazy_load: bool = True):
        self.docs_path = docs_path
        self.lazy_load = lazy_load
        self.documentation = {}
        self._file_map = {}  # Map doc paths to file paths
        
        if not lazy_load:
            # Legacy behavior - load everything at once
            import asyncio
            asyncio.create_task(self.load_all_docs())
        else:
            # Build file map for lazy loading
            self._build_file_map()
    
    def _build_file_map(self):
        """Build a map of documentation paths to file paths without loading content"""
        if not self.docs_path.exists():
            logger.warning(f"Docs path does not exist: {self.docs_path}")
            return
        
        # Find all MDX files
        mdx_files = list(self.docs_path.glob("**/*.mdx"))
        md_files = list(self.docs_path.glob("**/*.md"))
        all_files = mdx_files + md_files
        
        for file_path in all_files:
            # Create a relative path key
            rel_path = str(file_path.relative_to(self.docs_path))
            self._file_map[rel_path] = file_path
            logger.debug(f"Mapped doc '{rel_path}' to file: {file_path}")
    
    async def load_doc(self, doc_path: str) -> Optional[Dict[str, Any]]:
        """Load a specific documentation file on demand"""
        # Check if already loaded
        if doc_path in self.documentation:
            return self.documentation[doc_path]
        
        # Check if file exists in map
        if doc_path not in self._file_map:
            logger.warning(f"Doc '{doc_path}' not found in file map")
            return None
        
        file_path = self._file_map[doc_path]
        doc_data = await self._parse_mdx_file(file_path)
        
        if doc_data:
            self.documentation[doc_path] = doc_data
            logger.info(f"Lazy loaded documentation: {doc_path}")
            return doc_data
        
        return None
    
    async def load_essential_docs(self):
        """Load only essential documentation files"""
        essential_paths = [
            'api-docs/getting-started/api-rate-limits.mdx',
            'integrations/apps/quick-start.mdx',
            'start/intro-to-bigcommerce.mdx',
            'store-operations/catalog/index.mdx',
            'store-operations/catalog/inventory-adjustments.mdx'
        ]
        
        for path in essential_paths:
            if path in self._file_map:
                await self.load_doc(path)
    
    async def load_all_docs(self) -> Dict[str, Any]:
        """Load all MDX documentation files (legacy method)"""
        docs = {}
        
        if not self.docs_path.exists():
            logger.warning(f"Docs path does not exist: {self.docs_path}")
            return docs
        
        # Find all MDX files
        mdx_files = list(self.docs_path.glob("**/*.mdx"))
        md_files = list(self.docs_path.glob("**/*.md"))
        all_files = mdx_files + md_files
        
        for file_path in all_files:
            try:
                # Create a relative path key
                rel_path = str(file_path.relative_to(self.docs_path))
                doc_data = await self._parse_mdx_file(file_path)
                
                if doc_data:
                    docs[rel_path] = doc_data
                    logger.debug(f"Loaded documentation: {rel_path}")
                
            except Exception as e:
                logger.error(f"Error loading doc file {file_path}: {e}")
        
        self.documentation = docs
        return docs
    
    @lru_cache(maxsize=100)
    async def _parse_mdx_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single MDX file with caching"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                raw_content = file.read()
            
            # Parse frontmatter manually
            metadata = {}
            content = raw_content
            
            if raw_content.startswith('---'):
                parts = raw_content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    content = parts[2].strip()
                    
                    # Basic YAML parsing
                    for line in frontmatter_text.split('\n'):
                        if ':' in line and not line.strip().startswith('#'):
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            
                            # Handle arrays
                            if value.startswith('[') and value.endswith(']'):
                                value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                            
                            metadata[key] = value
                
                # Extract title from metadata or content
                title = metadata.get('title', '')
                if not title:
                    # Try to extract from first # heading
                    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if title_match:
                        title = title_match.group(1)
                
                # Extract headings
                headings = self._extract_headings(content)
                
                # Extract code blocks
                code_blocks = self._extract_code_blocks(content)
                
                return {
                    'title': title,
                    'description': metadata.get('description', ''),
                    'keywords': metadata.get('keywords', []),
                    'content': content,
                    'metadata': metadata,
                    'headings': headings,
                    'code_blocks': code_blocks,
                    'file_path': str(file_path)
                }
                
        except Exception as e:
            logger.error(f"Error parsing MDX file {file_path}: {e}")
            return None
    
    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """Extract headings from markdown content"""
        headings = []
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        for match in heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2)
            headings.append({
                'level': level,
                'text': text
            })
        
        return headings
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract code blocks from markdown content"""
        code_blocks = []
        code_block_pattern = re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL)
        
        for match in code_block_pattern.finditer(content):
            language = match.group(1) or 'text'
            code = match.group(2)
            code_blocks.append({
                'language': language,
                'code': code
            })
        
        return code_blocks
    
    def search_documentation(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documentation (only searches loaded docs in lazy mode)"""
        results = []
        query_lower = query.lower()
        
        # In lazy mode, only search loaded docs
        docs_to_search = self.documentation
        
        for doc_path, doc_data in docs_to_search.items():
            score = 0
            
            # Check title
            if query_lower in doc_data.get('title', '').lower():
                score += 10
            
            # Check description
            if query_lower in doc_data.get('description', '').lower():
                score += 7
            
            # Check keywords
            keywords = doc_data.get('keywords', [])
            if any(query_lower in keyword.lower() for keyword in keywords):
                score += 8
            
            # Check content (limited)
            content = doc_data.get('content', '')[:1000]  # Check first 1000 chars
            if query_lower in content.lower():
                score += 5
            
            if score > 0:
                results.append({
                    'path': doc_path,
                    'score': score,
                    'data': doc_data
                })
        
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def get_documentation(self, doc_path: str) -> Optional[Dict[str, Any]]:
        """Get specific documentation (loads if needed in lazy mode)"""
        if self.lazy_load and doc_path not in self.documentation:
            # Try to load it
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use asyncio.run
                return None  # Or handle this differently
            else:
                asyncio.run(self.load_doc(doc_path))
        
        return self.documentation.get(doc_path)
    
    def list_topics(self) -> List[Dict[str, str]]:
        """List available documentation topics"""
        topics = []
        
        # In lazy mode, use file map
        if self.lazy_load:
            for doc_path in self._file_map.keys():
                # Extract topic info from path
                parts = doc_path.split('/')
                category = parts[0] if parts else 'root'
                
                # Try to get title from loaded docs
                title = 'Unknown'
                if doc_path in self.documentation:
                    title = self.documentation[doc_path].get('title', doc_path)
                else:
                    # Use filename as title
                    title = Path(doc_path).stem.replace('-', ' ').title()
                
                topics.append({
                    'path': doc_path,
                    'title': title,
                    'category': category,
                    'loaded': doc_path in self.documentation
                })
        else:
            # Use loaded docs
            for doc_path, doc_data in self.documentation.items():
                parts = doc_path.split('/')
                category = parts[0] if parts else 'root'
                
                topics.append({
                    'path': doc_path,
                    'title': doc_data.get('title', doc_path),
                    'description': doc_data.get('description', ''),
                    'category': category
                })
        
        return sorted(topics, key=lambda x: x['path']) 