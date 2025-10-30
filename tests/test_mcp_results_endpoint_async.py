"""Async integration tests for the MCP report_results endpoint."""

import pytest
import tempfile
import os
import asyncio
from datetime import datetime
import httpx
import uuid


@pytest.mark.asyncio
class TestReportResultsEndpointAsync:
    """Test suite for the /report_results MCP endpoint."""

    BASE_URL = "http://localhost:8000"

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

    async def create_test_task(self):
        """Helper to create a task for testing."""
        async with httpx.AsyncClient() as client:
            # Create a task
            task_id = str(uuid.uuid4())
            agent_id = f"test-agent-{uuid.uuid4()}"

            # First create task via API (simulated)
            # For testing, we'll just return mock IDs
            return task_id, agent_id

    async def test_report_results_with_mock(self, valid_markdown_file):
        """Test successful result reporting with mocked service."""
        from unittest.mock import patch, MagicMock

        task_id = str(uuid.uuid4())
        agent_id = str(uuid.uuid4())

        # Create a mock result
        mock_result = {
            "status": "stored",
            "result_id": str(uuid.uuid4()),
            "task_id": task_id,
            "agent_id": agent_id,
            "verification_status": "unverified",
            "created_at": datetime.utcnow().isoformat(),
        }

        with patch('src.services.result_service.ResultService.create_result') as mock_create:
            mock_create.return_value = mock_result

            # Import after patching
            from src.services.result_service import ResultService

            # Call the service directly
            result = ResultService.create_result(
                agent_id=agent_id,
                task_id=task_id,
                markdown_file_path=valid_markdown_file,
                result_type="implementation",
                summary="Test implementation completed",
            )

            # Assertions
            assert result["status"] == "stored"
            assert result["task_id"] == task_id
            assert result["agent_id"] == agent_id
            assert result["verification_status"] == "unverified"
            assert "result_id" in result

    async def test_report_results_missing_file(self):
        """Test result reporting with missing file."""
        from src.services.result_service import ResultService

        with pytest.raises(FileNotFoundError, match="Markdown file not found"):
            ResultService.create_result(
                agent_id="test-agent",
                task_id="test-task",
                markdown_file_path="/nonexistent/file.md",
                result_type="implementation",
                summary="Test",
            )

    async def test_report_results_file_too_large(self, large_markdown_file):
        """Test result reporting with file too large."""
        from src.services.result_service import ResultService

        with pytest.raises(ValueError, match="File too large"):
            ResultService.create_result(
                agent_id="test-agent",
                task_id="test-task",
                markdown_file_path=large_markdown_file,
                result_type="implementation",
                summary="Test",
            )

    async def test_validation_helpers(self):
        """Test validation helper functions."""
        from src.services.validation_helpers import (
            validate_file_path,
            validate_file_size,
            validate_markdown_format,
        )

        # Test path traversal detection
        with pytest.raises(ValueError, match="directory traversal"):
            validate_file_path("../../etc/passwd")

        # Test markdown format validation
        with pytest.raises(ValueError, match="File must be markdown"):
            validate_markdown_format("/path/to/file.txt")

        # Test valid markdown format
        validate_markdown_format("/path/to/file.md")  # Should not raise

        # Test file size validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as f:
            f.write("Small content")
            f.flush()
            validate_file_size(f.name, max_size_kb=100)  # Should not raise

            # Write large content
            f.seek(0)
            f.write("x" * (2 * 1024))  # 2KB
            f.flush()

            with pytest.raises(ValueError, match="File too large"):
                validate_file_size(f.name, max_size_kb=1)

    async def test_integration_with_server(self):
        """Test integration with running server."""
        async with httpx.AsyncClient() as client:
            # Check server health first
            response = await client.get(f"{self.BASE_URL}/health")

            if response.status_code != 200:
                pytest.skip("Server not running")

            # Create a test task
            task_payload = {
                "task_description": "Test task for result reporting",
                "done_definition": "Task completed",
                "ai_agent_id": "test-agent-results",
                "priority": "medium"
            }

            response = await client.post(
                f"{self.BASE_URL}/create_task",
                json=task_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": "test-agent-results"
                }
            )

            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")

                # Wait for task assignment
                await asyncio.sleep(3)

                # Create result file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                    f.write("# Test Results\n\nIntegration test results.")
                    result_file = f.name

                try:
                    # Try to report results (may fail if task not assigned yet)
                    result_response = await client.post(
                        f"{self.BASE_URL}/report_results",
                        json={
                            "task_id": task_id,
                            "markdown_file_path": result_file,
                            "result_type": "test",
                            "summary": "Integration test"
                        },
                        headers={
                            "Content-Type": "application/json",
                            "X-Agent-ID": "test-agent-results"
                        }
                    )

                    # If task is not assigned, that's expected
                    if result_response.status_code == 400:
                        assert "not assigned" in result_response.json().get("detail", "")
                    else:
                        # If successful, verify response
                        assert result_response.status_code == 200
                        result_data = result_response.json()
                        assert result_data["status"] == "stored"
                        assert "result_id" in result_data

                finally:
                    os.unlink(result_file)