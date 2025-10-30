#!/usr/bin/env python3
"""Tests for the git worktree isolation system."""

import os
import sys
import tempfile
import shutil
import uuid
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
import git
from git import Repo

from src.core.database import DatabaseManager, Base, Agent
from src.core.worktree_manager import WorktreeManager


@pytest.fixture
def temp_repo():
    """Create a temporary git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)

    # Create initial commit
    test_file = Path(temp_dir) / "README.md"
    test_file.write_text("# Test Repository\n")
    repo.index.add([str(test_file)])
    repo.index.commit("Initial commit")

    yield repo

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_db():
    """Create a test database."""
    db_manager = DatabaseManager(":memory:")
    db_manager.create_tables()
    return db_manager


@pytest.fixture
def worktree_manager(test_db, temp_repo, monkeypatch):
    """Create a WorktreeManager with test configuration."""
    # Mock the config
    import src.core.simple_config
    config = src.core.simple_config.Config()
    config.worktree_base_path = Path(tempfile.mkdtemp())
    config.main_repo_path = Path(temp_repo.working_dir)
    config.worktree_branch_prefix = "test-agent-"
    config.conflict_resolution_strategy = "newest_file_wins"
    config.prefer_child_on_tie = True

    monkeypatch.setattr('src.core.simple_config.get_config', lambda: config)

    manager = WorktreeManager(test_db)

    yield manager

    # Cleanup worktrees
    shutil.rmtree(config.worktree_base_path, ignore_errors=True)


def test_create_agent_worktree(worktree_manager, test_db):
    """Test creating an isolated worktree for an agent."""
    agent_id = str(uuid.uuid4())

    # Create a test agent
    session = test_db.get_session()
    agent = Agent(
        id=agent_id,
        system_prompt="Test agent",
        status="working",
        cli_type="test"
    )
    session.add(agent)
    session.commit()
    session.close()

    # Create worktree
    result = worktree_manager.create_agent_worktree(agent_id)

    # Verify result
    assert "working_directory" in result
    assert "branch_name" in result
    assert "parent_commit" in result

    # Verify worktree exists
    worktree_path = Path(result["working_directory"])
    assert worktree_path.exists()
    assert worktree_path.is_dir()

    # Verify git worktree
    worktree_repo = Repo(worktree_path)
    assert worktree_repo.active_branch.name == result["branch_name"]

    # Cleanup
    worktree_manager.cleanup_worktree(agent_id)


def test_parent_child_inheritance(worktree_manager, test_db):
    """Test that child agents inherit parent's state."""
    parent_id = str(uuid.uuid4())
    child_id = str(uuid.uuid4())

    # Create parent agent
    session = test_db.get_session()
    parent_agent = Agent(id=parent_id, system_prompt="Parent", status="working", cli_type="test")
    session.add(parent_agent)
    session.commit()
    session.close()

    # Create parent worktree
    parent_result = worktree_manager.create_agent_worktree(parent_id)
    parent_path = Path(parent_result["working_directory"])

    # Parent creates a file
    parent_file = parent_path / "parent_work.txt"
    parent_file.write_text("Parent's work content")

    # Commit parent's work
    parent_repo = Repo(parent_path)
    parent_repo.index.add([str(parent_file)])
    parent_repo.index.commit("Parent work")

    # Create child agent
    session = test_db.get_session()
    child_agent = Agent(id=child_id, system_prompt="Child", status="working", cli_type="test")
    session.add(child_agent)
    session.commit()
    session.close()

    # Create child worktree with parent
    child_result = worktree_manager.create_agent_worktree(child_id, parent_agent_id=parent_id)
    child_path = Path(child_result["working_directory"])

    # Verify child has parent's file
    child_parent_file = child_path / "parent_work.txt"
    assert child_parent_file.exists()
    assert child_parent_file.read_text() == "Parent's work content"

    # Cleanup
    worktree_manager.cleanup_worktree(parent_id)
    worktree_manager.cleanup_worktree(child_id)


def test_parallel_isolation(worktree_manager, test_db):
    """Test that parallel agents work in isolation."""
    agent1_id = str(uuid.uuid4())
    agent2_id = str(uuid.uuid4())

    # Create two agents
    session = test_db.get_session()
    agent1 = Agent(id=agent1_id, system_prompt="Agent 1", status="working", cli_type="test")
    agent2 = Agent(id=agent2_id, system_prompt="Agent 2", status="working", cli_type="test")
    session.add(agent1)
    session.add(agent2)
    session.commit()
    session.close()

    # Create worktrees for both
    result1 = worktree_manager.create_agent_worktree(agent1_id)
    result2 = worktree_manager.create_agent_worktree(agent2_id)

    path1 = Path(result1["working_directory"])
    path2 = Path(result2["working_directory"])

    # Each agent creates a different file
    file1 = path1 / "agent1_file.txt"
    file1.write_text("Agent 1 content")

    file2 = path2 / "agent2_file.txt"
    file2.write_text("Agent 2 content")

    # Verify isolation - agent1's file not in agent2's worktree
    assert not (path2 / "agent1_file.txt").exists()
    assert not (path1 / "agent2_file.txt").exists()

    # Cleanup
    worktree_manager.cleanup_worktree(agent1_id)
    worktree_manager.cleanup_worktree(agent2_id)


def test_commit_for_validation(worktree_manager, test_db):
    """Test creating validation commits."""
    agent_id = str(uuid.uuid4())

    # Create agent
    session = test_db.get_session()
    agent = Agent(id=agent_id, system_prompt="Test", status="working", cli_type="test")
    session.add(agent)
    session.commit()
    session.close()

    # Create worktree
    result = worktree_manager.create_agent_worktree(agent_id)
    worktree_path = Path(result["working_directory"])

    # Create some work
    work_file = worktree_path / "work.py"
    work_file.write_text("def hello():\n    return 'world'")

    # Create validation commit
    commit_result = worktree_manager.commit_for_validation(agent_id, iteration=1)

    assert "commit_sha" in commit_result
    assert commit_result["files_changed"] == 1
    assert "Ready for validation" in commit_result["message"]

    # Verify commit exists
    worktree_repo = Repo(worktree_path)
    commit = worktree_repo.commit(commit_result["commit_sha"])
    assert commit.message == commit_result["message"]

    # Cleanup
    worktree_manager.cleanup_worktree(agent_id)


def test_cleanup_worktree(worktree_manager, test_db):
    """Test worktree cleanup."""
    agent_id = str(uuid.uuid4())

    # Create agent
    session = test_db.get_session()
    agent = Agent(id=agent_id, system_prompt="Test", status="working", cli_type="test")
    session.add(agent)
    session.commit()
    session.close()

    # Create worktree
    result = worktree_manager.create_agent_worktree(agent_id)
    worktree_path = Path(result["working_directory"])

    # Verify it exists
    assert worktree_path.exists()

    # Cleanup
    cleanup_result = worktree_manager.cleanup_worktree(agent_id)

    assert cleanup_result["status"] == "cleaned"
    assert cleanup_result["branch_preserved"] == True

    # Verify worktree is gone
    assert not worktree_path.exists()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])