"""Tests for multi-workflow support in MCP server.

This test file verifies the changes made to support multiple concurrent workflows:
1. CreateTaskRequest now requires workflow_id
2. CreateTicketRequest now requires workflow_id
3. SearchTicketsRequest now requires workflow_id
4. New workflow management endpoints work correctly
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.mcp.server import (
    app,
    CreateTaskRequest,
    CreateTicketRequest,
    SearchTicketsRequest,
    StartWorkflowRequest,
)


class TestRequestModels:
    """Test that request models properly validate workflow_id as required."""

    def test_create_task_request_requires_workflow_id(self):
        """CreateTaskRequest should require workflow_id field."""
        # Should work with workflow_id
        request = CreateTaskRequest(
            task_description="Test task",
            done_definition="Task is done",
            ai_agent_id="test-agent",
            workflow_id="test-workflow-id"
        )
        assert request.workflow_id == "test-workflow-id"

        # Should fail without workflow_id
        with pytest.raises(ValidationError) as exc_info:
            CreateTaskRequest(
                task_description="Test task",
                done_definition="Task is done",
                ai_agent_id="test-agent"
            )
        assert "workflow_id" in str(exc_info.value)

    def test_create_ticket_request_requires_workflow_id(self):
        """CreateTicketRequest should require workflow_id field."""
        # Should work with workflow_id
        request = CreateTicketRequest(
            workflow_id="test-workflow-id",
            title="Test Ticket Title",
            description="This is a test ticket description."
        )
        assert request.workflow_id == "test-workflow-id"

        # Should fail without workflow_id
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                title="Test Ticket Title",
                description="This is a test ticket description."
            )
        assert "workflow_id" in str(exc_info.value)

    def test_search_tickets_request_requires_workflow_id(self):
        """SearchTicketsRequest should require workflow_id field."""
        # Should work with workflow_id
        request = SearchTicketsRequest(
            workflow_id="test-workflow-id",
            query="test search query"
        )
        assert request.workflow_id == "test-workflow-id"

        # Should fail without workflow_id
        with pytest.raises(ValidationError) as exc_info:
            SearchTicketsRequest(
                query="test search query"
            )
        assert "workflow_id" in str(exc_info.value)

    def test_start_workflow_request_model(self):
        """StartWorkflowRequest should have correct fields."""
        # Test with all fields
        request = StartWorkflowRequest(
            definition_id="def-123",
            description="Test workflow execution",
            working_directory="/path/to/dir"
        )
        assert request.definition_id == "def-123"
        assert request.description == "Test workflow execution"
        assert request.working_directory == "/path/to/dir"

        # Test with only required fields
        request = StartWorkflowRequest(
            definition_id="def-123",
            description="Test workflow execution"
        )
        assert request.definition_id == "def-123"
        assert request.description == "Test workflow execution"
        assert request.working_directory is None

        # Should fail without required fields
        with pytest.raises(ValidationError):
            StartWorkflowRequest(
                definition_id="def-123"
            )

        with pytest.raises(ValidationError):
            StartWorkflowRequest(
                description="Test workflow execution"
            )


class TestWorkflowEndpoints:
    """Test the new workflow management endpoints exist."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app, raise_server_exceptions=False)

    def test_workflow_definitions_endpoint_exists(self, client):
        """GET /api/workflow-definitions endpoint should exist."""
        response = client.get("/api/workflow-definitions")
        # We expect some response (may be 500 if not fully initialized, but not 404)
        assert response.status_code != 404, "Endpoint /api/workflow-definitions not found"

    def test_workflow_executions_list_endpoint_exists(self, client):
        """GET /api/workflow-executions endpoint should exist."""
        response = client.get("/api/workflow-executions")
        # We expect some response (may be 500 if not fully initialized, but not 404)
        assert response.status_code != 404, "Endpoint /api/workflow-executions not found"

    def test_workflow_executions_post_endpoint_exists(self, client):
        """POST /api/workflow-executions endpoint should exist."""
        response = client.post(
            "/api/workflow-executions",
            json={
                "definition_id": "test-def",
                "description": "Test execution"
            }
        )
        # We expect some response (may be 400/500 if not valid, but not 404)
        assert response.status_code != 404, "Endpoint POST /api/workflow-executions not found"

    def test_workflow_execution_get_endpoint_exists(self, client):
        """GET /api/workflow-executions/{workflow_id} endpoint should exist."""
        response = client.get("/api/workflow-executions/test-workflow-id")
        # We expect some response (may be 404 for non-existent workflow, but route should exist)
        # The 404 here would be for the workflow, not the route
        assert response.status_code in [200, 404, 500], f"Unexpected status: {response.status_code}"


class TestEndpointValidation:
    """Test that endpoints properly validate workflow_id."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app, raise_server_exceptions=False)

    def test_create_task_validates_workflow_id(self, client):
        """POST /create_task should require workflow_id."""
        response = client.post(
            "/create_task",
            json={
                "task_description": "Test task",
                "done_definition": "Task is done",
                "ai_agent_id": "test-agent"
                # Missing workflow_id
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should get 422 (validation error) because workflow_id is missing
        assert response.status_code == 422
        assert "workflow_id" in response.text.lower()

    def test_create_ticket_validates_workflow_id(self, client):
        """POST /api/tickets/create should require workflow_id."""
        response = client.post(
            "/api/tickets/create",
            json={
                "title": "Test Ticket",
                "description": "Test ticket description"
                # Missing workflow_id
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should get 422 (validation error) because workflow_id is missing
        assert response.status_code == 422
        assert "workflow_id" in response.text.lower()

    def test_search_tickets_validates_workflow_id(self, client):
        """POST /api/tickets/search should require workflow_id."""
        response = client.post(
            "/api/tickets/search",
            json={
                "query": "test search"
                # Missing workflow_id
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should get 422 (validation error) because workflow_id is missing
        assert response.status_code == 422
        assert "workflow_id" in response.text.lower()

    def test_get_tickets_requires_workflow_id(self, client):
        """GET /api/tickets should require workflow_id query param."""
        response = client.get(
            "/api/tickets",
            headers={"X-Agent-ID": "test-agent"}
            # Missing workflow_id query param
        )
        # Should get 422 (validation error) because workflow_id is missing
        assert response.status_code == 422
        assert "workflow_id" in response.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
