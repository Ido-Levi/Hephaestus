"""Unit tests for QueueService."""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base, DatabaseManager, Task, Agent
from src.services.queue_service import QueueService


@pytest.fixture
def db_manager():
    """Create a test database manager with in-memory SQLite."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    class TestDatabaseManager:
        def __init__(self):
            self.engine = engine
            self.Session = Session

        def get_session(self):
            return self.Session()

        def create_tables(self):
            Base.metadata.create_all(self.engine)

    return TestDatabaseManager()


@pytest.fixture
def queue_service(db_manager):
    """Create a QueueService instance with max 3 concurrent agents."""
    return QueueService(db_manager, max_concurrent_agents=3)


def create_test_task(db_manager, task_id=None, priority="medium", status="pending"):
    """Helper to create a test task."""
    session = db_manager.get_session()
    try:
        task = Task(
            id=task_id or str(uuid.uuid4()),
            raw_description="Test task",
            enriched_description="Test task description",
            done_definition="Complete the task",
            status=status,
            priority=priority,
        )
        session.add(task)
        session.commit()
        task_id = task.id
    finally:
        session.close()
    return task_id


def create_test_agent(db_manager, agent_id=None, status="working"):
    """Helper to create a test agent."""
    session = db_manager.get_session()
    try:
        agent = Agent(
            id=agent_id or str(uuid.uuid4()),
            system_prompt="Test prompt",
            status=status,
            cli_type="claude",
        )
        session.add(agent)
        session.commit()
        agent_id = agent.id
    finally:
        session.close()
    return agent_id


class TestGetActiveAgentCount:
    """Tests for get_active_agent_count method."""

    def test_no_agents(self, queue_service):
        """Should return 0 when no agents exist."""
        count = queue_service.get_active_agent_count()
        assert count == 0

    def test_only_active_agents(self, queue_service, db_manager):
        """Should count only non-terminated agents."""
        create_test_agent(db_manager, status="working")
        create_test_agent(db_manager, status="idle")
        create_test_agent(db_manager, status="stuck")
        create_test_agent(db_manager, status="terminated")
        create_test_agent(db_manager, status="terminated")

        count = queue_service.get_active_agent_count()
        assert count == 3  # Only non-terminated agents

    def test_all_terminated(self, queue_service, db_manager):
        """Should return 0 when all agents are terminated."""
        create_test_agent(db_manager, status="terminated")
        create_test_agent(db_manager, status="terminated")

        count = queue_service.get_active_agent_count()
        assert count == 0


class TestShouldQueueTask:
    """Tests for should_queue_task method."""

    def test_below_limit(self, queue_service, db_manager):
        """Should return False when below concurrent limit."""
        create_test_agent(db_manager, status="working")
        create_test_agent(db_manager, status="working")

        # 2 agents < 3 max
        assert queue_service.should_queue_task() is False

    def test_at_limit(self, queue_service, db_manager):
        """Should return True when at concurrent limit."""
        create_test_agent(db_manager, status="working")
        create_test_agent(db_manager, status="working")
        create_test_agent(db_manager, status="idle")

        # 3 agents == 3 max
        assert queue_service.should_queue_task() is True

    def test_above_limit(self, queue_service, db_manager):
        """Should return True when above concurrent limit."""
        for _ in range(5):
            create_test_agent(db_manager, status="working")

        # 5 agents > 3 max
        assert queue_service.should_queue_task() is True

    def test_terminated_agents_not_counted(self, queue_service, db_manager):
        """Terminated agents should not count toward limit."""
        create_test_agent(db_manager, status="working")
        create_test_agent(db_manager, status="working")
        create_test_agent(db_manager, status="terminated")
        create_test_agent(db_manager, status="terminated")

        # 2 active agents < 3 max
        assert queue_service.should_queue_task() is False


class TestEnqueueTask:
    """Tests for enqueue_task method."""

    def test_enqueue_task_basic(self, queue_service, db_manager):
        """Should mark task as queued and set timestamp."""
        task_id = create_test_task(db_manager, status="pending")

        queue_service.enqueue_task(task_id)

        session = db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            assert task.status == "queued"
            assert task.queued_at is not None
            assert task.queue_position == 1
        finally:
            session.close()

    def test_enqueue_multiple_tasks(self, queue_service, db_manager):
        """Should set correct queue positions for multiple tasks."""
        # Create tasks with different priorities
        task1_id = create_test_task(db_manager, priority="low", status="pending")
        task2_id = create_test_task(db_manager, priority="high", status="pending")
        task3_id = create_test_task(db_manager, priority="medium", status="pending")

        queue_service.enqueue_task(task1_id)
        queue_service.enqueue_task(task2_id)
        queue_service.enqueue_task(task3_id)

        session = db_manager.get_session()
        try:
            task1 = session.query(Task).filter_by(id=task1_id).first()
            task2 = session.query(Task).filter_by(id=task2_id).first()
            task3 = session.query(Task).filter_by(id=task3_id).first()

            # High priority should be position 1
            assert task2.queue_position == 1
            # Medium priority should be position 2
            assert task3.queue_position == 2
            # Low priority should be position 3
            assert task1.queue_position == 3
        finally:
            session.close()

    def test_enqueue_nonexistent_task(self, queue_service):
        """Should handle enqueueing nonexistent task gracefully."""
        # Should not raise exception
        queue_service.enqueue_task("nonexistent-task-id")


class TestGetNextQueuedTask:
    """Tests for get_next_queued_task method."""

    def test_empty_queue(self, queue_service):
        """Should return None when queue is empty."""
        task = queue_service.get_next_queued_task()
        assert task is None

    def test_priority_ordering(self, queue_service, db_manager):
        """Should return highest priority task."""
        # Create tasks in different order
        low_id = create_test_task(db_manager, priority="low", status="queued")
        medium_id = create_test_task(db_manager, priority="medium", status="queued")
        high_id = create_test_task(db_manager, priority="high", status="queued")

        task = queue_service.get_next_queued_task()
        assert task.id == high_id

    def test_fifo_within_same_priority(self, queue_service, db_manager):
        """Should return earliest queued task when priorities are equal."""
        session = db_manager.get_session()
        try:
            # Create tasks with same priority but different queued times
            task1 = Task(
                id=str(uuid.uuid4()),
                raw_description="Task 1",
                done_definition="Done",
                status="queued",
                priority="medium",
                queued_at=datetime.utcnow() - timedelta(minutes=5),
            )
            task2 = Task(
                id=str(uuid.uuid4()),
                raw_description="Task 2",
                done_definition="Done",
                status="queued",
                priority="medium",
                queued_at=datetime.utcnow() - timedelta(minutes=2),
            )
            session.add(task1)
            session.add(task2)
            session.commit()
            task1_id = task1.id
        finally:
            session.close()

        next_task = queue_service.get_next_queued_task()
        # Should get task1 (queued earlier)
        assert next_task.id == task1_id

    def test_boosted_priority_first(self, queue_service, db_manager):
        """Boosted tasks should be returned before high priority tasks."""
        session = db_manager.get_session()
        try:
            # Create high priority task
            high_task = Task(
                id=str(uuid.uuid4()),
                raw_description="High priority",
                done_definition="Done",
                status="queued",
                priority="high",
                queued_at=datetime.utcnow() - timedelta(minutes=10),
            )
            # Create boosted medium priority task
            boosted_task = Task(
                id=str(uuid.uuid4()),
                raw_description="Boosted medium",
                done_definition="Done",
                status="queued",
                priority="medium",
                priority_boosted=True,
                queued_at=datetime.utcnow(),
            )
            session.add(high_task)
            session.add(boosted_task)
            session.commit()
            boosted_id = boosted_task.id
        finally:
            session.close()

        next_task = queue_service.get_next_queued_task()
        # Should get boosted task even though high priority task exists
        assert next_task.id == boosted_id


class TestDequeueTask:
    """Tests for dequeue_task method."""

    def test_dequeue_task_basic(self, queue_service, db_manager):
        """Should mark task as assigned and clear queue position."""
        task_id = create_test_task(db_manager, status="queued")
        session = db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            task.queued_at = datetime.utcnow()
            task.queue_position = 1
            session.commit()
        finally:
            session.close()

        queue_service.dequeue_task(task_id)

        session = db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            assert task.status == "assigned"
            assert task.queue_position is None
        finally:
            session.close()

    def test_dequeue_nonexistent_task(self, queue_service):
        """Should handle dequeueing nonexistent task gracefully."""
        # Should not raise exception
        queue_service.dequeue_task("nonexistent-task-id")

    def test_dequeue_non_queued_task(self, queue_service, db_manager):
        """Should handle dequeueing task that's not queued."""
        task_id = create_test_task(db_manager, status="pending")

        # Should not raise exception
        queue_service.dequeue_task(task_id)

        # Task status should remain unchanged
        session = db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            assert task.status == "pending"
        finally:
            session.close()


