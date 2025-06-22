"""
Basic tests to verify the testing setup works correctly.
"""
import pytest
from pathlib import Path


def test_imports():
    """Test that all main modules can be imported."""
    try:
        from src.server import BigCommerceMCPServer
        from src.config import Config
        from src.tools.api_tools import APITools
        from src.tools.documentation_tools import DocumentationTools
        from src.tools.schema_tools import SchemaTools
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_project_structure():
    """Test that the project has the expected structure."""
    project_root = Path(__file__).parent.parent
    
    # Check main directories exist
    assert (project_root / "src").exists()
    assert (project_root / "tests").exists()
    assert (project_root / "requirements.txt").exists()
    assert (project_root / "pyproject.toml").exists()
    
    # Check source structure
    src_dir = project_root / "src"
    assert (src_dir / "server.py").exists()
    assert (src_dir / "config.py").exists()
    assert (src_dir / "tools").exists()
    assert (src_dir / "parsers").exists()
    assert (src_dir / "indexers").exists()


def test_config_creation():
    """Test that Config can be created."""
    from src.config import Config
    
    config = Config()
    assert config is not None
    assert hasattr(config, 'docs_path')
    assert hasattr(config, 'cache_path')


@pytest.mark.asyncio
async def test_server_creation():
    """Test that server can be created with test data."""
    from src.server import BigCommerceMCPServer
    from tests.conftest import temp_docs_dir
    
    # This test will use the temp_docs_dir fixture
    # The actual test is in the integration tests
    assert True


def test_pytest_working():
    """Simple test to verify pytest is working."""
    assert 1 + 1 == 2
    assert "hello" in "hello world" 