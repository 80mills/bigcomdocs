"""
Pytest configuration and fixtures for BigCommerce MCP Server tests.
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.server import BigCommerceMCPServer
from src.config import Config


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory with sample documentation files."""
    temp_dir = tempfile.mkdtemp()
    docs_dir = Path(temp_dir) / "docs"
    docs_dir.mkdir()
    
    # Create sample OpenAPI spec
    api_dir = docs_dir / "api"
    api_dir.mkdir()
    sample_spec = api_dir / "products.v3.yml"
    sample_spec.write_text("""
openapi: 3.0.0
info:
  title: Products API
  version: 3.0.0
paths:
  /catalog/products:
    get:
      summary: Get Products
      operationId: getProducts
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Product'
components:
  schemas:
    Product:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        price:
          type: number
""")
    
    # Create sample MDX documentation
    mdx_dir = docs_dir / "store-operations"
    mdx_dir.mkdir()
    sample_mdx = mdx_dir / "products.mdx"
    sample_mdx.write_text("""
---
title: Products API Guide
description: Learn how to work with products in BigCommerce
---

# Products API Guide

This guide covers how to work with products using the BigCommerce API.

## Getting Started

To get started with products, you'll need to authenticate your requests.

\`\`\`javascript
const response = await fetch('/catalog/products', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
});
\`\`\`

## Examples

Here are some common examples of working with products.
""")
    
    yield docs_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def config(temp_docs_dir):
    """Create a test configuration."""
    return Config(
        docs_path=temp_docs_dir,
        cache_path=Path(temp_docs_dir) / ".cache"
    )


@pytest.fixture
async def mcp_server(config):
    """Create an MCP server instance for testing."""
    server = BigCommerceMCPServer(config)
    await server.initialize()
    yield server
    # Cleanup - no close method needed for SearchIndexer


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    client = AsyncMock()
    client.call_tool = AsyncMock()
    client.list_tools = AsyncMock()
    return client


@pytest.fixture
def sample_api_response():
    """Sample API response data for testing."""
    return {
        "data": [
            {
                "id": 1,
                "name": "Sample Product",
                "price": 29.99,
                "type": "physical"
            }
        ],
        "meta": {
            "pagination": {
                "total": 1,
                "count": 1,
                "per_page": 50,
                "current_page": 1,
                "total_pages": 1
            }
        }
    }


@pytest.fixture
def sample_documentation_response():
    """Sample documentation response data for testing."""
    return {
        "title": "Products API Guide",
        "content": "This guide covers how to work with products using the BigCommerce API.",
        "path": "store-operations/products.mdx",
        "sections": [
            {
                "title": "Getting Started",
                "content": "To get started with products, you'll need to authenticate your requests."
            }
        ]
    }


@pytest.fixture
def sample_schema_response():
    """Sample schema response data for testing."""
    return {
        "name": "Product",
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "price": {"type": "number"}
        },
        "required": ["id", "name"]
    }


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 