#!/usr/bin/env python3
"""
Comprehensive Integration Test for Hephaestus System

This test validates the entire system end-to-end by:
- Running real components (server, monitor, database, git)
- Creating actual agents and worktrees
- Testing validation flows
- Verifying cleanup and resource management

WARNING: This test is destructive! It will:
- Delete the existing database
- Kill running Hephaestus processes
- Remove worktrees
- Clean git branches
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database import (
    DatabaseManager,
    Base,
    Task,
    Agent,
    Phase,
    ValidationReview,
    Workflow,
    Memory,
    AgentWorktree,
)
from src.core.simple_config import Config
from src.interfaces.llm_interface import LLMProviderInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tests/integration/integration_test.log"),
    ],
)
logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProviderInterface):
    """Mock LLM provider for deterministic testing."""

    def __init__(self):
        self.call_count = 0
        self.responses = {}

    async def generate_agent_prompt(self, task: Dict, memories: List, project_context: str) -> str:
        """Generate a test prompt."""
        self.call_count += 1
        return f"Test prompt for task {task.get('id', 'unknown')}. Complete the task and update status."

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate a fixed embedding."""
        return [0.1] * 1536

    async def enhance_task_description(
        self, task_description: str, done_definition: str, memories: List
    ) -> Dict[str, Any]:
        """Return enhanced task data."""
        return {
            "specifications": [
                "Test specification 1",
                "Test specification 2"
            ],
            "estimated_complexity": 3,
            "suggested_approach": "Test approach",
            "potential_challenges": ["Test challenge"],
            "relevant_files": []
        }

    async def analyze_stuck_agent(self, agent_context: Dict) -> Dict[str, Any]:
        """Analyze stuck agent."""
        return {
            "likely_issue": "Test issue",
            "suggested_intervention": "restart",
            "confidence": 0.8,
            "reasoning": "Test reasoning"
        }

    async def generate_intervention_message(
        self, agent_id: str, intervention_type: str, context: Dict
    ) -> str:
        """Generate intervention message."""
        return f"Test intervention: {intervention_type} for agent {agent_id}"

    async def enrich_task(
        self,
        task_description: str,
        done_definition: str,
        context: List[str],
        phase_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich a task with test data."""
        return {
            "enriched_description": f"Test: {task_description}",
            "completion_criteria": [done_definition],
            "agent_prompt": "Test agent prompt",
            "required_capabilities": ["test"],
            "estimated_complexity": 3,
        }

    async def analyze_agent_state(
        self,
        agent_output: str,
        task_info: Dict[str, Any],
        project_context: str,
    ) -> Dict[str, Any]:
        """Analyze agent state for testing."""
        return {
            "status": "healthy",
            "progress": 50,
            "needs_intervention": False,
            "suggested_action": None,
        }

    def get_model_name(self) -> str:
        """Get test model name."""
        return "test-model"


class HephaestusIntegrationTest:
    """
    Full system integration test for Hephaestus.
    Tests real components with minimal mocking.
    """

    def __init__(self):
        self.server_process = None
        self.monitor_process = None
        self.db_manager = None
        self.base_url = "http://localhost:8000"
        self.test_dir = Path("tests/integration/test_data")
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Test configuration
        self.test_config = {
            "monitoring_interval_seconds": 5,
            "agent_timeout_minutes": 1,
            "max_health_check_failures": 2,
        }

    def setup(self):
        """Set up the test environment."""
        logger.info("=" * 80)
        logger.info("STARTING INTEGRATION TEST SETUP")
        logger.info("=" * 80)

        # 1. Kill existing processes
        self._kill_existing_processes()

        # 2. Clean filesystem
        self._clean_filesystem()

        # 3. Initialize fresh database
        self._initialize_database()

        # 4. Start services
        self._start_services()

        logger.info("Setup complete")

    def teardown(self):
        """Clean up after tests."""
        logger.info("=" * 80)
        logger.info("STARTING INTEGRATION TEST TEARDOWN")
        logger.info("=" * 80)

        # Stop services
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=5)

        if self.monitor_process:
            self.monitor_process.terminate()
            self.monitor_process.wait(timeout=5)

        # Clean up tmux sessions
        self._cleanup_tmux_sessions()

        # Clean up worktrees
        self._cleanup_worktrees()

        logger.info("Teardown complete")

    def _kill_existing_processes(self):
        """Kill any existing Hephaestus processes."""
        logger.info("Killing existing processes...")

        # Kill server processes
        subprocess.run(["pkill", "-f", "run_server.py"], capture_output=True)
        subprocess.run(["pkill", "-f", "uvicorn.*hephaestus"], capture_output=True)

        # Kill monitor processes
        subprocess.run(["pkill", "-f", "run_monitor.py"], capture_output=True)

        # Kill test tmux sessions
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for session in result.stdout.strip().split("\n"):
                if session.startswith("hep_agent_") or session.startswith("agent_"):
                    subprocess.run(["tmux", "kill-session", "-t", session])
                    logger.info(f"Killed tmux session: {session}")

        time.sleep(2)  # Give processes time to die

    def _clean_filesystem(self):
        """Clean up filesystem state."""
        logger.info("Cleaning filesystem...")

        # Remove test database
        db_path = Path("hephaestus_test.db")
        if db_path.exists():
            db_path.unlink()
            logger.info("Removed test database")

        # Clean worktrees directory
        worktrees_dir = Path("worktrees")
        if worktrees_dir.exists():
            shutil.rmtree(worktrees_dir, ignore_errors=True)
            logger.info("Cleaned worktrees directory")

        # Create fresh directories
        worktrees_dir.mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

    def _initialize_database(self):
        """Initialize fresh database."""
        logger.info("Initializing database...")

        # Use test database
        os.environ["DATABASE_PATH"] = "./hephaestus_test.db"

        # Run init script
        result = subprocess.run(
            [sys.executable, "scripts/init_db.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error(f"Database init failed: {result.stderr}")
            raise RuntimeError("Failed to initialize database")

        logger.info("Database initialized")

        # Create database manager
        self.db_manager = DatabaseManager(database_path="hephaestus_test.db")

    def _start_services(self):
        """Start MCP server and monitor."""
        logger.info("Starting services...")

        # Set test environment variables
        env = os.environ.copy()
        env.update({
            "DATABASE_PATH": "./hephaestus_test.db",
            "MCP_PORT": "8000",
            "MONITORING_INTERVAL_SECONDS": "5",
            "LLM_PROVIDER": "openai",  # Will be mocked
            "OPENAI_API_KEY": "test-key",
            "WORKTREE_BASE_PATH": "./worktrees",
            "MAIN_REPO_PATH": str(Path.cwd()),
        })

        # Start MCP server
        self.server_process = subprocess.Popen(
            [sys.executable, "run_server.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Started MCP server")

        # Wait for server to be ready
        self._wait_for_server()

        # Start monitor (optional for some tests)
        self.monitor_process = subprocess.Popen(
            [sys.executable, "run_monitor.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Started monitor")

        time.sleep(3)  # Give services time to fully start

    def _wait_for_server(self, timeout=30):
        """Wait for server to be ready."""
        logger.info("Waiting for server to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=1)
                if response.status_code == 200:
                    logger.info("Server is ready")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        raise RuntimeError("Server failed to start within timeout")

    def _cleanup_tmux_sessions(self):
        """Clean up tmux sessions."""
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for session in result.stdout.strip().split("\n"):
                if session.startswith("hep_agent_") or session.startswith("agent_"):
                    subprocess.run(["tmux", "kill-session", "-t", session])

    def _cleanup_worktrees(self):
        """Clean up git worktrees."""
        worktrees_dir = Path("worktrees")
        if worktrees_dir.exists():
            for worktree in worktrees_dir.iterdir():
                if worktree.is_dir():
                    # Remove from git
                    subprocess.run(
                        ["git", "worktree", "remove", str(worktree), "--force"],
                        capture_output=True
                    )

        # Clean up test branches
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "agent-" in line or "test-" in line:
                    branch = line.strip().replace("*", "").strip()
                    subprocess.run(
                        ["git", "branch", "-D", branch],
                        capture_output=True
                    )

    # ========== Test Scenarios ==========

    @patch('src.interfaces.llm_interface.get_llm_provider')
    def test_basic_agent_task_completion(self, mock_get_llm):
        """Test Scenario 1: Basic agent completes a task without validation."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SCENARIO 1: Basic Agent Task Completion")
        logger.info("=" * 80)

        # Use mock LLM provider
        mock_llm = MockLLMProvider()
        mock_get_llm.return_value = mock_llm

        # 1. Create a simple task
        logger.info("Creating task...")
        response = requests.post(
            f"{self.base_url}/create_task",
            json={
                "task_description": "Create a test file",
                "done_definition": "test.txt exists",
                "ai_agent_id": "test-agent"
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["task_id"]
        logger.info(f"Created task: {task_id}")

        # 2. Wait for agent to spawn
        agent_id = self._wait_for_agent_spawn(task_id)
        logger.info(f"Agent spawned: {agent_id}")

        # 3. Verify worktree created
        self._verify_worktree_exists(agent_id)

        # 4. Simulate work in worktree
        self._simulate_agent_work(agent_id, ["test.txt"])

        # 5. Update task status to done
        response = requests.post(
            f"{self.base_url}/update_task_status",
            json={
                "task_id": task_id,
                "status": "done",
                "summary": "Created test file",
                "key_learnings": []
            },
            headers={"X-Agent-ID": agent_id}
        )
        if response.status_code != 200:
            logger.error(f"Update task status failed: {response.status_code} - {response.text}")
        assert response.status_code == 200

        # 6. Verify task completed
        task = self._get_task_from_db(task_id)
        assert task.status == "done"
        logger.info("Task marked as done")

        # 7. Verify agent terminated (with delay)
        time.sleep(3)
        agent = self._get_agent_from_db(agent_id)
        assert agent.status in ["completed", "terminated"]
        logger.info("Agent terminated successfully")

        logger.info("✅ Scenario 1 PASSED")

    @patch('src.interfaces.llm_interface.get_llm_provider')
    def test_validation_single_pass(self, mock_get_llm):
        """Test Scenario 2: Task with validation that passes on first try."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SCENARIO 2: Validation Single Pass")
        logger.info("=" * 80)

        mock_llm = MockLLMProvider()
        mock_get_llm.return_value = mock_llm

        # 1. Create workflow with validation
        workflow_id = self._create_test_workflow_with_validation()

        # 2. Create task with validation enabled
        response = requests.post(
            f"{self.base_url}/create_task",
            json={
                "task_description": "Create validated test file",
                "done_definition": "test.txt exists with content",
                "ai_agent_id": "test-agent",
                "phase": 1
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        # Enable validation on task
        self._enable_task_validation(task_id)

        # 3. Wait for agent
        agent_id = self._wait_for_agent_spawn(task_id)

        # 4. Simulate work
        self._simulate_agent_work(agent_id, ["test.txt"], content="Test content")

        # 5. Agent claims done
        response = requests.post(
            f"{self.base_url}/update_task_status",
            json={
                "task_id": task_id,
                "status": "done",
                "summary": "Created test file with content",
                "key_learnings": []
            },
            headers={"X-Agent-ID": agent_id}
        )
        if response.status_code != 200:
            logger.error(f"Update task status failed (validation test): {response.status_code} - {response.text}")
        assert response.status_code == 200

        # 6. Verify validation triggered
        time.sleep(2)
        task = self._get_task_from_db(task_id)
        assert task.status in ["under_review", "validation_in_progress"]
        logger.info("Validation triggered")

        # 7. Wait for validator agent
        validator_id = self._wait_for_validator_agent(task_id)
        logger.info(f"Validator spawned: {validator_id}")

        # 8. Simulate validation pass
        response = requests.post(
            f"{self.base_url}/give_validation_review",
            json={
                "task_id": task_id,
                "validator_agent_id": validator_id,
                "validation_passed": True,
                "feedback": "All checks passed",
                "evidence": [{"check": "file_exists", "result": "passed"}]
            },
            headers={"X-Agent-ID": validator_id}
        )
        assert response.status_code == 200

        # 9. Verify task completed
        task = self._get_task_from_db(task_id)
        assert task.status == "done"
        assert task.review_done is True
        logger.info("Task validated and completed")

        logger.info("✅ Scenario 2 PASSED")

    @patch('src.interfaces.llm_interface.get_llm_provider')
    def test_validation_with_feedback_loop(self, mock_get_llm):
        """Test Scenario 3: Validation fails first, succeeds after fix."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SCENARIO 3: Validation with Feedback Loop")
        logger.info("=" * 80)

        mock_llm = MockLLMProvider()
        mock_get_llm.return_value = mock_llm

        # 1. Create task with validation
        workflow_id = self._create_test_workflow_with_validation()

        response = requests.post(
            f"{self.base_url}/create_task",
            json={
                "task_description": "Create file with tests",
                "done_definition": "File and tests exist",
                "ai_agent_id": "test-agent",
                "phase": 1
            },
            headers={"X-Agent-ID": "test-agent"}
        )
        task_id = response.json()["task_id"]
        self._enable_task_validation(task_id)

        # 2. Agent completes without tests (will fail)
        agent_id = self._wait_for_agent_spawn(task_id)
        self._simulate_agent_work(agent_id, ["main.py"])

        response = requests.post(
            f"{self.base_url}/update_task_status",
            json={"task_id": task_id, "status": "done", "summary": "Created main.py", "key_learnings": []},
            headers={"X-Agent-ID": agent_id}
        )

        # 3. Validator fails
        validator_id = self._wait_for_validator_agent(task_id)
        response = requests.post(
            f"{self.base_url}/give_validation_review",
            json={
                "task_id": task_id,
                "validator_agent_id": validator_id,
                "validation_passed": False,
                "feedback": "Missing test file - please add test.py",
                "evidence": [{"check": "test_file", "result": "missing"}]
            },
            headers={"X-Agent-ID": validator_id}
        )

        # 4. Verify agent receives feedback
        task = self._get_task_from_db(task_id)
        assert task.status == "needs_work"
        assert task.validation_iteration == 1
        assert "Missing test file" in task.last_validation_feedback
        logger.info("Agent received feedback")

        # 5. Agent fixes issue
        self._simulate_agent_work(agent_id, ["test.py"])

        # 6. Agent tries again
        response = requests.post(
            f"{self.base_url}/update_task_status",
            json={"task_id": task_id, "status": "done", "summary": "Added tests", "key_learnings": []},
            headers={"X-Agent-ID": agent_id}
        )

        # 7. New validator passes
        validator_id_2 = self._wait_for_validator_agent(task_id)
        response = requests.post(
            f"{self.base_url}/give_validation_review",
            json={
                "task_id": task_id,
                "validator_agent_id": validator_id_2,
                "validation_passed": True,
                "feedback": "Tests now present",
                "evidence": [{"check": "test_file", "result": "passed"}]
            },
            headers={"X-Agent-ID": validator_id_2}
        )

        # 8. Verify completion
        task = self._get_task_from_db(task_id)
        assert task.status == "done"
        assert task.validation_iteration == 2
        logger.info(f"Task completed after {task.validation_iteration} iterations")

        logger.info("✅ Scenario 3 PASSED")

    @patch('src.interfaces.llm_interface.get_llm_provider')
    def test_parallel_agents_isolation(self, mock_get_llm):
        """Test Scenario 4: Multiple agents work in parallel without interference."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SCENARIO 4: Parallel Agents with Isolation")
        logger.info("=" * 80)

        mock_llm = MockLLMProvider()
        mock_get_llm.return_value = mock_llm

        task_ids = []
        agent_ids = []

        # 1. Create 3 tasks simultaneously
        for i in range(3):
            response = requests.post(
                f"{self.base_url}/create_task",
                json={
                    "task_description": f"Create file{i}.txt",
                    "done_definition": f"file{i}.txt exists",
                    "ai_agent_id": f"test-agent-{i}"
                },
                headers={"X-Agent-ID": f"test-agent-{i}"}
            )
            task_ids.append(response.json()["task_id"])
            logger.info(f"Created task {i}: {task_ids[i]}")

        # 2. Wait for all agents to spawn
        for task_id in task_ids:
            agent_id = self._wait_for_agent_spawn(task_id)
            agent_ids.append(agent_id)
            logger.info(f"Agent spawned: {agent_id}")

        # 3. Verify each has separate worktree
        worktrees = []
        for agent_id in agent_ids:
            worktree_path = self._verify_worktree_exists(agent_id)
            worktrees.append(worktree_path)

        # Verify no duplicate paths
        assert len(worktrees) == len(set(worktrees))
        logger.info("All agents have separate worktrees")

        # 4. Each agent creates different files
        for i, agent_id in enumerate(agent_ids):
            self._simulate_agent_work(agent_id, [f"file{i}.txt"])

        # 5. Complete tasks in different order
        for i in [1, 0, 2]:  # Complete out of order
            response = requests.post(
                f"{self.base_url}/update_task_status",
                json={
                    "task_id": task_ids[i],
                    "status": "done",
                    "summary": f"Created file{i}.txt",
                    "key_learnings": []
                },
                headers={"X-Agent-ID": agent_ids[i]}
            )
            assert response.status_code == 200
            logger.info(f"Task {i} completed")

        # 6. Verify all completed successfully
        for task_id in task_ids:
            task = self._get_task_from_db(task_id)
            assert task.status == "done"

        # 7. Verify no cross-contamination
        for i, agent_id in enumerate(agent_ids):
            worktree_path = Path(f"worktrees/wt_{agent_id}")
            assert (worktree_path / f"file{i}.txt").exists()
            # Check other files don't exist
            for j in range(3):
                if j != i:
                    assert not (worktree_path / f"file{j}.txt").exists()

        logger.info("No cross-contamination between worktrees")
        logger.info("✅ Scenario 4 PASSED")

    # ========== Helper Methods ==========

    def _wait_for_agent_spawn(self, task_id: str, timeout: int = 30) -> str:
        """Wait for agent to spawn for a task."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            task = self._get_task_from_db(task_id)
            if task and task.assigned_agent_id:
                return task.assigned_agent_id
            time.sleep(1)
        raise TimeoutError(f"Agent did not spawn for task {task_id}")

    def _wait_for_validator_agent(self, task_id: str, timeout: int = 30) -> str:
        """Wait for validator agent to spawn."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            session = self.db_manager.get_session()
            validators = session.query(Agent).filter_by(
                agent_type="validator",
                current_task_id=task_id
            ).all()
            session.close()
            if validators:
                return validators[0].id
            time.sleep(1)
        raise TimeoutError(f"Validator did not spawn for task {task_id}")

    def _verify_worktree_exists(self, agent_id: str) -> Path:
        """Verify worktree exists for agent."""
        worktree_path = Path(f"worktrees/wt_{agent_id}")
        assert worktree_path.exists(), f"Worktree not found at {worktree_path}"
        assert (worktree_path / ".git").exists(), "Not a valid git worktree"
        logger.info(f"Worktree exists: {worktree_path}")
        return worktree_path

    def _simulate_agent_work(self, agent_id: str, files: List[str], content: str = "test"):
        """Simulate agent creating files in worktree."""
        worktree_path = Path(f"worktrees/wt_{agent_id}")
        for filename in files:
            file_path = worktree_path / filename
            file_path.write_text(content)
            logger.info(f"Created {filename} in {worktree_path}")

        # Commit the changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=worktree_path,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Test commit"],
            cwd=worktree_path,
            capture_output=True
        )

    def _get_task_from_db(self, task_id: str) -> Optional[Task]:
        """Get task from database."""
        session = self.db_manager.get_session()
        task = session.query(Task).filter_by(id=task_id).first()
        session.close()
        return task

    def _get_agent_from_db(self, agent_id: str) -> Optional[Agent]:
        """Get agent from database."""
        session = self.db_manager.get_session()
        agent = session.query(Agent).filter_by(id=agent_id).first()
        session.close()
        return agent

    def _create_test_workflow_with_validation(self) -> str:
        """Create a test workflow with validation enabled."""
        session = self.db_manager.get_session()

        # Create workflow
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name="Test Workflow",
            phases_folder_path="tests/fixtures/test_workflows",
            status="active"
        )
        session.add(workflow)

        # Create phase with validation
        phase = Phase(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            order=1,
            name="Test Phase",
            description="Test phase with validation",
            done_definitions=["File exists"],
            validation={
                "enabled": True,
                "criteria": [
                    {
                        "description": "File exists",
                        "check_type": "file_exists",
                        "target": ["test.txt"]
                    }
                ]
            }
        )
        session.add(phase)
        session.commit()
        workflow_id = workflow.id
        session.close()

        return workflow_id

    def _enable_task_validation(self, task_id: str):
        """Enable validation on a task."""
        session = self.db_manager.get_session()
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            task.validation_enabled = True
            session.commit()
        session.close()

    def run_all_tests(self):
        """Run all test scenarios."""
        try:
            self.setup()

            # Run each test scenario
            self.test_basic_agent_task_completion()
            self.test_validation_single_pass()
            self.test_validation_with_feedback_loop()
            self.test_parallel_agents_isolation()

            logger.info("\n" + "=" * 80)
            logger.info("ALL INTEGRATION TESTS PASSED! ✅")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"\nTEST FAILED: {e}", exc_info=True)
            raise
        finally:
            self.teardown()


if __name__ == "__main__":
    # Check if running in CI or with pytest
    if len(sys.argv) > 1 and "pytest" in sys.argv[0]:
        # Let pytest handle the test discovery
        pass
    else:
        # Run directly
        test = HephaestusIntegrationTest()
        test.run_all_tests()