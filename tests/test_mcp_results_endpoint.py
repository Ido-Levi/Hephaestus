"""Unit tests for the MCP report_results endpoint."""

import pytest
import tempfile
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import httpx


class TestReportResultsEndpoint:
    """Test suite for the /report_results MCP endpoint."""

    @pytest.fixture
    async def client(self):
        """Create async HTTP client for testing."""
        async with httpx.AsyncClient(base_url="http://testserver") as client:
            yield client

    @pytest.fixture
    def valid_markdown_file(self):
        """Create a valid markdown file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Results\n\nThis is a test result.")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def large_markdown_file(self):
        """Create a large markdown file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            # Write 101KB of data
            f.write("# Large File\n" + "x" * (101 * 1024))
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @patch('src.mcp.server.ResultService.create_result')
    @patch('src.mcp.server.server_state.broadcast_update')
    def test_report_results_success(
        self, mock_broadcast, mock_create_result, client, valid_markdown_file
    ):
        """Test successful result reporting."""
        # Setup mock
        mock_create_result.return_value = {
            "status": "stored",
            "result_id": "result-123",
            "task_id": "task-456",
            "agent_id": "agent-789",
            "verification_status": "unverified",
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_broadcast.return_value = AsyncMock()

        # Make request
        response = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": valid_markdown_file,
                "result_type": "implementation",
                "summary": "Test implementation completed",
            },
            headers={"X-Agent-ID": "agent-789"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stored"
        assert data["result_id"] == "result-123"
        assert data["task_id"] == "task-456"
        assert data["agent_id"] == "agent-789"
        assert data["verification_status"] == "unverified"

        # Verify create_result was called correctly
        mock_create_result.assert_called_once_with(
            agent_id="agent-789",
            task_id="task-456",
            markdown_file_path=valid_markdown_file,
            result_type="implementation",
            summary="Test implementation completed",
        )

    @patch('src.mcp.server.ResultService.create_result')
    def test_report_results_missing_file(self, mock_create_result, client):
        """Test result reporting with missing file."""
        # Setup mock to raise FileNotFoundError
        mock_create_result.side_effect = FileNotFoundError("Markdown file not found: /missing.md")

        # Make request
        response = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": "/missing.md",
                "result_type": "implementation",
                "summary": "Test",
            },
            headers={"X-Agent-ID": "agent-789"},
        )

        # Assertions
        assert response.status_code == 404
        assert "Markdown file not found" in response.json()["detail"]

    @patch('src.mcp.server.ResultService.create_result')
    def test_report_results_invalid_task(self, mock_create_result, client, valid_markdown_file):
        """Test result reporting with invalid task."""
        # Setup mock to raise ValueError
        mock_create_result.side_effect = ValueError("Task not found: invalid-task")

        # Make request
        response = client.post(
            "/report_results",
            json={
                "task_id": "invalid-task",
                "markdown_file_path": valid_markdown_file,
                "result_type": "implementation",
                "summary": "Test",
            },
            headers={"X-Agent-ID": "agent-789"},
        )

        # Assertions
        assert response.status_code == 400
        assert "Task not found" in response.json()["detail"]

    @patch('src.mcp.server.ResultService.create_result')
    def test_report_results_wrong_agent(self, mock_create_result, client, valid_markdown_file):
        """Test result reporting by wrong agent."""
        # Setup mock to raise ValueError
        mock_create_result.side_effect = ValueError(
            "Task task-456 is not assigned to agent wrong-agent"
        )

        # Make request
        response = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": valid_markdown_file,
                "result_type": "implementation",
                "summary": "Test",
            },
            headers={"X-Agent-ID": "wrong-agent"},
        )

        # Assertions
        assert response.status_code == 400
        assert "not assigned to agent" in response.json()["detail"]

    @patch('src.mcp.server.ResultService.create_result')
    def test_report_results_file_too_large(self, mock_create_result, client, large_markdown_file):
        """Test result reporting with file too large."""
        # Setup mock to raise ValueError
        mock_create_result.side_effect = ValueError("File too large: 101.00KB exceeds maximum of 100KB")

        # Make request
        response = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": large_markdown_file,
                "result_type": "implementation",
                "summary": "Test",
            },
            headers={"X-Agent-ID": "agent-789"},
        )

        # Assertions
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

    def test_report_results_missing_agent_id(self, client, valid_markdown_file):
        """Test result reporting without agent ID header."""
        # Make request without X-Agent-ID header
        response = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": valid_markdown_file,
                "result_type": "implementation",
                "summary": "Test",
            }
        )

        # Assertions
        assert response.status_code == 422  # Unprocessable Entity
        assert "Field required" in str(response.json())

    def test_report_results_invalid_result_type(self, client, valid_markdown_file):
        """Test result reporting with invalid result type."""
        # Make request with invalid result_type
        response = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": valid_markdown_file,
                "result_type": "invalid_type",
                "summary": "Test",
            },
            headers={"X-Agent-ID": "agent-789"},
        )

        # Assertions
        assert response.status_code == 422  # Validation error
        assert "String should match pattern" in str(response.json())

    @patch('src.mcp.server.ResultService.create_result')
    def test_report_results_path_traversal_attack(self, mock_create_result, client):
        """Test protection against path traversal attacks."""
        # Setup mock to raise ValueError
        mock_create_result.side_effect = ValueError("Invalid file path - directory traversal detected")

        # Make request with path traversal attempt
        response = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": "../../etc/passwd",
                "result_type": "implementation",
                "summary": "Test",
            },
            headers={"X-Agent-ID": "agent-789"},
        )

        # Assertions
        assert response.status_code == 400
        assert "directory traversal" in response.json()["detail"].lower()

    @patch('src.mcp.server.ResultService.create_result')
    @patch('src.mcp.server.server_state.broadcast_update')
    def test_multiple_results_per_task(
        self, mock_broadcast, mock_create_result, client, valid_markdown_file
    ):
        """Test submitting multiple results for the same task."""
        # Setup mock for first result
        mock_create_result.return_value = {
            "status": "stored",
            "result_id": "result-001",
            "task_id": "task-456",
            "agent_id": "agent-789",
            "verification_status": "unverified",
            "created_at": datetime.utcnow().isoformat(),
        }
        mock_broadcast.return_value = AsyncMock()

        # First result
        response1 = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": valid_markdown_file,
                "result_type": "implementation",
                "summary": "First result",
            },
            headers={"X-Agent-ID": "agent-789"},
        )
        assert response1.status_code == 200
        assert response1.json()["result_id"] == "result-001"

        # Setup mock for second result
        mock_create_result.return_value = {
            "status": "stored",
            "result_id": "result-002",
            "task_id": "task-456",
            "agent_id": "agent-789",
            "verification_status": "unverified",
            "created_at": datetime.utcnow().isoformat(),
        }

        # Second result
        response2 = client.post(
            "/report_results",
            json={
                "task_id": "task-456",
                "markdown_file_path": valid_markdown_file,
                "result_type": "fix",
                "summary": "Second result",
            },
            headers={"X-Agent-ID": "agent-789"},
        )
        assert response2.status_code == 200
        assert response2.json()["result_id"] == "result-002"

        # Verify create_result was called twice
        assert mock_create_result.call_count == 2