"""Tests for prompt delivery verification and retry logic."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from src.agents.manager import AgentManager
from src.core.database import DatabaseManager, Task
from src.interfaces import LLMProviderInterface, ClaudeCodeAgent


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    db_manager = Mock(spec=DatabaseManager)
    db_manager.get_session = Mock()
    return db_manager


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock(spec=LLMProviderInterface)
    provider.generate_agent_prompt = AsyncMock(return_value="Test system prompt")
    return provider


@pytest.fixture
def agent_manager(mock_db_manager, mock_llm_provider):
    """Create an AgentManager instance with mocks."""
    return AgentManager(
        db_manager=mock_db_manager,
        llm_provider=mock_llm_provider
    )


@pytest.fixture
def mock_pane():
    """Create a mock tmux pane."""
    pane = Mock()
    pane.send_keys = Mock()
    return pane


@pytest.fixture
def mock_cli_agent():
    """Create a mock CLI agent."""
    cli_agent = Mock(spec=ClaudeCodeAgent)
    cli_agent.format_message = Mock(side_effect=lambda msg: msg)
    return cli_agent


@pytest.mark.asyncio
async def test_verify_prompt_delivery_success(agent_manager, mock_pane):
    """Test successful prompt verification."""
    # Mock the capture-pane command to return output containing the verification string
    mock_result = Mock()
    mock_result.stdout = [
        "Some output line 1",
        "Task ID: test-task-123",
        "Some output line 2",
    ]
    mock_pane.cmd = Mock(return_value=mock_result)

    # Verify that the string is found
    result = await agent_manager._verify_prompt_delivery(
        pane=mock_pane,
        verification_string="Task ID: test-task-123",
        wait_seconds=0.1  # Short wait for testing
    )

    assert result is True
    mock_pane.cmd.assert_called_once_with("capture-pane", "-p", "-S", "-1000")


@pytest.mark.asyncio
async def test_verify_prompt_delivery_failure(agent_manager, mock_pane):
    """Test failed prompt verification when string not found."""
    # Mock the capture-pane command to return output NOT containing the verification string
    mock_result = Mock()
    mock_result.stdout = [
        "Some output line 1",
        "Some output line 2",
        "No task ID here",
    ]
    mock_pane.cmd = Mock(return_value=mock_result)

    # Verify that the string is NOT found
    result = await agent_manager._verify_prompt_delivery(
        pane=mock_pane,
        verification_string="Task ID: test-task-123",
        wait_seconds=0.1  # Short wait for testing
    )

    assert result is False
    mock_pane.cmd.assert_called_once_with("capture-pane", "-p", "-S", "-1000")


@pytest.mark.asyncio
async def test_verify_prompt_delivery_empty_output(agent_manager, mock_pane):
    """Test prompt verification with empty output."""
    # Mock the capture-pane command to return empty output
    mock_result = Mock()
    mock_result.stdout = []
    mock_pane.cmd = Mock(return_value=mock_result)

    result = await agent_manager._verify_prompt_delivery(
        pane=mock_pane,
        verification_string="Task ID: test-task-123",
        wait_seconds=0.1
    )

    assert result is False


@pytest.mark.asyncio
async def test_send_initial_prompt_without_verification(
    agent_manager, mock_pane, mock_cli_agent
):
    """Test prompt delivery without verification (default behavior)."""
    agent_id = "test-agent-123"
    task_id = "test-task-456"
    initial_message = "Test initial message\nTask ID: test-task-456"

    # Should not raise an exception
    await agent_manager._send_initial_prompt_with_retry(
        pane=mock_pane,
        cli_agent=mock_cli_agent,
        initial_message=initial_message,
        agent_id=agent_id,
        task_id=task_id,
        max_retries=3,
        verify_delivery=False  # Default behavior
    )

    # Verify send_keys was called (1 chunk for short message + 1 Enter)
    assert mock_pane.send_keys.call_count == 2
    mock_cli_agent.format_message.assert_called_once_with(initial_message)


@pytest.mark.asyncio
async def test_send_initial_prompt_with_retry_success_first_attempt(
    agent_manager, mock_pane, mock_cli_agent
):
    """Test successful prompt delivery on first attempt with verification enabled."""
    agent_id = "test-agent-123"
    task_id = "test-task-456"
    initial_message = "Test initial message\nTask ID: test-task-456"

    # Mock verification to succeed on first attempt
    agent_manager._verify_prompt_delivery = AsyncMock(return_value=True)

    # Should not raise an exception
    await agent_manager._send_initial_prompt_with_retry(
        pane=mock_pane,
        cli_agent=mock_cli_agent,
        initial_message=initial_message,
        agent_id=agent_id,
        task_id=task_id,
        max_retries=3,
        verify_delivery=True  # Enable verification
    )

    # Verify send_keys was called (1 chunk for short message + 1 Enter)
    assert mock_pane.send_keys.call_count == 2
    mock_cli_agent.format_message.assert_called_once_with(initial_message)

    # Verify verification was called once
    agent_manager._verify_prompt_delivery.assert_called_once()


@pytest.mark.asyncio
async def test_send_initial_prompt_with_retry_success_second_attempt(
    agent_manager, mock_pane, mock_cli_agent
):
    """Test successful prompt delivery on second attempt with verification enabled."""
    agent_id = "test-agent-123"
    task_id = "test-task-456"
    initial_message = "Test initial message\nTask ID: test-task-456"

    # Mock verification to fail first, then succeed
    agent_manager._verify_prompt_delivery = AsyncMock(side_effect=[False, True])

    # Should not raise an exception
    await agent_manager._send_initial_prompt_with_retry(
        pane=mock_pane,
        cli_agent=mock_cli_agent,
        initial_message=initial_message,
        agent_id=agent_id,
        task_id=task_id,
        max_retries=3,
        verify_delivery=True  # Enable verification
    )

    # Verify send_keys was called for both attempts (2 calls per attempt)
    assert mock_pane.send_keys.call_count == 4  # 2 attempts × 2 calls each
    assert mock_cli_agent.format_message.call_count == 2  # Called twice

    # Verify verification was called twice
    assert agent_manager._verify_prompt_delivery.call_count == 2


@pytest.mark.asyncio
async def test_send_initial_prompt_with_retry_success_third_attempt(
    agent_manager, mock_pane, mock_cli_agent
):
    """Test successful prompt delivery on third (final) attempt with verification enabled."""
    agent_id = "test-agent-123"
    task_id = "test-task-456"
    initial_message = "Test initial message\nTask ID: test-task-456"

    # Mock verification to fail twice, then succeed on third attempt
    agent_manager._verify_prompt_delivery = AsyncMock(side_effect=[False, False, True])

    # Should not raise an exception
    await agent_manager._send_initial_prompt_with_retry(
        pane=mock_pane,
        cli_agent=mock_cli_agent,
        initial_message=initial_message,
        agent_id=agent_id,
        task_id=task_id,
        max_retries=3,
        verify_delivery=True  # Enable verification
    )

    # Verify send_keys was called for all three attempts (2 calls per attempt)
    assert mock_pane.send_keys.call_count == 6  # 3 attempts × 2 calls each
    assert mock_cli_agent.format_message.call_count == 3  # Called three times

    # Verify verification was called three times
    assert agent_manager._verify_prompt_delivery.call_count == 3


@pytest.mark.asyncio
async def test_send_initial_prompt_with_retry_all_retries_fail(
    agent_manager, mock_pane, mock_cli_agent
):
    """Test that exception is raised when all retries fail with verification enabled."""
    agent_id = "test-agent-123"
    task_id = "test-task-456"
    initial_message = "Test initial message\nTask ID: test-task-456"

    # Mock verification to always fail
    agent_manager._verify_prompt_delivery = AsyncMock(return_value=False)

    # Should raise an exception after all retries
    with pytest.raises(Exception) as exc_info:
        await agent_manager._send_initial_prompt_with_retry(
            pane=mock_pane,
            cli_agent=mock_cli_agent,
            initial_message=initial_message,
            agent_id=agent_id,
            task_id=task_id,
            max_retries=3,
            verify_delivery=True  # Enable verification
        )

    # Verify the error message
    assert "Failed to deliver initial prompt" in str(exc_info.value)
    assert agent_id in str(exc_info.value)
    assert "3 attempts" in str(exc_info.value)

    # Verify send_keys was called for all three attempts
    assert mock_pane.send_keys.call_count == 6  # 3 attempts × 2 calls each
    assert mock_cli_agent.format_message.call_count == 3

    # Verify verification was called three times
    assert agent_manager._verify_prompt_delivery.call_count == 3


@pytest.mark.asyncio
async def test_send_initial_prompt_with_retry_custom_max_retries(
    agent_manager, mock_pane, mock_cli_agent
):
    """Test that custom max_retries parameter is respected with verification enabled."""
    agent_id = "test-agent-123"
    task_id = "test-task-456"
    initial_message = "Test initial message\nTask ID: test-task-456"

    # Mock verification to always fail
    agent_manager._verify_prompt_delivery = AsyncMock(return_value=False)

    # Should fail after 5 retries (custom value)
    with pytest.raises(Exception) as exc_info:
        await agent_manager._send_initial_prompt_with_retry(
            pane=mock_pane,
            cli_agent=mock_cli_agent,
            initial_message=initial_message,
            agent_id=agent_id,
            task_id=task_id,
            max_retries=5,  # Custom value
            verify_delivery=True  # Enable verification
        )

    # Verify the error message mentions 5 attempts
    assert "5 attempts" in str(exc_info.value)

    # Verify send_keys was called for all 5 attempts
    assert mock_pane.send_keys.call_count == 10  # 5 attempts × 2 calls each

    # Verify verification was called 5 times
    assert agent_manager._verify_prompt_delivery.call_count == 5


@pytest.mark.asyncio
async def test_verify_prompt_delivery_with_custom_wait_time(agent_manager, mock_pane):
    """Test that custom wait_seconds parameter is respected."""
    mock_result = Mock()
    mock_result.stdout = ["Task ID: test-task-123"]
    mock_pane.cmd = Mock(return_value=mock_result)

    import time
    start_time = time.time()

    # Use a 0.5 second wait
    result = await agent_manager._verify_prompt_delivery(
        pane=mock_pane,
        verification_string="Task ID: test-task-123",
        wait_seconds=0.5
    )

    elapsed_time = time.time() - start_time

    assert result is True
    # Verify that approximately 0.5 seconds elapsed (with some tolerance)
    assert 0.4 < elapsed_time < 0.7


@pytest.mark.asyncio
async def test_verify_prompt_delivery_multiline_output(agent_manager, mock_pane):
    """Test verification works with multiline output."""
    mock_result = Mock()
    mock_result.stdout = [
        "=== TASK ASSIGNMENT ===",
        "Your Agent ID: agent-abc-123",
        "Task ID: task-xyz-789",
        "Working Directory: /path/to/worktree",
        "",
        "TASK DESCRIPTION:",
        "Complete the implementation",
    ]
    mock_pane.cmd = Mock(return_value=mock_result)

    # Verify we can find strings from different parts of the output
    result1 = await agent_manager._verify_prompt_delivery(
        pane=mock_pane,
        verification_string="Task ID: task-xyz-789",
        wait_seconds=0.1
    )

    result2 = await agent_manager._verify_prompt_delivery(
        pane=mock_pane,
        verification_string="TASK ASSIGNMENT",
        wait_seconds=0.1
    )

    result3 = await agent_manager._verify_prompt_delivery(
        pane=mock_pane,
        verification_string="NOT IN OUTPUT",
        wait_seconds=0.1
    )

    assert result1 is True
    assert result2 is True
    assert result3 is False


@pytest.mark.asyncio
async def test_send_initial_prompt_with_chunking_large_message(
    agent_manager, mock_pane, mock_cli_agent
):
    """Test that large messages are sent in chunks without verification."""
    agent_id = "test-agent-123"
    task_id = "test-task-456"
    # Create a message larger than 1500 chars (chunk size)
    large_message = "X" * 2000 + "\nTask ID: test-task-456"

    # Should not raise an exception
    await agent_manager._send_initial_prompt_with_retry(
        pane=mock_pane,
        cli_agent=mock_cli_agent,
        initial_message=large_message,
        agent_id=agent_id,
        task_id=task_id,
        max_retries=3,
        verify_delivery=False  # No verification, just testing chunking
    )

    # With 2000 chars and chunk_size=1500, we expect:
    # Chunk 1: chars 0-1500 (1500 chars)
    # Chunk 2: chars 1500-end (~527 chars)
    # Total: 2 chunks + 1 Enter = 3 send_keys calls
    assert mock_pane.send_keys.call_count == 3

    # Verify the first call was the first chunk (1500 chars)
    first_call_arg = mock_pane.send_keys.call_args_list[0][0][0]
    assert len(first_call_arg) == 1500

    # Verify the last call was just Enter
    last_call = mock_pane.send_keys.call_args_list[-1]
    assert last_call[0][0] == ''  # Empty string
    assert last_call[1].get('enter') is True  # enter=True

    # Verify formatting was called once
    mock_cli_agent.format_message.assert_called_once_with(large_message)
