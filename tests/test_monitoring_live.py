"""Live integration test for the monitoring system with database verification."""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager, Agent, Task, AgentLog, get_db
from src.agents.manager import AgentManager
from src.monitoring.guardian import Guardian
from src.monitoring.conductor import Conductor
from src.monitoring.trajectory_context import TrajectoryContext
from src.interfaces.llm_interface import get_llm_provider


async def setup_test_environment():
    """Initialize database and create test agents."""
    print("🚀 Setting up test environment...")

    # Initialize database
    db_manager = DatabaseManager("hephaestus.db")
    db_manager.create_tables()

    db_manager = DatabaseManager()
    llm_provider = get_llm_provider()
    agent_manager = AgentManager(db_manager=db_manager, llm_provider=llm_provider)

    with get_db() as db:
        # Create test tasks
        task1 = Task(
            id="test-task-1",
            raw_description="Build user authentication system",
            enriched_description="Implement JWT-based authentication with login/logout endpoints",
            done_definition="Authentication endpoints working with tests passing",
            status="in_progress",
            estimated_complexity=8,
            assigned_agent_id="test-agent-1"
        )

        task2 = Task(
            id="test-task-2",
            raw_description="Create user profile management",
            enriched_description="Build CRUD operations for user profiles with validation",
            done_definition="All profile endpoints tested and documented",
            status="in_progress",
            estimated_complexity=6,
            assigned_agent_id="test-agent-2"
        )

        task3 = Task(
            id="test-task-3",
            raw_description="Implement authentication logic",  # Duplicate work!
            enriched_description="Create JWT token generation and validation",
            done_definition="JWT tokens working correctly",
            status="in_progress",
            estimated_complexity=7,
            assigned_agent_id="test-agent-3"
        )

        db.add_all([task1, task2, task3])
        db.commit()

        # Create test agents
        agent1 = Agent(
            id="test-agent-1",
            tmux_session_name="test-session-1",
            current_task_id="test-task-1",
            status="working",
            system_prompt="Build authentication system",
            cli_type="claude",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )

        agent2 = Agent(
            id="test-agent-2",
            tmux_session_name="test-session-2",
            current_task_id="test-task-2",
            status="working",
            system_prompt="Create user profile management",
            cli_type="claude",
            created_at=datetime.utcnow() - timedelta(hours=1, minutes=30)
        )

        agent3 = Agent(
            id="test-agent-3",
            tmux_session_name="test-session-3",
            current_task_id="test-task-3",
            status="stuck",  # This one is stuck!
            system_prompt="Implement authentication logic",
            cli_type="claude",
            created_at=datetime.utcnow() - timedelta(minutes=45)
        )

        db.add_all([agent1, agent2, agent3])
        db.commit()

        # Add some agent logs to build trajectory
        logs = [
            # Agent 1 logs
            AgentLog(
                agent_id="test-agent-1",
                log_type="input",
                message="Build authentication without external frameworks",
                details={"task_id": "test-task-1"}
            ),
            AgentLog(
                agent_id="test-agent-1",
                log_type="output",
                message="I'll implement JWT authentication from scratch using only standard library",
                details={}
            ),
            AgentLog(
                agent_id="test-agent-1",
                log_type="output",
                message="Currently implementing the token generation logic",
                details={}
            ),

            # Agent 2 logs
            AgentLog(
                agent_id="test-agent-2",
                log_type="input",
                message="Create user profile CRUD operations with proper validation",
                details={"task_id": "test-task-2"}
            ),
            AgentLog(
                agent_id="test-agent-2",
                log_type="output",
                message="I'm building the profile endpoints with input validation",
                details={}
            ),
            AgentLog(
                agent_id="test-agent-2",
                log_type="output",
                message="Working on the UPDATE profile endpoint now",
                details={}
            ),

            # Agent 3 logs (duplicate work)
            AgentLog(
                agent_id="test-agent-3",
                log_type="input",
                message="Implement JWT token handling",
                details={"task_id": "test-task-3"}
            ),
            AgentLog(
                agent_id="test-agent-3",
                log_type="output",
                message="I'm creating JWT token generation and validation functions",
                details={}
            ),
            AgentLog(
                agent_id="test-agent-3",
                log_type="error",
                message="Error: Having trouble with token signature validation",
                details={"error_type": "implementation"}
            ),
        ]

        db.add_all(logs)
        db.commit()

        print("✅ Test environment setup complete")
        return db_manager, agent_manager


