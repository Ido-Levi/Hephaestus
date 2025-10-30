#!/bin/bash
#
# Run Hephaestus Integration Tests
#
# This script runs the full system integration tests.
# WARNING: This will delete the test database and kill running processes!
#

set -e  # Exit on error

echo "=================================================="
echo "HEPHAESTUS INTEGRATION TEST RUNNER"
echo "=================================================="
echo ""
echo "⚠️  WARNING: This test is destructive!"
echo "It will:"
echo "  - Kill running Hephaestus processes"
echo "  - Delete test database"
echo "  - Clean up worktrees"
echo "  - Modify git branches"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create necessary directories
mkdir -p tests/integration/logs
mkdir -p worktrees

# Check prerequisites
echo "Checking prerequisites..."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed. Please install tmux first."
    exit 1
fi

# Check if git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Please run from Hephaestus root."
    exit 1
fi

# Check if Qdrant is running (optional)
if command -v docker &> /dev/null; then
    if docker ps | grep -q qdrant; then
        echo "✅ Qdrant is running"
    else
        echo "⚠️  Qdrant not running. Starting Qdrant..."
        docker run -d -p 6333:6333 --name qdrant_test qdrant/qdrant || true
        sleep 3
    fi
else
    echo "⚠️  Docker not found, assuming Qdrant is available"
fi

# Set test environment
export INTEGRATION_TEST=true
export DATABASE_PATH=./hephaestus_test.db
export LOG_LEVEL=INFO

echo ""
echo "Running integration tests..."
echo "Logs will be saved to: tests/integration/integration_test.log"
echo ""

# Run the tests
if [ "$1" = "--pytest" ]; then
    # Run with pytest for better output
    python -m pytest tests/integration/test_full_system.py -v --tb=short --capture=no
else
    # Run directly
    python tests/integration/test_full_system.py
fi

# Capture exit code
EXIT_CODE=$?

# Cleanup
echo ""
echo "Cleaning up..."

# Stop test Qdrant if we started it
if command -v docker &> /dev/null; then
    docker stop qdrant_test 2>/dev/null || true
    docker rm qdrant_test 2>/dev/null || true
fi

# Show results
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Integration tests PASSED!"
else
    echo "❌ Integration tests FAILED!"
    echo "Check logs at: tests/integration/integration_test.log"
fi

exit $EXIT_CODE