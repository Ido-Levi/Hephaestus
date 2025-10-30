"""Test structured analysis using real OpenAI API."""

import pytest
import asyncio
import os
from dotenv import load_dotenv

from src.interfaces.llm_interface import get_llm_provider
from src.monitoring.models import GuardianTrajectoryAnalysis, ConductorSystemAnalysis


# Load environment variables
load_dotenv()


@pytest.mark.asyncio
async def test_guardian_structured_analysis():
    """Test Guardian analysis returns proper Pydantic structure."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No OPENAI_API_KEY found in environment")

    provider = get_llm_provider()

    # Mock data for testing
    agent_output = """
    Agent is working on analyzing a file structure.
    Current task: Reading configuration files
    Progress: Found 3 config files, analyzing contents
    Next steps: Parse JSON configurations
    """

    accumulated_context = {
        "goal": "Analyze configuration system",
        "constraints": ["Read-only access", "No external dependencies"],
        "session_start": "2025-09-25T21:00:00Z"
    }

    past_summaries = [
        {
            "phase": "exploration",
            "summary": "Started exploring codebase structure",
            "timestamp": "2025-09-25T21:05:00Z"
        }
    ]

    task_info = {
        "id": "test-task-123",
        "description": "Analyze configuration files and document their structure",
        "agent_id": "test-agent-456"
    }

    # Call the analysis method
    result = await provider.analyze_agent_trajectory(
        agent_output=agent_output,
        accumulated_context=accumulated_context,
        past_summaries=past_summaries,
        task_info=task_info
    )

    # Verify it's a dict (from model_dump())
    assert isinstance(result, dict)

    # Verify all required fields are present
    assert "current_phase" in result
    assert "trajectory_aligned" in result
    assert "alignment_score" in result
    assert "alignment_issues" in result
    assert "needs_steering" in result
    assert "steering_type" in result
    assert "steering_recommendation" in result
    assert "trajectory_summary" in result

    # Verify types and constraints
    assert isinstance(result["trajectory_aligned"], bool)
    assert isinstance(result["alignment_score"], (int, float))
    assert 0.0 <= result["alignment_score"] <= 1.0
    assert isinstance(result["alignment_issues"], list)
    assert isinstance(result["needs_steering"], bool)
    assert isinstance(result["trajectory_summary"], str)
    assert len(result["trajectory_summary"]) > 0

    # Verify phase is valid
    valid_phases = ["exploration", "information_gathering", "planning", "implementation", "verification", "completed", "unknown"]
    assert result["current_phase"] in valid_phases

    # Verify steering_type is valid if present
    if result["steering_type"] is not None:
        valid_steering_types = ["stuck", "drifting", "violating_constraints", "over_engineering", "confused"]
        assert result["steering_type"] in valid_steering_types

    # Test that we can create a Pydantic model from the result
    model = GuardianTrajectoryAnalysis(**result)
    assert model is not None


@pytest.mark.asyncio
async def test_conductor_structured_analysis():
    """Test Conductor analysis returns proper Pydantic structure."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No OPENAI_API_KEY found in environment")

    provider = get_llm_provider()

    # Mock Guardian summaries
    guardian_summaries = [
        {
            "agent_id": "agent-1",
            "summary": "Working on configuration analysis",
            "phase": "implementation",
            "aligned": True,
            "needs_steering": False,
            "accumulated_goal": "Analyze config files"
        },
        {
            "agent_id": "agent-2",
            "summary": "Testing API endpoints",
            "phase": "verification",
            "aligned": True,
            "needs_steering": False,
            "accumulated_goal": "Test system APIs"
        }
    ]

    system_goals = {
        "primary": "Complete system analysis",
        "constraints": "No external dependencies",
        "coordination": "Agents should not duplicate work"
    }

    # Call the analysis method
    result = await provider.analyze_system_coherence(
        guardian_summaries=guardian_summaries,
        system_goals=system_goals
    )

    # Verify it's a dict (from model_dump())
    assert isinstance(result, dict)

    # Verify all required fields are present
    assert "coherence_score" in result
    assert "duplicates" in result
    assert "alignment_issues" in result
    assert "termination_recommendations" in result
    assert "coordination_needs" in result
    assert "system_summary" in result

    # Verify types and constraints
    assert isinstance(result["coherence_score"], (int, float))
    assert 0.0 <= result["coherence_score"] <= 1.0
    assert isinstance(result["duplicates"], list)
    assert isinstance(result["alignment_issues"], list)
    assert isinstance(result["termination_recommendations"], list)
    assert isinstance(result["coordination_needs"], list)
    assert isinstance(result["system_summary"], str)
    assert len(result["system_summary"]) > 0

    # Test that we can create a Pydantic model from the result
    model = ConductorSystemAnalysis(**result)
    assert model is not None


@pytest.mark.asyncio
async def test_analysis_retry_mechanism():
    """Test that analysis methods handle failures gracefully with retries."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No OPENAI_API_KEY found in environment")

    provider = get_llm_provider()

    # Use invalid model to trigger failure
    original_model = provider.model
    provider.model = "invalid-model-name"

    try:
        # This should fail and fallback after 3 retries
        result = await provider.analyze_agent_trajectory(
            agent_output="test output",
            accumulated_context={"goal": "test"},
            past_summaries=[],
            task_info={"id": "test", "agent_id": "test"}
        )

        # Should get fallback response
        assert result["trajectory_summary"] == "Analysis failed after 3 attempts"
        assert result["current_phase"] == "unknown"
        assert result["alignment_score"] == 0.5

    finally:
        # Restore original model
        provider.model = original_model


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_guardian_structured_analysis())
    asyncio.run(test_conductor_structured_analysis())
    print("All tests passed!")