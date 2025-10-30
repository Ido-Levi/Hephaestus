"""Additional tests to improve coverage for result service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.result_service import ResultService


class TestResultServiceAdditionalCoverage:
    """Additional tests to reach 90% coverage."""

    @patch('src.services.result_service.get_db')
    def test_get_results_for_agent(self, mock_get_db):
        """Test retrieving results for a specific agent."""
        # Setup mock results
        mock_result1 = Mock(
            id="result-1",
            agent_id="agent-123",
            task_id="task-1",
            result_type="implementation",
            summary="First result",
            verification_status="verified",
            created_at=datetime.utcnow(),
            verified_at=datetime.utcnow(),
        )
        mock_result2 = Mock(
            id="result-2",
            agent_id="agent-123",
            task_id="task-2",
            result_type="analysis",
            summary="Second result",
            verification_status="unverified",
            created_at=datetime.utcnow(),
            verified_at=None,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.all.return_value = [
            mock_result1, mock_result2
        ]
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Call get_results_for_agent
        results = ResultService.get_results_for_agent("agent-123")

        # Assertions
        assert len(results) == 2
        assert results[0]["result_id"] == "result-1"
        assert results[0]["agent_id"] == "agent-123"
        assert results[0]["task_id"] == "task-1"
        assert results[0]["verification_status"] == "verified"
        assert results[1]["result_id"] == "result-2"
        assert results[1]["task_id"] == "task-2"
        assert results[1]["verification_status"] == "unverified"

        # Verify correct query was made
        mock_db.query.return_value.filter_by.assert_called_once_with(agent_id="agent-123")

    @patch('src.services.result_service.get_db')
    def test_get_result_content(self, mock_get_db):
        """Test retrieving markdown content of a specific result."""
        # Setup mock result
        mock_result = Mock(
            id="result-1",
            markdown_content="# Test Result\n\nThis is the content."
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_result
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Call get_result_content
        content = ResultService.get_result_content("result-1")

        # Assertions
        assert content == "# Test Result\n\nThis is the content."

        # Verify correct query was made
        mock_db.query.return_value.filter_by.assert_called_once_with(id="result-1")

    @patch('src.services.result_service.get_db')
    def test_get_result_content_not_found(self, mock_get_db):
        """Test retrieving content for non-existent result."""
        # Setup mock to return None
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Call get_result_content
        content = ResultService.get_result_content("nonexistent")

        # Assertions
        assert content is None

    @patch('src.services.result_service.get_db')
    def test_verify_result_not_found(self, mock_get_db):
        """Test verifying a result that doesn't exist."""
        # Setup mock to return None
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Call verify_result and expect ValueError
        with pytest.raises(ValueError, match="Result not found"):
            ResultService.verify_result(
                result_id="nonexistent",
                validation_review_id="review-123",
                verified=True
            )

    @patch('src.services.result_service.get_db')
    def test_verify_result_as_disputed(self, mock_get_db):
        """Test marking a result as disputed instead of verified."""
        # Setup mock result
        mock_result = Mock(
            id="result-1",
            verification_status="unverified",
            verified_at=None,
            verified_by_validation_id=None,
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_result
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Call verify_result with verified=False
        result = ResultService.verify_result(
            result_id="result-1",
            validation_review_id="review-123",
            verified=False,  # This should mark as disputed
        )

        # Assertions
        assert result["result_id"] == "result-1"
        assert result["verification_status"] == "disputed"
        assert "verified_at" in result
        assert result["verified_by"] == "review-123"
        assert mock_result.verification_status == "disputed"
        assert mock_result.verified_by_validation_id == "review-123"
        mock_db.commit.assert_called()