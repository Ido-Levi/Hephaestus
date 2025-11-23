"""End-to-end tests for multi-workflow support.

This module tests end-to-end workflow scenarios including:
1. Multiple concurrent workflows
2. Same definition with multiple executions
3. Workflow isolation
4. SDK client integration
5. Backward compatibility
"""

import pytest
import os
import uuid
from datetime import datetime

# Set test environment before imports
os.environ["HEPHAESTUS_TEST_DB"] = ":memory:"

from src.core.database import DatabaseManager, Task, Agent, Workflow
from src.phases.phase_manager import PhaseManager
from src.sdk.models import (
    Phase as SDKPhase, WorkflowConfig, WorkflowDefinition, WorkflowExecution
)


class TestMultiWorkflowE2E:
    """End-to-end tests for multiple concurrent workflows."""

    @pytest.fixture
    def multi_definition_phase_manager(self, db_manager, test_workflow_definition, test_bugfix_definition):
        """Create phase manager with multiple workflow definitions."""
        manager = PhaseManager(db_manager)

        # Register first definition (test workflow)
        phases_config_1 = [
            {
                "order": phase.id,
                "name": phase.name,
                "description": phase.description,
                "done_definitions": phase.done_definitions,
                "working_directory": phase.working_directory,
            }
            for phase in test_workflow_definition.phases
        ]

        workflow_config_1 = {}
        if test_workflow_definition.config:
            workflow_config_1 = {
                "has_result": test_workflow_definition.config.has_result,
                "result_criteria": test_workflow_definition.config.result_criteria,
            }

        manager.register_definition(
            definition_id=test_workflow_definition.id,
            name=test_workflow_definition.name,
            description=test_workflow_definition.description,
            phases_config=phases_config_1,
            workflow_config=workflow_config_1,
        )

        # Register second definition (bugfix workflow)
        phases_config_2 = [
            {
                "order": phase.id,
                "name": phase.name,
                "description": phase.description,
                "done_definitions": phase.done_definitions,
                "working_directory": phase.working_directory,
            }
            for phase in test_bugfix_definition.phases
        ]

        workflow_config_2 = {}
        if test_bugfix_definition.config:
            workflow_config_2 = {
                "has_result": test_bugfix_definition.config.has_result,
                "result_criteria": test_bugfix_definition.config.result_criteria,
            }

        manager.register_definition(
            definition_id=test_bugfix_definition.id,
            name=test_bugfix_definition.name,
            description=test_bugfix_definition.description,
            phases_config=phases_config_2,
            workflow_config=workflow_config_2,
        )

        yield manager

    def test_concurrent_workflows_different_definitions(self, multi_definition_phase_manager):
        """Test running two workflows concurrently from different definitions."""
        manager = multi_definition_phase_manager

        # Start two different workflows
        wf1_id = manager.start_execution("test-workflow", "Build URL Shortener")
        wf2_id = manager.start_execution("bugfix-workflow", "Fix Auth Bug #123")

        # Verify IDs are different
        assert wf1_id != wf2_id

        # Verify both are tracked with correct definitions
        assert manager.active_executions[wf1_id] == "test-workflow"
        assert manager.active_executions[wf2_id] == "bugfix-workflow"

        # Verify both can be retrieved
        wf1 = manager.get_workflow(wf1_id)
        wf2 = manager.get_workflow(wf2_id)

        assert wf1 is not None
        assert wf2 is not None
        assert wf1.description == "Build URL Shortener"
        assert wf2.description == "Fix Auth Bug #123"

    def test_same_definition_multiple_executions(self, multi_definition_phase_manager):
        """Test running multiple instances of the same workflow definition."""
        manager = multi_definition_phase_manager

        # Start two workflows from the same definition
        wf1_id = manager.start_execution("test-workflow", "Project A - URL Shortener")
        wf2_id = manager.start_execution("test-workflow", "Project B - Chat App")

        # Verify IDs are different
        assert wf1_id != wf2_id

        # Both should have the same definition
        assert manager.active_executions[wf1_id] == "test-workflow"
        assert manager.active_executions[wf2_id] == "test-workflow"

        # Verify distinct descriptions
        wf1 = manager.get_workflow(wf1_id)
        wf2 = manager.get_workflow(wf2_id)

        assert wf1.description == "Project A - URL Shortener"
        assert wf2.description == "Project B - Chat App"

    def test_workflow_isolation_tasks(self, multi_definition_phase_manager, db_manager):
        """Test that tasks are properly isolated between workflows."""
        manager = multi_definition_phase_manager

        # Start two workflows
        wf1_id = manager.start_execution("test-workflow", "Project 1")
        wf2_id = manager.start_execution("test-workflow", "Project 2")

        # Create tasks in each workflow
        session = db_manager.get_session()
        try:
            # Create tasks for workflow 1
            for i in range(3):
                task = Task(
                    id=str(uuid.uuid4()),
                    raw_description=f"Task {i} in WF1",
                    enriched_description=f"Enriched task {i} in WF1",
                    done_definition="Complete",
                    created_by_agent_id="test-agent",
                    workflow_id=wf1_id,
                    status="pending",
                    priority="medium",
                )
                session.add(task)

            # Create tasks for workflow 2
            for i in range(2):
                task = Task(
                    id=str(uuid.uuid4()),
                    raw_description=f"Task {i} in WF2",
                    enriched_description=f"Enriched task {i} in WF2",
                    done_definition="Complete",
                    created_by_agent_id="test-agent",
                    workflow_id=wf2_id,
                    status="pending",
                    priority="medium",
                )
                session.add(task)

            session.commit()

            # Verify task counts
            wf1_tasks = session.query(Task).filter_by(workflow_id=wf1_id).count()
            wf2_tasks = session.query(Task).filter_by(workflow_id=wf2_id).count()

            assert wf1_tasks == 3
            assert wf2_tasks == 2

            # Verify stats through phase manager
            stats1 = manager.get_execution_stats(wf1_id)
            stats2 = manager.get_execution_stats(wf2_id)

            assert stats1["total_tasks"] == 3
            assert stats2["total_tasks"] == 2

        finally:
            session.close()

    def test_list_definitions(self, multi_definition_phase_manager):
        """Test listing all workflow definitions."""
        manager = multi_definition_phase_manager

        definitions = manager.list_definitions()

        assert len(definitions) == 2
        def_ids = [d.id for d in definitions]
        assert "test-workflow" in def_ids
        assert "bugfix-workflow" in def_ids

    def test_list_active_executions(self, multi_definition_phase_manager):
        """Test listing active workflow executions."""
        manager = multi_definition_phase_manager

        # Start multiple executions
        manager.start_execution("test-workflow", "Execution 1")
        manager.start_execution("test-workflow", "Execution 2")
        manager.start_execution("bugfix-workflow", "Bug Fix 1")

        # List all active executions
        executions = manager.list_active_executions(status="active")

        assert len(executions) >= 3

    def test_get_definition(self, multi_definition_phase_manager):
        """Test getting a specific workflow definition."""
        manager = multi_definition_phase_manager

        definition = manager.get_definition("test-workflow")

        assert definition is not None
        assert definition.name == "Test Workflow"

    def test_get_nonexistent_definition(self, multi_definition_phase_manager):
        """Test getting a definition that doesn't exist."""
        manager = multi_definition_phase_manager

        definition = manager.get_definition("nonexistent-workflow")
        assert definition is None

    def test_execution_creates_phases(self, multi_definition_phase_manager):
        """Test that starting execution creates phases in database."""
        manager = multi_definition_phase_manager

        workflow_id = manager.start_execution(
            definition_id="test-workflow",
            description="Test phases creation",
        )

        # Verify phases were created
        phases = manager.get_phases_for_workflow(workflow_id)

        # Test workflow has 3 phases
        assert len(phases) == 3
        phase_names = [p.name for p in phases]
        assert "Planning" in phase_names
        assert "Implementation" in phase_names
        assert "Testing" in phase_names


