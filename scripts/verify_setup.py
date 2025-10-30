#!/usr/bin/env python3
"""
Verify Hephaestus setup and dependencies.

Run this script after installation to ensure all dependencies are correctly installed
and there are no version conflicts.
"""
import sys
import subprocess


def check_python_version():
    """Check Python version (3.10+ required)"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major == 3 and version.minor >= 10:
        print("✅ Python version OK")
        return True
    else:
        print(f"❌ Python 3.10+ required, got {version.major}.{version.minor}")
        return False


def check_package_version(package_name, expected_version):
    """Check if package is installed with correct version"""
    try:
        result = subprocess.run(
            ["pip", "show", package_name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print(f"❌ {package_name} not installed")
            return False

        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                installed_version = line.split(':', 1)[1].strip()
                if installed_version == expected_version:
                    print(f"✅ {package_name}=={installed_version}")
                    return True
                else:
                    print(f"❌ {package_name}: expected {expected_version}, got {installed_version}")
                    return False

        print(f"❌ Could not determine {package_name} version")
        return False
    except Exception as e:
        print(f"❌ Error checking {package_name}: {e}")
        return False


def check_imports():
    """Test critical imports"""
    print("\nTesting critical imports...")

    imports_to_test = [
        ("fastapi", "FastAPI server"),
        ("pydantic", "Data validation"),
        ("sqlalchemy", "Database ORM"),
        ("qdrant_client", "Vector database client"),
        ("mcp.server.fastmcp", "MCP server"),
        ("anyio", "Async I/O"),
    ]

    all_ok = True
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: {description}")
        except ImportError as e:
            print(f"❌ {module}: {description} - {e}")
            all_ok = False

    return all_ok


def main():
    print("=" * 60)
    print("Hephaestus Setup Verification")
    print("=" * 60)
    print()

    # Check Python version
    python_ok = check_python_version()
    print()

    # Check critical package versions
    print("Checking critical package versions...")
    critical_packages = {
        "fastapi": "0.115.5",
        "pydantic": "2.11.0",
        "anyio": "4.7.0",
        "httpx": "0.27.2",
        "mcp": "1.18.0",
        "sqlalchemy": "2.0.23",
    }

    packages_ok = all(
        check_package_version(pkg, ver)
        for pkg, ver in critical_packages.items()
    )
    print()

    # Check imports
    imports_ok = check_imports()
    print()

    # Summary
    print("=" * 60)
    if python_ok and packages_ok and imports_ok:
        print("✅ All checks passed! Hephaestus is ready to use.")
        print()
        print("Next steps:")
        print("  1. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        print("  2. Initialize DB: python scripts/init_db.py")
        print("  3. Initialize Qdrant: python scripts/init_qdrant.py")
        print("  4. Start server: python run_server.py")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        print("To fix dependency issues:")
        print("  pip uninstall -y anyio pydantic pydantic-core pydantic-settings fastapi mcp")
        print("  pip install --no-cache-dir -r requirements.txt")
        print("  find . -type d -name __pycache__ -exec rm -rf {} +")
        return 1


if __name__ == "__main__":
    sys.exit(main())
