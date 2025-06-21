# BigCommerce MCP Server

A Model Context Protocol (MCP) server that provides AI models with access to BigCommerce API documentation, enabling intelligent assistance for developers working with BigCommerce APIs.

## Features

- **API Specification Access**: Search and browse all BigCommerce OpenAPI specifications
- **Documentation Search**: Full-text search across BigCommerce documentation (MDX files)
- **Schema Exploration**: Access to JSON schemas and data models
- **Code Examples**: Extract and search code examples from documentation
- **Intelligent Search**: Contextual search with relevance scoring

## Available Tools

### API Tools
- `search_api_endpoints` - Search for API endpoints across all BigCommerce APIs
- `get_api_spec` - Get complete OpenAPI specification for a specific API
- `get_endpoint_details` - Get detailed information about a specific API endpoint
- `list_api_categories` - List all available API categories

### Documentation Tools
- `search_documentation` - Search across all BigCommerce documentation
- `get_documentation_section` - Get specific documentation section content
- `list_documentation_topics` - List available documentation topics and sections
- `get_code_examples` - Get code examples for specific use cases

### Schema Tools
- `get_schema` - Get JSON schema for BigCommerce data models
- `search_schemas` - Search for schemas by name or properties

## Installation

1. **Clone or set up the directory structure**:
   ```bash
   # Ensure you're in the bigcommerce docs repository
   cd /path/to/bigcomdocs
   ```

2. **Install dependencies**:
   ```bash
   cd bigcommerce-mcp-server
   pip install -r requirements.txt
   ```

3. **Install in development mode** (optional):
   ```bash
   pip install -e .
   ```

## Usage

### Running the Server

Run the MCP server from the BigCommerce documentation repository root:

```bash
cd bigcommerce-mcp-server
python -m src.server /path/to/bigcomdocs
```

Or if you installed it as a package:

```bash
bigcommerce-mcp-server /path/to/bigcomdocs
```

### Example Queries

Once connected to an MCP client, you can use queries like:

- "Search for widget creation endpoints"
- "Get the complete Orders API specification"
- "Show me code examples for creating products"
- "Find documentation about webhooks"
- "Get the schema for product objects"

## Architecture

The server consists of several components:

### Parsers
- **OpenAPIParser**: Parses OpenAPI YAML specifications
- **MDXParser**: Parses MDX documentation files
- **SchemaParser**: Parses JSON schema files

### Indexers
- **SearchIndexer**: Provides search functionality across all content
- **ContentIndexer**: Manages content indexing for fast retrieval

### Tools
- **APITools**: Handles API-related queries
- **DocumentationTools**: Manages documentation search and retrieval
- **SchemaTools**: Provides schema access and search

## Development

### Project Structure

```
bigcommerce-mcp-server/
├── src/
│   ├── server.py              # Main MCP server
│   ├── config.py             # Configuration
│   ├── parsers/              # Content parsers
│   ├── indexers/             # Search indexing
│   ├── tools/                # MCP tools
│   └── utils/                # Utilities
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

### Adding New Features

1. **New Parser**: Add parsers in `src/parsers/` for new content types
2. **New Tools**: Implement new MCP tools in `src/tools/`
3. **Enhanced Search**: Improve indexing in `src/indexers/`

### Testing

```bash
# Basic functionality test
python -c "from src.server import BigCommerceMCPServer; print('Import successful')"

# Run with verbose logging
PYTHONPATH=. python src/server.py --verbose
```

## Configuration

The server can be configured through the `Config` class in `src/config.py`. Available options:

- `docs_path`: Path to BigCommerce documentation
- `cache_path`: Path for caching indexes
- `max_search_results`: Maximum search results per query
- `enable_semantic_search`: Enable/disable semantic search features

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`
2. **Path Issues**: Make sure the docs path points to the BigCommerce documentation root
3. **Permission Issues**: Ensure read access to documentation files

### Logging

Enable debug logging:

```bash
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.server import main
import asyncio
asyncio.run(main())
"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project follows the same license as the BigCommerce documentation repository.

## Future Enhancements

- Advanced semantic search with embeddings
- Real-time documentation updates
- Interactive code generation
- API testing capabilities
- Multi-language support for examples
- Caching improvements for better performance 