class TestSDKClientMultiWorkflow:
    """Test SDK client multi-workflow initialization and methods."""

    def test_sdk_init_with_workflow_definitions(self):
        """Test SDK initialization with multiple workflow definitions."""
        from src.sdk.client import HephaestusSDK

        phases1 = [
            SDKPhase(
                id=1,
                name="Phase 1",
                description="First",
                done_definitions=["Done"],
                working_directory="/project",
            ),
        ]
        phases2 = [
            SDKPhase(
                id=1,
                name="Phase A",
                description="Alpha",
                done_definitions=["Complete"],
                working_directory="/other",
            ),
        ]

        definitions = [
            WorkflowDefinition(
                id="workflow-1",
                name="Workflow One",
                phases=phases1,
            ),
            WorkflowDefinition(
                id="workflow-2",
                name="Workflow Two",
                phases=phases2,
            ),
        ]

        sdk = HephaestusSDK(workflow_definitions=definitions)

        assert len(sdk.definitions) == 2
        assert "workflow-1" in sdk.definitions
        assert "workflow-2" in sdk.definitions
        assert sdk.definitions["workflow-1"].name == "Workflow One"
        assert sdk.definitions["workflow-2"].name == "Workflow Two"

    def test_sdk_init_backward_compatibility_phases(self):
        """Test SDK initialization with legacy phases parameter."""
        from src.sdk.client import HephaestusSDK

        phases = [
            SDKPhase(
                id=1,
                name="Legacy Phase",
                description="Old style",
                done_definitions=["Done"],
                working_directory="/project",
            ),
        ]

        sdk = HephaestusSDK(phases=phases)

        # Should still work with backward compatibility
        assert sdk.phases_list == phases
        assert len(sdk.phases_map) == 1
        assert 1 in sdk.phases_map

    def test_sdk_list_workflow_definitions(self):
        """Test listing workflow definitions from SDK."""
        from src.sdk.client import HephaestusSDK

        definitions = [
            WorkflowDefinition(
                id="def-1",
                name="Definition 1",
                phases=[],
            ),
            WorkflowDefinition(
                id="def-2",
                name="Definition 2",
                phases=[],
            ),
        ]

        sdk = HephaestusSDK(workflow_definitions=definitions)
        listed = sdk.list_workflow_definitions()

        assert len(listed) == 2

    def test_sdk_init_with_config_object(self):
        """Test SDK initialization with both workflow_definitions and config."""
        from src.sdk.client import HephaestusSDK
        from src.sdk.config import HephaestusConfig

        phases = [
            SDKPhase(
                id=1,
                name="Phase",
                description="Test",
                done_definitions=["Done"],
                working_directory="/project",
            ),
        ]

        definitions = [
            WorkflowDefinition(
                id="config-test",
                name="Config Test",
                phases=phases,
                config=WorkflowConfig(has_result=True),
            ),
        ]

        config = HephaestusConfig(
            llm_provider="anthropic",
            mcp_port=9000,
        )

        sdk = HephaestusSDK(workflow_definitions=definitions, config=config)

        assert sdk.config.mcp_port == 9000
        assert "config-test" in sdk.definitions

    def test_sdk_validation_error_no_phases(self):
        """Test that SDK raises error when no phases are provided."""
        from src.sdk.client import HephaestusSDK

        with pytest.raises(ValueError) as exc_info:
            HephaestusSDK()
        assert "workflow_definitions" in str(exc_info.value) or "phases" in str(exc_info.value)

    def test_sdk_validation_error_both_phases_and_dir(self):
        """Test that SDK raises error when both phases and phases_dir provided."""
        from src.sdk.client import HephaestusSDK

        phases = [
            SDKPhase(
                id=1,
                name="Phase",
                description="Test",
                done_definitions=["Done"],
                working_directory="/project",
            ),
        ]

        with pytest.raises(ValueError) as exc_info:
            HephaestusSDK(phases=phases, phases_dir="/some/dir")
        assert "both" in str(exc_info.value).lower()


