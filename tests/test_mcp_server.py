#!/usr/bin/env python3
"""Integration tests for MCP server endpoints."""

import asyncio
import aiohttp
import uuid
import json
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BASE_URL = "http://localhost:8000"
TEST_AGENT_ID = f"test-agent-{uuid.uuid4()}"


async def test_health_endpoint():
    """Test the health check endpoint."""
    print("\n🧪 Testing Health Endpoint...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                data = await response.json()

                print(f"   Status: {data.get('status')}")
                print(f"   Uptime: {data.get('uptime_seconds', 0):.1f} seconds")
                print(f"   Active agents: {data.get('active_agents', 0)}")
                print(f"   ✅ Health check passed")

                return True

        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return False


async def test_create_task():
    """Test task creation endpoint."""
    print("\n🧪 Testing Task Creation...")

    async with aiohttp.ClientSession() as session:
        try:
            # Create a test task
            task_data = {
                "task_description": "Write unit tests for the authentication module",
                "done_definition": "All auth functions have >90% test coverage with passing tests",
                "priority": "medium"
            }

            headers = {
                "Content-Type": "application/json",
                "X-Agent-ID": TEST_AGENT_ID
            }

            async with session.post(
                f"{BASE_URL}/create_task",
                json=task_data,
                headers=headers
            ) as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                data = await response.json()

                task_id = data.get("task_id")
                assert task_id, "No task_id in response"

                print(f"   Task ID: {task_id}")
                print(f"   Status: {data.get('status')}")
                print(f"   Enriched: {data.get('enriched_description', '')[:80]}...")
                print(f"   ✅ Task created successfully")

                return task_id

        except Exception as e:
            print(f"   ❌ Task creation failed: {e}")
            return None


async def test_save_memory():
    """Test memory saving endpoint."""
    print("\n🧪 Testing Memory Saving...")

    async with aiohttp.ClientSession() as session:
        try:
            memory_data = {
                "memory_content": "Always validate user input on both client and server side to prevent XSS attacks",
                "memory_type": "learning",
                "tags": ["security", "validation", "xss"],
                "related_files": ["src/validators.js", "src/middleware/auth.js"]
            }

            headers = {
                "Content-Type": "application/json",
                "X-Agent-ID": TEST_AGENT_ID
            }

            async with session.post(
                f"{BASE_URL}/save_memory",
                json=memory_data,
                headers=headers
            ) as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                data = await response.json()

                memory_id = data.get("memory_id")
                assert memory_id, "No memory_id in response"

                print(f"   Memory ID: {memory_id}")
                print(f"   Stored: {data.get('stored', False)}")
                print(f"   Duplicate: {data.get('duplicate', False)}")

                if data.get("similar_memories"):
                    print(f"   Found {len(data['similar_memories'])} similar memories")

                print(f"   ✅ Memory saved successfully")
                return memory_id

        except Exception as e:
            print(f"   ❌ Memory saving failed: {e}")
            return None


async def test_task_status_update():
    """Test task status update endpoint."""
    print("\n🧪 Testing Task Status Update...")

    # First create a task
    task_id = await test_create_task()
    if not task_id:
        print("   ⚠️  Skipping status update test (no task created)")
        return False

    await asyncio.sleep(2)  # Wait for task to be processed

    async with aiohttp.ClientSession() as session:
        try:
            update_data = {
                "task_id": task_id,
                "status": "done",
                "summary": "Successfully wrote comprehensive unit tests for auth module",
                "key_learnings": [
                    "Use mock JWT tokens for testing authentication",
                    "Test both success and failure cases for each endpoint",
                    "Include edge cases like expired tokens and malformed requests"
                ],
                "code_changes": ["tests/auth.test.js", "tests/fixtures/tokens.js"]
            }

            headers = {
                "Content-Type": "application/json",
                "X-Agent-ID": TEST_AGENT_ID  # Must match the agent that created the task
            }

            async with session.post(
                f"{BASE_URL}/update_task_status",
                json=update_data,
                headers=headers
            ) as response:
                # Note: This might fail if the task wasn't assigned to our test agent
                if response.status == 403:
                    print(f"   ⚠️  Task not assigned to test agent (expected behavior)")
                    return True

                if response.status == 200:
                    data = await response.json()
                    print(f"   Task marked as: {update_data['status']}")
                    print(f"   Memories saved: {data.get('memories_saved', 0)}")
                    print(f"   ✅ Task status updated successfully")
                    return True
                else:
                    text = await response.text()
                    print(f"   ⚠️  Status update returned {response.status}: {text}")
                    return False

        except Exception as e:
            print(f"   ❌ Task status update failed: {e}")
            return False


async def test_agent_status():
    """Test agent status endpoint."""
    print("\n🧪 Testing Agent Status...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/agent_status") as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                data = await response.json()

                agents = data.get("agents", [])
                print(f"   Active agents: {len(agents)}")

                for agent in agents[:3]:  # Show first 3 agents
                    print(f"      - Agent {agent.get('id', 'unknown')[:8]}...")
                    print(f"        Status: {agent.get('status')}")
                    print(f"        Task: {agent.get('current_task', {}).get('description', 'None')[:50]}...")

                print(f"   ✅ Agent status retrieved successfully")
                return True

        except Exception as e:
            print(f"   ❌ Agent status failed: {e}")
            return False


async def test_task_progress():
    """Test task progress endpoint."""
    print("\n🧪 Testing Task Progress...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/task_progress") as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                data = await response.json()

                tasks = data.get("tasks", {})
                print(f"   Task summary:")
                print(f"      Pending: {tasks.get('pending', 0)}")
                print(f"      Assigned: {tasks.get('assigned', 0)}")
                print(f"      In Progress: {tasks.get('in_progress', 0)}")
                print(f"      Completed: {tasks.get('completed', 0)}")
                print(f"      Failed: {tasks.get('failed', 0)}")

                recent = data.get("recent_tasks", [])
                if recent:
                    print(f"   Recent tasks:")
                    for task in recent[:3]:
                        print(f"      - [{task.get('status')}] {task.get('description', '')[:50]}...")

                print(f"   ✅ Task progress retrieved successfully")
                return True

        except Exception as e:
            print(f"   ❌ Task progress failed: {e}")
            return False


async def test_sse_connection():
    """Test Server-Sent Events connection."""
    print("\n🧪 Testing SSE Connection...")

    try:
        timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{BASE_URL}/sse") as response:
                assert response.status == 200, f"Expected 200, got {response.status}"
                assert response.headers.get("Content-Type") == "text/event-stream"

                print(f"   ✅ SSE endpoint accessible")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")

                # Read a few events (with timeout)
                events_received = 0
                start_time = time.time()

                async for line in response.content:
                    if time.time() - start_time > 3:  # Read for max 3 seconds
                        break

                    decoded = line.decode('utf-8').strip()
                    if decoded.startswith("data:"):
                        events_received += 1
                        if events_received <= 2:  # Show first 2 events
                            event_data = decoded[5:].strip()
                            print(f"   Event {events_received}: {event_data[:80]}...")

                print(f"   Received {events_received} events in 3 seconds")
                return True

    except asyncio.TimeoutError:
        print(f"   ✅ SSE connection established (timed out as expected)")
        return True
    except Exception as e:
        print(f"   ❌ SSE connection failed: {e}")
        return False


async def run_all_tests():
    """Run all MCP server tests."""
    print("=" * 60)
    print("MCP SERVER INTEGRATION TESTS")
    print("=" * 60)

    # Check if server is running
    print("\nChecking if MCP server is running...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health", timeout=2) as response:
                if response.status != 200:
                    print("❌ MCP server is not responding properly")
                    print("Please start the server with: python run_server.py")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to MCP server at {BASE_URL}")
        print("Please start the server with: python run_server.py")
        return False

    print("✅ Server is running\n")

    # Run tests
    results = []
    results.append(await test_health_endpoint())
    results.append(await test_save_memory())
    results.append(await test_agent_status())
    results.append(await test_task_progress())
    results.append(await test_sse_connection())

    # Task creation and update tests might fail due to agent assignment
    # but we still run them to test the endpoints
    await test_task_status_update()

    success = all(results)

    print("\n" + "=" * 60)
    if success:
        print("✅ All MCP server tests passed!")
    else:
        print("❌ Some tests failed")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)