"""Integration tests for multi-workflow MCP endpoints.

This module tests all MCP endpoint changes for multi-workflow support:
1. Workflow definition and execution endpoints
2. Task creation with workflow_id requirement
3. Ticket operations with workflow_id requirement
4. Error handling for missing workflow_id
"""

import pytest
import os
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import ValidationError

# Set test environment before imports
os.environ["HEPHAESTUS_TEST_DB"] = ":memory:"

from fastapi.testclient import TestClient

from src.mcp.server import (
    app,
    CreateTaskRequest,
    CreateTicketRequest,
    SearchTicketsRequest,
    StartWorkflowRequest,
    GetTicketsRequest,
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
        assert request.task_description == "Test task"

    def test_create_task_request_fails_without_workflow_id(self):
        """CreateTaskRequest should fail without workflow_id."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTaskRequest(
                task_description="Test task",
                done_definition="Task is done",
                ai_agent_id="test-agent"
            )
        assert "workflow_id" in str(exc_info.value)

    def test_create_task_request_with_optional_fields(self):
        """CreateTaskRequest should accept all optional fields."""
        request = CreateTaskRequest(
            task_description="Test task",
            done_definition="Task is done",
            ai_agent_id="test-agent",
            workflow_id="test-workflow-id",
            priority="high",
            phase_id="1",
            cwd="/project",
            ticket_id="ticket-123"
        )
        assert request.priority == "high"
        assert request.phase_id == "1"
        assert request.cwd == "/project"
        assert request.ticket_id == "ticket-123"

    def test_create_ticket_request_requires_workflow_id(self):
        """CreateTicketRequest should require workflow_id field."""
        # Should work with workflow_id
        request = CreateTicketRequest(
            workflow_id="test-workflow-id",
            title="Test Ticket Title",
            description="This is a test ticket description."
        )
        assert request.workflow_id == "test-workflow-id"

    def test_create_ticket_request_fails_without_workflow_id(self):
        """CreateTicketRequest should fail without workflow_id."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                title="Test Ticket Title",
                description="This is a test ticket description."
            )
        assert "workflow_id" in str(exc_info.value)

    def test_create_ticket_request_validates_min_lengths(self):
        """CreateTicketRequest should validate minimum lengths."""
        # Title too short
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                workflow_id="test-workflow",
                title="AB",  # min_length=3
                description="Valid description"
            )
        error_str = str(exc_info.value)
        assert "title" in error_str.lower()

        # Description too short
        with pytest.raises(ValidationError) as exc_info:
            CreateTicketRequest(
                workflow_id="test-workflow",
                title="Valid Title",
                description="Short"  # min_length=10
            )
        error_str = str(exc_info.value)
        assert "description" in error_str.lower()

    def test_search_tickets_request_requires_workflow_id(self):
        """SearchTicketsRequest should require workflow_id field."""
        # Should work with workflow_id
        request = SearchTicketsRequest(
            workflow_id="test-workflow-id",
            query="test search query"
        )
        assert request.workflow_id == "test-workflow-id"
        assert request.query == "test search query"

    def test_search_tickets_request_fails_without_workflow_id(self):
        """SearchTicketsRequest should fail without workflow_id."""
        with pytest.raises(ValidationError) as exc_info:
            SearchTicketsRequest(
                query="test search query"
            )
        assert "workflow_id" in str(exc_info.value)

    def test_search_tickets_request_default_values(self):
        """SearchTicketsRequest should have correct default values."""
        request = SearchTicketsRequest(
            workflow_id="test-workflow-id",
            query="test query"
        )
        assert request.search_type == "hybrid"
        assert request.limit == 10
        assert request.include_comments is True
        assert request.filters == {}

    def test_get_tickets_request_requires_workflow_id(self):
        """GetTicketsRequest should require workflow_id field."""
        # Should work with workflow_id
        request = GetTicketsRequest(
            workflow_id="test-workflow-id"
        )
        assert request.workflow_id == "test-workflow-id"

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

    def test_start_workflow_request_requires_fields(self):
        """StartWorkflowRequest should require both definition_id and description."""
        with pytest.raises(ValidationError):
            StartWorkflowRequest(
                definition_id="def-123"
            )

        with pytest.raises(ValidationError):
            StartWorkflowRequest(
                description="Test workflow execution"
            )