class TestSDKModels:
    """Test SDK model dataclasses for multi-workflow."""

    def test_workflow_definition_creation(self):
        """Test creating a WorkflowDefinition dataclass."""
        phases = [
            SDKPhase(
                id=1,
                name="Planning",
                description="Plan the project",
                done_definitions=["Requirements documented"],
                working_directory="/project",
            ),
            SDKPhase(
                id=2,
                name="Implementation",
                description="Implement code",
                done_definitions=["Code written"],
                working_directory="/project",
            ),
        ]

        config = WorkflowConfig(
            has_result=True,
            result_criteria="Working application",
            on_result_found="stop_all",
        )

        definition = WorkflowDefinition(
            id="prd-to-software",
            name="PRD to Software Builder",
            phases=phases,
            config=config,
            description="Build software from PRD",
        )

        assert definition.id == "prd-to-software"
        assert definition.name == "PRD to Software Builder"
        assert len(definition.phases) == 2
        assert definition.config.has_result is True
        assert definition.description == "Build software from PRD"

    def test_workflow_execution_creation(self):
        """Test creating a WorkflowExecution dataclass."""
        execution = WorkflowExecution(
            id="abc-123",
            definition_id="prd-to-software",
            description="Building URL Shortener",
            status="active",
            created_at=datetime.utcnow(),
            active_tasks=5,
            total_tasks=10,
            done_tasks=3,
            failed_tasks=1,
            active_agents=2,
            working_directory="/project",
            definition_name="PRD to Software Builder",
        )

        assert execution.id == "abc-123"
        assert execution.definition_id == "prd-to-software"
        assert execution.status == "active"
        assert execution.active_tasks == 5
        assert execution.total_tasks == 10
        assert execution.active_agents == 2

    def test_workflow_definition_default_values(self):
        """Test WorkflowDefinition with default values."""
        definition = WorkflowDefinition(
            id="simple",
            name="Simple Workflow",
            phases=[],
        )

        assert definition.config is None
        assert definition.description == ""

    def test_workflow_execution_default_values(self):
        """Test WorkflowExecution with default values."""
        execution = WorkflowExecution(
            id="test-id",
            definition_id="test-def",
            description="Test",
            status="active",
            created_at=datetime.utcnow(),
        )

        assert execution.active_tasks == 0
        assert execution.total_tasks == 0
        assert execution.done_tasks == 0
        assert execution.failed_tasks == 0
        assert execution.active_agents == 0
        assert execution.working_directory is None
        assert execution.definition_name is None


