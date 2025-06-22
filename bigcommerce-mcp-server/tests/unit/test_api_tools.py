"""
Unit tests for API tools.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from src.tools.api_tools import APITools


class TestAPITools:
    """Test cases for APITools class."""
    
    @pytest.fixture
    def api_tools(self):
        """Create an APITools instance for testing."""
        mock_parser = MagicMock()
        mock_indexer = MagicMock()
        mock_indexer.api_index = {
            "products": {
                "name": "products",
                "title": "Products API",
                "endpoints": [
                    {
                        "path": "/catalog/products",
                        "method": "GET",
                        "summary": "Get Products",
                        "operationId": "getProducts"
                    }
                ]
            }
        }
        return APITools(mock_parser, mock_indexer)
    
    def test_search_endpoints(self, api_tools):
        """Test searching for API endpoints."""
        # Mock the parser's search_endpoints method
        api_tools.openapi_parser.search_endpoints.return_value = [
            {
                "api_name": "products",
                "path": "/catalog/products",
                "method": "GET",
                "summary": "Get Products"
            }
        ]
        
        results = api_tools.search_endpoints("products")
        
        assert "Found 1 endpoint(s)" in results
        assert "products" in results
    
    def test_get_api_spec(self, api_tools):
        """Test getting API specification."""
        # Mock the parser's get_spec method
        api_tools.openapi_parser.get_spec.return_value = {
            "name": "products",
            "title": "Products API",
            "endpoints": []
        }
        
        spec = api_tools.get_api_spec("products")
        
        assert "Products API" in spec
        assert "products" in spec
    
    def test_get_endpoint_details(self, api_tools):
        """Test getting endpoint details."""
        # Mock the parser's get_endpoint_details method
        api_tools.openapi_parser.get_endpoint_details.return_value = {
            "path": "/catalog/products",
            "method": "GET",
            "summary": "Get Products"
        }
        
        details = api_tools.get_endpoint_details("products", "/catalog/products", "GET")
        
        assert "Get Products" in details
        assert "/catalog/products" in details
    
    def test_list_categories(self, api_tools):
        """Test listing API categories."""
        # Mock the parser's list_api_categories method
        api_tools.openapi_parser.list_api_categories.return_value = [
            {
                "name": "products",
                "title": "Products API",
                "endpoint_count": 10
            }
        ]
        
        categories = api_tools.list_categories()
        
        assert "Products API" in categories
        assert "products" in categories
    
    def test_recommend_api_for_use_case(self, api_tools):
        """Test API recommendation for use cases."""
        # Test product management
        recommendation = api_tools.recommend_api_for_use_case("I need to manage products")
        assert "products" in recommendation
        assert "catalog" in recommendation
        
        # Test inventory
        recommendation = api_tools.recommend_api_for_use_case("I want to update inventory")
        assert "inventory" in recommendation
        
        # Test orders
        recommendation = api_tools.recommend_api_for_use_case("I need to process orders")
        assert "orders" in recommendation
    
    def test_get_bulk_operation_guide(self, api_tools):
        """Test bulk operation guide."""
        guide = api_tools.get_bulk_operation_guide("products")
        
        assert "bulk" in guide.lower()
        assert "batch" in guide.lower()
        assert "rate limits" in guide.lower()


class TestAPIToolsIntegration:
    """Integration tests for APITools with real data."""
    
    @pytest.fixture
    def api_tools_with_data(self, temp_docs_dir):
        """Create APITools with real documentation data."""
        from src.indexers.search_indexer import SearchIndexer
        from src.parsers.openapi_parser import OpenAPIParser
        
        # Create parser with reference path
        reference_path = temp_docs_dir / "api"
        parser = OpenAPIParser(reference_path)
        
        # Create search indexer
        indexer = SearchIndexer()
        
        return APITools(parser, indexer)
    
    @pytest.mark.asyncio
    async def test_search_with_real_data(self, api_tools_with_data):
        """Test search with real OpenAPI data."""
        # Load specs first
        await api_tools_with_data.openapi_parser.load_all_specs()
        
        results = api_tools_with_data.search_endpoints("products")
        
        # Should find products API if it exists
        assert isinstance(results, str)
    
    @pytest.mark.asyncio
    async def test_get_spec_with_real_data(self, api_tools_with_data):
        """Test getting API spec with real data."""
        # Load specs first
        await api_tools_with_data.openapi_parser.load_all_specs()
        
        spec = api_tools_with_data.get_api_spec("products")
        
        # Should return a string response
        assert isinstance(spec, str) 