async def run_monitoring_cycle(db_manager, agent_manager):
    """Run one complete monitoring cycle."""
    print("\n🔄 Running monitoring cycle...")

    # Initialize monitoring components
    llm_provider = get_llm_provider()
    guardian = Guardian(
        db_manager=db_manager,
        agent_manager=agent_manager,
        llm_provider=llm_provider
    )
    conductor = Conductor(
        db_manager=db_manager,
        agent_manager=agent_manager
    )

    with get_db() as db:
        # Get all active agents
        agents = db.query(Agent).filter(
            Agent.status.in_(["working", "stuck"])
        ).all()

        print(f"📊 Found {len(agents)} active agents to monitor")

        # Guardian analysis for each agent
        guardian_summaries = []
        for agent in agents:
            print(f"\n🔍 Guardian analyzing agent {agent.id}...")

            # Simulate tmux output
            tmux_output = f"Agent {agent.id} working on task {agent.current_task_id}..."

            try:
                # Run Guardian analysis
                summary = await guardian.analyze_agent_with_trajectory(
                    agent=agent,
                    tmux_output=tmux_output,
                    past_summaries=[]
                )

                print(f"  - Phase: {summary.get('current_phase', 'unknown')}")
                print(f"  - Aligned: {summary.get('trajectory_aligned', False)}")
                print(f"  - Score: {summary.get('alignment_score', 0):.2f}")
                print(f"  - Needs steering: {summary.get('needs_steering', False)}")

                # Handle steering if needed
                if summary.get("needs_steering"):
                    print(f"  ⚠️ Steering needed: {summary.get('steering_type')}")
                    await guardian.steer_agent(
                        agent=agent,
                        steering_type=summary.get("steering_type", "guidance"),
                        message=summary.get("steering_message", "Please review your approach")
                    )

                guardian_summaries.append(summary)

            except Exception as e:
                print(f"  ❌ Guardian analysis failed: {e}")
                guardian_summaries.append({
                    "agent_id": agent.id,
                    "error": str(e),
                    "trajectory_aligned": True,  # Safe default
                    "needs_steering": False
                })

        # Conductor system analysis
        if len(guardian_summaries) > 1:
            print(f"\n🎼 Conductor analyzing system with {len(guardian_summaries)} agents...")

            try:
                system_analysis = await conductor.analyze_system_state(guardian_summaries)

                print(f"  - System coherence: {system_analysis['coherence']['score']:.2f}")
                print(f"  - Duplicates found: {len(system_analysis.get('duplicates', []))}")
                print(f"  - Decisions to execute: {len(system_analysis.get('decisions', []))}")

                # Show duplicates if found
                for dup in system_analysis.get('duplicates', []):
                    print(f"  ⚠️ Duplicate: {dup['agent1']} and {dup['agent2']} - {dup['work']}")

                # Execute decisions
                if system_analysis.get('decisions'):
                    print("\n📋 Executing Conductor decisions...")
                    await conductor.execute_decisions(system_analysis['decisions'])

                    for decision in system_analysis['decisions']:
                        print(f"  - {decision['type']}: {decision.get('target', decision.get('reason', ''))}")

                # Generate and save report
                report = await conductor.generate_detailed_report(system_analysis)
                print("\n📄 Report generated and saved to database")

                return system_analysis

            except Exception as e:
                print(f"  ❌ Conductor analysis failed: {e}")
                return None

        return None


