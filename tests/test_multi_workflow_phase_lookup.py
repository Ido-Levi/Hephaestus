"""Tests for multi-workflow phase lookup fix.

This test file verifies the fix for the bug where starting a second workflow
would incorrectly use the first workflow's phases when creating the initial task.

The bug was caused by:
1. phase_manager.workflow_id (singleton) only being set for the FIRST workflow
2. get_phase_for_task() using self.workflow_id instead of the provided workflow_id
3. Task creation using the wrong workflow_id from phase context

The fix ensures:
1. get_phase_for_task() accepts and uses an explicit workflow_id parameter
2. Task creation passes request.workflow_id to phase lookup
3. request.workflow_id takes priority over derived workflow_id
"""

import pytest
import uuid
import os

# Set test environment before imports
os.environ["HEPHAESTUS_TEST_DB"] = ":memory:"

from src.core.database import DatabaseManager, Phase, Workflow
from src.phases.phase_manager import PhaseManager


class TestGetPhaseForTaskWithWorkflowId:
    """Test that get_phase_for_task correctly uses the workflow_id parameter."""

    @pytest.fixture
    def db_manager(self):
        """Create a fresh in-memory database manager for each test."""
        manager = DatabaseManager(":memory:")
        manager.create_tables()
        yield manager

    @pytest.fixture
    def phase_manager_with_two_workflows(self, db_manager):
        """Create a phase manager with two different workflows registered."""
        manager = PhaseManager(db_manager)

        # Register first workflow definition (prd_to_software)
        phases_config_1 = [
            {
                "order": 1,
                "name": "Requirements Analysis",
                "description": "Analyze PRD and create requirements",
                "done_definitions": ["Requirements documented"],
            },
            {
                "order": 2,
                "name": "Implementation",
                "description": "Implement the solution",
                "done_definitions": ["Code written"],
            },
        ]

        manager.register_definition(
            definition_id="prd-to-software",
            name="PRD to Software",
            description="Build software from PRD",
            phases_config=phases_config_1,
        )

        # Register second workflow definition (bugfix)
        phases_config_2 = [
            {
                "order": 1,
                "name": "Bug Analysis",
                "description": "Analyze and reproduce the bug",
                "done_definitions": ["Bug reproduced", "Root cause identified"],
            },
            {
                "order": 2,
                "name": "Fix Implementation",
                "description": "Implement the fix",
                "done_definitions": ["Fix implemented", "Tests pass"],
            },
        ]

        manager.register_definition(
            definition_id="bugfix",
            name="Bug Fix",
            description="Fix a bug",
            phases_config=phases_config_2,
        )

        return manager

    def test_get_phase_for_task_uses_explicit_workflow_id(self, phase_manager_with_two_workflows):
        """Test that get_phase_for_task uses the explicitly provided workflow_id."""
        manager = phase_manager_with_two_workflows

        # Start first workflow (prd-to-software)
        result1 = manager.start_execution(
            definition_id="prd-to-software",
            description="First workflow execution",
        )
        # Handle tuple return (workflow_id, initial_task_info)
        workflow_id_1 = result1[0] if isinstance(result1, tuple) else result1

        # Start second workflow (bugfix)
        result2 = manager.start_execution(
            definition_id="bugfix",
            description="Second workflow execution",
        )
        workflow_id_2 = result2[0] if isinstance(result2, tuple) else result2

        # Verify the singleton is set to the first workflow (the bug condition)
        assert manager.workflow_id == workflow_id_1, \
            "Singleton should be set to first workflow (this is expected legacy behavior)"

        # Get Phase 1 for first workflow - should work with singleton
        phase_1_wf1 = manager.get_phase_for_task(
            phase_id=None,
            order=1,
            requesting_agent_id="test-agent",
            workflow_id=workflow_id_1  # Explicit workflow_id
        )
        assert phase_1_wf1 is not None, "Should find Phase 1 for first workflow"

        # Get Phase 1 for second workflow - MUST use explicit workflow_id, not singleton
        phase_1_wf2 = manager.get_phase_for_task(
            phase_id=None,
            order=1,
            requesting_agent_id="test-agent",
            workflow_id=workflow_id_2  # Explicit workflow_id for SECOND workflow
        )
        assert phase_1_wf2 is not None, "Should find Phase 1 for second workflow"

        # CRITICAL: The two phases should be DIFFERENT
        assert phase_1_wf1 != phase_1_wf2, \
            "Phase 1 of first workflow should be different from Phase 1 of second workflow"

    def test_phase_belongs_to_correct_workflow(self, phase_manager_with_two_workflows):
        """Verify that the returned phase actually belongs to the correct workflow."""
        manager = phase_manager_with_two_workflows

        # Start both workflows
        result1 = manager.start_execution("prd-to-software", "First workflow")
        workflow_id_1 = result1[0] if isinstance(result1, tuple) else result1

        result2 = manager.start_execution("bugfix", "Second workflow")
        workflow_id_2 = result2[0] if isinstance(result2, tuple) else result2

        # Get Phase 1 for second workflow
        phase_id = manager.get_phase_for_task(
            phase_id=None,
            order=1,
            workflow_id=workflow_id_2
        )

        # Verify the phase belongs to the second workflow
        session = manager.db_manager.get_session()
        try:
            phase = session.query(Phase).filter_by(id=phase_id).first()
            assert phase is not None, "Phase should exist"
            assert phase.workflow_id == workflow_id_2, \
                f"Phase should belong to workflow_id_2 ({workflow_id_2}), not {phase.workflow_id}"
            assert phase.name == "Bug Analysis", \
                f"Phase name should be 'Bug Analysis' (from bugfix workflow), got '{phase.name}'"
        finally:
            session.close()

    def test_without_explicit_workflow_id_uses_singleton(self, phase_manager_with_two_workflows):
        """Test that without explicit workflow_id, the singleton is used (backward compat)."""
        manager = phase_manager_with_two_workflows

        # Start first workflow
        result1 = manager.start_execution("prd-to-software", "First workflow")
        workflow_id_1 = result1[0] if isinstance(result1, tuple) else result1

        # Start second workflow
        result2 = manager.start_execution("bugfix", "Second workflow")
        workflow_id_2 = result2[0] if isinstance(result2, tuple) else result2

        # Get Phase 1 WITHOUT explicit workflow_id (should use singleton = first workflow)
        phase_id_no_explicit = manager.get_phase_for_task(
            phase_id=None,
            order=1,
            # No workflow_id parameter - uses self.workflow_id
        )

        # Get Phase 1 WITH explicit first workflow
        phase_id_explicit = manager.get_phase_for_task(
            phase_id=None,
            order=1,
            workflow_id=workflow_id_1
        )

        # Both should return the same phase (first workflow's Phase 1)
        assert phase_id_no_explicit == phase_id_explicit, \
            "Without explicit workflow_id, should use singleton (first workflow)"


