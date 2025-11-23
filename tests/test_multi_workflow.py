"""Tests for multi-workflow infrastructure."""

import os
import uuid
import pytest
import tempfile
from datetime import datetime

# Set test database before imports
os.environ["HEPHAESTUS_TEST_DB"] = ":memory:"

from src.core.database import (
    DatabaseManager, Workflow, Phase, Task, WorkflowDefinition as DBWorkflowDefinition,
    get_db
)
from src.phases.phase_manager import PhaseManager
from src.sdk.models import (
    Phase as SDKPhase, WorkflowConfig, WorkflowDefinition, WorkflowExecution,
    ValidationCriteria
)


class TestDatabaseModels:
    """Test database models for multi-workflow support."""

    def setup_method(self):
        """Set up test database."""
        self.db_manager = DatabaseManager(":memory:")
        self.db_manager.create_tables()

    def test_workflow_definition_creation(self):
        """Test creating a workflow definition in database."""
        session = self.db_manager.get_session()
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

    def test_workflow_with_definition_relationship(self):
        """Test that Workflow properly references WorkflowDefinition."""
        session = self.db_manager.get_session()
        try:
            # Create definition
            definition = DBWorkflowDefinition(
                id="bugfix",
                name="Bug Fix",
                description="Fix bugs",
                phases_config=[],
                workflow_config={},
            )
            session.add(definition)
            session.commit()

            # Create workflow execution referencing definition
            workflow = Workflow(
                id=str(uuid.uuid4()),
                name="Bug Fix",
                description="Fixing auth bug #123",
                definition_id="bugfix",
                phases_folder_path="/tmp/test",
                working_directory="/project",
                status="active",
            )
            session.add(workflow)
            session.commit()

            # Verify relationship
            retrieved = session.query(Workflow).filter_by(definition_id="bugfix").first()
            assert retrieved is not None
            assert retrieved.description == "Fixing auth bug #123"
            assert retrieved.working_directory == "/project"

            # Verify back-reference
            definition = session.query(DBWorkflowDefinition).filter_by(id="bugfix").first()
            assert len(definition.executions) == 1
            assert definition.executions[0].description == "Fixing auth bug #123"

        finally:
            session.close()

    def test_multiple_executions_from_same_definition(self):
        """Test creating multiple workflow executions from one definition."""
        session = self.db_manager.get_session()
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


