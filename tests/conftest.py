"""Shared pytest fixtures for Hephaestus tests."""

import pytest
import tempfile
import os
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# Set test database environment variable before any imports
os.environ["HEPHAESTUS_TEST_DB"] = ":memory:"


@pytest.fixture(scope="session")
def temp_db():
    """Create temporary database file for tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Cleanup after session
    if os.path.exists(f.name):
        os.unlink(f.name)


@pytest.fixture
def clean_db(temp_db):
    """Ensure clean database for each test."""
    if os.path.exists(temp_db):
        os.unlink(temp_db)
    yield temp_db


@pytest.fixture
def db_manager():
    """Create a fresh in-memory database manager for each test."""
    from src.core.database import DatabaseManager

    manager = DatabaseManager(":memory:")
    manager.create_tables()
    yield manager


@pytest.fixture
def phase_manager(db_manager):
    """Create a phase manager with test database."""
    from src.phases.phase_manager import PhaseManager

    manager = PhaseManager(db_manager)
    yield manager


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider for tests."""
    mock = AsyncMock()
    mock.enrich_task = AsyncMock(return_value={
        "enriched_description": "Enriched test task description",
        "complexity": "medium",
        "suggested_approach": "Test approach"
    })
    mock.generate_agent_prompt = AsyncMock(return_value="System prompt for test agent")
    return mock


@pytest.fixture
def test_workflow_definition():
    """Create a test workflow definition."""
    from src.sdk.models import Phase, WorkflowConfig, WorkflowDefinition

    phases = [
        Phase(
            id=1,
            name="Planning",
            description="Plan the project",
            done_definitions=["Requirements documented"],
            working_directory="/project",
        ),
        Phase(
            id=2,
            name="Implementation",
            description="Implement the solution",
            done_definitions=["Code written", "Tests pass"],
            working_directory="/project",
        ),
        Phase(
            id=3,
            name="Testing",
            description="Test the solution",
            done_definitions=["All tests pass"],
            working_directory="/project",
        ),
    ]

    config = WorkflowConfig(
        has_result=True,
        result_criteria="Working application",
        on_result_found="stop_all",
    )

    return WorkflowDefinition(
        id="test-workflow",
        name="Test Workflow",
        phases=phases,
        config=config,
        description="Test workflow for integration tests",
    )


@pytest.fixture
def test_bugfix_definition():
    """Create a bugfix workflow definition for testing multiple definitions."""
    from src.sdk.models import Phase, WorkflowConfig, WorkflowDefinition

    phases = [
        Phase(
            id=1,
            name="Analysis",
            description="Analyze the bug",
            done_definitions=["Bug understood", "Root cause identified"],
            working_directory="/project",
        ),
        Phase(
            id=2,
            name="Fix",
            description="Implement the fix",
            done_definitions=["Fix implemented", "Tests updated"],
            working_directory="/project",
        ),
    ]

    config = WorkflowConfig(
        has_result=True,
        result_criteria="Bug fixed and tests pass",
        on_result_found="stop_all",
    )

    return WorkflowDefinition(
        id="bugfix-workflow",
        name="Bug Fix Workflow",
        phases=phases,
        config=config,
        description="Workflow for fixing bugs",
    )


@pytest.fixture
def sample_task_data():
    """Create sample task data for tests."""
    return {
        "task_description": "Write unit tests for authentication module",
        "done_definition": "All auth functions have >90% test coverage with passing tests",
        "ai_agent_id": f"test-agent-{uuid.uuid4()}",
        "priority": "medium",
        "phase_id": "1",
    }


@pytest.fixture
def sample_ticket_data():
    """Create sample ticket data for tests."""
    return {
        "title": "Fix login bug #123",
        "description": "Users cannot log in with valid credentials. Need to investigate auth flow.",
        "ticket_type": "bug",
        "priority": "high",
        "tags": ["auth", "urgent"],
    }


@pytest.fixture
def mock_agent_manager():
    """Create a mock agent manager."""
    mock = MagicMock()
    mock.create_agent_for_task = AsyncMock()
    mock.get_project_context = AsyncMock(return_value="Test project context")
    return mock


@pytest.fixture
def mock_rag_system():
    """Create a mock RAG system."""
    mock = MagicMock()
    mock.retrieve_for_task = AsyncMock(return_value=[
        {"content": "Memory 1", "type": "learning"},
        {"content": "Memory 2", "type": "discovery"},
    ])
    return mock


@pytest.fixture
def test_workflow_id():
    """Generate a unique test workflow ID."""
    return f"test-workflow-{uuid.uuid4()}"


@pytest.fixture
def test_agent_id():
    """Generate a unique test agent ID."""
    return str(uuid.uuid4())


@pytest.fixture
def initialized_phase_manager(db_manager, test_workflow_definition):
    """Create a phase manager with registered workflow definition."""
    from src.phases.phase_manager import PhaseManager

    manager = PhaseManager(db_manager)

    # Register the test definition
    phases_config = [
        {
            "order": phase.id,
            "name": phase.name,
            "description": phase.description,
            "done_definitions": phase.done_definitions,
            "working_directory": phase.working_directory,
        }
        for phase in test_workflow_definition.phases
    ]

    workflow_config = {}
    if test_workflow_definition.config:
        workflow_config = {
            "has_result": test_workflow_definition.config.has_result,
            "result_criteria": test_workflow_definition.config.result_criteria,
            "on_result_found": test_workflow_definition.config.on_result_found,
        }

    manager.register_definition(
        definition_id=test_workflow_definition.id,
        name=test_workflow_definition.name,
        description=test_workflow_definition.description,
        phases_config=phases_config,
        workflow_config=workflow_config,
    )

    yield manager


@pytest.fixture
def workflow_with_execution(initialized_phase_manager):
    """Create a phase manager with a started workflow execution."""
    workflow_id = initialized_phase_manager.start_execution(
        definition_id="test-workflow",
        description="Test execution for integration tests",
        working_directory="/tmp/test-project",
    )
    return initialized_phase_manager, workflow_id


# Async fixtures
@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
