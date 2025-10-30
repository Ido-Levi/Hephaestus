"""
Test ticket_id validation in create_task endpoint.

This test verifies:
1. SDK agents can create tasks WITHOUT ticket_id (they are ticket creators)
2. MCP agents can create tasks WITH ticket_id (normal flow)
3. MCP agents CANNOT create tasks WITHOUT ticket_id when ticket tracking is enabled
"""

import pytest
import requests
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BASE_URL = "http://localhost:8000"

class TestTicketIDValidation:
    """Test ticket_id validation in create_task endpoint."""

    @classmethod
    def setup_class(cls):
        """Setup - check if server is running and workflow exists."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200, "Server not running"
            print("✓ Server is running")
        except Exception as e:
            pytest.fail(f"Server not available: {e}")

        # Check if ticket tracking workflow exists
        try:
            response = requests.get(
                f"{BASE_URL}/api/workflows",
                headers={"X-Agent-ID": "test-user"},
                timeout=5
            )
            workflows = response.json()
            cls.workflow_id = None
            if workflows and len(workflows) > 0:
                # Use the first workflow that has ticket tracking
                for wf in workflows:
                    # Check if this workflow has a board config (ticket tracking enabled)
                    board_check = requests.get(
                        f"{BASE_URL}/tickets/stats/{wf['id']}",
                        headers={"X-Agent-ID": "test-user"},
                        timeout=5
                    )
                    if board_check.status_code == 200:
                        cls.workflow_id = wf['id']
                        print(f"✓ Found workflow with ticket tracking: {cls.workflow_id}")
                        break

            if not cls.workflow_id:
                print("⚠ No workflow with ticket tracking found - validation tests may not run")
        except Exception as e:
            print(f"⚠ Could not verify workflows: {e}")
            cls.workflow_id = None

    def test_1_sdk_agent_without_ticket_id_succeeds(self):
        """Test 1: SDK agent can create task WITHOUT ticket_id (they create tickets)."""
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
        print(f"Response: {response.text[:200]}")

        assert response.status_code == 200, f"SDK task creation should succeed: {response.text}"
        data = response.json()
        assert "task_id" in data, "Response should contain task_id"
        print(f"✓ SDK agent created task without ticket_id: {data['task_id']}")

        return data["task_id"]

    def test_2_mcp_agent_with_ticket_id_succeeds(self):
        """Test 2: MCP agent can create task WITH ticket_id."""
        print("\n=== Test 2: MCP Agent With ticket_id ===")

        if not self.workflow_id:
            pytest.skip("No workflow with ticket tracking available")

        # First create a ticket
        ticket_payload = {
            "workflow_id": self.workflow_id,
            "title": "Test Ticket for Task Creation",
            "description": "This ticket is for testing task creation with ticket_id",
            "ticket_type": "task",
            "priority": "medium"
        }

        ticket_response = requests.post(
            f"{BASE_URL}/tickets/create",
            json=ticket_payload,
            headers={
                "Content-Type": "application/json",
                "X-Agent-ID": "test-mcp-agent"
            },
            timeout=10
        )

        assert ticket_response.status_code == 200, f"Ticket creation failed: {ticket_response.text}"
        ticket_data = ticket_response.json()
        ticket_id = ticket_data["ticket_id"]
        print(f"✓ Created ticket: {ticket_id}")

        # Now create task with ticket_id
        task_payload = {
            "task_description": "Test MCP task with ticket_id",
            "done_definition": "Task completed successfully",
            "ai_agent_id": "test-mcp-agent",
            "phase_id": "1",
            "priority": "medium",
            "ticket_id": ticket_id  # Include ticket_id
        }

        response = requests.post(
            f"{BASE_URL}/create_task",
            json=task_payload,
            headers={
                "Content-Type": "application/json",
                "X-Agent-ID": "test-mcp-agent"
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")

        assert response.status_code == 200, f"MCP task creation with ticket_id should succeed: {response.text}"
        data = response.json()
        assert "task_id" in data, "Response should contain task_id"
        print(f"✓ MCP agent created task with ticket_id: {data['task_id']}")

        return data["task_id"]

    def test_3_mcp_agent_without_ticket_id_fails(self):
        """Test 3: MCP agent CANNOT create task WITHOUT ticket_id when tracking enabled."""
        print("\n=== Test 3: MCP Agent Without ticket_id (Should Fail) ===")

        if not self.workflow_id:
            pytest.skip("No workflow with ticket tracking available")

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

    def test_4_sdk_agent_variants(self):
        """Test 4: Verify different SDK agent ID patterns work."""
        print("\n=== Test 4: SDK Agent ID Variants ===")

        sdk_agent_ids = [
            "main-session-agent",  # Primary SDK agent
            "sdk-test-agent",      # Agent with 'sdk' in name
            "main-workflow-agent"  # Agent with 'main' in name
        ]

        for agent_id in sdk_agent_ids:
            print(f"\nTesting agent: {agent_id}")

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
            print(f"  ✓ {agent_id} created task successfully")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing ticket_id Validation in create_task Endpoint")
    print("=" * 60)

    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s"])
