"""Integration test for steering messages with real OpenAI API."""

import asyncio
import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime
from dotenv import load_dotenv

from src.core.database import DatabaseManager, Agent, Task, AgentLog
from src.agents.manager import AgentManager
from src.monitoring.guardian import Guardian
from src.interfaces.llm_interface import OpenAIProvider
from src.memory.rag import RAGSystem

# Load environment variables
load_dotenv()


@pytest.fixture
def openai_api_key():
    """Get OpenAI API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        pytest.skip("OPENAI_API_KEY not found in environment")
    return api_key


@pytest.fixture
def mock_db_manager():
    """Mock database manager."""
    mock = Mock(spec=DatabaseManager)

    # Mock session behavior
    session_mock = Mock()
    session_mock.query.return_value.filter_by.return_value.first.return_value = Task(
        id="test-task-1",
        raw_description="Fix import error in authentication module",
        enriched_description="Fix the import error in the authentication module by checking the module path and dependencies",
        done_definition="Import error is resolved and authentication module loads correctly",
        status="in_progress"
    )
    session_mock.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
    session_mock.close = Mock()
    mock.get_session.return_value = session_mock

    return mock


@pytest.fixture
def mock_agent_manager():
    """Mock agent manager."""
    mock = Mock(spec=AgentManager)
    mock.send_message_to_agent = Mock()

    return mock


@pytest.fixture
def test_agent():
    """Test agent for integration testing."""
    agent = Agent(
        id="integration-test-agent",
        status="working",
        current_task_id="test-task-1",
        tmux_session_name="agent-integration-test",
        cli_type="claude_code",
        last_activity=datetime.utcnow()
    )
    agent.health_check_failures = 0
    return agent


class TestSteeringOpenAIIntegration:
    """Integration tests with real OpenAI API."""

    @pytest.mark.asyncio
    async def test_guardian_steering_with_real_openai_stuck_agent(
        self,
        openai_api_key,
        mock_db_manager,
        mock_agent_manager,
        test_agent
    ):
        """Test that Guardian properly generates steering messages for stuck agent using real OpenAI."""

        # Create real OpenAI provider
        llm_provider = OpenAIProvider(api_key=openai_api_key, model="gpt-4o-mini")

        # Create Guardian with real LLM
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=llm_provider
        )

        # Simulate agent clearly stuck in a loop with the same error repeatedly
        tmux_output = """
        Traceback (most recent call last):
          File "auth.py", line 5, in <module>
            from authentication.models import User
        ImportError: No module named 'authentication.models'

        Let me try again...

        Traceback (most recent call last):
          File "auth.py", line 5, in <module>
            from authentication.models import User
        ImportError: No module named 'authentication.models'

        Still getting the same error. Let me try once more...

        Traceback (most recent call last):
          File "auth.py", line 5, in <module>
            from authentication.models import User
        ImportError: No module named 'authentication.models'

        I keep getting this same import error over and over. I've tried the same import statement 6 times now and it fails every time with the exact same error. I'm clearly stuck and repeating the same failed approach. I don't know what else to try and I'm just running the same failing code repeatedly.
        """

        # Add past summaries showing the agent has been stuck for a while
        past_summaries = [
            {
                "current_phase": "implementation",
                "trajectory_aligned": False,
                "trajectory_summary": "Agent repeatedly encountering the same ImportError without changing approach",
                "needs_steering": False,
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "current_phase": "implementation",
                "trajectory_aligned": False,
                "trajectory_summary": "Still stuck on the same import error, trying identical approach multiple times",
                "needs_steering": False,
                "timestamp": "2024-01-01T10:05:00"
            }
        ]

        # Perform analysis with real OpenAI
        analysis = await guardian.analyze_agent_with_trajectory(
            agent=test_agent,
            tmux_output=tmux_output,
            past_summaries=past_summaries
        )

        # Verify the analysis structure
        assert "needs_steering" in analysis
        assert "steering_type" in analysis
        assert "steering_message" in analysis
        assert "trajectory_summary" in analysis
        assert "current_phase" in analysis
        assert "trajectory_aligned" in analysis

        # Verify steering is recommended for stuck agent
        assert analysis["needs_steering"] is True, f"Expected steering needed, but got: {analysis}"
        assert analysis["steering_type"] in ["stuck", "confused", "drifting"], f"Expected valid steering type, got: {analysis['steering_type']}"
        assert analysis["steering_message"] is not None, "Expected steering message to be provided"
        assert len(analysis["steering_message"]) > 10, f"Expected meaningful steering message, got: {analysis['steering_message']}"

        # Verify the steering message contains helpful guidance
        steering_message = analysis["steering_message"].lower()
        assert any(keyword in steering_message for keyword in [
            "import", "path", "module", "check", "try", "look", "find"
        ]), f"Expected import-related guidance in steering message: {analysis['steering_message']}"

        print(f"\n=== OpenAI Steering Analysis ===")
        print(f"Current Phase: {analysis['current_phase']}")
        print(f"Trajectory Aligned: {analysis['trajectory_aligned']}")
        print(f"Needs Steering: {analysis['needs_steering']}")
        print(f"Steering Type: {analysis['steering_type']}")
        print(f"Steering Message: {analysis['steering_message']}")
        print(f"Trajectory Summary: {analysis['trajectory_summary']}")

    @pytest.mark.asyncio
    async def test_guardian_steering_with_real_openai_healthy_agent(
        self,
        openai_api_key,
        mock_db_manager,
        mock_agent_manager,
        test_agent
    ):
        """Test that Guardian doesn't recommend steering for healthy agent using real OpenAI."""

        # Create real OpenAI provider
        llm_provider = OpenAIProvider(api_key=openai_api_key, model="gpt-4o-mini")

        # Create Guardian with real LLM
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=llm_provider
        )

        # Simulate healthy agent making progress
        tmux_output = """
        Successfully imported the authentication models.
        Now implementing the login endpoint functionality.
        Adding proper error handling and validation.

        def login(username, password):
            user = authenticate_user(username, password)
            if user:
                return generate_token(user)
            else:
                raise ValueError("Invalid credentials")

        Running tests to verify the implementation...
        All authentication tests passing.
        """

        # Perform analysis with real OpenAI
        analysis = await guardian.analyze_agent_with_trajectory(
            agent=test_agent,
            tmux_output=tmux_output,
            past_summaries=[]
        )

        # Verify no steering needed for healthy agent
        assert analysis["needs_steering"] is False, f"Expected no steering needed for healthy agent, but got: {analysis}"
        assert analysis["trajectory_aligned"] is True, f"Expected aligned trajectory for healthy agent: {analysis}"
        assert analysis["steering_message"] is None, f"Expected no steering message for healthy agent: {analysis['steering_message']}"

        print(f"\n=== OpenAI Healthy Agent Analysis ===")
        print(f"Current Phase: {analysis['current_phase']}")
        print(f"Trajectory Aligned: {analysis['trajectory_aligned']}")
        print(f"Needs Steering: {analysis['needs_steering']}")
        print(f"Trajectory Summary: {analysis['trajectory_summary']}")

    @pytest.mark.asyncio
    async def test_guardian_steering_with_real_openai_constraint_violation(
        self,
        openai_api_key,
        mock_db_manager,
        mock_agent_manager,
        test_agent
    ):
        """Test that Guardian detects constraint violations using real OpenAI."""

        # Create real OpenAI provider
        llm_provider = OpenAIProvider(api_key=openai_api_key, model="gpt-4o-mini")

        # Create Guardian with real LLM
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=llm_provider
        )

        # Simulate agent violating "no external libraries" constraint
        tmux_output = """
        I need to implement JWT authentication. Let me install the PyJWT library.

        $ pip install PyJWT
        Collecting PyJWT
        Successfully installed PyJWT-2.8.0

        Now I can use PyJWT to generate tokens:

        import jwt

        def generate_token(user_data):
            return jwt.encode(user_data, 'secret_key', algorithm='HS256')
        """

        # Add past summary with constraint
        past_summaries = [{
            "constraints": ["No external libraries - use only built-in Python modules"],
            "current_phase": "implementation",
            "trajectory_summary": "Agent was instructed to implement JWT without external libraries"
        }]

        # Perform analysis with real OpenAI
        analysis = await guardian.analyze_agent_with_trajectory(
            agent=test_agent,
            tmux_output=tmux_output,
            past_summaries=past_summaries
        )

        # Verify constraint violation is detected
        assert analysis["needs_steering"] is True, f"Expected steering for constraint violation, got: {analysis}"
        assert analysis["steering_type"] in ["violating_constraints", "drifting", "off_track"], f"Expected constraint-related steering type: {analysis['steering_type']}"
        assert analysis["steering_message"] is not None, "Expected steering message for constraint violation"

        # Check that steering message mentions the constraint
        steering_message = analysis["steering_message"].lower()
        assert any(keyword in steering_message for keyword in [
            "external", "library", "constraint", "built-in", "avoid", "without"
        ]), f"Expected constraint-related guidance in steering message: {analysis['steering_message']}"

        print(f"\n=== OpenAI Constraint Violation Analysis ===")
        print(f"Current Phase: {analysis['current_phase']}")
        print(f"Trajectory Aligned: {analysis['trajectory_aligned']}")
        print(f"Needs Steering: {analysis['needs_steering']}")
        print(f"Steering Type: {analysis['steering_type']}")
        print(f"Steering Message: {analysis['steering_message']}")
        print(f"Trajectory Summary: {analysis['trajectory_summary']}")

    @pytest.mark.asyncio
    async def test_steering_message_field_consistency_with_openai(
        self,
        openai_api_key,
        mock_db_manager,
        mock_agent_manager,
        test_agent
    ):
        """Test that steering message field mapping works correctly with real OpenAI."""

        # Create real OpenAI provider
        llm_provider = OpenAIProvider(api_key=openai_api_key, model="gpt-4o-mini")

        # Create Guardian with real LLM
        guardian = Guardian(
            db_manager=mock_db_manager,
            agent_manager=mock_agent_manager,
            llm_provider=llm_provider
        )

        # Simulate agent that needs steering
        tmux_output = """
        I'm confused about what to do next. The task says to fix the authentication but I'm not sure where to start.
        I've been looking at the code for a while but can't figure out the issue.
        """

        # Perform analysis
        analysis = await guardian.analyze_agent_with_trajectory(
            agent=test_agent,
            tmux_output=tmux_output,
            past_summaries=[]
        )

        # Verify field mapping from LLM response to Guardian output
        if analysis["needs_steering"]:
            # Guardian should map steering_recommendation -> steering_message
            assert "steering_message" in analysis, "Guardian should provide steering_message field"
            assert analysis["steering_message"] is not None, "Guardian should map steering_recommendation to steering_message"

            # Test the actual steering call
            await guardian.steer_agent(
                agent=test_agent,
                steering_type=analysis["steering_type"],
                message=analysis["steering_message"]
            )

            # Verify the agent manager was called with the message
            mock_agent_manager.send_message_to_agent.assert_called_once()
            call_args = mock_agent_manager.send_message_to_agent.call_args

            agent_id_called = call_args[0][0]
            message_sent = call_args[0][1]

            assert agent_id_called == test_agent.id
            assert analysis["steering_message"] in message_sent, f"Expected steering message in sent message. Expected: {analysis['steering_message']}, Sent: {message_sent}"
            assert "GUARDIAN GUIDANCE" in message_sent, "Expected Guardian identifier in message"

            print(f"\n=== Field Mapping Test ===")
            print(f"Steering Message from Guardian: {analysis['steering_message']}")
            print(f"Message sent to agent: {message_sent}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])