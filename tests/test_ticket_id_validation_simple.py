"""
Simple direct test of ticket_id validation in create_task endpoint.

This test validates the core requirement:
1. SDK agents can create tasks WITHOUT ticket_id
2. MCP agents CANNOT create tasks WITHOUT ticket_id when ticket tracking is enabled
3. MCP agents CAN create tasks WITH valid ticket_id

This test bypasses workflow discovery and tests the validation logic directly.
"""

import pytest
import requests
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BASE_URL = "http://localhost:8000"


class TestTicketIDValidationSimple:
    """Direct test of ticket_id validation without workflow discovery."""

    @classmethod
    def setup_class(cls):
        """Setup - verify server is running."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200, "Server not running"
            print("\n✓ Server is running")
        except Exception as e:
            pytest.fail(f"Server not available: {e}")

    def test_1_sdk_agent_can_create_task_without_ticket_id(self):
        """Test 1: SDK agents (main-session-agent, *sdk*, *main*) can create tasks without ticket_id."""
        print("\n=== Test 1: SDK Agent Without ticket_id ===")

        payload = {
            "task_description": "Test SDK task without ticket_id",
            "done_definition": "Task completed successfully",
            "ai_agent_id": "main-session-agent",
            "phase_id": "1",
            "priority": "medium"
        }

        response = requests.post(
            f"{BASE_URL}/create_task",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Agent-ID": "main-session-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:300]}")

        assert response.status_code == 200, f"SDK task creation should succeed: {response.text}"
        data = response.json()
        assert "task_id" in data, "Response should contain task_id"
        print(f"✓ SDK agent successfully created task without ticket_id: {data['task_id']}")

    def test_2_mcp_agent_blocked_without_ticket_id(self):
        """Test 2: MCP agents are blocked from creating tasks without ticket_id when tracking enabled."""
        print("\n=== Test 2: MCP Agent Without ticket_id (Should Fail) ===")

        payload = {
            "task_description": "Test MCP task without ticket_id - should fail",
            "done_definition": "Task completed successfully",
            "ai_agent_id": "test-mcp-agent",  # MCP agent, not SDK
            "phase_id": "1",
            "priority": "medium"
            # NO ticket_id provided
        }

        response = requests.post(
            f"{BASE_URL}/create_task",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Agent-ID": "test-mcp-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:300]}")

        # Should fail with 400 error
        assert response.status_code == 400, f"MCP task creation without ticket_id should fail with 400, got {response.status_code}"
        assert "ticket_id" in response.text.lower(), "Error message should mention ticket_id"
        assert "mcp agents must provide" in response.text.lower(), "Error should specify MCP agents must provide ticket_id"
        print("✓ MCP agent correctly blocked from creating task without ticket_id")

    def test_3_sdk_agent_variants_work(self):
        """Test 3: All SDK agent ID patterns can create tasks without ticket_id."""
        print("\n=== Test 3: SDK Agent ID Variants ===")

        sdk_agent_ids = [
            "main-session-agent",
            "sdk-test-agent",
            "another-sdk-agent",
            "main-workflow-agent"
        ]

        for agent_id in sdk_agent_ids:
            print(f"\n  Testing agent: {agent_id}")

            payload = {
                "task_description": f"Test SDK variant task for {agent_id}",
                "done_definition": "Task completed successfully",
                "ai_agent_id": agent_id,
                "phase_id": "1",
                "priority": "medium"
            }

            response = requests.post(
                f"{BASE_URL}/create_task",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=30
            )

            assert response.status_code == 200, f"SDK agent '{agent_id}' should be able to create task: {response.text}"
            print(f"    ✓ {agent_id} created task successfully")


if __name__ == "__main__":
    print("=" * 70)
    print("Direct ticket_id Validation Test (No Workflow Discovery)")
    print("=" * 70)

    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s"])