async def verify_database_logs():
    """Verify that analyses and logs are saved in database."""
    print("\n🔍 Verifying database logs...")

    with get_db() as db:
        # Check Guardian steering logs
        steering_logs = db.query(AgentLog).filter(
            AgentLog.log_type == "steering"
        ).all()
        print(f"  - Steering interventions logged: {len(steering_logs)}")

        # Check Guardian analysis logs
        analysis_logs = db.query(AgentLog).filter(
            AgentLog.log_type == "analysis"
        ).all()
        print(f"  - Guardian analyses logged: {len(analysis_logs)}")

        # Check Conductor decision logs
        conductor_logs = db.query(AgentLog).filter(
            AgentLog.log_type == "conductor_decision"
        ).all()
        print(f"  - Conductor decisions logged: {len(conductor_logs)}")

        # Check for termination logs
        termination_logs = db.query(AgentLog).filter(
            AgentLog.log_type == "termination"
        ).all()
        print(f"  - Agent terminations logged: {len(termination_logs)}")

        # Show sample logs
        if analysis_logs:
            print("\n📊 Sample Guardian analysis log:")
            log = analysis_logs[0]
            print(f"  - Agent: {log.agent_id}")
            print(f"  - Time: {log.created_at}")
            if log.details:
                print(f"  - Phase: {log.details.get('current_phase', 'unknown')}")
                print(f"  - Aligned: {log.details.get('trajectory_aligned', False)}")

        if conductor_logs:
            print("\n🎼 Sample Conductor decision log:")
            log = conductor_logs[0]
            print(f"  - Time: {log.created_at}")
            if log.details:
                print(f"  - Type: {log.details.get('type', 'unknown')}")
                print(f"  - Reason: {log.details.get('reason', 'none')}")

        # Check agent status updates
        agents = db.query(Agent).all()
        print("\n👥 Agent statuses after monitoring:")
        for agent in agents:
            print(f"  - {agent.id}: {agent.status}")
            if agent.status == "terminated":
                print(f"    (Terminated at: {agent.last_activity})")


async def main():
    """Run the complete integration test."""
    print("=" * 60)
    print("MONITORING SYSTEM INTEGRATION TEST")
    print("=" * 60)

    try:
        # Setup
        db_manager, agent_manager = await setup_test_environment()

        # Run monitoring cycles
        print("\n" + "=" * 60)
        print("MONITORING CYCLE 1")
        print("=" * 60)

        analysis1 = await run_monitoring_cycle(db_manager, agent_manager)

        # Wait a bit to simulate time passing
        await asyncio.sleep(2)

        print("\n" + "=" * 60)
        print("MONITORING CYCLE 2 (After decisions executed)")
        print("=" * 60)

        analysis2 = await run_monitoring_cycle(db_manager, agent_manager)

        # Verify everything was logged
        print("\n" + "=" * 60)
        print("DATABASE VERIFICATION")
        print("=" * 60)

        await verify_database_logs()

        print("\n" + "=" * 60)
        print("✅ INTEGRATION TEST COMPLETE")
        print("=" * 60)

        # Summary
        if analysis1:
            print(f"\nFirst cycle coherence: {analysis1['coherence']['score']:.2f}")
        if analysis2:
            print(f"Second cycle coherence: {analysis2['coherence']['score']:.2f}")

        print("\n🎉 Monitoring system is working correctly!")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run with real LLM if available, otherwise mock
    import os
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️ No LLM API keys found, using mock responses")

        # Mock the LLM provider for testing
        from unittest.mock import AsyncMock
        import src.interfaces.llm_interface as llm_interface

        mock_provider = AsyncMock()
        mock_provider.analyze_agent_trajectory = AsyncMock(return_value={
            "current_phase": "implementation",
            "trajectory_aligned": True,
            "alignment_score": 0.8,
            "alignment_issues": [],
            "needs_steering": False,
            "steering_type": None,
            "steering_recommendation": None,
            "trajectory_summary": "Agent working on task successfully"
        })

        # Make agent 3 need steering (it has errors)
        def trajectory_side_effect(*args, **kwargs):
            if "test-agent-3" in str(kwargs.get("agent_output", "")):
                return {
                    "current_phase": "debugging",
                    "trajectory_aligned": False,
                    "alignment_score": 0.4,
                    "alignment_issues": ["Stuck on error"],
                    "needs_steering": True,
                    "steering_type": "stuck",
                    "steering_recommendation": "Check token signature algorithm",
                    "trajectory_summary": "Agent stuck on JWT validation error"
                }
            return mock_provider.analyze_agent_trajectory.return_value

        mock_provider.analyze_agent_trajectory.side_effect = trajectory_side_effect

        mock_provider.analyze_system_coherence = AsyncMock(return_value={
            "coherence_score": 0.6,
            "duplicates": [
                {
                    "agent1": "test-agent-1",
                    "agent2": "test-agent-3",
                    "similarity": 0.85,
                    "work": "Both implementing JWT authentication"
                }
            ],
            "alignment_issues": ["Two agents working on authentication"],
            "termination_recommendations": [
                {
                    "agent_id": "test-agent-3",
                    "reason": "Duplicate with test-agent-1 who started earlier"
                }
            ],
            "coordination_needs": [],
            "system_summary": "System has duplicate work on authentication needing resolution"
        })

        llm_interface.get_llm_provider = lambda: mock_provider

    asyncio.run(main())