class TestGetQueueStatus:
    """Tests for get_queue_status method."""

    def test_empty_queue(self, queue_service):
        """Should return correct status for empty queue."""
        status = queue_service.get_queue_status()

        assert status["active_agents"] == 0
        assert status["max_concurrent_agents"] == 3
        assert status["queued_tasks_count"] == 0
        assert status["queued_tasks"] == []
        assert status["slots_available"] == 3
        assert status["at_capacity"] is False

    def test_with_agents_and_tasks(self, queue_service, db_manager):
        """Should return correct status with agents and queued tasks."""
        # Create 2 active agents
        create_test_agent(db_manager, status="working")
        create_test_agent(db_manager, status="idle")

        # Create 2 queued tasks
        task1_id = create_test_task(db_manager, priority="high", status="queued")
        task2_id = create_test_task(db_manager, priority="low", status="queued")

        # Set queue positions
        session = db_manager.get_session()
        try:
            task1 = session.query(Task).filter_by(id=task1_id).first()
            task1.queued_at = datetime.utcnow()
            task1.queue_position = 1
            task2 = session.query(Task).filter_by(id=task2_id).first()
            task2.queued_at = datetime.utcnow()
            task2.queue_position = 2
            session.commit()
        finally:
            session.close()

        status = queue_service.get_queue_status()

        assert status["active_agents"] == 2
        assert status["queued_tasks_count"] == 2
        assert status["slots_available"] == 1
        assert status["at_capacity"] is False
        assert len(status["queued_tasks"]) == 2

    def test_at_capacity(self, queue_service, db_manager):
        """Should indicate when at capacity."""
        # Create 3 active agents (at max)
        for _ in range(3):
            create_test_agent(db_manager, status="working")

        status = queue_service.get_queue_status()

        assert status["active_agents"] == 3
        assert status["slots_available"] == 0
        assert status["at_capacity"] is True


