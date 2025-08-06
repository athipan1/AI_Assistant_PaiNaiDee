#!/usr/bin/env python3
"""
Run All Tests for AI Assistant PaiNaiDee
========================================

This script runs all automated tests for the AI Assistant PaiNaiDee project.
It provides a convenient way to execute the complete test suite.

Usage:
    python tests/run_all_tests.py

Requirements:
    - pytest
    - pytest-asyncio
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def main():
    """Run all tests in the project."""
    print("🧪 AI Assistant PaiNaiDee - Running All Tests")
    print("=" * 50)
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "painaidee_ai_assistant" / "tests"
    
    # Change to project root
    os.chdir(project_root)
    
    # Check if pytest is installed
    try:
        subprocess.run([sys.executable, "-c", "import pytest"], 
                      check=True, capture_output=True)
        print("✅ pytest is available")
    except subprocess.CalledProcessError:
        print("❌ pytest not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", 
                          "pytest", "pytest-asyncio"], check=True)
            print("✅ pytest installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install pytest: {e}")
            return 1
    
    # Check if tests directory exists
    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        return 1
    
    print(f"📁 Tests directory: {tests_dir}")
    print(f"🔍 Available test files:")
    
    # List all test files
    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        print("⚠️  No test files found in tests directory")
        return 0
    
    for test_file in test_files:
        print(f"   - {test_file.name}")
    
    print("\n🚀 Starting test execution...")
    print("-" * 50)
    
    # Run pytest with appropriate options
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "-x",  # Stop on first failure
    ]
    
    # Add coverage if available
    try:
        subprocess.run([sys.executable, "-c", "import pytest_cov"], 
                      check=True, capture_output=True)
        cmd.extend(["--cov=painaidee_ai_assistant", "--cov-report=term-missing"])
        print("📊 Coverage reporting enabled")
    except subprocess.CalledProcessError:
        print("ℹ️  Coverage reporting not available (pytest-cov not installed)")
    
    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("\n🎉 All tests passed successfully!")
            return 0
        else:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")
            return result.returncode
            
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)