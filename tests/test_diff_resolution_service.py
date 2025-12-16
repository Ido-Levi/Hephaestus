"""Unit tests for the DiffResolutionService.

Tests cover:
- Queueing diffs for resolution
- Retrieving pending diffs
- AI-driven diff resolution in batches
- Resolution content retrieval
- Status tracking
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import uuid

from src.services.diff_resolution_service import (
    DiffResolutionService,
    get_diff_resolution_service,
)
from src.core.database import PendingDiffResolution


@pytest.fixture
def diff_resolution_service(db_manager):
    """Create DiffResolutionService with test database."""
    service = DiffResolutionService(db_manager)
    return service


@pytest.fixture
def sample_parent_content():
    """Sample parent (main branch) file content."""
    return """def calculate_sum(a, b):
    '''Calculate the sum of two numbers.'''
    return a + b


def calculate_product(a, b):
    '''Calculate the product of two numbers.'''
    return a * b
"""


@pytest.fixture
def sample_child_content():
    """Sample child (agent's work) file content."""
    return """def calculate_sum(a, b):
    '''Calculate the sum of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    '''
    return a + b


def calculate_product(a, b):
    '''Calculate the product of two numbers.'''
    result = a * b
    return result


def calculate_difference(a, b):
    '''Calculate the difference of two numbers.'''
    return a - b
"""


@pytest.fixture
def sample_diff_context():
    """Sample unified diff context."""
    return """@@ -1,7 +1,20 @@
 def calculate_sum(a, b):
-    '''Calculate the sum of two numbers.'''
+    '''Calculate the sum of two numbers.
+    
+    Args:
+        a: First number
+        b: Second number
+        
+    Returns:
+        Sum of a and b
+    '''
     return a + b
 
 
 def calculate_product(a, b):
     '''Calculate the product of two numbers.'''
-    return a * b
+    result = a * b
+    return result
+
+
+def calculate_difference(a, b):
+    '''Calculate the difference of two numbers.'''
+    return a - b
"""


class TestQueueDiffForResolution:
    """Test diff queueing functionality."""

    def test_queue_diff_basic(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test basic diff queueing."""
        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-agent-1",
            worktree_agent_id="worktree-agent-1",
            file_path="src/utils/math.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
        )

        assert diff_id is not None
        assert isinstance(diff_id, str)
        # UUID format check
        uuid.UUID(diff_id)

    def test_queue_diff_with_timestamps(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test diff queueing with timestamps."""
        parent_time = datetime.utcnow() - timedelta(hours=2)
        child_time = datetime.utcnow() - timedelta(minutes=30)

        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-agent-1",
            worktree_agent_id="worktree-agent-1",
            file_path="src/utils/math.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
            parent_timestamp=parent_time,
            child_timestamp=child_time,
        )

        # Verify the diff was stored with timestamps
        status = diff_resolution_service.get_diff_status(diff_id)
        assert status is not None
        assert status["status"] == "pending"

    def test_queue_diff_with_context(
        self,
        diff_resolution_service,
        sample_parent_content,
        sample_child_content,
        sample_diff_context,
    ):
        """Test diff queueing with diff context."""
        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-agent-1",
            worktree_agent_id="worktree-agent-1",
            file_path="src/utils/math.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
            diff_context=sample_diff_context,
        )

        assert diff_id is not None
        status = diff_resolution_service.get_diff_status(diff_id)
        assert status["status"] == "pending"

    def test_queue_multiple_diffs(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test queueing multiple diffs."""
        files = [
            "src/utils/math.py",
            "src/core/database.py",
            "src/services/auth.py",
        ]

        diff_ids = []
        for file_path in files:
            diff_id = diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-agent-1",
                worktree_agent_id="worktree-agent-1",
                file_path=file_path,
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )
            diff_ids.append(diff_id)

        assert len(diff_ids) == 3
        assert len(set(diff_ids)) == 3  # All unique IDs

        # Verify count
        count = diff_resolution_service.get_pending_diff_count()
        assert count == 3


class TestGetPendingDiffs:
    """Test pending diff retrieval functionality."""

    def test_get_pending_diffs_empty(self, diff_resolution_service):
        """Test getting pending diffs when none exist."""
        diffs = diff_resolution_service.get_pending_diffs()
        assert diffs == []

    def test_get_pending_diffs_with_limit(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test getting pending diffs with a limit."""
        # Queue 5 diffs
        for i in range(5):
            diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-agent-1",
                worktree_agent_id="worktree-agent-1",
                file_path=f"src/file_{i}.py",
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )

        # Get only 3
        diffs = diff_resolution_service.get_pending_diffs(limit=3)
        assert len(diffs) == 3

    def test_get_pending_diff_count(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test getting pending diff count."""
        assert diff_resolution_service.get_pending_diff_count() == 0

        for i in range(4):
            diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-agent-1",
                worktree_agent_id="worktree-agent-1",
                file_path=f"src/file_{i}.py",
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )

        assert diff_resolution_service.get_pending_diff_count() == 4


class TestResolveDiffBatch:
    """Test batch diff resolution functionality."""

    @pytest.mark.asyncio
    async def test_resolve_batch_no_pending(self, diff_resolution_service):
        """Test resolving batch when no diffs are pending."""
        results = await diff_resolution_service.resolve_diff_batch(
            resolver_agent_id="resolver-1"
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_resolve_batch_with_mocked_llm(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test resolving a batch of diffs with mocked LLM."""
        # Queue diffs
        for i in range(3):
            diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-agent-1",
                worktree_agent_id="worktree-agent-1",
                file_path=f"src/file_{i}.py",
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )

        # Mock the LLM call
        with patch.object(
            diff_resolution_service,
            "_call_llm_for_resolution",
            new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = {
                "choice": "child",
                "reasoning": "Agent's version has better documentation",
                "content": None,
            }

            results = await diff_resolution_service.resolve_diff_batch(
                resolver_agent_id="resolver-1",
                batch_size=3
            )

        assert len(results) == 3
        for result in results:
            assert result["status"] == "resolved"
            assert result["resolution_choice"] == "child"
            assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_resolve_batch_respects_batch_size(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test that batch resolution respects batch size."""
        # Queue 5 diffs
        for i in range(5):
            diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-agent-1",
                worktree_agent_id="worktree-agent-1",
                file_path=f"src/file_{i}.py",
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )

        with patch.object(
            diff_resolution_service,
            "_call_llm_for_resolution",
            new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = {
                "choice": "parent",
                "reasoning": "Parent version is stable",
                "content": None,
            }

            # Only resolve 2
            results = await diff_resolution_service.resolve_diff_batch(
                resolver_agent_id="resolver-1",
                batch_size=2
            )

        assert len(results) == 2
        # 3 should still be pending
        assert diff_resolution_service.get_pending_diff_count() == 3

    @pytest.mark.asyncio
    async def test_resolve_batch_merged_content(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test resolving with merged content choice."""
        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-agent-1",
            worktree_agent_id="worktree-agent-1",
            file_path="src/utils/math.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
        )

        merged_content = """def calculate_sum(a, b):
    '''Calculate the sum of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    '''
    return a + b


def calculate_product(a, b):
    '''Calculate the product of two numbers.'''
    return a * b


def calculate_difference(a, b):
    '''Calculate the difference of two numbers.'''
    return a - b
"""

        with patch.object(
            diff_resolution_service,
            "_call_llm_for_resolution",
            new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.return_value = {
                "choice": "merged",
                "reasoning": "Combined documentation from parent with new function from child",
                "content": merged_content,
            }

            results = await diff_resolution_service.resolve_diff_batch(
                resolver_agent_id="resolver-1"
            )

        assert len(results) == 1
        assert results[0]["resolution_choice"] == "merged"

        # Verify resolved content
        resolved = diff_resolution_service.get_resolved_content(diff_id)
        assert resolved is not None
        choice, content = resolved
        assert choice == "merged"
        assert content == merged_content

    @pytest.mark.asyncio
    async def test_resolve_batch_handles_llm_error(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test that batch resolution handles LLM errors gracefully."""
        diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-agent-1",
            worktree_agent_id="worktree-agent-1",
            file_path="src/file.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
        )

        with patch.object(
            diff_resolution_service,
            "_call_llm_for_resolution",
            new_callable=AsyncMock
        ) as mock_llm:
            mock_llm.side_effect = Exception("LLM API error")

            results = await diff_resolution_service.resolve_diff_batch(
                resolver_agent_id="resolver-1"
            )

        assert len(results) == 1
        assert results[0]["status"] == "failed"
        assert "error" in results[0]


class TestBuildResolutionPrompt:
    """Test prompt building functionality."""

    def test_build_prompt_includes_file_path(
        self, diff_resolution_service, db_manager
    ):
        """Test that the prompt includes file path."""
        session = db_manager.get_session()
        try:
            diff = PendingDiffResolution(
                id=str(uuid.uuid4()),
                merge_agent_id="merge-1",
                worktree_agent_id="worktree-1",
                file_path="src/core/important.py",
                parent_content="parent code",
                child_content="child code",
                status="pending",
            )
            session.add(diff)
            session.flush()

            prompt = diff_resolution_service._build_resolution_prompt(diff)

            assert "src/core/important.py" in prompt
            assert "parent code" in prompt
            assert "child code" in prompt
        finally:
            session.close()

    def test_build_prompt_includes_timestamps(
        self, diff_resolution_service, db_manager
    ):
        """Test that the prompt includes timestamps when provided."""
        session = db_manager.get_session()
        try:
            parent_time = datetime(2025, 12, 1, 10, 0, 0)
            child_time = datetime(2025, 12, 15, 14, 30, 0)

            diff = PendingDiffResolution(
                id=str(uuid.uuid4()),
                merge_agent_id="merge-1",
                worktree_agent_id="worktree-1",
                file_path="src/file.py",
                parent_content="parent",
                child_content="child",
                parent_timestamp=parent_time,
                child_timestamp=child_time,
                status="pending",
            )
            session.add(diff)
            session.flush()

            prompt = diff_resolution_service._build_resolution_prompt(diff)

            assert "2025-12-01" in prompt
            assert "2025-12-15" in prompt
        finally:
            session.close()

    def test_build_prompt_includes_diff_context(
        self, diff_resolution_service, db_manager, sample_diff_context
    ):
        """Test that the prompt includes diff context when provided."""
        session = db_manager.get_session()
        try:
            diff = PendingDiffResolution(
                id=str(uuid.uuid4()),
                merge_agent_id="merge-1",
                worktree_agent_id="worktree-1",
                file_path="src/file.py",
                parent_content="parent",
                child_content="child",
                diff_context=sample_diff_context,
                status="pending",
            )
            session.add(diff)
            session.flush()

            prompt = diff_resolution_service._build_resolution_prompt(diff)

            assert "```diff" in prompt
            assert "@@ -1,7 +1,20 @@" in prompt
        finally:
            session.close()


class TestGetResolvedContent:
    """Test resolved content retrieval."""

    def test_get_resolved_content_not_found(self, diff_resolution_service):
        """Test getting content for non-existent diff."""
        result = diff_resolution_service.get_resolved_content("nonexistent-id")
        assert result is None

    def test_get_resolved_content_pending(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test getting content for pending diff returns None."""
        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-1",
            worktree_agent_id="worktree-1",
            file_path="src/file.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
        )

        result = diff_resolution_service.get_resolved_content(diff_id)
        assert result is None  # Not resolved yet

    def test_get_resolved_content_parent_choice(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test getting content when parent was chosen."""
        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-1",
            worktree_agent_id="worktree-1",
            file_path="src/file.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
        )

        # Manually resolve the diff
        session = diff_resolution_service.db_manager.get_session()
        try:
            diff = session.query(PendingDiffResolution).filter(
                PendingDiffResolution.id == diff_id
            ).first()
            diff.status = "resolved"
            diff.resolution_choice = "parent"
            session.commit()
        finally:
            session.close()

        result = diff_resolution_service.get_resolved_content(diff_id)
        assert result is not None
        choice, content = result
        assert choice == "parent"
        assert content == sample_parent_content

    def test_get_resolved_content_child_choice(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test getting content when child was chosen."""
        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-1",
            worktree_agent_id="worktree-1",
            file_path="src/file.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
        )

        # Manually resolve the diff
        session = diff_resolution_service.db_manager.get_session()
        try:
            diff = session.query(PendingDiffResolution).filter(
                PendingDiffResolution.id == diff_id
            ).first()
            diff.status = "resolved"
            diff.resolution_choice = "child"
            session.commit()
        finally:
            session.close()

        result = diff_resolution_service.get_resolved_content(diff_id)
        assert result is not None
        choice, content = result
        assert choice == "child"
        assert content == sample_child_content


class TestGetDiffStatus:
    """Test diff status retrieval."""

    def test_get_status_not_found(self, diff_resolution_service):
        """Test getting status for non-existent diff."""
        result = diff_resolution_service.get_diff_status("nonexistent-id")
        assert result is None

    def test_get_status_pending(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test getting status for pending diff."""
        diff_id = diff_resolution_service.queue_diff_for_resolution(
            merge_agent_id="merge-1",
            worktree_agent_id="worktree-1",
            file_path="src/file.py",
            parent_content=sample_parent_content,
            child_content=sample_child_content,
        )

        status = diff_resolution_service.get_diff_status(diff_id)
        assert status is not None
        assert status["id"] == diff_id
        assert status["file_path"] == "src/file.py"
        assert status["status"] == "pending"
        assert status["resolution_choice"] is None
        assert status["created_at"] is not None


class TestGetAllDiffs:
    """Test getting all diffs with filters."""

    def test_get_all_diffs_empty(self, diff_resolution_service):
        """Test getting all diffs when none exist."""
        result = diff_resolution_service.get_all_diffs()
        assert result == []

    def test_get_all_diffs_with_status_filter(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test filtering diffs by status."""
        # Create pending diffs
        for i in range(3):
            diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-1",
                worktree_agent_id="worktree-1",
                file_path=f"src/file_{i}.py",
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )

        # Filter by pending
        pending = diff_resolution_service.get_all_diffs(status_filter="pending")
        assert len(pending) == 3

        # Filter by resolved (should be empty)
        resolved = diff_resolution_service.get_all_diffs(status_filter="resolved")
        assert len(resolved) == 0

    def test_get_all_diffs_with_limit(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test limiting diff results."""
        for i in range(10):
            diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-1",
                worktree_agent_id="worktree-1",
                file_path=f"src/file_{i}.py",
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )

        result = diff_resolution_service.get_all_diffs(limit=5)
        assert len(result) == 5


class TestMapResolutionChoice:
    """Test resolution choice mapping."""

    def test_map_parent(self, diff_resolution_service):
        """Test mapping parent choice."""
        assert diff_resolution_service._map_resolution_choice("parent") == "parent"

    def test_map_child(self, diff_resolution_service):
        """Test mapping child choice."""
        assert diff_resolution_service._map_resolution_choice("child") == "child"

    def test_map_merged(self, diff_resolution_service):
        """Test mapping merged choice (maps to child)."""
        assert diff_resolution_service._map_resolution_choice("merged") == "child"

    def test_map_unknown(self, diff_resolution_service):
        """Test mapping unknown choice (defaults to child)."""
        assert diff_resolution_service._map_resolution_choice("unknown") == "child"


class TestCallLLMForResolution:
    """Test LLM calling functionality."""

    @pytest.mark.asyncio
    async def test_llm_response_parsing_child(self, diff_resolution_service):
        """Test parsing LLM response for child choice."""
        # Patch the _llm_provider attribute directly and the single provider call
        diff_resolution_service._llm_provider = Mock()

        with patch.object(
            diff_resolution_service,
            "_call_single_provider",
            new_callable=AsyncMock
        ) as mock_single:
            mock_single.return_value = '{"choice": "child", "reasoning": "Agent version is better"}'

            result = await diff_resolution_service._call_llm_for_resolution("test prompt")

        assert result["choice"] == "child"
        assert "Agent version is better" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_llm_response_parsing_with_markdown(self, diff_resolution_service):
        """Test parsing LLM response wrapped in markdown."""
        diff_resolution_service._llm_provider = Mock()

        with patch.object(
            diff_resolution_service,
            "_call_single_provider",
            new_callable=AsyncMock
        ) as mock_single:
            mock_single.return_value = '''```json
{"choice": "parent", "reasoning": "Parent is stable"}
```'''

            result = await diff_resolution_service._call_llm_for_resolution("test prompt")

        assert result["choice"] == "parent"

    @pytest.mark.asyncio
    async def test_llm_error_fallback(self, diff_resolution_service):
        """Test fallback when LLM fails."""
        diff_resolution_service._llm_provider = Mock()

        with patch.object(
            diff_resolution_service,
            "_call_single_provider",
            new_callable=AsyncMock
        ) as mock_single:
            mock_single.side_effect = Exception("API timeout")

            result = await diff_resolution_service._call_llm_for_resolution("test prompt")

        # Should fallback to child
        assert result["choice"] == "child"
        assert "failed" in result["reasoning"].lower()


class TestSingleton:
    """Test singleton pattern for the service."""

    def test_get_diff_resolution_service_creates_instance(self, db_manager):
        """Test that get_diff_resolution_service creates an instance."""
        # Reset the singleton
        import src.services.diff_resolution_service as module
        module._diff_resolution_service = None

        service = get_diff_resolution_service(db_manager)
        assert service is not None
        assert isinstance(service, DiffResolutionService)

        # Cleanup
        module._diff_resolution_service = None

    def test_get_diff_resolution_service_returns_same_instance(self, db_manager):
        """Test that subsequent calls return the same instance."""
        import src.services.diff_resolution_service as module
        module._diff_resolution_service = None

        service1 = get_diff_resolution_service(db_manager)
        service2 = get_diff_resolution_service()  # No db_manager needed

        assert service1 is service2

        # Cleanup
        module._diff_resolution_service = None


class TestConcurrency:
    """Test concurrent access handling."""

    @pytest.mark.asyncio
    async def test_concurrent_batch_resolution(
        self, diff_resolution_service, sample_parent_content, sample_child_content
    ):
        """Test that concurrent batch resolutions are serialized."""
        # Queue many diffs
        for i in range(10):
            diff_resolution_service.queue_diff_for_resolution(
                merge_agent_id="merge-1",
                worktree_agent_id="worktree-1",
                file_path=f"src/file_{i}.py",
                parent_content=sample_parent_content,
                child_content=sample_child_content,
            )

        resolve_count = 0

        async def mock_resolve(prompt):
            nonlocal resolve_count
            resolve_count += 1
            await asyncio.sleep(0.01)  # Simulate LLM latency
            return {
                "choice": "child",
                "reasoning": "Test",
                "content": None,
            }

        with patch.object(
            diff_resolution_service,
            "_call_llm_for_resolution",
            side_effect=mock_resolve
        ):
            # Start two concurrent batches
            results = await asyncio.gather(
                diff_resolution_service.resolve_diff_batch("resolver-1", batch_size=3),
                diff_resolution_service.resolve_diff_batch("resolver-2", batch_size=3),
            )

        # Due to locking, batches should be processed sequentially
        # Total resolved should be 6 (3 + 3)
        total_resolved = sum(len(r) for r in results)
        assert total_resolved == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