class TestMultipleWorkflowPhaseSeparation:
    """Test that phases from different workflows remain properly separated."""

    @pytest.fixture
    def db_manager(self):
        """Create a fresh in-memory database manager for each test."""
        manager = DatabaseManager(":memory:")
        manager.create_tables()
        yield manager

    @pytest.fixture
    def manager_with_workflows(self, db_manager):
        """Create phase manager with multiple started workflows."""
        manager = PhaseManager(db_manager)

        # Register definitions
        manager.register_definition(
            definition_id="workflow-a",
            name="Workflow A",
            description="First type",
            phases_config=[
                {"order": 1, "name": "A-Phase-1", "description": "First phase of A"},
                {"order": 2, "name": "A-Phase-2", "description": "Second phase of A"},
            ],
        )

        manager.register_definition(
            definition_id="workflow-b",
            name="Workflow B",
            description="Second type",
            phases_config=[
                {"order": 1, "name": "B-Phase-1", "description": "First phase of B"},
                {"order": 2, "name": "B-Phase-2", "description": "Second phase of B"},
            ],
        )

        # Start multiple executions
        result_a1 = manager.start_execution("workflow-a", "A instance 1")
        result_a2 = manager.start_execution("workflow-a", "A instance 2")
        result_b1 = manager.start_execution("workflow-b", "B instance 1")

        wf_a1 = result_a1[0] if isinstance(result_a1, tuple) else result_a1
        wf_a2 = result_a2[0] if isinstance(result_a2, tuple) else result_a2
        wf_b1 = result_b1[0] if isinstance(result_b1, tuple) else result_b1

        return manager, wf_a1, wf_a2, wf_b1

    def test_each_workflow_has_own_phases(self, manager_with_workflows):
        """Verify each workflow execution has its own distinct phases."""
        manager, wf_a1, wf_a2, wf_b1 = manager_with_workflows

        # Get Phase 1 for each workflow
        phase_a1_1 = manager.get_phase_for_task(order=1, workflow_id=wf_a1)
        phase_a2_1 = manager.get_phase_for_task(order=1, workflow_id=wf_a2)
        phase_b1_1 = manager.get_phase_for_task(order=1, workflow_id=wf_b1)

        # All should be different phase IDs
        all_phases = [phase_a1_1, phase_a2_1, phase_b1_1]
        assert len(set(all_phases)) == 3, \
            f"Each workflow should have distinct phases, got: {all_phases}"

    def test_phase_names_match_workflow_type(self, manager_with_workflows):
        """Verify phases have correct names based on their workflow definition."""
        manager, wf_a1, wf_a2, wf_b1 = manager_with_workflows

        session = manager.db_manager.get_session()
        try:
            # Get Phase 1 for workflow A instance 1
            phase_id_a1 = manager.get_phase_for_task(order=1, workflow_id=wf_a1)
            phase_a1 = session.query(Phase).filter_by(id=phase_id_a1).first()
            assert phase_a1.name == "A-Phase-1", f"Expected 'A-Phase-1', got '{phase_a1.name}'"

            # Get Phase 1 for workflow B instance 1
            phase_id_b1 = manager.get_phase_for_task(order=1, workflow_id=wf_b1)
            phase_b1 = session.query(Phase).filter_by(id=phase_id_b1).first()
            assert phase_b1.name == "B-Phase-1", f"Expected 'B-Phase-1', got '{phase_b1.name}'"
        finally:
            session.close()