class TestWorkflowConfigSerialization:
    """Test workflow config serialization for database storage."""

    def test_phases_config_to_json(self, db_manager):
        """Test that phases config can be serialized to JSON in database."""
        from src.core.database import WorkflowDefinition as DBWorkflowDefinition

        phases_config = [
            {
                "order": 1,
                "name": "Planning",
                "description": "Plan the project",
                "done_definitions": ["Requirements documented", "Design approved"],
                "additional_notes": "Be thorough",
                "outputs": "Design document",
                "working_directory": "/project",
            },
        ]

        session = db_manager.get_session()
        try:
            definition = DBWorkflowDefinition(
                id="serialize-test",
                name="Serialize Test",
                phases_config=phases_config,
                workflow_config={},
            )
            session.add(definition)
            session.commit()

            # Retrieve
            retrieved = session.query(DBWorkflowDefinition).filter_by(id="serialize-test").first()
            assert retrieved.phases_config[0]["name"] == "Planning"
            assert len(retrieved.phases_config[0]["done_definitions"]) == 2

        finally:
            session.close()


class TestDatabaseModels:
    """Test database models for multi-workflow support."""

    def test_workflow_definition_creation(self, db_manager):
        """Test creating a workflow definition in database."""
        from src.core.database import WorkflowDefinition as DBWorkflowDefinition

        session = db_manager.get_session()
        try:
            definition = DBWorkflowDefinition(
                id="prd-to-software",
                name="PRD to Software Builder",
                description="Build software from PRD",
                phases_config=[
                    {"order": 1, "name": "Planning", "description": "Plan the project"},
                    {"order": 2, "name": "Implementation", "description": "Implement features"},
                ],
                workflow_config={
                    "has_result": True,
                    "result_criteria": "Working software",
                    "on_result_found": "stop_all",
                },
            )
            session.add(definition)
            session.commit()

            # Retrieve and verify
            retrieved = session.query(DBWorkflowDefinition).filter_by(id="prd-to-software").first()
            assert retrieved is not None
            assert retrieved.name == "PRD to Software Builder"
            assert len(retrieved.phases_config) == 2
            assert retrieved.workflow_config["has_result"] is True

        finally:
            session.close()

    def test_multiple_executions_from_same_definition(self, db_manager):
        """Test creating multiple workflow executions from one definition."""
        from src.core.database import WorkflowDefinition as DBWorkflowDefinition

        session = db_manager.get_session()
        try:
            # Create definition
            definition = DBWorkflowDefinition(
                id="feature-build",
                name="Feature Build",
                description="Build new features",
                phases_config=[],
                workflow_config={},
            )
            session.add(definition)
            session.commit()

            # Create multiple executions
            for i in range(3):
                workflow = Workflow(
                    id=str(uuid.uuid4()),
                    name="Feature Build",
                    description=f"Building feature {i+1}",
                    definition_id="feature-build",
                    phases_folder_path="/tmp/test",
                    status="active",
                )
                session.add(workflow)
            session.commit()

            # Verify
            executions = session.query(Workflow).filter_by(definition_id="feature-build").all()
            assert len(executions) == 3

        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
