#!/usr/bin/env python3
"""Integration tests for Vector Store operations."""

import asyncio
import uuid
import time
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.vector_store import VectorStoreManager
from src.interfaces.llm_interface import OpenAIProvider
from src.core.simple_config import Config

# Test data
TEST_MEMORIES = [
    {
        "content": "When working with React hooks, always use useEffect with proper dependency arrays to avoid infinite loops.",
        "memory_type": "learning",
        "tags": ["react", "hooks", "javascript"],
    },
    {
        "content": "Fixed authentication bug by implementing proper JWT token refresh logic with automatic retry on 401 errors.",
        "memory_type": "error_fix",
        "tags": ["auth", "jwt", "bug"],
    },
    {
        "content": "The payment processing module uses Stripe API v3 with webhook signature verification for security.",
        "memory_type": "discovery",
        "tags": ["payments", "stripe", "security"],
    },
    {
        "content": "Database migrations should always be tested in staging before production deployment.",
        "memory_type": "warning",
        "tags": ["database", "deployment", "best-practice"],
    },
]


async def test_vector_store_operations():
    """Test vector store CRUD operations."""
    print("\n🧪 Testing Vector Store Operations...")

    # Initialize components
    config = Config()
    vector_store = VectorStoreManager(embedding_dimension=config.embedding_dimension)
    llm_provider = OpenAIProvider(
        api_key=config.openai_api_key,
        model=config.llm_model,
        embedding_model=config.embedding_model
    )

    test_collection = "agent_memories"
    stored_ids = []

    print("\n1️⃣ Testing memory storage...")
    for i, memory_data in enumerate(TEST_MEMORIES):
        try:
            # Generate embedding
            embedding = await llm_provider.generate_embedding(memory_data["content"])

            # Verify embedding dimension
            expected_dim = config.embedding_dimension
            assert len(embedding) == expected_dim, f"Expected {expected_dim} dimensions, got {len(embedding)}"

            # Store memory (use UUID string for Qdrant)
            memory_id = str(uuid.uuid4())
            success = await vector_store.store_memory(
                collection=test_collection,
                memory_id=memory_id,
                embedding=embedding,
                content=memory_data["content"],
                metadata={
                    "memory_type": memory_data["memory_type"],
                    "tags": memory_data["tags"],
                    "test_run": True,
                    "index": i,
                }
            )

            assert success, f"Failed to store memory {i}"
            stored_ids.append(memory_id)
            print(f"   ✅ Stored memory {i+1}/{len(TEST_MEMORIES)}: {memory_data['content'][:50]}...")

        except Exception as e:
            print(f"   ❌ Failed to store memory {i}: {e}")
            raise

    # Wait a bit for indexing
    await asyncio.sleep(2)

    print("\n2️⃣ Testing similarity search...")
    search_queries = [
        "How to fix React hook problems?",
        "Authentication and JWT token issues",
        "Payment processing security",
    ]

    for query in search_queries:
        try:
            # Generate query embedding
            query_embedding = await llm_provider.generate_embedding(query)

            # Search for similar memories
            results = await vector_store.search(
                collection=test_collection,
                query_vector=query_embedding,
                limit=3,
                score_threshold=0.5,
            )

            print(f"\n   Query: '{query}'")
            print(f"   Found {len(results)} results:")
            for result in results[:2]:
                print(f"      - Score: {result['score']:.3f} | {result['content'][:60]}...")

        except Exception as e:
            print(f"   ❌ Search failed for '{query}': {e}")
            raise

    print("\n3️⃣ Testing cross-collection search...")
    try:
        # Test search across all collections
        test_query = "How to handle errors in production?"
        query_embedding = await llm_provider.generate_embedding(test_query)

        all_results = await vector_store.search_all_collections(
            query_vector=query_embedding,
            limit_per_collection=2,
            total_limit=10,
        )

        print(f"   Query: '{test_query}'")
        print(f"   Found {len(all_results)} total results across collections")

        # Group results by collection
        by_collection = {}
        for result in all_results:
            collection = result.get("collection", "unknown")
            if collection not in by_collection:
                by_collection[collection] = []
            by_collection[collection].append(result)

        for collection, results in by_collection.items():
            print(f"      Collection '{collection}': {len(results)} results")

    except Exception as e:
        print(f"   ❌ Cross-collection search failed: {e}")
        raise

    print("\n4️⃣ Testing filtered search...")
    try:
        # Search with metadata filters
        query_embedding = await llm_provider.generate_embedding("authentication")

        filtered_results = await vector_store.search(
            collection=test_collection,
            query_vector=query_embedding,
            limit=5,
            filters={"memory_type": "error_fix"},
        )

        print(f"   Filtered search for memory_type='error_fix':")
        print(f"   Found {len(filtered_results)} results")
        for result in filtered_results:
            assert result["metadata"]["memory_type"] == "error_fix", "Filter not applied correctly"
            print(f"      ✅ {result['content'][:60]}...")

    except Exception as e:
        print(f"   ❌ Filtered search failed: {e}")
        raise

    print("\n5️⃣ Testing collection stats...")
    try:
        stats = vector_store.get_collection_stats(test_collection)
        print(f"   Collection: {stats['name']}")
        print(f"   Vector count: {stats['vectors_count']}")
        print(f"   Status: {stats['status']}")

        all_stats = vector_store.get_all_stats()
        print(f"   Total collections tracked: {len(all_stats)}")

    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}")
        raise

    print("\n6️⃣ Cleaning up test data...")
    cleanup_count = 0
    for memory_id in stored_ids:
        try:
            success = vector_store.delete_memory(test_collection, memory_id)
            if success:
                cleanup_count += 1
        except:
            pass

    print(f"   Cleaned up {cleanup_count}/{len(stored_ids)} test memories")

    print("\n✅ Vector Store tests completed successfully!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("VECTOR STORE INTEGRATION TESTS")
    print("=" * 60)

    try:
        asyncio.run(test_vector_store_operations())
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)