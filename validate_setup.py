#!/usr/bin/env python3
"""
Basic validation script for LLM Logic Trading System
Tests core functionality that doesn't require external dependencies or network access.
"""
import json
import os
import sys
from pathlib import Path

def test_project_structure():
    """Test that all required files and directories exist."""
    print("🔍 Testing project structure...")
    
    required_files = [
        'README.md',
        '.env.example', 
        '.gitignore',
        'requirements.txt',
        'main.py',
        'demo.py',
        'config/trading_config.json',
        'config/trading_config.example.json',
        'docs/RUNBOOK.md',
        '.github/workflows/ci.yml'
    ]
    
    required_dirs = [
        'src/',
        'src/data_sources/',
        'src/portfolio/',
        'src/risk/',
        'src/llm/',
        'src/utils/',
        'tests/',
        'config/',
        'docs/'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Required file missing: {file_path}")
        print(f"  ✓ {file_path}")
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            raise FileNotFoundError(f"Required directory missing: {dir_path}")
        print(f"  ✓ {dir_path}")
    
    print("✅ Project structure is complete")

def test_config_files():
    """Test configuration files are valid JSON."""
    print("\n🔍 Testing configuration files...")
    
    config_files = [
        'config/trading_config.json',
        'config/trading_config.example.json'
    ]
    
    for config_file in config_files:
        with open(config_file, 'r') as f:
            config = json.load(f)
            assert isinstance(config, dict), f"{config_file} must be a JSON object"
            print(f"  ✓ {config_file} is valid JSON")
    
    # Test specific config structure
    with open('config/trading_config.json', 'r') as f:
        config = json.load(f)
        required_sections = ['trading', 'risk_management', 'llm']
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"
            print(f"  ✓ Has {section} section")
    
    print("✅ Configuration files are valid")

def test_env_example():
    """Test .env.example has required variables."""
    print("\n🔍 Testing .env.example...")
    
    with open('.env.example', 'r') as f:
        content = f.read()
    
    required_vars = [
        'OPENAI_API_KEY',
        'COINBASE_API_KEY', 
        'COINBASE_API_SECRET',
        'COINBASE_API_PASSPHRASE',
        'COINBASE_USE_SANDBOX',
        'LOG_LEVEL'
    ]
    
    for var in required_vars:
        assert var in content, f"Missing required environment variable: {var}"
        print(f"  ✓ {var}")
    
    print("✅ .env.example contains required variables")

def test_documentation():
    """Test documentation files exist and have content."""
    print("\n🔍 Testing documentation...")
    
    # Test README.md
    with open('README.md', 'r') as f:
        readme_content = f.read()
        assert 'LLM Logic Trading System' in readme_content
        assert 'Installation' in readme_content
        assert 'Usage' in readme_content
        print("  ✓ README.md has required sections")
    
    # Test RUNBOOK.md
    with open('docs/RUNBOOK.md', 'r') as f:
        runbook_content = f.read()
        assert 'Prerequisites' in runbook_content
        assert 'Operating Modes' in runbook_content
        assert 'Troubleshooting' in runbook_content
        print("  ✓ RUNBOOK.md has required sections")
    
    print("✅ Documentation is complete")

def test_ci_workflow():
    """Test CI workflow file is valid."""
    print("\n🔍 Testing CI workflow...")
    
    with open('.github/workflows/ci.yml', 'r') as f:
        content = f.read()
        # Basic structure checks
        assert 'name: CI' in content
        assert 'on:' in content
        assert 'jobs:' in content
        assert 'python-version:' in content
        print("  ✓ CI workflow has basic structure")
    
    print("✅ CI workflow is valid")

def test_gitignore():
    """Test .gitignore covers important files."""
    print("\n🔍 Testing .gitignore...")
    
    with open('.gitignore', 'r') as f:
        content = f.read()
    
    important_ignores = ['.env', '__pycache__', '*.log']
    
    for ignore_pattern in important_ignores:
        assert ignore_pattern in content, f"Missing important ignore pattern: {ignore_pattern}"
        print(f"  ✓ Ignores {ignore_pattern}")
    
    print("✅ .gitignore is properly configured")

def main():
    """Run all validation tests."""
    print("🚀 Running LLM Logic Trading System validation tests")
    print("=" * 60)
    
    try:
        test_project_structure()
        test_config_files()
        test_env_example()
        test_documentation()
        test_ci_workflow()
        test_gitignore()
        
        print("\n🎉 All validation tests passed!")
        print("✅ Repository is properly configured for development")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and fill in your API keys")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run: python demo.py (no API keys needed)")
        print("4. Run: python main.py --mode analyze --symbols BTC ETH")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())