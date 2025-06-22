#!/usr/bin/env python3
"""
Basic test script to verify the BigCommerce MCP Server setup.
This script can run without pytest to check basic functionality.
"""
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all main modules can be imported."""
    print("Testing imports...")
    
    try:
        from server import BigCommerceMCPServer
        print("✅ BigCommerceMCPServer imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import BigCommerceMCPServer: {e}")
        return False
    
    try:
        from config import Config
        print("✅ Config imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Config: {e}")
        return False
    
    try:
        from tools.api_tools import APITools
        print("✅ APITools imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import APITools: {e}")
        return False
    
    try:
        from tools.documentation_tools import DocumentationTools
        print("✅ DocumentationTools imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import DocumentationTools: {e}")
        return False
    
    try:
        from tools.schema_tools import SchemaTools
        print("✅ SchemaTools imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SchemaTools: {e}")
        return False
    
    return True


def test_project_structure():
    """Test that the project has the expected structure."""
    print("\nTesting project structure...")
    
    project_root = Path(__file__).parent
    
    required_files = [
        "src/server.py",
        "src/config.py",
        "src/tools/api_tools.py",
        "src/tools/documentation_tools.py",
        "src/tools/schema_tools.py",
        "requirements.txt",
        "pyproject.toml",
        "README.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist


def test_config_creation():
    """Test that Config can be created."""
    print("\nTesting Config creation...")
    
    try:
        from config import Config
        config = Config()
        print("✅ Config created successfully")
        print(f"   - docs_path: {config.docs_path}")
        print(f"   - cache_path: {config.cache_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create Config: {e}")
        return False


def test_dependencies():
    """Test that required dependencies are available."""
    print("\nTesting dependencies...")
    
    required_packages = [
        "mcp",
        "pyyaml",
        "markdown",
        "python-frontmatter",
        "whoosh",
        "aiofiles",
        "pydantic",
        "click"
    ]
    
    all_available = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_available = False
    
    return all_available


def main():
    """Run all basic tests."""
    print("🧪 Running BigCommerce MCP Server Basic Tests\n")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Project Structure", test_project_structure),
        ("Imports", test_imports),
        ("Config Creation", test_config_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The setup looks good.")
        print("\nNext steps:")
        print("1. Install test dependencies: pip install -e .[test]")
        print("2. Run full test suite: python run_tests.py")
        print("3. Start the server: python -m src.server")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the setup.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 