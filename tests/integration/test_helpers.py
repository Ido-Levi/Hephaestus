"""
Helper utilities and assertions for integration tests.
"""

import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from src.core.database import Task, Agent, ValidationReview, AgentWorktree, Memory

logger = logging.getLogger(__name__)


class IntegrationAssertions:
    """Collection of assertion methods for integration tests."""

    def __init__(self, db_manager, base_url: str = "http://localhost:8000"):
        self.db_manager = db_manager
        self.base_url = base_url

    def assert_agent_spawned(self, task_id: str, timeout: int = 30) -> str:
        """Assert that an agent spawns for a task within timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            session = self.db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            session.close()

            if task and task.assigned_agent_id:
                agent_id = task.assigned_agent_id
                logger.info(f"Agent {agent_id} spawned for task {task_id}")
                return agent_id

            time.sleep(1)

        raise AssertionError(f"Agent did not spawn for task {task_id} within {timeout}s")

    def assert_worktree_exists(self, agent_id: str) -> Path:
        """Assert that worktree exists for an agent."""
        worktree_path = Path(f"worktrees/wt_{agent_id}")

        if not worktree_path.exists():
            raise AssertionError(f"Worktree does not exist at {worktree_path}")

        if not (worktree_path / ".git").exists():
            raise AssertionError(f"Worktree at {worktree_path} is not a valid git worktree")

        # Check it's registered in git
        result = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True,
            text=True
        )
        if str(worktree_path.absolute()) not in result.stdout:
            raise AssertionError(f"Worktree {worktree_path} not registered in git")

        logger.info(f"Worktree verified at {worktree_path}")
        return worktree_path

    def assert_task_state(self, task_id: str, expected_state: str, timeout: int = 10):
        """Assert task reaches expected state within timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            session = self.db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            session.close()

            if task and task.status == expected_state:
                logger.info(f"Task {task_id} is in state: {expected_state}")
                return

            time.sleep(1)

        # Final check with detailed error
        session = self.db_manager.get_session()
        task = session.query(Task).filter_by(id=task_id).first()
        actual_state = task.status if task else "NOT_FOUND"
        session.close()

        raise AssertionError(
            f"Task {task_id} did not reach state '{expected_state}' within {timeout}s. "
            f"Current state: '{actual_state}'"
        )

    def assert_validation_triggered(self, task_id: str, timeout: int = 15):
        """Assert that validation is triggered for a task."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            session = self.db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()

            if task and task.status in ["under_review", "validation_in_progress", "needs_work"]:
                # Check for validator agent
                validator = session.query(Agent).filter_by(
                    agent_type="validator",
                    current_task_id=task_id
                ).first()
                session.close()

                if validator:
                    logger.info(f"Validation triggered for task {task_id}, validator: {validator.id}")
                    return

            session.close()
            time.sleep(1)

        raise AssertionError(f"Validation was not triggered for task {task_id} within {timeout}s")

    def assert_tmux_session_alive(self, agent_id: str):
        """Assert that tmux session exists and is alive for an agent."""
        session_name = f"hep_agent_{agent_id[:8]}"

        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise AssertionError("No tmux sessions found")

        sessions = result.stdout.strip().split("\n")
        if session_name not in sessions:
            # Try alternative naming
            alt_session = f"agent_{agent_id}"
            if alt_session not in sessions:
                raise AssertionError(
                    f"Tmux session not found for agent {agent_id}. "
                    f"Available sessions: {sessions}"
                )

        logger.info(f"Tmux session alive for agent {agent_id}")

    def assert_git_branch_exists(self, agent_id: str):
        """Assert that git branch exists for an agent."""
        branch_name = f"agent-{agent_id}"

        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True
        )

        if branch_name not in result.stdout:
            raise AssertionError(
                f"Git branch '{branch_name}' not found. "
                f"Available branches:\n{result.stdout}"
            )

        logger.info(f"Git branch exists: {branch_name}")

    def assert_memory_stored(self, memory_content: str, timeout: int = 10):
        """Assert that a memory is stored in the database."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            session = self.db_manager.get_session()
            memory = session.query(Memory).filter(
                Memory.content.contains(memory_content)
            ).first()
            session.close()

            if memory:
                logger.info(f"Memory found with content: {memory_content[:50]}...")
                return memory.id

            time.sleep(1)

        raise AssertionError(f"Memory with content '{memory_content}' not found within {timeout}s")

    def assert_no_zombie_processes(self):
        """Assert that there are no zombie Hephaestus processes."""
        # Check for zombie tmux sessions
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}:#{session_attached}"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.startswith(("hep_agent_", "agent_")):
                    session_name, attached = line.split(":")
                    # Session exists but might be orphaned
                    # Check if corresponding agent exists
                    agent_id = session_name.replace("hep_agent_", "").replace("agent_", "")
                    session = self.db_manager.get_session()
                    agent = session.query(Agent).filter_by(id=agent_id).first()
                    session.close()

                    if not agent or agent.status in ["terminated", "failed", "completed"]:
                        raise AssertionError(f"Zombie tmux session found: {session_name}")

        logger.info("No zombie processes detected")

    def assert_database_consistent(self):
        """Assert that database is in a consistent state."""
        session = self.db_manager.get_session()

        try:
            # Check for orphaned agents
            orphaned = session.query(Agent).filter(
                Agent.current_task_id.isnot(None)
            ).all()

            for agent in orphaned:
                task = session.query(Task).filter_by(id=agent.current_task_id).first()
                if not task:
                    raise AssertionError(f"Agent {agent.id} references non-existent task {agent.current_task_id}")

            # Check for tasks without valid states
            invalid_tasks = session.query(Task).filter(
                ~Task.status.in_([
                    "pending", "assigned", "in_progress",
                    "under_review", "validation_in_progress", "needs_work",
                    "done", "failed"
                ])
            ).all()

            if invalid_tasks:
                raise AssertionError(f"Tasks with invalid states: {[t.id for t in invalid_tasks]}")

            # Check validation reviews reference valid tasks
            reviews = session.query(ValidationReview).all()
            for review in reviews:
                task = session.query(Task).filter_by(id=review.task_id).first()
                if not task:
                    raise AssertionError(f"ValidationReview {review.id} references non-existent task")

            logger.info("Database consistency check passed")

        finally:
            session.close()

    def assert_validation_iteration(self, task_id: str, expected_iteration: int):
        """Assert task has expected validation iteration count."""
        session = self.db_manager.get_session()
        task = session.query(Task).filter_by(id=task_id).first()
        session.close()

        if not task:
            raise AssertionError(f"Task {task_id} not found")

        if task.validation_iteration != expected_iteration:
            raise AssertionError(
                f"Task {task_id} validation iteration is {task.validation_iteration}, "
                f"expected {expected_iteration}"
            )

        logger.info(f"Task {task_id} is at iteration {expected_iteration}")

    def assert_worktree_merged(self, agent_id: str, timeout: int = 10):
        """Assert that agent's worktree has been merged."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            session = self.db_manager.get_session()
            worktree = session.query(AgentWorktree).filter_by(agent_id=agent_id).first()
            session.close()

            if worktree and worktree.merge_status == "merged":
                logger.info(f"Worktree for agent {agent_id} has been merged")
                return

            time.sleep(1)

        raise AssertionError(f"Worktree for agent {agent_id} was not merged within {timeout}s")

    def assert_files_in_worktree(self, agent_id: str, expected_files: List[str]):
        """Assert that specific files exist in agent's worktree."""
        worktree_path = Path(f"worktrees/wt_{agent_id}")

        for filename in expected_files:
            file_path = worktree_path / filename
            if not file_path.exists():
                raise AssertionError(
                    f"Expected file '{filename}' not found in worktree {worktree_path}. "
                    f"Existing files: {list(worktree_path.iterdir())}"
                )

        logger.info(f"All expected files found in worktree for agent {agent_id}")

    def assert_commit_exists(self, agent_id: str, commit_type: str = None):
        """Assert that a commit exists for the agent."""
        branch_name = f"agent-{agent_id}"

        # Get commits from branch
        result = subprocess.run(
            ["git", "log", branch_name, "--oneline", "-n", "10"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise AssertionError(f"Could not get commits from branch {branch_name}")

        commits = result.stdout.strip()
        if not commits:
            raise AssertionError(f"No commits found on branch {branch_name}")

        if commit_type:
            if commit_type not in commits:
                raise AssertionError(
                    f"No commit with type '{commit_type}' found. Commits:\n{commits}"
                )

        logger.info(f"Commits verified for agent {agent_id}")


class SystemStateVerifier:
    """Verify overall system state."""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state for debugging."""
        session = self.db_manager.get_session()

        state = {
            "timestamp": datetime.utcnow().isoformat(),
            "tasks": [],
            "agents": [],
            "worktrees": [],
            "tmux_sessions": [],
            "git_branches": []
        }

        # Get all tasks
        tasks = session.query(Task).all()
        for task in tasks:
            state["tasks"].append({
                "id": task.id,
                "status": task.status,
                "assigned_agent": task.assigned_agent_id,
                "validation_enabled": task.validation_enabled,
                "validation_iteration": task.validation_iteration
            })

        # Get all agents
        agents = session.query(Agent).all()
        for agent in agents:
            state["agents"].append({
                "id": agent.id,
                "type": agent.agent_type,
                "status": agent.status,
                "current_task": agent.current_task_id,
                "tmux_session": agent.tmux_session_name
            })

        # Get worktrees
        worktrees = session.query(AgentWorktree).all()
        for worktree in worktrees:
            state["worktrees"].append({
                "agent_id": worktree.agent_id,
                "path": worktree.worktree_path,
                "branch": worktree.branch_name,
                "merge_status": worktree.merge_status
            })

        session.close()

        # Get tmux sessions
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            state["tmux_sessions"] = result.stdout.strip().split("\n")

        # Get git branches
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            state["git_branches"] = [
                line.strip() for line in result.stdout.split("\n")
                if "agent-" in line
            ]

        return state

    def dump_state_on_failure(self, test_name: str):
        """Dump system state to file for debugging failed tests."""
        state = self.get_system_state()
        state["failed_test"] = test_name

        dump_file = Path(f"tests/integration/logs/failure_{test_name}_{int(time.time())}.json")
        dump_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(dump_file, "w") as f:
            json.dump(state, f, indent=2)

        logger.error(f"System state dumped to {dump_file}")

        # Also log to console
        logger.error("Current system state:")
        logger.error(f"  Tasks: {len(state['tasks'])}")
        logger.error(f"  Agents: {len(state['agents'])}")
        logger.error(f"  Worktrees: {len(state['worktrees'])}")
        logger.error(f"  Tmux sessions: {len(state['tmux_sessions'])}")


class PerformanceMetrics:
    """Track performance metrics during tests."""

    def __init__(self):
        self.metrics = {}
        self.start_times = {}

    def start_timer(self, metric_name: str):
        """Start timing a metric."""
        self.start_times[metric_name] = time.time()

    def end_timer(self, metric_name: str) -> float:
        """End timing and record metric."""
        if metric_name not in self.start_times:
            raise ValueError(f"Timer {metric_name} was not started")

        duration = time.time() - self.start_times[metric_name]
        self.metrics[metric_name] = duration
        del self.start_times[metric_name]

        logger.info(f"Performance metric - {metric_name}: {duration:.2f}s")
        return duration

    def assert_metric_within(self, metric_name: str, max_seconds: float):
        """Assert that a metric is within expected bounds."""
        if metric_name not in self.metrics:
            raise AssertionError(f"Metric {metric_name} not recorded")

        actual = self.metrics[metric_name]
        if actual > max_seconds:
            raise AssertionError(
                f"Performance metric {metric_name} took {actual:.2f}s, "
                f"expected under {max_seconds}s"
            )

    def get_summary(self) -> str:
        """Get summary of all metrics."""
        lines = ["Performance Metrics Summary:"]
        for name, duration in self.metrics.items():
            lines.append(f"  {name}: {duration:.2f}s")
        return "\n".join(lines)