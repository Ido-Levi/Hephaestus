"""Tests for workflow result service."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.services.workflow_result_service import WorkflowResultService
from src.core.database import get_db, Workflow, Agent, WorkflowResult


class TestWorkflowResultService:
    """Test cases for workflow result service."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary test file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False
        )
        self.temp_file.write("""# Test Result

## Solution
This is a test solution with proper evidence.

```bash
$ ./test_command
Success: Test completed
Result: PASS
```

## Methodology
1. Analyzed the problem
2. Implemented solution
3. Tested thoroughly
4. Verified results

## Evidence
- Screenshot attached
- Execution logs included
- All tests passing
""")
        self.temp_file.close()
        self.temp_file_path = self.temp_file.name

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)

    @patch('src.services.workflow_result_service.get_db')
    def test_submit_result_success(self, mock_get_db):
        """Test successful result submission."""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock workflow and agent
        mock_workflow = MagicMock()
        mock_workflow.id = "workflow-123"
        mock_agent = MagicMock()
        mock_agent.id = "agent-456"

        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_workflow)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_agent)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))))  # No existing result
        ]

        # Test result submission
        result = WorkflowResultService.submit_result(
            agent_id="agent-456",
            workflow_id="workflow-123",
            markdown_file_path=self.temp_file_path
        )

        # Verify result
        assert result["status"] == "submitted"
        assert result["workflow_id"] == "workflow-123"
        assert result["agent_id"] == "agent-456"
        assert result["validation_status"] == "pending_validation"
        assert "result_id" in result
        assert "created_at" in result

        # Verify database calls
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('src.services.workflow_result_service.get_db')
    def test_submit_result_existing_validated_result(self, mock_get_db):
        """Test submission when workflow already has validated result."""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock workflow and agent
        mock_workflow = MagicMock()
        mock_agent = MagicMock()
        mock_existing_result = MagicMock()
        mock_existing_result.id = "existing-result-123"

        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_workflow)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_agent)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_existing_result))))
        ]

        # Test result submission
        result = WorkflowResultService.submit_result(
            agent_id="agent-456",
            workflow_id="workflow-123",
            markdown_file_path=self.temp_file_path
        )

        # Verify rejection
        assert result["status"] == "rejected"
        assert "already has a validated result" in result["message"]
        assert result["existing_result_id"] == "existing-result-123"

        # Verify no database add called
        mock_db.add.assert_not_called()

    def test_submit_result_file_not_found(self):
        """Test submission with non-existent file."""
        with pytest.raises(FileNotFoundError):
            WorkflowResultService.submit_result(
                agent_id="agent-456",
                workflow_id="workflow-123",
                markdown_file_path="/non/existent/file.md"
            )

    @patch('src.services.workflow_result_service.get_db')
    def test_submit_result_workflow_not_found(self, mock_get_db):
        """Test submission with invalid workflow ID."""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Workflow not found"):
            WorkflowResultService.submit_result(
                agent_id="agent-456",
                workflow_id="invalid-workflow",
                markdown_file_path=self.temp_file_path
            )

    @patch('src.services.workflow_result_service.get_db')
    def test_update_result_status_success(self, mock_get_db):
        """Test successful result status update."""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock result and workflow
        mock_result = MagicMock()
        mock_result.id = "result-123"
        mock_result.workflow_id = "workflow-456"
        mock_workflow = MagicMock()

        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_result)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_workflow))))
        ]

        # Test status update
        result = WorkflowResultService.update_result_status(
            result_id="result-123",
            status="validated",
            feedback="All criteria met",
            evidence={"criteria_passed": True},
            validator_agent_id="validator-789"
        )

        # Verify result
        assert result["result_id"] == "result-123"
        assert result["status"] == "validated"
        assert result["validation_feedback"] == "All criteria met"
        assert result["validated_by"] == "validator-789"

        # Verify workflow updated
        assert mock_workflow.result_found == True
        assert mock_workflow.result_id == "result-123"

        # Verify database commit
        mock_db.commit.assert_called_once()

    @patch('src.services.workflow_result_service.get_db')
    def test_update_result_status_invalid_status(self, mock_get_db):
        """Test update with invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            WorkflowResultService.update_result_status(
                result_id="result-123",
                status="invalid_status",
                feedback="Test feedback"
            )

    @patch('src.services.workflow_result_service.get_db')
    def test_get_workflow_results(self, mock_get_db):
        """Test getting workflow results."""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock results
        mock_result1 = MagicMock()
        mock_result1.id = "result-1"
        mock_result1.agent_id = "agent-1"
        mock_result1.workflow_id = "workflow-123"
        mock_result1.status = "validated"
        mock_result1.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_result1.validated_at = datetime(2024, 1, 1, 13, 0, 0)
        mock_result1.validated_by_agent_id = "validator-1"
        mock_result1.validation_feedback = "Good result"
        mock_result1.result_file_path = "/path/to/result1.md"

        mock_result2 = MagicMock()
        mock_result2.id = "result-2"
        mock_result2.agent_id = "agent-2"
        mock_result2.workflow_id = "workflow-123"
        mock_result2.status = "pending_validation"
        mock_result2.created_at = datetime(2024, 1, 1, 14, 0, 0)
        mock_result2.validated_at = None
        mock_result2.validated_by_agent_id = None
        mock_result2.validation_feedback = None
        mock_result2.result_file_path = "/path/to/result2.md"

        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_result1, mock_result2]

        # Test getting results
        results = WorkflowResultService.get_workflow_results("workflow-123")

        # Verify results
        assert len(results) == 2

        result1 = results[0]
        assert result1["result_id"] == "result-1"
        assert result1["status"] == "validated"
        assert result1["validation_feedback"] == "Good result"
        assert result1["validated_at"] == "2024-01-01T13:00:00"

        result2 = results[1]
        assert result2["result_id"] == "result-2"
        assert result2["status"] == "pending_validation"
        assert result2["validation_feedback"] is None
        assert result2["validated_at"] is None

    @patch('src.services.workflow_result_service.get_db')
    def test_check_workflow_completion(self, mock_get_db):
        """Test checking workflow completion status."""
        # Mock database
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Test with completed workflow
        mock_workflow = MagicMock()
        mock_workflow.result_found = True
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_workflow

        assert WorkflowResultService.check_workflow_completion("workflow-123") == True

        # Test with incomplete workflow
        mock_workflow.result_found = False
        assert WorkflowResultService.check_workflow_completion("workflow-123") == False

        # Test with non-existent workflow
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        assert WorkflowResultService.check_workflow_completion("invalid-workflow") == False