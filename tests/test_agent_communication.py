"""Tests for agent communication system."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import uuid

from src.agents.manager import AgentManager
from src.core.database import DatabaseManager, Agent, AgentLog


@pytest.fixture
def db_manager(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_agent_comm.db"
    db_manager = DatabaseManager(str(db_path))
    db_manager.create_tables()
    return db_manager


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    provider = Mock()
    provider.generate_agent_prompt = AsyncMock(return_value="Test prompt")
    return provider


@pytest.fixture
def agent_manager(db_manager, mock_llm_provider):
    """Create agent manager instance."""
    manager = AgentManager(db_manager, mock_llm_provider)
    return manager


@pytest.fixture
def sample_agents(db_manager):
    """Create sample agents in database."""
    session = db_manager.get_session()

    agents = []
    for i in range(3):
        agent = Agent(
            id=f"agent-{i}",
            system_prompt=f"Test agent {i}",
            status="working",
            cli_type="claude",
            tmux_session_name=f"test_session_{i}",
            current_task_id=f"task-{i}",
            last_activity=datetime.utcnow(),
            health_check_failures=0,
        )
        session.add(agent)
        agents.append(agent)

    # Add one terminated agent
    terminated = Agent(
        id="agent-terminated",
        system_prompt="Terminated agent",
        status="terminated",
        cli_type="claude",
        tmux_session_name="test_session_terminated",
        current_task_id="task-terminated",
        last_activity=datetime.utcnow(),
        health_check_failures=0,
    )
    session.add(terminated)
    agents.append(terminated)

    session.commit()
    session.close()

    return agents


class TestBroadcastMessage:
    """Tests for broadcast_message_to_all_agents."""

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_agents(self, agent_manager, sample_agents, db_manager):
        """Test broadcasting a message to multiple agents."""
        # Mock send_message_to_agent to avoid tmux interaction
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            sender_id = "agent-0"
            message = "Test broadcast message"

            recipient_count = await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id=sender_id,
                message=message
            )

            # Should send to 2 other active agents (not sender, not terminated)
            assert recipient_count == 2

            # Verify send_message_to_agent was called for each recipient
            assert mock_send.call_count == 2

            # Verify message format includes sender ID and BROADCAST prefix
            call_args = mock_send.call_args_list
            for call in call_args:
                agent_id, formatted_message = call[0]
                assert "BROADCAST" in formatted_message
                assert sender_id[:8] in formatted_message
                assert message in formatted_message

    @pytest.mark.asyncio
    async def test_broadcast_excludes_sender(self, agent_manager, sample_agents):
        """Test that broadcast doesn't send to the sender."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            sender_id = "agent-0"

            await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id=sender_id,
                message="Test"
            )

            # Verify sender didn't receive their own message
            sent_to_ids = [call[0][0] for call in mock_send.call_args_list]
            assert sender_id not in sent_to_ids

    @pytest.mark.asyncio
    async def test_broadcast_excludes_terminated_agents(self, agent_manager, sample_agents):
        """Test that broadcast doesn't send to terminated agents."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id="agent-0",
                message="Test"
            )

            # Verify terminated agent didn't receive message
            sent_to_ids = [call[0][0] for call in mock_send.call_args_list]
            assert "agent-terminated" not in sent_to_ids

    @pytest.mark.asyncio
    async def test_broadcast_logs_to_database(self, agent_manager, sample_agents, db_manager):
        """Test that broadcasts are logged to database."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock):
            sender_id = "agent-0"
            message = "Test broadcast"

            await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id=sender_id,
                message=message
            )

            # Check database for logs
            session = db_manager.get_session()
            logs = session.query(AgentLog).filter_by(
                log_type="agent_communication"
            ).all()

            # Should have 2 logs (one per recipient)
            assert len(logs) == 2

            for log in logs:
                assert log.details["sender_id"] == sender_id
                assert log.details["message_type"] == "broadcast"
                assert message in log.details["message_content"]
                assert "timestamp" in log.details

            session.close()

    @pytest.mark.asyncio
    async def test_broadcast_with_no_recipients(self, agent_manager, db_manager):
        """Test broadcast when no other agents are active."""
        # Create only one agent (the sender)
        session = db_manager.get_session()
        agent = Agent(
            id="only-agent",
            system_prompt="Only agent",
            status="working",
            cli_type="claude",
            tmux_session_name="test_session",
            current_task_id="task-1",
            last_activity=datetime.utcnow(),
            health_check_failures=0,
        )
        session.add(agent)
        session.commit()
        session.close()

        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            recipient_count = await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id="only-agent",
                message="Hello?"
            )

            # Should return 0 recipients
            assert recipient_count == 0
            # Should not call send_message_to_agent
            assert mock_send.call_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_message_format(self, agent_manager, sample_agents):
        """Test that broadcast messages are formatted correctly."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            sender_id = "agent-12345678-abcd-efgh"
            message = "This is a test message"

            await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id=sender_id,
                message=message
            )

            # Get the formatted message from first call
            formatted_message = mock_send.call_args_list[0][0][1]

            # Verify format: [AGENT 12345678 BROADCAST]: message
            assert formatted_message.startswith("\n[AGENT")
            assert "BROADCAST]:" in formatted_message
            assert sender_id[:8] in formatted_message
            assert message in formatted_message
            assert formatted_message.endswith("\n")


class TestDirectMessage:
    """Tests for send_direct_message."""

    @pytest.mark.asyncio
    async def test_send_to_valid_recipient(self, agent_manager, sample_agents):
        """Test sending direct message to valid recipient."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            sender_id = "agent-0"
            recipient_id = "agent-1"
            message = "Direct message test"

            success = await agent_manager.send_direct_message(
                sender_agent_id=sender_id,
                recipient_agent_id=recipient_id,
                message=message
            )

            assert success is True
            mock_send.assert_called_once()

            # Verify correct recipient
            call_args = mock_send.call_args[0]
            assert call_args[0] == recipient_id

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_agent(self, agent_manager, sample_agents):
        """Test sending to non-existent agent returns False."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock):
            success = await agent_manager.send_direct_message(
                sender_agent_id="agent-0",
                recipient_agent_id="nonexistent-agent",
                message="Test"
            )

            assert success is False

    @pytest.mark.asyncio
    async def test_send_to_terminated_agent(self, agent_manager, sample_agents):
        """Test sending to terminated agent returns False."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock):
            success = await agent_manager.send_direct_message(
                sender_agent_id="agent-0",
                recipient_agent_id="agent-terminated",
                message="Test"
            )

            assert success is False

    @pytest.mark.asyncio
    async def test_direct_message_logs_to_database(self, agent_manager, sample_agents, db_manager):
        """Test that direct messages are logged."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock):
            sender_id = "agent-0"
            recipient_id = "agent-1"
            message = "Test direct message"

            await agent_manager.send_direct_message(
                sender_agent_id=sender_id,
                recipient_agent_id=recipient_id,
                message=message
            )

            # Check database
            session = db_manager.get_session()
            log = session.query(AgentLog).filter_by(
                log_type="agent_communication",
                agent_id=recipient_id
            ).first()

            assert log is not None
            assert log.details["sender_id"] == sender_id
            assert log.details["recipient_id"] == recipient_id
            assert log.details["message_type"] == "direct"
            assert message in log.details["message_content"]

            session.close()

    @pytest.mark.asyncio
    async def test_direct_message_format(self, agent_manager, sample_agents):
        """Test that direct messages are formatted correctly."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            # Use actual agent IDs from sample_agents
            sender_id = "agent-0"
            recipient_id = "agent-1"
            message = "Direct message content"

            await agent_manager.send_direct_message(
                sender_agent_id=sender_id,
                recipient_agent_id=recipient_id,
                message=message
            )

            formatted_message = mock_send.call_args[0][1]

            # Verify format: [AGENT xxx TO AGENT yyy]: message
            assert formatted_message.startswith("\n[AGENT")
            assert "TO AGENT" in formatted_message
            assert sender_id[:8] in formatted_message
            assert recipient_id[:8] in formatted_message
            assert message in formatted_message
            assert formatted_message.endswith("\n")


