#!/bin/bash

# MCP Integration Test Runner
# This script tests the Hephaestus MCP integration without running Claude Code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Hephaestus MCP Integration Test Suite${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if server is running
echo -e "${YELLOW}Checking if Hephaestus server is running...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not running${NC}"
    echo ""
    echo "Please start the server first with:"
    echo "  cd /Users/idol/projects/hephaestus"
    echo "  python run_server.py"
    echo ""
    exit 1
fi

echo ""
echo -e "${YELLOW}Running MCP integration tests...${NC}"
echo ""

# Run the test script
cd /Users/idol/projects/hephaestus
python tests/mcp_integration/test_mcp_flow.py

echo ""
echo -e "${GREEN}Test execution complete!${NC}"