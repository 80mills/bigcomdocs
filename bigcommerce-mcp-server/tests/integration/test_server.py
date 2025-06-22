"""
Integration tests for the BigCommerce MCP Server.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from src.server import BigCommerceMCPServer


class TestMCPServerIntegration:
    """Integration tests for the MCP server."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, mcp_server):
        """Test that the server initializes correctly."""
        assert mcp_server is not None
        assert hasattr(mcp_server, 'api_tools')
        assert hasattr(mcp_server, 'documentation_tools')
        assert hasattr(mcp_server, 'schema_tools')
    
    @pytest.mark.asyncio
    async def test_tool_registration(self, mcp_server):
        """Test that tools are properly registered."""
        # Check that tools are available
        assert mcp_server.api_tools is not None
        assert mcp_server.documentation_tools is not None
        assert mcp_server.schema_tools is not None
    
    @pytest.mark.asyncio
    async def test_api_search_functionality(self, mcp_server):
        """Test API search functionality with real data."""
        # Test searching for products
        result = await mcp_server.api_tools.search_endpoints("products")
        assert isinstance(result, str)
        
        # Test getting API spec
        result = await mcp_server.api_tools.get_api_spec("products")
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_documentation_search_functionality(self, mcp_server):
        """Test documentation search functionality with real data."""
        # Test searching documentation
        result = await mcp_server.documentation_tools.search_documentation("products")
        assert isinstance(result, str)
        
        # Test listing topics
        result = await mcp_server.documentation_tools.list_topics()
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_use_case_recommendation(self, mcp_server):
        """Test use case recommendation functionality."""
        # Test product management recommendation
        result = await mcp_server.api_tools.recommend_api_for_use_case("I need to manage products")
        assert isinstance(result, str)
        assert "products" in result.lower()
        
        # Test inventory management recommendation
        result = await mcp_server.api_tools.recommend_api_for_use_case("I want to update inventory")
        assert isinstance(result, str)
        assert "inventory" in result.lower()
    
    @pytest.mark.asyncio
    async def test_bulk_operation_guidance(self, mcp_server):
        """Test bulk operation guidance."""
        result = await mcp_server.api_tools.get_bulk_operation_guide("products")
        assert isinstance(result, str)
        assert "bulk" in result.lower()


class TestMCPServerWithRealData:
    """Integration tests with real BigCommerce documentation."""
    
    @pytest.mark.asyncio
    async def test_with_real_docs_directory(self):
        """Test server with the actual BigCommerce docs directory."""
        # Use the real docs directory from the parent project
        docs_path = Path(__file__).parent.parent.parent.parent / "docs"
        
        if docs_path.exists():
            server = BigCommerceMCPServer(docs_path)
            await server.initialize()
            
            # Test basic functionality
            result = await server.api_tools.search_endpoints("products")
            assert isinstance(result, str)
            
            result = await server.documentation_tools.search_documentation("authentication")
            assert isinstance(result, str)
        else:
            pytest.skip("Real docs directory not found")


class TestMCPServerPerformance:
    """Performance tests for the MCP server."""
    
    @pytest.mark.asyncio
    async def test_search_performance(self, mcp_server):
        """Test search performance with multiple queries."""
        import time
        
        queries = ["products", "orders", "customers", "inventory", "pricing"]
        
        start_time = time.time()
        for query in queries:
            await mcp_server.api_tools.search_endpoints(query)
            await mcp_server.documentation_tools.search_documentation(query)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete all searches in reasonable time
        assert total_time < 10.0  # 10 seconds max for 10 searches
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, mcp_server):
        """Test concurrent search operations."""
        async def search_operation(query):
            return await mcp_server.api_tools.search_endpoints(query)
        
        # Run multiple searches concurrently
        queries = ["products", "orders", "customers"]
        tasks = [search_operation(query) for query in queries]
        
        results = await asyncio.gather(*tasks)
        
        # All searches should complete successfully
        assert len(results) == len(queries)
        for result in results:
            assert isinstance(result, str) 