class TestWorkflowIdSingletonBehavior:
    """Test the singleton workflow_id behavior and its interaction with multi-workflow."""

    @pytest.fixture
    def db_manager(self):
        """Create a fresh in-memory database manager for each test."""
        manager = DatabaseManager(":memory:")
        manager.create_tables()
        yield manager

    @pytest.fixture
    def phase_manager(self, db_manager):
        """Create a basic phase manager."""
        manager = PhaseManager(db_manager)
        manager.register_definition(
            definition_id="test-def",
            name="Test",
            description="Test workflow",
            phases_config=[{"order": 1, "name": "Phase 1", "description": "Test phase"}],
        )
        return manager

    def test_singleton_only_set_once(self, phase_manager):
        """Verify singleton workflow_id is only set on first execution."""
        manager = phase_manager

        # Initially no singleton
        assert manager.workflow_id is None

        # Start first workflow
        result1 = manager.start_execution("test-def", "First")
        wf_id_1 = result1[0] if isinstance(result1, tuple) else result1

        # Singleton should be set
        assert manager.workflow_id == wf_id_1

        # Start second workflow
        result2 = manager.start_execution("test-def", "Second")
        wf_id_2 = result2[0] if isinstance(result2, tuple) else result2

        # Singleton should STILL be first workflow (this is the legacy behavior we preserve)
        assert manager.workflow_id == wf_id_1, \
            "Singleton should not change when second workflow is started"
        assert manager.workflow_id != wf_id_2, \
            "Singleton should remain as first workflow"

    def test_explicit_workflow_id_overrides_singleton(self, phase_manager):
        """Verify explicit workflow_id parameter overrides singleton."""
        manager = phase_manager

        # Start two workflows
        result1 = manager.start_execution("test-def", "First")
        wf_id_1 = result1[0] if isinstance(result1, tuple) else result1

        result2 = manager.start_execution("test-def", "Second")
        wf_id_2 = result2[0] if isinstance(result2, tuple) else result2

        # Get phase with explicit workflow_id for second workflow
        phase_wf2 = manager.get_phase_for_task(order=1, workflow_id=wf_id_2)

        # Verify phase belongs to second workflow, not singleton
        session = manager.db_manager.get_session()
        try:
            phase = session.query(Phase).filter_by(id=phase_wf2).first()
            assert phase.workflow_id == wf_id_2, \
                f"Phase should belong to wf_id_2 ({wf_id_2}), not singleton ({manager.workflow_id})"
        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
