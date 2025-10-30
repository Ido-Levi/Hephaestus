"""Unit tests for the result service."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.result_service import ResultService
from src.services.validation_helpers import (
    validate_file_path,
    validate_file_size,
    validate_markdown_format,
    validate_task_ownership,
)


class TestResultService:
    """Test suite for ResultService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.commit = Mock()
        return mock_session

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

    @pytest.fixture
    def non_markdown_file(self):
        """Create a non-markdown file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not markdown")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @patch('src.services.result_service.get_db')
    def test_create_result_success(self, mock_get_db, mock_db, valid_markdown_file):
        """Test successful result creation."""
        # Setup mock database
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock task and agent
        mock_task = Mock(id="task-123", assigned_agent_id="agent-456", has_results=False)
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        # Call create_result
        result = ResultService.create_result(
            agent_id="agent-456",
            task_id="task-123",
            markdown_file_path=valid_markdown_file,
            result_type="implementation",
            summary="Test implementation completed",
        )

        # Assertions
        assert result["status"] == "stored"
        assert result["task_id"] == "task-123"
        assert result["agent_id"] == "agent-456"
        assert result["verification_status"] == "unverified"
        assert "result_id" in result
        assert "created_at" in result

        # Verify task was updated
        assert mock_task.has_results == True
        mock_db.commit.assert_called()

    @patch('src.services.result_service.get_db')
    def test_create_result_file_not_found(self, mock_get_db):
        """Test result creation with non-existent file."""
        with pytest.raises(FileNotFoundError, match="Markdown file not found"):
            ResultService.create_result(
                agent_id="agent-456",
                task_id="task-123",
                markdown_file_path="/nonexistent/file.md",
                result_type="implementation",
                summary="Test",
            )

    @patch('src.services.result_service.get_db')
    def test_create_result_file_too_large(self, mock_get_db, large_markdown_file):
        """Test result creation with file exceeding size limit."""
        with pytest.raises(ValueError, match="File too large"):
            ResultService.create_result(
                agent_id="agent-456",
                task_id="task-123",
                markdown_file_path=large_markdown_file,
                result_type="implementation",
                summary="Test",
            )

    @patch('src.services.result_service.get_db')
    def test_create_result_invalid_format(self, mock_get_db, non_markdown_file):
        """Test result creation with non-markdown file."""
        with pytest.raises(ValueError, match="File must be markdown"):
            ResultService.create_result(
                agent_id="agent-456",
                task_id="task-123",
                markdown_file_path=non_markdown_file,
                result_type="implementation",
                summary="Test",
            )

    @patch('src.services.result_service.get_db')
    def test_create_result_wrong_agent(self, mock_get_db, mock_db, valid_markdown_file):
        """Test result creation by wrong agent."""
        # Setup mock database
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock task assigned to different agent
        mock_task = Mock(id="task-123", assigned_agent_id="agent-999")
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        with pytest.raises(ValueError, match="not assigned to agent"):
            ResultService.create_result(
                agent_id="agent-456",
                task_id="task-123",
                markdown_file_path=valid_markdown_file,
                result_type="implementation",
                summary="Test",
            )

    @patch('src.services.result_service.get_db')
    def test_get_results_for_task(self, mock_get_db, mock_db):
        """Test retrieving results for a task."""
        # Setup mock results
        mock_result1 = Mock(
            id="result-1",
            agent_id="agent-456",
            task_id="task-123",
            result_type="implementation",
            summary="First result",
            verification_status="verified",
            created_at=datetime.utcnow(),
            verified_at=datetime.utcnow(),
            markdown_file_path="/path/to/result1.md",
        )
        mock_result2 = Mock(
            id="result-2",
            agent_id="agent-456",
            task_id="task-123",
            result_type="fix",
            summary="Second result",
            verification_status="unverified",
            created_at=datetime.utcnow(),
            verified_at=None,
            markdown_file_path="/path/to/result2.md",
        )

        mock_db.query.return_value.filter_by.return_value.all.return_value = [
            mock_result1, mock_result2
        ]
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Call get_results_for_task
        results = ResultService.get_results_for_task("task-123")

        # Assertions
        assert len(results) == 2
        assert results[0]["result_id"] == "result-1"
        assert results[0]["verification_status"] == "verified"
        assert results[1]["result_id"] == "result-2"
        assert results[1]["verification_status"] == "unverified"

    @patch('src.services.result_service.get_db')
    def test_verify_result(self, mock_get_db, mock_db):
        """Test verifying a result."""
        # Setup mock result
        mock_result = Mock(
            id="result-1",
            verification_status="unverified",
            verified_at=None,
            verified_by_validation_id=None,
        )
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_result
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Call verify_result
        result = ResultService.verify_result(
            result_id="result-1",
            validation_review_id="review-123",
            verified=True,
        )

        # Assertions
        assert result["result_id"] == "result-1"
        assert result["verification_status"] == "verified"
        assert "verified_at" in result
        assert result["verified_by"] == "review-123"
        assert mock_result.verification_status == "verified"
        assert mock_result.verified_by_validation_id == "review-123"
        mock_db.commit.assert_called()


class TestValidationHelpers:
    """Test suite for validation helper functions."""

    def test_validate_file_path_valid(self):
        """Test valid file path validation."""
        # Should not raise
        validate_file_path("/valid/path/to/file.md")
        validate_file_path("relative/path.md")

    def test_validate_file_path_traversal(self):
        """Test detection of path traversal attempts."""
        with pytest.raises(ValueError, match="directory traversal detected"):
            validate_file_path("../../etc/passwd")

        with pytest.raises(ValueError, match="directory traversal detected"):
            validate_file_path("/path/../../../etc/passwd")

    def test_validate_file_size_valid(self):
        """Test valid file size validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as f:
            f.write("Small content")
            f.flush()
            # Should not raise
            validate_file_size(f.name, max_size_kb=100)

    def test_validate_file_size_too_large(self):
        """Test file size exceeding limit."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md') as f:
            # Write 2KB of data
            f.write("x" * (2 * 1024))
            f.flush()
            with pytest.raises(ValueError, match="File too large"):
                validate_file_size(f.name, max_size_kb=1)

    def test_validate_markdown_format_valid(self):
        """Test valid markdown format validation."""
        # Should not raise
        validate_markdown_format("/path/to/file.md")
        validate_markdown_format("/path/to/FILE.MD")

    def test_validate_markdown_format_invalid(self):
        """Test invalid file format validation."""
        with pytest.raises(ValueError, match="File must be markdown"):
            validate_markdown_format("/path/to/file.txt")

        with pytest.raises(ValueError, match="File must be markdown"):
            validate_markdown_format("/path/to/file.py")

    def test_validate_task_ownership_valid(self):
        """Test valid task ownership validation."""
        mock_db = Mock()
        mock_task = Mock(id="task-123", assigned_agent_id="agent-456")
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        # Should not raise
        validate_task_ownership(mock_db, "task-123", "agent-456")

    def test_validate_task_ownership_wrong_agent(self):
        """Test task ownership validation with wrong agent."""
        mock_db = Mock()
        mock_task = Mock(id="task-123", assigned_agent_id="agent-999")
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_task

        with pytest.raises(ValueError, match="not assigned to agent"):
            validate_task_ownership(mock_db, "task-123", "agent-456")

    def test_validate_task_ownership_task_not_found(self):
        """Test task ownership validation with non-existent task."""
        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Task not found"):
            validate_task_ownership(mock_db, "task-123", "agent-456")