class TestBoostTaskPriority:
    """Tests for boost_task_priority method."""

    def test_boost_queued_task(self, queue_service, db_manager):
        """Should boost a queued task's priority."""
        task_id = create_test_task(db_manager, priority="low", status="queued")
        session = db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            task.queued_at = datetime.utcnow()
            task.queue_position = 5
            session.commit()
        finally:
            session.close()

        result = queue_service.boost_task_priority(task_id)

        assert result is True

        session = db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            assert task.priority_boosted is True
            assert task.queue_position == 1
        finally:
            session.close()

    def test_boost_non_queued_task(self, queue_service, db_manager):
        """Should fail to boost a non-queued task."""
        task_id = create_test_task(db_manager, status="pending")

        result = queue_service.boost_task_priority(task_id)

        assert result is False

    def test_boost_nonexistent_task(self, queue_service):
        """Should fail to boost nonexistent task."""
        result = queue_service.boost_task_priority("nonexistent-task-id")

        assert result is False

    def test_boost_moves_to_front(self, queue_service, db_manager):
        """Boosted task should be returned first by get_next_queued_task."""
        # Create multiple queued tasks
        high_id = create_test_task(db_manager, priority="high", status="queued")
        low_id = create_test_task(db_manager, priority="low", status="queued")

        # Boost the low priority task
        queue_service.boost_task_priority(low_id)

        # Should get the boosted low priority task first
        next_task = queue_service.get_next_queued_task()
        assert next_task.id == low_id


class TestGetQueuedTasks:
    """Tests for get_queued_tasks method."""

    def test_empty_queue(self, queue_service):
        """Should return empty list when no queued tasks."""
        tasks = queue_service.get_queued_tasks()
        assert tasks == []

    def test_ordered_by_priority(self, queue_service, db_manager):
        """Should return tasks ordered by priority."""
        # Create tasks in random order
        low_id = create_test_task(db_manager, priority="low", status="queued")
        high_id = create_test_task(db_manager, priority="high", status="queued")
        medium_id = create_test_task(db_manager, priority="medium", status="queued")

        tasks = queue_service.get_queued_tasks()

        assert len(tasks) == 3
        assert tasks[0].id == high_id
        assert tasks[1].id == medium_id
        assert tasks[2].id == low_id

    def test_boosted_tasks_first(self, queue_service, db_manager):
        """Boosted tasks should appear first."""
        high_id = create_test_task(db_manager, priority="high", status="queued")
        low_id = create_test_task(db_manager, priority="low", status="queued")

        # Boost the low priority task
        queue_service.boost_task_priority(low_id)

        tasks = queue_service.get_queued_tasks()

        assert len(tasks) == 2
        # Boosted task should be first
        assert tasks[0].id == low_id
        assert tasks[0].priority_boosted is True
        # Regular high priority task should be second
        assert tasks[1].id == high_id
