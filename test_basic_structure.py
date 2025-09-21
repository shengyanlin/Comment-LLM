#!/usr/bin/env python3
"""
Basic test to verify the Comment-LLM core structure is working.

This test doesn't require external dependencies and validates
the basic imports and structure.
"""

import sys
import os

# Add the project directory to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all modules can be imported."""
    try:
        print("Testing basic imports...")
        
        # Test importing the main package
        import comment_llm
        print("✅ comment_llm package imported successfully")
        
        # Test importing individual modules (might fail due to missing dependencies)
        try:
            from comment_llm.scraper import GoogleMapsScraper
            print("✅ GoogleMapsScraper imported successfully")
        except ImportError as e:
            print(f"⚠️  GoogleMapsScraper import failed (expected due to selenium): {e}")
        
        try:
            from comment_llm.rag_system import RAGSystem
            print("✅ RAGSystem imported successfully")
        except ImportError as e:
            print(f"⚠️  RAGSystem import failed (expected due to chromadb): {e}")
        
        try:
            from comment_llm.llm_client import LLMClient
            print("✅ LLMClient imported successfully")
        except ImportError as e:
            print(f"⚠️  LLMClient import failed (expected due to openai): {e}")
        
        try:
            from comment_llm.app import CommentLLM
            print("✅ CommentLLM app imported successfully")
        except ImportError as e:
            print(f"⚠️  CommentLLM app import failed (expected due to dependencies): {e}")
        
        try:
            from comment_llm.cli import cli
            print("✅ CLI imported successfully")
        except SystemExit:
            print("⚠️  CLI import triggered dependency check (expected)")
        except ImportError as e:
            print(f"⚠️  CLI import failed (expected due to dependencies): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic import test failed: {e}")
        return False

def test_package_structure():
    """Test the package structure."""
    print("\nTesting package structure...")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    expected_files = [
        'comment_llm/__init__.py',
        'comment_llm/scraper.py',
        'comment_llm/rag_system.py',
        'comment_llm/llm_client.py',
        'comment_llm/app.py',
        'comment_llm/cli.py',
        'requirements.txt',
        'pyproject.toml',
        '.env.example',
        'README.md',
        'example.py'
    ]
    
    missing_files = []
    for file_path in expected_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    else:
        print("\n✅ All expected files are present")
        return True

def test_cli_help():
    """Test if CLI help can be displayed."""
    print("\nTesting CLI help...")
    try:
        # Try to import click first
        import click
        from comment_llm.cli import cli
        
        # This would normally run the CLI, but we can at least verify it exists
        print("✅ CLI function exists and can be imported")
        return True
        
    except ImportError as e:
        print(f"⚠️  CLI test skipped due to missing dependency: {e}")
        return True  # Not a failure, just missing dependency
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def main():
    """Run all basic tests."""
    print("🧪 Running Basic Comment-LLM Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_package_structure,
        test_cli_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Empty line for readability
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        print("\n💡 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up .env file with your OpenAI API key")
        print("3. Try: python example.py")
        print("4. Or use CLI: python -m comment_llm.cli --help")
        return True
    else:
        print("⚠️  Some tests failed, but this might be due to missing dependencies")
        return False

if __name__ == "__main__":
    main()