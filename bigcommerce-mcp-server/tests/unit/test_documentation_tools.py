"""
Unit tests for documentation tools.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from src.tools.documentation_tools import DocumentationTools


class TestDocumentationTools:
    """Test cases for DocumentationTools class."""
    
    @pytest.fixture
    def doc_tools(self):
        """Create a DocumentationTools instance for testing."""
        mock_parser = MagicMock()
        mock_indexer = MagicMock()
        mock_indexer.doc_index = {
            "store-operations/products.mdx": {
                "title": "Products API Guide",
                "content": "This guide covers how to work with products using the BigCommerce API.",
                "description": "Learn how to work with products in BigCommerce",
                "sections": [
                    {
                        "title": "Getting Started",
                        "content": "To get started with products, you'll need to authenticate your requests."
                    }
                ]
            }
        }
        return DocumentationTools(mock_parser, mock_indexer)
    
    def test_search_documentation(self, doc_tools):
        """Test searching documentation."""
        # Mock the parser's search_documentation method
        doc_tools.mdx_parser.search_documentation.return_value = [
            {
                "path": "store-operations/products.mdx",
                "data": {
                    "title": "Products API Guide",
                    "content": "This guide covers how to work with products using the BigCommerce API."
                }
            }
        ]
        
        results = doc_tools.search_documentation("products")
        
        assert "Found 1 documentation result(s)" in results
        assert "Products API Guide" in results
    
    def test_get_section(self, doc_tools):
        """Test getting a specific documentation section."""
        # Mock the parser's get_documentation method
        doc_tools.mdx_parser.get_documentation.return_value = {
            "title": "Products API Guide",
            "content": "This guide covers how to work with products using the BigCommerce API.",
            "headings": [
                {"level": 1, "text": "Getting Started"},
                {"level": 2, "text": "Authentication"}
            ],
            "code_blocks": [
                {"language": "javascript", "code": "const response = await fetch('/catalog/products');"}
            ]
        }
        
        section = doc_tools.get_section("store-operations/products.mdx")
        
        assert "Products API Guide" in section
        assert "Getting Started" in section
    
    def test_list_topics(self, doc_tools):
        """Test listing available documentation topics."""
        # Mock the parser's list_topics method
        doc_tools.mdx_parser.list_topics.return_value = [
            {
                "path": "store-operations/products.mdx",
                "title": "Products API Guide",
                "description": "Learn how to work with products in BigCommerce"
            }
        ]
        
        topics = doc_tools.list_topics()
        
        assert "BigCommerce Documentation Topics" in topics
        assert "Products API Guide" in topics
    
    def test_get_code_examples(self, doc_tools):
        """Test extracting code examples from documentation."""
        # Mock the parser's search_documentation method
        doc_tools.mdx_parser.search_documentation.return_value = [
            {
                "path": "store-operations/products.mdx",
                "data": {
                    "title": "Products API Guide",
                    "code_blocks": [
                        {"language": "javascript", "code": "const response = await fetch('/catalog/products');"}
                    ]
                }
            }
        ]
        
        examples = doc_tools.get_code_examples("products")
        
        assert "Code Examples for 'products'" in examples
        assert "javascript" in examples.lower()


class TestDocumentationToolsIntegration:
    """Integration tests for DocumentationTools with real data."""
    
    @pytest.fixture
    def doc_tools_with_data(self, temp_docs_dir):
        """Create DocumentationTools with real documentation data."""
        from src.indexers.search_indexer import SearchIndexer
        from src.parsers.mdx_parser import MDXParser
        
        # Create parser with docs path
        docs_path = temp_docs_dir
        parser = MDXParser(docs_path)
        
        # Create search indexer
        indexer = SearchIndexer()
        
        return DocumentationTools(parser, indexer)
    
    @pytest.mark.asyncio
    async def test_search_with_real_data(self, doc_tools_with_data):
        """Test search with real MDX data."""
        # Load docs first
        await doc_tools_with_data.mdx_parser.load_all_docs()
        
        results = doc_tools_with_data.search_documentation("products")
        
        # Should return a string response
        assert isinstance(results, str)
    
    @pytest.mark.asyncio
    async def test_get_section_with_real_data(self, doc_tools_with_data):
        """Test getting section with real data."""
        # Load docs first
        await doc_tools_with_data.mdx_parser.load_all_docs()
        
        section = doc_tools_with_data.get_section("store-operations/products.mdx")
        
        # Should return a string response
        assert isinstance(section, str) 