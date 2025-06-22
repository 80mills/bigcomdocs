#!/usr/bin/env python3
"""
Test runner for BigCommerce MCP Server
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", coverage=False, verbose=False):
    """Run tests with specified options"""
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if test_type == "unit":
        cmd.extend(["tests/unit/"])
    elif test_type == "integration":
        cmd.extend(["tests/integration/"])
    elif test_type == "all":
        cmd.extend(["tests/"])
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    if verbose:
        cmd.append("-v")
    
    # Add some useful pytest options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print(f"Running tests: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("pytest not found. Please install test dependencies:")
        print("pip install -e .[test]")
        return False


def install_test_dependencies():
    """Install test dependencies"""
    print("Installing test dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", ".[test]"
        ], check=True)
        print("Test dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install test dependencies")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run BigCommerce MCP Server tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration"], 
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--install-deps", 
        action="store_true",
        help="Install test dependencies first"
    )
    
    args = parser.parse_args()
    
    if args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)
    
    success = run_tests(args.type, args.coverage, args.verbose)
    
    if success:
        print("\n✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 