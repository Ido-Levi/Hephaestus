#!/usr/bin/env python3
"""
MCP Integration Test Script
Tests the full flow of Hephaestus MCP integration without running Claude Code
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Server configuration
HEPHAESTUS_URL = "http://localhost:8000"


class MCPIntegrationTester:
    """Test the MCP integration flow"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.test_results = []
        self.created_task_id = None
        self.assigned_agent_id = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        print(f"{status} {test_name}")
        if message:
            print(f"  {YELLOW}→{RESET} {message}")
        self.test_results.append({"test": test_name, "success": success, "message": message})

    async def test_server_health(self) -> bool:
        """Test 1: Check if server is healthy"""
        try:
            response = await self.client.get(f"{HEPHAESTUS_URL}/health")
            success = response.status_code == 200
            self.log_test("Server Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Server Health Check", False, f"Error: {e}")
            return False

    async def test_create_task(self) -> bool:
        """Test 2: Create a task via MCP endpoint"""
        try:
            # This simulates what the MCP tool would send
            payload = {
                "task_description": "Test task: Create a hello world script",
                "done_definition": "Script created and prints 'Hello, World!'",
                "ai_agent_id": "test-agent-001",
                "priority": "medium"
            }

            response = await self.client.post(
                f"{HEPHAESTUS_URL}/create_task",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": "test-agent-001"
                }
            )

            success = response.status_code == 200
            if success:
                data = response.json()
                self.created_task_id = data.get("task_id")
                self.assigned_agent_id = data.get("assigned_agent_id")

                # Wait for async task assignment to complete
                max_retries = 10
                retry_delay = 2

                for retry in range(max_retries):
                    await asyncio.sleep(retry_delay)

                    # Query the specific task to get the assigned agent
                    task_query_response = await self.client.get(
                        f"{HEPHAESTUS_URL}/task_progress",
                        headers={"X-Agent-ID": "test-agent-001"}
                    )

                    if task_query_response.status_code == 200:
                        tasks = task_query_response.json()
                        # Find our specific task
                        for task in (tasks if isinstance(tasks, list) else [tasks]):
                            if task.get("id") == self.created_task_id:
                                agent_id = task.get("assigned_agent_id")
                                if agent_id and agent_id != "pending":
                                    self.assigned_agent_id = agent_id
                                    break

                        if self.assigned_agent_id and self.assigned_agent_id != "pending":
                            break

                self.log_test(
                    "Create Task via MCP",
                    success,
                    f"Task ID: {self.created_task_id[:8] if self.created_task_id else 'None'}, Agent: {self.assigned_agent_id[:8] if self.assigned_agent_id and self.assigned_agent_id != 'pending' else 'pending'}"
                )
            else:
                self.log_test("Create Task via MCP", success, f"Response: {response.text}")
            return success
        except Exception as e:
            self.log_test("Create Task via MCP", False, f"Error: {e}")
            return False

    async def test_get_tasks(self) -> bool:
        """Test 3: Get tasks list"""
        try:
            response = await self.client.get(
                f"{HEPHAESTUS_URL}/task_progress",
                headers={"X-Agent-ID": "test-agent-001"}
            )

            success = response.status_code == 200
            if success:
                tasks = response.json()
                task_count = len(tasks) if isinstance(tasks, list) else 1
                self.log_test("Get Tasks List", success, f"Found {task_count} task(s)")
            else:
                self.log_test("Get Tasks List", success, f"Response: {response.text}")
            return success
        except Exception as e:
            self.log_test("Get Tasks List", False, f"Error: {e}")
            return False

    async def test_save_memory(self) -> bool:
        """Test 4: Save memory via MCP"""
        try:
            payload = {
                "ai_agent_id": self.assigned_agent_id or "test-agent-001",
                "memory_content": "Test memory: Hello world scripts should use print() function in Python",
                "memory_type": "learning",
                "tags": ["test", "python"],
                "related_files": []
            }

            response = await self.client.post(
                f"{HEPHAESTUS_URL}/save_memory",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": self.assigned_agent_id or "test-agent-001"
                }
            )

            success = response.status_code == 200
            if success:
                data = response.json()
                memory_id = data.get("memory_id")
                self.log_test("Save Memory", success, f"Memory ID: {memory_id[:8] if memory_id else 'None'}")
            else:
                self.log_test("Save Memory", success, f"Response: {response.text}")
            return success
        except Exception as e:
            self.log_test("Save Memory", False, f"Error: {e}")
            return False

    async def test_update_task_wrong_agent(self) -> bool:
        """Test 5: Try to update task with wrong agent ID (should fail)"""
        if not self.created_task_id:
            self.log_test("Update Task (Wrong Agent)", False, "No task created to test")
            return False

        try:
            payload = {
                "task_id": self.created_task_id,
                "status": "done",
                "agent_id": "wrong-agent-id",
                "summary": "This should fail",
                "key_learnings": ["Testing authorization"]
            }

            response = await self.client.post(
                f"{HEPHAESTUS_URL}/update_task_status",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": "wrong-agent-id"
                }
            )

            # This should fail with 403 or similar
            success = response.status_code != 200
            if success:
                self.log_test(
                    "Update Task (Wrong Agent)",
                    success,
                    f"Correctly rejected with: {response.json().get('detail', response.text)}"
                )
            else:
                self.log_test("Update Task (Wrong Agent)", False, "Should have been rejected but wasn't")
            return success
        except Exception as e:
            self.log_test("Update Task (Wrong Agent)", False, f"Error: {e}")
            return False

    async def test_report_results(self) -> bool:
        """Test 6: Report results for a task"""
        if not self.created_task_id:
            self.log_test("Report Results", False, "No task to test")
            return False

        # Skip if agent not assigned yet
        if not self.assigned_agent_id or self.assigned_agent_id == "pending":
            self.log_test("Report Results", False, "Task not yet assigned to agent (async processing)")
            return False

        try:
            # Create a temporary markdown file
            import tempfile
            import os

            # Create markdown content
            markdown_content = """# Task Results: Create Hello World Script

## Summary
Successfully created a Python script that prints "Hello, World!" to the console.

## Detailed Achievements
- Created hello_world.py with proper Python syntax
- Tested script execution
- Verified output matches requirements

## Artifacts Created
| File Path | Type | Description |
|-----------|------|-------------|
| hello_world.py | Python Script | Main script file |

## Validation Evidence
```bash
$ python hello_world.py
Hello, World!
```

## Known Limitations
None identified.

## Recommended Next Steps
- Consider adding command-line argument support
- Add unit tests for the script
"""

            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(markdown_content)
                result_file_path = f.name

            # Report results
            payload = {
                "task_id": self.created_task_id,
                "markdown_file_path": result_file_path,
                "result_type": "implementation",
                "summary": "Created hello world script with proper output"
            }

            response = await self.client.post(
                f"{HEPHAESTUS_URL}/report_results",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": self.assigned_agent_id
                }
            )

            # Clean up temp file
            os.unlink(result_file_path)

            success = response.status_code == 200
            if success:
                data = response.json()
                result_id = data.get("result_id")
                self.log_test("Report Results", success, f"Result ID: {result_id[:8] if result_id else 'None'}")
            else:
                self.log_test(
                    "Report Results",
                    success,
                    f"Failed: {response.json().get('detail', response.text)}"
                )
            return success
        except Exception as e:
            self.log_test("Report Results", False, f"Error: {e}")
            return False

    async def test_report_multiple_results(self) -> bool:
        """Test 7: Report multiple results for the same task"""
        if not self.created_task_id:
            self.log_test("Report Multiple Results", False, "No task to test")
            return False

        # Skip if agent not assigned yet
        if not self.assigned_agent_id or self.assigned_agent_id == "pending":
            self.log_test("Report Multiple Results", False, "Task not yet assigned to agent (async processing)")
            return False

        try:
            import tempfile
            import os

            # Create second result markdown
            markdown_content = """# Additional Results: Code Optimization

## Summary
Optimized the hello world script for better performance.

## Improvements Made
- Added proper shebang line
- Added main function guard
"""

            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(markdown_content)
                result_file_path = f.name

            # Report second result
            payload = {
                "task_id": self.created_task_id,
                "markdown_file_path": result_file_path,
                "result_type": "fix",
                "summary": "Optimized hello world script"
            }

            response = await self.client.post(
                f"{HEPHAESTUS_URL}/report_results",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": self.assigned_agent_id
                }
            )

            # Clean up temp file
            os.unlink(result_file_path)

            success = response.status_code == 200
            if success:
                data = response.json()
                result_id = data.get("result_id")
                self.log_test("Report Multiple Results", success, f"Second Result ID: {result_id[:8] if result_id else 'None'}")
            else:
                self.log_test(
                    "Report Multiple Results",
                    success,
                    f"Failed: {response.json().get('detail', response.text)}"
                )
            return success
        except Exception as e:
            self.log_test("Report Multiple Results", False, f"Error: {e}")
            return False

    async def test_update_task_correct_agent(self) -> bool:
        """Test 8: Update task with correct agent ID (should succeed)"""
        if not self.created_task_id:
            self.log_test("Update Task (Correct Agent)", False, "No task to test")
            return False

        # Skip if agent not assigned yet
        if not self.assigned_agent_id or self.assigned_agent_id == "pending":
            self.log_test("Update Task (Correct Agent)", False, "Task not yet assigned to agent (async processing)")
            return False

        try:
            payload = {
                "task_id": self.created_task_id,
                "status": "done",
                "agent_id": self.assigned_agent_id,
                "summary": "Successfully created hello world script",
                "key_learnings": [
                    "Used print() function in Python",
                    "Script tested successfully"
                ]
            }

            response = await self.client.post(
                f"{HEPHAESTUS_URL}/update_task_status",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": self.assigned_agent_id
                }
            )

            success = response.status_code == 200
            if success:
                self.log_test("Update Task (Correct Agent)", success, "Task marked as done")
            else:
                self.log_test(
                    "Update Task (Correct Agent)",
                    success,
                    f"Failed: {response.json().get('detail', response.text)}"
                )
            return success
        except Exception as e:
            self.log_test("Update Task (Correct Agent)", False, f"Error: {e}")
            return False

    async def test_update_missing_fields(self) -> bool:
        """Test 9: Update task with missing required fields (should fail)"""
        # This test requires an existing task with agent
        if not self.created_task_id or not self.assigned_agent_id or self.assigned_agent_id == "pending":
            self.log_test("Update Task (Missing Fields)", False, "Requires existing task with assigned agent")
            return False

        try:
            # Missing key_learnings field
            payload = {
                "task_id": self.created_task_id,
                "status": "done",
                "agent_id": self.assigned_agent_id,
                "summary": "Missing key_learnings field"
                # key_learnings is missing!
            }

            response = await self.client.post(
                f"{HEPHAESTUS_URL}/update_task_status",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": self.assigned_agent_id
                }
            )

            # This should fail with validation error
            success = response.status_code == 422
            if success:
                detail = response.json().get('detail', [])
                if detail and isinstance(detail, list):
                    missing_field = detail[0].get('loc', [])[-1] if detail else 'unknown'
                    self.log_test(
                        "Update Task (Missing Fields)",
                        success,
                        f"Correctly rejected missing field: {missing_field}"
                    )
                else:
                    self.log_test("Update Task (Missing Fields)", success, "Validation error as expected")
            else:
                self.log_test(
                    "Update Task (Missing Fields)",
                    False,
                    f"Should have failed but got {response.status_code}"
                )
            return success
        except Exception as e:
            self.log_test("Update Task (Missing Fields)", False, f"Error: {e}")
            return False

    async def test_agent_status(self) -> bool:
        """Test 10: Get agent status"""
        try:
            response = await self.client.get(
                f"{HEPHAESTUS_URL}/agent_status",
                headers={"X-Agent-ID": "test-agent-001"}
            )

            success = response.status_code == 200
            if success:
                agents = response.json()
                agent_count = len(agents) if isinstance(agents, list) else 0
                self.log_test("Get Agent Status", success, f"Found {agent_count} agent(s)")
            else:
                self.log_test("Get Agent Status", success, f"Response: {response.text}")
            return success
        except Exception as e:
            self.log_test("Get Agent Status", False, f"Error: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n{BOLD}{BLUE}=== MCP Integration Tests ==={RESET}\n")
        print(f"Testing against: {HEPHAESTUS_URL}\n")

        # Check server is running first
        if not await self.test_server_health():
            print(f"\n{RED}ERROR: Server is not running at {HEPHAESTUS_URL}{RESET}")
            print(f"Please start the server with: {YELLOW}python run_server.py{RESET}\n")
            return

        print(f"\n{BOLD}Running MCP Flow Tests:{RESET}\n")

        # Run tests in order
        await self.test_create_task()
        await self.test_get_tasks()
        await self.test_save_memory()
        await self.test_update_task_wrong_agent()
        await self.test_report_results()  # New test for reporting results
        await self.test_report_multiple_results()  # New test for multiple results
        await self.test_update_task_correct_agent()
        await self.test_update_missing_fields()
        await self.test_agent_status()

        # Print summary
        print(f"\n{BOLD}{BLUE}=== Test Summary ==={RESET}\n")

        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed

        if failed == 0:
            print(f"{GREEN}{BOLD}All {passed} tests passed!{RESET}")
        else:
            print(f"{GREEN}Passed: {passed}{RESET} | {RED}Failed: {failed}{RESET}")

        print("\nDetailed Results:")
        for result in self.test_results:
            status = f"{GREEN}PASS{RESET}" if result["success"] else f"{RED}FAIL{RESET}"
            print(f"  [{status}] {result['test']}")
            if not result["success"] and result["message"]:
                print(f"        {result['message']}")


async def main():
    """Main entry point"""
    async with MCPIntegrationTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        sys.exit(1)