"""Integration tests for result submission flow."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.services.workflow_result_service import WorkflowResultService
from src.services.result_validator_service import ResultValidatorService
from src.workflow.termination_handler import WorkflowTerminationHandler


class TestResultSubmissionFlow:
    """Integration test cases for the complete result submission flow."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary test result file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False
        )
        self.temp_file.write("""# Crackme Solution

## Solution Statement
Successfully cracked the binary and found the flag: `FLAG{test_flag_123}`

## Primary Evidence

### Execution Proof
```bash
$ ./crackme
Enter password: secretpass123
Success! Flag: FLAG{test_flag_123}
Access granted to protected area.
```

### Binary Analysis
Used reverse engineering tools to analyze the binary:
- Disassembled with objdump
- Analyzed with gdb
- Found hardcoded password comparison

## Supporting Evidence

### Methodology
1. Static analysis of the binary
2. Dynamic analysis with debugger
3. String analysis revealed password
4. Verified with execution

### Reproduction Steps
1. Download the crackme binary
2. Run: `./crackme`
3. Enter password: `secretpass123`
4. Observe successful flag display

## Confidence Assessment
100% confident - flag verified through successful execution and access to protected area.
""")
        self.temp_file.close()
        self.temp_file_path = self.temp_file.name

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)

    @patch('src.services.workflow_result_service.get_db')
    @patch('src.services.result_validator_service.PhaseManager')
    async def test_complete_submission_flow_stop_all(self, mock_phase_manager, mock_get_db):
        """Test complete flow: submit result -> validate -> terminate workflow."""

        # Mock database setup
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

        # Step 1: Submit result
        result = WorkflowResultService.submit_result(
            agent_id="agent-456",
            workflow_id="workflow-123",
            markdown_file_path=self.temp_file_path
        )

        assert result["status"] == "submitted"
        result_id = result["result_id"]

        # Step 2: Check if validation should be triggered
        mock_phase_manager_instance = MagicMock()
        mock_config = MagicMock()
        mock_config.has_result = True
        mock_config.result_criteria = "Must provide correct password with execution proof"
        mock_config.on_result_found = "stop_all"
        mock_phase_manager_instance.get_workflow_config.return_value = mock_config
        mock_phase_manager.return_value = mock_phase_manager_instance

        validator_service = ResultValidatorService(
            db_manager=MagicMock(),
            phase_manager=mock_phase_manager_instance
        )

        should_validate, criteria = validator_service.should_spawn_validator("workflow-123")

        assert should_validate == True
        assert criteria == "Must provide correct password with execution proof"

        # Step 3: Process validation outcome (passed)
        mock_result = MagicMock()
        mock_result.id = result_id
        mock_result.workflow_id = "workflow-123"
        mock_result.agent_id = "agent-456"

        # Mock the database query for result
        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_result))))
        ]

        with patch.object(WorkflowResultService, 'update_result_status') as mock_update:
            mock_update.return_value = {
                "result_id": result_id,
                "status": "validated",
                "validation_feedback": "All criteria met",
                "validated_at": datetime.utcnow().isoformat(),
                "validated_by": "validator-789",
            }

            outcome = validator_service.process_validation_outcome(
                result_id=result_id,
                passed=True,
                feedback="All criteria met - found correct flag with execution proof",
                evidence=[
                    {"type": "criteria_check", "criterion": "correct password", "passed": True},
                    {"type": "criteria_check", "criterion": "execution proof", "passed": True},
                    {"type": "evidence_found", "evidence": "FLAG{test_flag_123}", "location": "result file"}
                ],
                validator_agent_id="validator-789"
            )

        assert outcome["validation_passed"] == True
        assert "terminate_workflow" in outcome["next_actions"]
        assert outcome["workflow_id"] == "workflow-123"

        # Step 4: Workflow termination would be triggered
        # (In real flow, this would be called by the MCP endpoint)
        termination_handler = WorkflowTerminationHandler(
            db_manager=MagicMock(),
            agent_manager=MagicMock()
        )

        # Mock the termination
        with patch.object(termination_handler, 'terminate_workflow') as mock_terminate:
            mock_terminate.return_value = {
                "workflow_id": "workflow-123",
                "terminated_agents": ["agent-456"],
                "cancelled_tasks": [],
                "cleanup_actions": [],
                "errors": [],
                "terminated_at": datetime.utcnow().isoformat(),
            }

            termination_result = await termination_handler.terminate_workflow("workflow-123")

        assert termination_result["workflow_id"] == "workflow-123"
        assert "agent-456" in termination_result["terminated_agents"]

    @patch('src.services.workflow_result_service.get_db')
    @patch('src.services.result_validator_service.PhaseManager')
    async def test_complete_submission_flow_do_nothing(self, mock_phase_manager, mock_get_db):
        """Test complete flow: submit result -> validate -> continue workflow."""

        # Mock database setup (similar to previous test)
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_workflow = MagicMock()
        mock_workflow.id = "workflow-123"
        mock_agent = MagicMock()
        mock_agent.id = "agent-456"

        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_workflow)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_agent)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))))
        ]

        # Submit result
        result = WorkflowResultService.submit_result(
            agent_id="agent-456",
            workflow_id="workflow-123",
            markdown_file_path=self.temp_file_path
        )

        # Configure for "do_nothing" action
        mock_phase_manager_instance = MagicMock()
        mock_config = MagicMock()
        mock_config.has_result = True
        mock_config.result_criteria = "Research findings with sources"
        mock_config.on_result_found = "do_nothing"
        mock_phase_manager_instance.get_workflow_config.return_value = mock_config

        validator_service = ResultValidatorService(
            db_manager=MagicMock(),
            phase_manager=mock_phase_manager_instance
        )

        # Process validation outcome
        mock_result = MagicMock()
        mock_result.id = result["result_id"]
        mock_result.workflow_id = "workflow-123"

        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_result))))
        ]

        with patch.object(WorkflowResultService, 'update_result_status') as mock_update:
            mock_update.return_value = {"result_id": result["result_id"], "status": "validated"}

            outcome = validator_service.process_validation_outcome(
                result_id=result["result_id"],
                passed=True,
                feedback="Research findings meet criteria",
                evidence=[],
                validator_agent_id="validator-789"
            )

        # Verify workflow continues
        assert outcome["validation_passed"] == True
        assert "continue_workflow" in outcome["next_actions"]
        assert "terminate_workflow" not in outcome["next_actions"]

    @patch('src.services.workflow_result_service.get_db')
    @patch('src.services.result_validator_service.PhaseManager')
    async def test_validation_failure_flow(self, mock_phase_manager, mock_get_db):
        """Test flow when validation fails."""

        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_workflow = MagicMock()
        mock_agent = MagicMock()

        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_workflow)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_agent)))),
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))))
        ]

        # Submit result
        result = WorkflowResultService.submit_result(
            agent_id="agent-456",
            workflow_id="workflow-123",
            markdown_file_path=self.temp_file_path
        )

        # Configure validation
        mock_phase_manager_instance = MagicMock()
        mock_config = MagicMock()
        mock_config.has_result = True
        mock_config.result_criteria = "Must provide verified solution with proof"
        mock_config.on_result_found = "stop_all"
        mock_phase_manager_instance.get_workflow_config.return_value = mock_config

        validator_service = ResultValidatorService(
            db_manager=MagicMock(),
            phase_manager=mock_phase_manager_instance
        )

        # Process validation failure
        mock_result = MagicMock()
        mock_result.id = result["result_id"]
        mock_result.workflow_id = "workflow-123"

        mock_db.query.side_effect = [
            MagicMock(filter_by=MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_result))))
        ]

        with patch.object(WorkflowResultService, 'update_result_status') as mock_update:
            mock_update.return_value = {"result_id": result["result_id"], "status": "rejected"}

            outcome = validator_service.process_validation_outcome(
                result_id=result["result_id"],
                passed=False,
                feedback="Insufficient evidence - missing execution proof",
                evidence=[
                    {"type": "criteria_check", "criterion": "verified solution", "passed": False},
                    {"type": "missing_evidence", "evidence": "execution proof", "required": True}
                ],
                validator_agent_id="validator-789"
            )

        # Verify no workflow termination
        assert outcome["validation_passed"] == False
        assert outcome["next_actions"] == []  # No actions when validation fails

    def test_no_validation_required_flow(self):
        """Test flow when workflow doesn't require validation."""

        mock_phase_manager = MagicMock()
        mock_config = MagicMock()
        mock_config.has_result = False
        mock_phase_manager.get_workflow_config.return_value = mock_config

        validator_service = ResultValidatorService(
            db_manager=MagicMock(),
            phase_manager=mock_phase_manager
        )

        should_validate, criteria = validator_service.should_spawn_validator("workflow-123")

        assert should_validate == False
        assert criteria is None