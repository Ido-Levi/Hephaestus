#!/usr/bin/env python3
"""Main test runner for Hephaestus integration tests."""

import asyncio
import sys
import os
import time
from datetime import datetime
import subprocess

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print a section header."""
    print("\n" + "-" * 60)
    print(f"  {title}")
    print("-" * 60)


async def check_prerequisites():
    """Check that all required services are running."""
    print_section("Checking Prerequisites")

    issues = []

    # Check Qdrant
    print("\n📍 Checking Qdrant...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:6333/collections")
            if response.status_code == 200:
                print("   ✅ Qdrant is running on port 6333")
            else:
                issues.append("Qdrant is not responding properly")
    except Exception as e:
        issues.append("Qdrant is not running. Start it with: docker run -p 6333:6333 qdrant/qdrant")

    # Check MCP Server
    print("\n📍 Checking MCP Server...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("   ✅ MCP Server is running on port 8000")
            else:
                issues.append("MCP Server is not responding properly")
    except Exception:
        print("   ⚠️  MCP Server is not running (optional for some tests)")
        print("      Start it with: python run_server.py")

    # Check environment variables
    print("\n📍 Checking environment variables...")
    from src.core.simple_config import Config
    config = Config()

    if not config.openai_api_key or config.openai_api_key.startswith("sk-"):
        print("   ✅ OpenAI API key is configured")
    else:
        issues.append("OpenAI API key is not configured in .env file")

    print(f"   ℹ️  LLM Model: {config.llm_model}")
    print(f"   ℹ️  Embedding Model: {config.embedding_model}")

    if issues:
        print("\n❌ Prerequisites check failed:")
        for issue in issues:
            print(f"   - {issue}")
        return False

    print("\n✅ All prerequisites met!")
    return True


async def run_test_module(module_name, description):
    """Run a single test module."""
    print_section(description)

    start_time = time.time()

    try:
        # Run the test module as a subprocess
        result = subprocess.run(
            [sys.executable, f"tests/{module_name}"],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout per test module
        )

        # Print the output
        print(result.stdout)

        if result.stderr and "ERROR" in result.stderr:
            print("Errors detected:")
            print(result.stderr)

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"\n✅ {description} passed ({elapsed:.1f}s)")
            return True
        else:
            print(f"\n❌ {description} failed ({elapsed:.1f}s)")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n❌ {description} timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"\n❌ {description} failed with error: {e}")
        return False


async def main():
    """Run all integration tests."""
    print_header("HEPHAESTUS INTEGRATION TEST SUITE")
    print(f"\n📅 Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check prerequisites
    if not await check_prerequisites():
        print("\n⚠️  Please fix the prerequisites before running tests")
        return False

    # Define test modules
    test_modules = [
        ("test_llm_interface.py", "LLM Interface Tests"),
        ("test_vector_store.py", "Vector Store Tests"),
        ("test_rag_system.py", "RAG System Tests"),
        ("test_mcp_server.py", "MCP Server Tests"),
    ]

    # Run each test module
    results = {}
    total_start = time.time()

    for module, description in test_modules:
        result = await run_test_module(module, description)
        results[description] = result
        await asyncio.sleep(1)  # Brief pause between test suites

    # Print summary
    print_header("TEST SUMMARY")

    total_elapsed = time.time() - total_start
    passed = sum(1 for r in results.values() if r)
    failed = len(results) - passed

    print(f"\n📊 Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")

    print(f"\n⏱️  Total time: {total_elapsed:.1f} seconds")
    print(f"📈 Passed: {passed}/{len(results)}")
    print(f"📉 Failed: {failed}/{len(results)}")

    if failed == 0:
        print("\n🎉 All tests passed! The RAG system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test suite(s) failed. Please review the errors above.")
        return False


def run_quick_test():
    """Run a quick smoke test."""
    print_header("QUICK SMOKE TEST")

    print("\n🔥 Running quick smoke test...")

    try:
        # Quick import test
        print("   Importing modules...")
        from src.memory.vector_store import VectorStoreManager
        from src.memory.rag import RAGSystem
        from src.interfaces.llm_interface import OpenAIProvider
        from src.core.simple_config import Config

        print("   ✅ All modules imported successfully")

        # Quick connection test
        print("   Testing connections...")
        config = Config()

        # Initialize components (but don't make API calls)
        vector_store = VectorStoreManager(embedding_dimension=config.embedding_dimension)
        print("   ✅ Vector store initialized")

        llm_provider = OpenAIProvider(
            api_key=config.openai_api_key,
            model=config.llm_model,
            embedding_model=config.embedding_model
        )
        print("   ✅ LLM provider initialized")

        print("\n✅ Smoke test passed! System appears to be configured correctly.")
        return True

    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Hephaestus integration tests")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test only")
    parser.add_argument("--module", help="Run specific test module (e.g., test_vector_store.py)")

    args = parser.parse_args()

    try:
        if args.quick:
            success = run_quick_test()
        elif args.module:
            # Run specific module
            print_header(f"Running {args.module}")
            success = asyncio.run(run_test_module(args.module, args.module))
        else:
            # Run all tests
            success = asyncio.run(main())

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        sys.exit(1)