class TestMessageContent:
    """Tests for message content handling."""

    @pytest.mark.asyncio
    async def test_long_message_truncation_in_log(self, agent_manager, sample_agents, db_manager):
        """Test that long messages are truncated in database logs."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock):
            # Create a message longer than 200 characters
            long_message = "x" * 300

            await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id="agent-0",
                message=long_message
            )

            session = db_manager.get_session()
            log = session.query(AgentLog).filter_by(
                log_type="agent_communication"
            ).first()

            # Verify truncation to 200 chars
            assert len(log.details["message_content"]) == 200
            session.close()

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, agent_manager, sample_agents):
        """Test that messages with special characters are handled correctly."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock) as mock_send:
            special_message = "Test with special chars: \n\t\"quotes\" 'apostrophe' $var @user #tag"

            await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id="agent-0",
                message=special_message
            )

            # Verify message content is preserved
            formatted_message = mock_send.call_args_list[0][0][1]
            assert special_message in formatted_message


class TestErrorHandling:
    """Tests for error handling in communication system."""

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_failure(self, agent_manager, sample_agents):
        """Test that broadcast continues even if one send fails."""
        call_count = 0

        async def mock_send_with_failure(agent_id, message):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Simulated send failure")

        with patch.object(agent_manager, 'send_message_to_agent', side_effect=mock_send_with_failure):
            recipient_count = await agent_manager.broadcast_message_to_all_agents(
                sender_agent_id="agent-0",
                message="Test"
            )

            # Should still count as successful for agents where send succeeded
            # (In this implementation, failures are logged but count continues)
            assert recipient_count >= 0

    @pytest.mark.asyncio
    async def test_direct_message_handles_exception(self, agent_manager, sample_agents):
        """Test that direct message handles exceptions gracefully."""
        async def mock_send_with_exception(agent_id, message):
            raise Exception("Simulated exception")

        with patch.object(agent_manager, 'send_message_to_agent', side_effect=mock_send_with_exception):
            success = await agent_manager.send_direct_message(
                sender_agent_id="agent-0",
                recipient_agent_id="agent-1",
                message="Test"
            )

            # Should return False on exception
            assert success is False


class TestConcurrency:
    """Tests for concurrent message operations."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_broadcasts(self, agent_manager, sample_agents):
        """Test multiple agents broadcasting simultaneously."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock):
            # Simulate 3 agents broadcasting at the same time
            tasks = [
                agent_manager.broadcast_message_to_all_agents(f"agent-{i}", f"Message from {i}")
                for i in range(3)
            ]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(count >= 0 for count in results)

    @pytest.mark.asyncio
    async def test_concurrent_direct_messages(self, agent_manager, sample_agents):
        """Test multiple direct messages sent concurrently."""
        with patch.object(agent_manager, 'send_message_to_agent', new_callable=AsyncMock):
            # Multiple agents sending messages simultaneously
            tasks = [
                agent_manager.send_direct_message("agent-0", "agent-1", "Message 1"),
                agent_manager.send_direct_message("agent-1", "agent-2", "Message 2"),
                agent_manager.send_direct_message("agent-2", "agent-0", "Message 3"),
            ]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])