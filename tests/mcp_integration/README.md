# MCP Integration Tests

This folder contains standalone tests for the Hephaestus MCP (Model Context Protocol) integration.

## Purpose

These tests verify that the MCP endpoints work correctly without actually running Claude Code or launching agents. They simulate what an agent would send via the MCP tools and verify the server responses.

## What's Tested

1. **Server Health Check** - Ensures the Hephaestus server is running
2. **Create Task** - Tests task creation via MCP endpoint
3. **Get Tasks** - Tests listing tasks
4. **Save Memory** - Tests saving memories to the knowledge base
5. **Update Task (Wrong Agent)** - Verifies authorization: wrong agent ID should be rejected
6. **Update Task (Correct Agent)** - Verifies correct agent can update their task
7. **Update Task (Missing Fields)** - Verifies required field validation (key_learnings)
8. **Get Agent Status** - Tests retrieving agent statuses

## Running the Tests

### Prerequisites

1. Start the Hephaestus server:
   ```bash
   cd /Users/idol/projects/hephaestus
   python run_server.py
   ```

2. Ensure the server is running on port 8000

### Run Tests

Option 1: Use the shell script
```bash
./run_tests.sh
```

Option 2: Run directly with Python
```bash
python test_mcp_flow.py
```

## Expected Output

When all tests pass, you should see:
- ✓ for each passing test
- Detailed information about what was tested
- A summary showing all tests passed

## Test Flow

The tests simulate the complete MCP flow:
1. Create a task (assigns an agent ID)
2. Attempt to update with wrong agent ID (should fail)
3. Update with correct agent ID and all required fields (should succeed)
4. Verify field validation works

This ensures that:
- Agent authorization is working correctly
- Required fields are validated
- The MCP tools match the server's expectations