class TestPhaseManager:
    """Test PhaseManager multi-workflow methods."""

    def setup_method(self):
        """Set up test database and phase manager."""
        self.db_manager = DatabaseManager(":memory:")
        self.db_manager.create_tables()
        self.phase_manager = PhaseManager(self.db_manager)

    def test_register_definition(self):
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

        definition_id = self.phase_manager.register_definition(
            definition_id="test-workflow",
            name="Test Workflow",
            description="A test workflow",
            phases_config=phases_config,
            workflow_config=workflow_config,
        )

        assert definition_id == "test-workflow"
        assert "test-workflow" in self.phase_manager.definitions

    def test_register_definition_update(self):
        """Test updating an existing workflow definition."""
        # Register first time
        self.phase_manager.register_definition(
            definition_id="update-test",
            name="Original Name",
            description="Original description",
        )

        # Update
        self.phase_manager.register_definition(
            definition_id="update-test",
            name="Updated Name",
            description="Updated description",
        )

        # Verify update
        definition = self.phase_manager.get_definition("update-test")
        assert definition.name == "Updated Name"
        assert definition.description == "Updated description"

    def test_start_execution(self):
        """Test starting a workflow execution from a definition."""
        # First register a definition
        phases_config = [
            {
                "order": 1,
                "name": "Phase 1",
                "description": "First phase",
                "done_definitions": ["Phase 1 complete"],
            },
        ]

        self.phase_manager.register_definition(
            definition_id="exec-test",
            name="Execution Test",
            phases_config=phases_config,
        )

        # Start execution
        workflow_id = self.phase_manager.start_execution(
            definition_id="exec-test",
            description="Test execution",
            working_directory="/project/path",
        )

        assert workflow_id is not None
        assert workflow_id in self.phase_manager.active_executions
        assert self.phase_manager.active_executions[workflow_id] == "exec-test"

    def test_start_execution_creates_phases(self):
        """Test that start_execution creates phases in database."""
        # Register definition with phases
        phases_config = [
            {"order": 1, "name": "Phase 1", "description": "First", "done_definitions": []},
            {"order": 2, "name": "Phase 2", "description": "Second", "done_definitions": []},
        ]

        self.phase_manager.register_definition(
            definition_id="phases-test",
            name="Phases Test",
            phases_config=phases_config,
        )

        # Start execution
        workflow_id = self.phase_manager.start_execution(
            definition_id="phases-test",
            description="Test phases",
        )

        # Verify phases were created
        phases = self.phase_manager.get_phases_for_workflow(workflow_id)
        assert len(phases) == 2
        assert phases[0].name == "Phase 1"
        assert phases[1].name == "Phase 2"

    def test_get_workflow(self):
        """Test getting a specific workflow execution."""
        # Register and start
        self.phase_manager.register_definition(
            definition_id="get-test",
            name="Get Test",
        )
        workflow_id = self.phase_manager.start_execution(
            definition_id="get-test",
            description="Get test execution",
        )

        # Get workflow
        workflow = self.phase_manager.get_workflow(workflow_id)
        assert workflow is not None
        assert workflow.id == workflow_id
        assert workflow.description == "Get test execution"

    def test_get_nonexistent_workflow(self):
        """Test getting a workflow that doesn't exist."""
        workflow = self.phase_manager.get_workflow("nonexistent-id")
        assert workflow is None

    def test_list_definitions(self):
        """Test listing all workflow definitions."""
        # Register multiple definitions
        for i in range(3):
            self.phase_manager.register_definition(
                definition_id=f"def-{i}",
                name=f"Definition {i}",
            )

        # List definitions
        definitions = self.phase_manager.list_definitions()
        assert len(definitions) == 3

    def test_list_active_executions(self):
        """Test listing active workflow executions."""
        # Register definition
        self.phase_manager.register_definition(
            definition_id="list-test",
            name="List Test",
        )

        # Start multiple executions
        for i in range(3):
            self.phase_manager.start_execution(
                definition_id="list-test",
                description=f"Execution {i}",
            )

        # List executions
        executions = self.phase_manager.list_active_executions(status="active")
        assert len(executions) == 3

    def test_get_execution_stats(self):
        """Test getting execution statistics."""
        # Register and start
        self.phase_manager.register_definition(
            definition_id="stats-test",
            name="Stats Test",
            phases_config=[
                {"order": 1, "name": "Phase 1", "description": "Test", "done_definitions": []},
            ],
        )
        workflow_id = self.phase_manager.start_execution(
            definition_id="stats-test",
            description="Stats test",
        )

        # Get stats (no tasks yet)
        stats = self.phase_manager.get_execution_stats(workflow_id)
        assert stats["total_tasks"] == 0
        assert stats["active_tasks"] == 0
        assert stats["done_tasks"] == 0
        assert stats["failed_tasks"] == 0

    def test_start_execution_invalid_definition(self):
        """Test starting execution with invalid definition ID."""
        with pytest.raises(ValueError) as exc_info:
            self.phase_manager.start_execution(
                definition_id="nonexistent",
                description="Should fail",
            )
        assert "not found" in str(exc_info.value)

    def test_multiple_concurrent_executions(self):
        """Test running multiple concurrent executions."""
        # Register two different definitions
        self.phase_manager.register_definition(
            definition_id="def-a",
            name="Definition A",
        )
        self.phase_manager.register_definition(
            definition_id="def-b",
            name="Definition B",
        )

        # Start executions from both
        wf_a1 = self.phase_manager.start_execution("def-a", "Execution A1")
        wf_a2 = self.phase_manager.start_execution("def-a", "Execution A2")
        wf_b1 = self.phase_manager.start_execution("def-b", "Execution B1")

        # Verify all are tracked
        assert len(self.phase_manager.active_executions) == 3
        assert self.phase_manager.active_executions[wf_a1] == "def-a"
        assert self.phase_manager.active_executions[wf_a2] == "def-a"
        assert self.phase_manager.active_executions[wf_b1] == "def-b"

    def test_load_active_executions(self):
        """Test loading active executions on startup."""
        # Register and start
        self.phase_manager.register_definition(
            definition_id="load-test",
            name="Load Test",
        )
        workflow_id = self.phase_manager.start_execution(
            definition_id="load-test",
            description="Test loading",
        )

        # Create new phase manager (simulating restart)
        new_manager = PhaseManager(self.db_manager)
        new_manager.load_active_executions()

        # Verify state was loaded
        assert workflow_id in new_manager.active_executions
        assert "load-test" in new_manager.definitions


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

        # Should still work but definitions dict will be empty
        # (backward compatibility maintains phases_list)
        assert sdk.phases_list == phases
        assert len(sdk.phases_map) == 1

    def test_sdk_list_workflow_definitions(self):
        """Test listing workflow definitions."""
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


class TestWorkflowConfigSerialization:
    """Test workflow config serialization for database storage."""

    def test_phases_config_to_json(self):
        """Test that phases config can be serialized to JSON."""
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

        # Verify it can round-trip through database
        db_manager = DatabaseManager(":memory:")
        db_manager.create_tables()

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
