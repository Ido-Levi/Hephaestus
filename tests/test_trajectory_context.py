"""Unit tests for the TrajectoryContext system."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json

from src.monitoring.trajectory_context import TrajectoryContext
from src.core.database import AgentLog, Task


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    mock = Mock()
    mock.get_session = Mock()
    return mock


@pytest.fixture
def trajectory_context(mock_db_manager):
    """Create TrajectoryContext instance with mocked dependencies."""
    return TrajectoryContext(db_manager=mock_db_manager)


@pytest.fixture
def sample_agent_logs():
    """Create sample agent logs for testing."""
    return [
        AgentLog(
            id=1,
            agent_id="test-agent-1",
            log_type="input",
            message="Build a REST API without external frameworks",
            created_at=datetime.utcnow() - timedelta(hours=2),
            details={}
        ),
        AgentLog(
            id=2,
            agent_id="test-agent-1",
            log_type="output",
            message="I'll build a REST API using only standard library",
            created_at=datetime.utcnow() - timedelta(hours=2, seconds=-30),
            details={}
        ),
        AgentLog(
            id=3,
            agent_id="test-agent-1",
            log_type="steering",
            message="Remember: no external frameworks allowed",
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            details={"type": "constraint_reminder"}
        ),
        AgentLog(
            id=4,
            agent_id="test-agent-1",
            log_type="input",
            message="Actually, you can use Flask now",
            created_at=datetime.utcnow() - timedelta(hours=1),
            details={}
        ),
        AgentLog(
            id=5,
            agent_id="test-agent-1",
            log_type="output",
            message="Great! I'll switch to Flask for better implementation",
            created_at=datetime.utcnow() - timedelta(minutes=50),
            details={}
        ),
        AgentLog(
            id=6,
            agent_id="test-agent-1",
            log_type="error",
            message="Error: ImportError: No module named flask",
            created_at=datetime.utcnow() - timedelta(minutes=30),
            details={"error_type": "ImportError"}
        ),
        AgentLog(
            id=7,
            agent_id="test-agent-1",
            log_type="input",
            message="Make sure to add comprehensive tests",
            created_at=datetime.utcnow() - timedelta(minutes=20),
            details={}
        ),
        AgentLog(
            id=8,
            agent_id="test-agent-1",
            log_type="output",
            message="I'm currently implementing the authentication endpoints",
            created_at=datetime.utcnow() - timedelta(minutes=10),
            details={}
        ),
    ]


class TestTrajectoryContext:
    """Test the TrajectoryContext system."""

    def test_build_accumulated_context_full(self, trajectory_context, mock_db_manager, sample_agent_logs):
        """Test building full accumulated context."""
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = sample_agent_logs

        # Mock task
        mock_task = Task(
            id="task-1",
            raw_description="Build REST API",
            enriched_description="Build a complete REST API with authentication",
            done_definition="API endpoints working with tests"
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
        mock_db_manager.get_session.return_value = mock_session

        # Execute
        context = trajectory_context.build_accumulated_context("test-agent-1", include_full_history=True)

        # Assert - the implementation extracts from conversation patterns
        assert context['overall_goal'] == "A rest api without external frameworks"
        assert context['done_definition'] == "API endpoints working with tests"
        assert len(context['constraints']) == 0  # "no external frameworks" was lifted
        assert "no external frameworks" in context['lifted_constraints']
        assert "add comprehensive tests" in context['standing_instructions']
        assert context['current_focus'] == "implementing the authentication endpoints"
        assert context['conversation_length'] == 8
        assert len(context['discovered_blockers']) == 1
        assert "ImportError" in context['discovered_blockers'][0]

    def test_build_accumulated_context_summary_only(self, trajectory_context, mock_db_manager, sample_agent_logs):
        """Test building context with summary only."""
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = sample_agent_logs

        mock_task = Task(id="task-1", enriched_description="Build API")
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_task
        mock_db_manager.get_session.return_value = mock_session

        # Execute with summary only
        context = trajectory_context.build_accumulated_context("test-agent-1", include_full_history=False)

        # Should have summary fields but no full history
        assert 'overall_goal' in context
        assert 'current_focus' in context
        assert 'full_conversation' not in context

    def test_extract_constraints(self, trajectory_context):
        """Test constraint extraction from messages."""
        messages = [
            "Build API without external frameworks",
            "Remember: no database writes allowed",
            "You must not use any third-party libraries",
            "Important: keep response times under 100ms"
        ]

        # Convert messages to the format expected by the method
        conversation = [{"content": msg, "type": "input", "timestamp": datetime.utcnow()} for msg in messages]
        constraints = trajectory_context._extract_persistent_constraints(conversation)

        assert len(constraints) >= 2
        assert any("external framework" in c.lower() for c in constraints)
        assert any("database write" in c.lower() or "third-party" in c.lower() for c in constraints)

    def test_extract_lifted_constraints(self, trajectory_context):
        """Test identifying lifted constraints."""
        conversation = [
            {"role": "user", "content": "Don't use external libraries"},
            {"role": "assistant", "content": "OK, using standard library only"},
            {"role": "user", "content": "Actually, you can use Flask now"},
            {"role": "assistant", "content": "Great! Switching to Flask"}
        ]

        lifted = trajectory_context._extract_lifted_constraints(conversation)

        assert len(lifted) > 0
        assert any("flask" in l.lower() or "external" in l.lower() for l in lifted)

    def test_extract_standing_instructions(self, trajectory_context):
        """Test extracting standing instructions."""
        messages = [
            "Make sure to add tests for everything",
            "Remember to document your code",
            "Always validate user input"
        ]

        instructions = trajectory_context._extract_standing_instructions(messages)

        assert len(instructions) >= 2
        assert any("test" in i.lower() for i in instructions)
        assert any("document" in i.lower() or "validate" in i.lower() for i in instructions)

    def test_identify_current_focus(self, trajectory_context):
        """Test identifying current focus from recent output."""
        recent_output = """
        I'm currently working on implementing the authentication system.
        Specifically, I'm adding JWT token validation to the endpoints.
        This involves checking token signatures and expiration times.
        """

        focus = trajectory_context._identify_current_focus(recent_output)

        assert focus is not None
        assert "authentication" in focus.lower() or "jwt" in focus.lower()

    def test_extract_discovered_blockers(self, trajectory_context):
        """Test extracting blockers from errors."""
        errors = [
            "Error: Module 'flask' not found",
            "TypeError: Cannot read property 'id' of undefined",
            "ConnectionError: Database connection failed"
        ]

        blockers = trajectory_context._extract_discovered_blockers(errors)

        assert len(blockers) == 3
        assert any("flask" in b.lower() for b in blockers)
        assert any("database" in b.lower() for b in blockers)

    def test_empty_agent_history(self, trajectory_context, mock_db_manager):
        """Test handling agent with no history."""
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db_manager.get_session.return_value = mock_session

        context = trajectory_context.build_accumulated_context("empty-agent")

        assert context['overall_goal'] == "Unknown"
        assert context['conversation_length'] == 0
        assert len(context['constraints']) == 0
        assert context['current_focus'] == "Unknown"

    def test_agent_with_only_errors(self, trajectory_context, mock_db_manager):
        """Test agent that only has error logs."""
        error_logs = [
            AgentLog(
                agent_id="error-agent",
                log_type="error",
                message="Failed to connect",
                created_at=datetime.utcnow(),
                details={}
            ),
            AgentLog(
                agent_id="error-agent",
                log_type="error",
                message="Timeout occurred",
                created_at=datetime.utcnow(),
                details={}
            )
        ]

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = error_logs
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db_manager.get_session.return_value = mock_session

        context = trajectory_context.build_accumulated_context("error-agent")

        assert len(context['discovered_blockers']) == 2
        assert context['conversation_length'] == 2

    def test_pattern_extraction_edge_cases(self, trajectory_context):
        """Test pattern extraction with edge cases."""
        # Empty messages
        assert trajectory_context._extract_constraints([]) == []

        # Messages with no patterns
        messages = ["Hello", "How are you?", "Working on the task"]
        assert len(trajectory_context._extract_constraints(messages)) == 0

        # Mixed case and punctuation
        messages = ["NEVER use external APIs!!!", "You MUST NOT modify the database"]
        # Convert messages to the format expected by the method
        conversation = [{"content": msg, "type": "input", "timestamp": datetime.utcnow()} for msg in messages]
        constraints = trajectory_context._extract_persistent_constraints(conversation)
        assert len(constraints) >= 1

    def test_session_duration_calculation(self, trajectory_context, mock_db_manager):
        """Test correct session duration calculation."""
        start_time = datetime.utcnow() - timedelta(hours=3, minutes=30)
        logs = [
            AgentLog(
                agent_id="test-agent",
                log_type="input",
                message="Start",
                created_at=start_time,
                details={}
            ),
            AgentLog(
                agent_id="test-agent",
                log_type="output",
                message="Working",
                created_at=datetime.utcnow(),
                details={}
            )
        ]

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = logs
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db_manager.get_session.return_value = mock_session

        context = trajectory_context.build_accumulated_context("test-agent")

        # Should be around 3.5 hours
        assert context['session_start'] == start_time
        duration = context['session_duration']
        assert "3:" in duration or "03:" in duration  # 3 hours

    def test_clear_agent_cache(self, trajectory_context):
        """Test clearing agent cache."""
        agent_id = "cached-agent"

        # Add to cache
        trajectory_context.context_cache[agent_id] = {
            "context": {"test": "data"},
            "timestamp": datetime.utcnow()
        }

        # Clear cache
        trajectory_context.clear_agent_cache(agent_id)

        assert agent_id not in trajectory_context.context_cache

    def test_cache_expiration(self, trajectory_context, mock_db_manager):
        """Test that cache expires after time limit."""
        agent_id = "test-agent"

        # Add old cache entry
        trajectory_context.context_cache[agent_id] = {
            "context": {"old": "data"},
            "timestamp": datetime.utcnow() - timedelta(minutes=11)  # Older than 10 minutes
        }

        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db_manager.get_session.return_value = mock_session

        # Should rebuild context instead of using cache
        context = trajectory_context.build_accumulated_context(agent_id)

        # Cache should be updated with new timestamp
        assert trajectory_context.context_cache[agent_id]["context"] != {"old": "data"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])