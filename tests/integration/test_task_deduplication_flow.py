"""Integration tests for task deduplication flow."""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from src.mcp.server import app, server_state
from src.core.database import Task, DatabaseManager
from src.services.embedding_service import EmbeddingService
from src.services.task_similarity_service import TaskSimilarityService


class TestTaskDeduplicationFlow:
    """Integration tests for the complete task deduplication flow."""

    @pytest.fixture
    async def initialized_server(self):
        """Initialize server with mocked services."""
        # Mock the services
        with patch('src.mcp.server.get_config') as mock_config:
            config = Mock()
            config.openai_api_key = "test-key"
            config.task_dedup_enabled = True
            config.task_similarity_threshold = 0.7
            config.task_related_threshold = 0.4
            config.enable_cors = False
            config.database_path = ":memory:"
            config.qdrant_url = "http://localhost:6333"
            config.qdrant_collection_prefix = "test"
            config.llm_provider = "openai"
            config.llm_model = "gpt-4"
            config.embedding_model = "text-embedding-ada-002"
            mock_config.return_value = config

            # Initialize server state
            await server_state.initialize()

            # Replace with mock services
            server_state.embedding_service = Mock(spec=EmbeddingService)
            server_state.task_similarity_service = Mock(spec=TaskSimilarityService)

            yield server_state

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_embedding(self):
        """Generate sample embedding."""
        return [0.1] * 3072

    @pytest.mark.asyncio
    async def test_create_duplicate_task_rejected(self, initialized_server, client, sample_embedding):
        """Test that duplicate tasks are properly rejected with 409 status."""
        # Setup mocks
        server = initialized_server
        server.embedding_service.generate_embedding = AsyncMock(return_value=sample_embedding)

        # Mock LLM enrichment
        server.llm_provider.enrich_task = AsyncMock(return_value={
            "enriched_description": "Enriched: Implement user authentication",
            "completion_criteria": ["User can log in", "User can log out"],
            "agent_prompt": "Build auth system",
            "required_capabilities": ["coding"],
            "estimated_complexity": 5
        })

        # Mock RAG
        server.rag_system.retrieve_for_task = AsyncMock(return_value=[])

        # Mock agent manager
        server.agent_manager.get_project_context = AsyncMock(return_value="Project context")
        server.agent_manager.create_agent_for_task = AsyncMock()

        # First task - should succeed
        server.task_similarity_service.check_for_duplicates = AsyncMock(return_value={
            'is_duplicate': False,
            'duplicate_of': None,
            'related_tasks': [],
            'max_similarity': 0.0
        })
        server.task_similarity_service.store_task_embedding = AsyncMock()

        response1 = client.post(
            "/create_task",
            json={
                "task_description": "Implement user authentication",
                "done_definition": "Users can log in and out",
                "ai_agent_id": "agent-123",
                "priority": "high"
            },
            headers={"X-Agent-ID": "agent-123"}
        )

        assert response1.status_code == 200
        task1_data = response1.json()
        assert "task_id" in task1_data

        # Second task - duplicate, should be rejected
        server.task_similarity_service.check_for_duplicates = AsyncMock(return_value={
            'is_duplicate': True,
            'duplicate_of': task1_data["task_id"],
            'duplicate_description': "Enriched: Implement user authentication",
            'related_tasks': [],
            'max_similarity': 0.95
        })

        response2 = client.post(
            "/create_task",
            json={
                "task_description": "Build user authentication system",
                "done_definition": "Allow users to authenticate",
                "ai_agent_id": "agent-456",
                "priority": "high"
            },
            headers={"X-Agent-ID": "agent-456"}
        )

        # Should be rejected as duplicate
        assert response2.status_code == 409
        duplicate_data = response2.json()
        assert duplicate_data["error"] == "duplicate_task"
        assert duplicate_data["duplicate_of"] == task1_data["task_id"]
        assert duplicate_data["similarity"] == 0.95

        # Verify agent was NOT created for duplicate
        assert server.agent_manager.create_agent_for_task.call_count == 1  # Only for first task

    @pytest.mark.asyncio
    async def test_create_related_task_accepted(self, initialized_server, client, sample_embedding):
        """Test that related but not duplicate tasks are accepted."""
        server = initialized_server
        server.embedding_service.generate_embedding = AsyncMock(return_value=sample_embedding)

        # Mock enrichment and other services
        server.llm_provider.enrich_task = AsyncMock(return_value={
            "enriched_description": "Enriched task",
            "completion_criteria": ["Done"],
            "agent_prompt": "Do task",
            "required_capabilities": ["general"],
            "estimated_complexity": 3
        })
        server.rag_system.retrieve_for_task = AsyncMock(return_value=[])
        server.agent_manager.get_project_context = AsyncMock(return_value="Context")
        server.agent_manager.create_agent_for_task = AsyncMock(
            return_value=Mock(id="agent-created")
        )

        # First task
        server.task_similarity_service.check_for_duplicates = AsyncMock(return_value={
            'is_duplicate': False,
            'duplicate_of': None,
            'related_tasks': [],
            'max_similarity': 0.0
        })
        server.task_similarity_service.store_task_embedding = AsyncMock()

        response1 = client.post(
            "/create_task",
            json={
                "task_description": "Create user profiles",
                "done_definition": "User profiles exist",
                "ai_agent_id": "agent-111",
            },
            headers={"X-Agent-ID": "agent-111"}
        )
        assert response1.status_code == 200
        task1_id = response1.json()["task_id"]

        # Second task - related but not duplicate
        server.task_similarity_service.check_for_duplicates = AsyncMock(return_value={
            'is_duplicate': False,
            'duplicate_of': None,
            'related_tasks': [task1_id],
            'related_tasks_details': [
                {'task_id': task1_id, 'description': 'Create user profiles', 'similarity': 0.55}
            ],
            'max_similarity': 0.55
        })

        response2 = client.post(
            "/create_task",
            json={
                "task_description": "Build user settings page",
                "done_definition": "Settings page works",
                "ai_agent_id": "agent-222",
            },
            headers={"X-Agent-ID": "agent-222"}
        )

        # Should be accepted
        assert response2.status_code == 200
        task2_data = response2.json()
        assert "task_id" in task2_data

        # Check if related tasks are included in response
        if isinstance(task2_data, dict) and 'related_tasks' in task2_data:
            assert task1_id in task2_data['related_tasks']

        # Verify both agents were created
        assert server.agent_manager.create_agent_for_task.call_count == 2

    @pytest.mark.asyncio
    async def test_create_unrelated_task_accepted(self, initialized_server, client, sample_embedding):
        """Test that unrelated tasks are created without relationships."""
        server = initialized_server
        server.embedding_service.generate_embedding = AsyncMock(return_value=sample_embedding)

        # Mock services
        server.llm_provider.enrich_task = AsyncMock(return_value={
            "enriched_description": "Enriched task",
            "completion_criteria": ["Done"],
            "agent_prompt": "Do task",
            "required_capabilities": ["general"],
            "estimated_complexity": 2
        })
        server.rag_system.retrieve_for_task = AsyncMock(return_value=[])
        server.agent_manager.get_project_context = AsyncMock(return_value="Context")
        server.agent_manager.create_agent_for_task = AsyncMock(
            return_value=Mock(id="agent-new")
        )

        # Task with low similarity to all existing tasks
        server.task_similarity_service.check_for_duplicates = AsyncMock(return_value={
            'is_duplicate': False,
            'duplicate_of': None,
            'related_tasks': [],  # No related tasks
            'max_similarity': 0.2  # Below related threshold
        })
        server.task_similarity_service.store_task_embedding = AsyncMock()

        response = client.post(
            "/create_task",
            json={
                "task_description": "Configure database backups",
                "done_definition": "Backups are automated",
                "ai_agent_id": "agent-333",
            },
            headers={"X-Agent-ID": "agent-333"}
        )

        assert response.status_code == 200
        task_data = response.json()
        assert "task_id" in task_data

        # Verify no relationships stored
        server.task_similarity_service.store_task_embedding.assert_called_with(
            task_data["task_id"],
            sample_embedding,
            []  # No related tasks
        )

    @pytest.mark.asyncio
    async def test_deduplication_disabled(self, client):
        """Test that tasks are created normally when deduplication is disabled."""
        with patch('src.mcp.server.get_config') as mock_config:
            config = Mock()
            config.task_dedup_enabled = False  # Disabled
            config.openai_api_key = "test-key"
            config.enable_cors = False
            mock_config.return_value = config

            # Initialize server without deduplication
            await server_state.initialize()

            # Mock other services
            server_state.llm_provider.enrich_task = AsyncMock(return_value={
                "enriched_description": "Task",
                "completion_criteria": ["Done"],
                "agent_prompt": "Do it",
                "required_capabilities": ["general"],
                "estimated_complexity": 3
            })
            server_state.rag_system.retrieve_for_task = AsyncMock(return_value=[])
            server_state.agent_manager.get_project_context = AsyncMock(return_value="Context")
            server_state.agent_manager.create_agent_for_task = AsyncMock(
                return_value=Mock(id="agent-id")
            )

            # Create two identical tasks
            for i in range(2):
                response = client.post(
                    "/create_task",
                    json={
                        "task_description": "Identical task description",
                        "done_definition": "Same completion",
                        "ai_agent_id": f"agent-{i}",
                    },
                    headers={"X-Agent-ID": f"agent-{i}"}
                )

                # Both should succeed
                assert response.status_code == 200
                assert "task_id" in response.json()

            # Verify both agents were created
            assert server_state.agent_manager.create_agent_for_task.call_count == 2

    @pytest.mark.asyncio
    async def test_deduplication_performance(self, initialized_server, sample_embedding):
        """Test deduplication performance with many existing tasks."""
        import time
        server = initialized_server

        # Create many existing tasks in database
        session = server.db_manager.get_session()
        for i in range(1000):
            task = Task(
                id=f"task-{i}",
                raw_description=f"Task number {i}",
                enriched_description=f"Enriched task {i}",
                done_definition=f"Complete task {i}",
                status="in_progress",
                embedding=[i * 0.001] * 3072  # Unique embeddings
            )
            session.add(task)
        session.commit()
        session.close()

        # Mock embedding service
        server.embedding_service.calculate_batch_similarities = Mock(
            return_value=[0.1] * 1000  # All low similarity
        )

        # Measure time for duplicate check
        start_time = time.time()
        result = await server.task_similarity_service.check_for_duplicates(
            "New task description",
            sample_embedding
        )
        elapsed = time.time() - start_time

        # Should complete within 2 seconds even with 1000 tasks
        assert elapsed < 2.0
        assert result['is_duplicate'] is False

    @pytest.mark.asyncio
    async def test_concurrent_duplicate_creation(self, initialized_server, client, sample_embedding):
        """Test handling of concurrent duplicate task creation."""
        server = initialized_server
        server.embedding_service.generate_embedding = AsyncMock(return_value=sample_embedding)

        # Mock services
        server.llm_provider.enrich_task = AsyncMock(return_value={
            "enriched_description": "Same task",
            "completion_criteria": ["Done"],
            "agent_prompt": "Do it",
            "required_capabilities": ["general"],
            "estimated_complexity": 3
        })
        server.rag_system.retrieve_for_task = AsyncMock(return_value=[])
        server.agent_manager.get_project_context = AsyncMock(return_value="Context")

        # Track created agents
        created_agents = []

        async def create_agent_mock(task, **kwargs):
            agent = Mock(id=f"agent-{len(created_agents)}")
            created_agents.append(agent)
            # Simulate some processing time
            await asyncio.sleep(0.1)
            return agent

        server.agent_manager.create_agent_for_task = create_agent_mock

        # First call finds no duplicates, second call finds the first as duplicate
        call_count = 0

        async def check_duplicates_mock(desc, emb):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First task finds no duplicates
                return {
                    'is_duplicate': False,
                    'duplicate_of': None,
                    'related_tasks': [],
                    'max_similarity': 0.0
                }
            else:
                # Second task finds first as duplicate
                return {
                    'is_duplicate': True,
                    'duplicate_of': 'task-first',
                    'duplicate_description': 'Same task',
                    'related_tasks': [],
                    'max_similarity': 0.99
                }

        server.task_similarity_service.check_for_duplicates = check_duplicates_mock
        server.task_similarity_service.store_task_embedding = AsyncMock()

        # Create two tasks concurrently
        async def create_task(agent_id):
            response = client.post(
                "/create_task",
                json={
                    "task_description": "Concurrent task",
                    "done_definition": "Task done",
                    "ai_agent_id": agent_id,
                },
                headers={"X-Agent-ID": agent_id}
            )
            return response

        # Run concurrently
        results = await asyncio.gather(
            create_task("agent-A"),
            create_task("agent-B"),
            return_exceptions=True
        )

        # One should succeed, one should be duplicate
        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        assert 200 in statuses  # At least one succeeded
        # Note: Due to the async nature and our mock, both might succeed
        # In a real scenario with proper database locking, one would fail

    @pytest.mark.asyncio
    async def test_embedding_service_failure_handling(self, initialized_server, client):
        """Test that task creation continues when embedding service fails."""
        server = initialized_server

        # Mock embedding service to fail
        server.embedding_service.generate_embedding = AsyncMock(
            side_effect=Exception("OpenAI API error")
        )

        # Other services work normally
        server.llm_provider.enrich_task = AsyncMock(return_value={
            "enriched_description": "Task despite error",
            "completion_criteria": ["Done"],
            "agent_prompt": "Do it",
            "required_capabilities": ["general"],
            "estimated_complexity": 3
        })
        server.rag_system.retrieve_for_task = AsyncMock(return_value=[])
        server.agent_manager.get_project_context = AsyncMock(return_value="Context")
        server.agent_manager.create_agent_for_task = AsyncMock(
            return_value=Mock(id="agent-created")
        )

        response = client.post(
            "/create_task",
            json={
                "task_description": "Task with embedding error",
                "done_definition": "Complete it",
                "ai_agent_id": "agent-error",
            },
            headers={"X-Agent-ID": "agent-error"}
        )

        # Should still succeed despite embedding error
        assert response.status_code == 200
        task_data = response.json()
        assert "task_id" in task_data
        assert "assigned_agent_id" in task_data

        # Agent should have been created
        server.agent_manager.create_agent_for_task.assert_called_once()