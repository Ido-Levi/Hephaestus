"""Integration test for Qdrant MCP memory search functionality."""

import pytest
import asyncio
import uuid
from src.core.database import DatabaseManager, Memory
from src.memory.vector_store import VectorStoreManager
from src.interfaces import get_llm_provider
from src.core.simple_config import get_config


@pytest.fixture
def db_manager():
    """Create test database manager."""
    db = DatabaseManager(":memory:")
    db.create_tables()
    yield db
    # Cleanup handled by in-memory DB


@pytest.fixture
def vector_store():
    """Create vector store manager."""
    config = get_config()
    return VectorStoreManager(
        qdrant_url=config.qdrant_url,
        collection_prefix="test_qdrant_mcp",
        embedding_dimension=config.embedding_dimension
    )


@pytest.fixture
def llm_provider():
    """Create LLM provider for embeddings."""
    config = get_config()
    return get_llm_provider()


@pytest.mark.asyncio
async def test_save_and_search_memory_via_qdrant(db_manager, vector_store, llm_provider):
    """
    Test that memories saved via save_memory can be found via Qdrant search.
    This simulates the flow where one agent saves a memory and another agent
    searches for it using the Qdrant MCP.
    """
    # 1. Save a test memory with embedding (simulating save_memory endpoint)
    test_content = "Fixed PostgreSQL connection timeout by increasing pool size to 20 and timeout to 30 seconds"
    test_agent_id = str(uuid.uuid4())
    test_memory_id = str(uuid.uuid4())

    # Generate embedding
    embedding = await llm_provider.generate_embedding(test_content)

    # Store in vector database
    await vector_store.store_memory(
        collection="agent_memories",
        memory_id=test_memory_id,
        embedding=embedding,
        content=test_content,
        metadata={
            "agent_id": test_agent_id,
            "memory_type": "error_fix",
            "tags": ["postgresql", "connection", "timeout"],
        }
    )

    # Store in SQLite
    session = db_manager.get_session()
    memory = Memory(
        id=test_memory_id,
        agent_id=test_agent_id,
        content=test_content,
        memory_type="error_fix",
        embedding_id=test_memory_id,
        tags=["postgresql", "connection", "timeout"],
    )
    session.add(memory)
    session.commit()
    session.close()

    # 2. Search for similar content (simulating qdrant-find)
    search_query = "How to fix database connection timeouts"
    search_embedding = await llm_provider.generate_embedding(search_query)

    results = await vector_store.search(
        collection="agent_memories",
        query_vector=search_embedding,
        limit=5,
        score_threshold=0.5,
    )

    # 3. Verify the memory was found
    assert len(results) > 0, "Should find at least one matching memory"

    # Find our test memory in results
    found = False
    for result in results:
        if result["id"] == test_memory_id:
            found = True
            assert "PostgreSQL" in result["content"]
            assert result["metadata"]["memory_type"] == "error_fix"
            assert "postgresql" in result["metadata"]["tags"]
            print(f"✓ Found memory with score: {result['score']:.3f}")
            break

    assert found, f"Test memory {test_memory_id} should be in search results"


@pytest.mark.asyncio
async def test_semantic_search_across_memory_types(vector_store, llm_provider):
    """
    Test that semantic search works across different memory types.
    This validates that agents can find relevant memories regardless of type.
    """
    # Create test memories of different types
    test_memories = [
        {
            "id": str(uuid.uuid4()),
            "content": "Error: ECONNREFUSED when connecting to Redis. Fixed by starting Redis service.",
            "type": "error_fix",
        },
        {
            "id": str(uuid.uuid4()),
            "content": "Discovered that Redis caching improves API response time by 70%.",
            "type": "discovery",
        },
        {
            "id": str(uuid.uuid4()),
            "content": "Decision: Use Redis for session storage instead of PostgreSQL for better performance.",
            "type": "decision",
        },
    ]

    # Store all memories
    for mem in test_memories:
        embedding = await llm_provider.generate_embedding(mem["content"])
        await vector_store.store_memory(
            collection="agent_memories",
            memory_id=mem["id"],
            embedding=embedding,
            content=mem["content"],
            metadata={"memory_type": mem["type"], "agent_id": "test-agent-002"},
        )

    # Search with Redis-related query
    search_query = "Redis connection issues"
    search_embedding = await llm_provider.generate_embedding(search_query)

    results = await vector_store.search(
        collection="agent_memories",
        query_vector=search_embedding,
        limit=10,
        score_threshold=0.3,
    )

    # Should find at least the error_fix memory
    found_types = set()
    memory_ids = {mem["id"] for mem in test_memories}
    for result in results:
        if result["id"] in memory_ids:
            found_types.add(result["metadata"]["memory_type"])
            print(f"Found {result['metadata']['memory_type']}: {result['content'][:60]}... (score: {result['score']:.3f})")

    assert "error_fix" in found_types, "Should find the error_fix memory about Redis connection"
    assert len(found_types) >= 1, "Should find at least one relevant memory"


@pytest.mark.asyncio
async def test_qdrant_collection_health(vector_store):
    """
    Test that the Qdrant collection is accessible and healthy.
    This validates the basic MCP connection.
    """
    # Get collection stats
    stats = vector_store.get_collection_stats("agent_memories")

    assert stats["name"] == "agent_memories"
    assert stats["status"] == "green"
    assert "vectors_count" in stats

    print(f"✓ Collection health check passed: {stats['vectors_count']} vectors")


def test_agent_prompt_includes_qdrant_instructions():
    """
    Test that agent prompts include instructions for using Qdrant MCP.
    This ensures agents know about the qdrant-find tool.
    """
    config = get_config()
    llm_provider = get_llm_provider()

    # Create a test task
    task = {
        "id": "test-task-001",
        "description": "Test task",
        "enriched_description": "Complete the test task",
        "done_definition": "Task is done when test passes",
        "agent_id": "test-agent-003",
    }

    memories = [
        {"content": "Test memory 1", "relevance_score": 0.9},
        {"content": "Test memory 2", "relevance_score": 0.8},
    ]

    project_context = "Test project"

    # Generate prompt
    prompt = asyncio.run(llm_provider.generate_agent_prompt(
        task=task,
        memories=memories,
        project_context=project_context
    ))

    # Verify prompt includes Qdrant instructions
    assert "qdrant-find" in prompt.lower(), "Prompt should mention qdrant-find tool"
    assert "search" in prompt.lower(), "Prompt should mention searching"
    assert "pre-loaded context" in prompt.lower() or "preloaded" in prompt.lower(), "Prompt should explain pre-loaded memories"

    print("✓ Agent prompt includes Qdrant MCP instructions")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])