class TestWorkflowEndpoints:
    """Test the workflow management endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client without server exceptions."""
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
        # The route should exist - status could be 200, 404 (for workflow), or 500
        assert response.status_code in [200, 404, 500], f"Unexpected status: {response.status_code}"


class TestEndpointValidation:
    """Test that endpoints properly validate workflow_id."""

    @pytest.fixture
    def client(self):
        """Create a test client without server exceptions."""
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

    def test_create_task_with_workflow_id(self, client):
        """POST /create_task should accept workflow_id."""
        response = client.post(
            "/create_task",
            json={
                "task_description": "Test task",
                "done_definition": "Task is done",
                "ai_agent_id": "test-agent",
                "workflow_id": "test-workflow-123",
                "phase_id": "1"
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should not get 422 validation error - may fail for other reasons
        assert response.status_code != 422

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

    def test_create_ticket_with_workflow_id(self, client):
        """POST /api/tickets/create should accept workflow_id."""
        response = client.post(
            "/api/tickets/create",
            json={
                "workflow_id": "test-workflow-123",
                "title": "Test Ticket",
                "description": "Test ticket description here"
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should not get 422 validation error
        assert response.status_code != 422

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

    def test_search_tickets_with_workflow_id(self, client):
        """POST /api/tickets/search should accept workflow_id."""
        response = client.post(
            "/api/tickets/search",
            json={
                "workflow_id": "test-workflow-123",
                "query": "test search query"
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should not get 422 validation error
        assert response.status_code != 422

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

    def test_get_tickets_with_workflow_id(self, client):
        """GET /api/tickets should work with workflow_id query param."""
        response = client.get(
            "/api/tickets",
            params={"workflow_id": "test-workflow-123"},
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should not get 422 validation error
        assert response.status_code != 422


class TestTaskEndpoints:
    """Test task-related endpoints with workflow_id."""

    @pytest.fixture
    def client(self):
        """Create a test client without server exceptions."""
        return TestClient(app, raise_server_exceptions=False)

    def test_create_task_requires_workflow_id(self, client):
        """Test that create_task returns error without workflow_id."""
        response = client.post(
            "/create_task",
            json={
                "task_description": "Test task",
                "done_definition": "Done when complete",
                "ai_agent_id": "test-agent",
                "phase_id": "1"
                # Missing workflow_id
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 422
        assert "workflow_id" in response.text.lower()

    def test_create_task_with_valid_request(self, client):
        """Test creating task with all required fields."""
        response = client.post(
            "/create_task",
            json={
                "task_description": "Test task",
                "done_definition": "Done when complete",
                "ai_agent_id": "test-agent",
                "workflow_id": f"workflow-{uuid.uuid4()}",
                "phase_id": "1"
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        # Should pass validation (might fail later due to workflow not existing)
        assert response.status_code != 422

    def test_create_task_with_invalid_priority(self, client):
        """Test creating task with invalid priority value."""
        response = client.post(
            "/create_task",
            json={
                "task_description": "Test task",
                "done_definition": "Done when complete",
                "ai_agent_id": "test-agent",
                "workflow_id": "test-workflow-id",
                "priority": "invalid"  # Should be low/medium/high
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 422


class TestTicketEndpoints:
    """Test ticket-related endpoints with workflow_id."""

    @pytest.fixture
    def client(self):
        """Create a test client without server exceptions."""
        return TestClient(app, raise_server_exceptions=False)

    def test_create_ticket_requires_workflow_id(self, client):
        """Test that create_ticket returns error without workflow_id."""
        response = client.post(
            "/api/tickets/create",
            json={
                "title": "Test ticket",
                "description": "Test description here"
                # Missing workflow_id
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 422

    def test_create_ticket_validates_title_length(self, client):
        """Test that ticket title is validated for minimum length."""
        response = client.post(
            "/api/tickets/create",
            json={
                "workflow_id": "test-workflow",
                "title": "AB",  # Too short - min 3
                "description": "Valid description here"
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 422

    def test_search_tickets_requires_workflow_id(self, client):
        """Test that search_tickets requires workflow_id."""
        response = client.post(
            "/api/tickets/search",
            json={
                "query": "test"
                # Missing workflow_id
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 422

    def test_search_tickets_validates_query_length(self, client):
        """Test that search query has minimum length."""
        response = client.post(
            "/api/tickets/search",
            json={
                "workflow_id": "test-workflow",
                "query": "ab"  # Too short - min 3
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 422


class TestPhaseManagerIntegration:
    """Test PhaseManager multi-workflow methods."""

    def test_register_definition(self, phase_manager):
        """Test registering a workflow definition."""
        phases_config = [
            {
                "order": 1,
                "name": "Planning",
                "description": "Plan the project",
                "done_definitions": ["Requirements documented"],
            },
            {
                "order": 2,
                "name": "Implementation",
                "description": "Implement the code",
                "done_definitions": ["Code written", "Tests pass"],
            },
        ]

        workflow_config = {
            "has_result": True,
            "result_criteria": "Working application",
        }

        definition_id = phase_manager.register_definition(
            definition_id="test-workflow",
            name="Test Workflow",
            description="A test workflow",
            phases_config=phases_config,
            workflow_config=workflow_config,
        )

        assert definition_id == "test-workflow"
        assert "test-workflow" in phase_manager.definitions

    def test_start_execution(self, initialized_phase_manager):
        """Test starting a workflow execution from a definition."""
        workflow_id = initialized_phase_manager.start_execution(
            definition_id="test-workflow",
            description="Test execution",
            working_directory="/project/path",
        )

        assert workflow_id is not None
        assert workflow_id in initialized_phase_manager.active_executions
        assert initialized_phase_manager.active_executions[workflow_id] == "test-workflow"

    def test_start_execution_invalid_definition(self, initialized_phase_manager):
        """Test starting execution with invalid definition ID."""
        with pytest.raises(ValueError) as exc_info:
            initialized_phase_manager.start_execution(
                definition_id="nonexistent",
                description="Should fail",
            )
        assert "not found" in str(exc_info.value)

    def test_multiple_concurrent_executions(self, initialized_phase_manager, test_bugfix_definition):
        """Test running multiple concurrent executions."""
        # Register second definition
        phases_config = [
            {
                "order": phase.id,
                "name": phase.name,
                "description": phase.description,
                "done_definitions": phase.done_definitions,
            }
            for phase in test_bugfix_definition.phases
        ]

        initialized_phase_manager.register_definition(
            definition_id=test_bugfix_definition.id,
            name=test_bugfix_definition.name,
            description=test_bugfix_definition.description,
            phases_config=phases_config,
        )

        # Start executions from both definitions
        wf_a1 = initialized_phase_manager.start_execution("test-workflow", "Execution A1")
        wf_a2 = initialized_phase_manager.start_execution("test-workflow", "Execution A2")
        wf_b1 = initialized_phase_manager.start_execution("bugfix-workflow", "Execution B1")

        # Verify all are tracked
        assert len(initialized_phase_manager.active_executions) >= 3
        assert initialized_phase_manager.active_executions[wf_a1] == "test-workflow"
        assert initialized_phase_manager.active_executions[wf_a2] == "test-workflow"
        assert initialized_phase_manager.active_executions[wf_b1] == "bugfix-workflow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
