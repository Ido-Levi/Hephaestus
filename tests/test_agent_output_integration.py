"""Integration tests for agent output capture with real tmux sessions."""

import asyncio
import uuid
import time
import libtmux
import pytest
from datetime import datetime

from src.agents.manager import AgentManager
from src.core.database import DatabaseManager, Agent, AgentLog, Task
from src.interfaces import get_llm_provider


@pytest.mark.integration
class TestAgentOutputIntegration:
    """Integration tests for agent output capture with real components."""

    @pytest.fixture
    def db_manager(self):
        """Create a real database manager with test database."""
        # Use an in-memory database for testing
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        # Initialize database
        from src.core.database import Base, engine
        from sqlalchemy import create_engine

        test_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(test_engine)

        # Create database manager
        db_manager = DatabaseManager(db_path)

        yield db_manager

        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass

    @pytest.fixture
    def agent_manager(self, db_manager):
        """Create a real agent manager."""
        llm_provider = get_llm_provider()
        return AgentManager(db_manager, llm_provider)

    @pytest.mark.asyncio
    @pytest.mark.skipif(not libtmux.Server().has_session("test"), reason="Requires tmux")
    async def test_full_agent_lifecycle_with_output_capture(self, agent_manager, db_manager):
        """Test complete agent lifecycle with output capture."""

        # Create a task
        session = db_manager.get_session()
        task_id = str(uuid.uuid4())
        agent_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            raw_description="Test task",
            enriched_description="Test task enriched",
            done_definition="Complete the test",
            status="pending",
            priority="medium",
            created_at=datetime.utcnow()
        )
        session.add(task)
        session.commit()
        session.close()

        # Create a tmux session manually to simulate an agent
        tmux_server = libtmux.Server()
        session_name = f"test_agent_{agent_id[:8]}"

        # Clean up any existing test session
        if tmux_server.has_session(session_name):
            tmux_server.get_by_id(session_name).kill_session()

        # Create new session
        tmux_session = tmux_server.new_session(
            session_name=session_name,
            window_name="test",
            attach=False
        )

        # Add some output to the session
        pane = tmux_session.attached_window.attached_pane
        test_commands = [
            "echo 'Starting test agent'",
            "echo 'Processing task...'",
            "echo 'Task completed successfully'",
            "echo 'Final result: SUCCESS'"
        ]

        for cmd in test_commands:
            pane.send_keys(cmd, enter=True)
            time.sleep(0.1)  # Small delay between commands

        # Register agent in database
        session = db_manager.get_session()
        agent = Agent(
            id=agent_id,
            system_prompt="Test prompt",
            status="working",
            cli_type="test",
            tmux_session_name=session_name,
            current_task_id=task_id,
            last_activity=datetime.utcnow(),
            health_check_failures=0,
            agent_type="phase"
        )
        session.add(agent)
        session.commit()
        session.close()

        # Verify agent can get live output
        live_output = agent_manager.get_agent_output(agent_id, lines=100)
        assert "Starting test agent" in live_output
        assert "Task completed successfully" in live_output

        # Terminate the agent
        await agent_manager.terminate_agent(agent_id)

        # Verify agent is terminated
        session = db_manager.get_session()
        agent = session.query(Agent).filter_by(id=agent_id).first()
        assert agent.status == "terminated"

        # Verify output was captured in AgentLog
        log_entry = session.query(AgentLog).filter_by(
            agent_id=agent_id,
            log_type="terminated"
        ).first()
        assert log_entry is not None
        assert log_entry.details is not None
        assert "final_output" in log_entry.details

        stored_output = log_entry.details["final_output"]
        assert "Starting test agent" in stored_output
        assert "Task completed successfully" in stored_output
        assert "Final result: SUCCESS" in stored_output

        session.close()

        # Verify we can still get output after termination
        terminated_output = agent_manager.get_agent_output(agent_id)
        assert "Starting test agent" in terminated_output
        assert "Task completed successfully" in terminated_output

        # Verify tmux session is gone
        assert not tmux_server.has_session(session_name)

    @pytest.mark.asyncio
    async def test_get_output_for_nonexistent_agent(self, agent_manager):
        """Test getting output for an agent that doesn't exist."""
        fake_agent_id = str(uuid.uuid4())
        output = agent_manager.get_agent_output(fake_agent_id)
        assert output == ""

    @pytest.mark.asyncio
    async def test_terminate_nonexistent_agent(self, agent_manager):
        """Test terminating an agent that doesn't exist."""
        fake_agent_id = str(uuid.uuid4())
        # Should not raise an exception
        await agent_manager.terminate_agent(fake_agent_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])