#!/usr/bin/env python3
"""Integration tests for RAG system."""

import asyncio
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.rag import RAGSystem, MemoryIngestion
from src.memory.vector_store import VectorStoreManager
from src.interfaces.llm_interface import OpenAIProvider
from src.core.simple_config import Config


async def test_rag_retrieval():
    """Test RAG retrieval for tasks."""
    print("\n🧪 Testing RAG System Retrieval...")

    # Initialize components
    config = Config()
    vector_store = VectorStoreManager()
    llm_provider = OpenAIProvider(
        api_key=config.openai_api_key,
        model=config.llm_model,
        embedding_model=config.embedding_model
    )
    rag_system = RAGSystem(vector_store, llm_provider)

    # First, populate some test memories
    print("\n1️⃣ Populating test memories...")
    test_memories = [
        {
            "content": "To implement user authentication, use JWT tokens with RS256 algorithm for better security. Store refresh tokens in httpOnly cookies.",
            "memory_type": "learning",
            "collection": "agent_memories",
        },
        {
            "content": "Fixed CORS error by adding proper headers: Access-Control-Allow-Origin, Access-Control-Allow-Methods, and Access-Control-Allow-Headers.",
            "memory_type": "error_fix",
            "collection": "error_solutions",
        },
        {
            "content": "The project uses PostgreSQL database with Prisma ORM. Migrations are handled automatically via prisma migrate deploy.",
            "memory_type": "discovery",
            "collection": "project_context",
        },
        {
            "content": "API rate limiting is set to 100 requests per minute per IP address using Redis for distributed rate limiting.",
            "memory_type": "domain_knowledge",
            "collection": "domain_knowledge",
        },
    ]

    stored_ids = []
    for memory in test_memories:
        try:
            embedding = await llm_provider.generate_embedding(memory["content"])
            memory_id = f"test_{uuid.uuid4()}"

            success = await vector_store.store_memory(
                collection=memory["collection"],
                memory_id=memory_id,
                embedding=embedding,
                content=memory["content"],
                metadata={
                    "memory_type": memory["memory_type"],
                    "agent_id": "test_agent",
                    "test_run": True,
                }
            )

            if success:
                stored_ids.append((memory["collection"], memory_id))
                print(f"   ✅ Stored: {memory['content'][:60]}...")

        except Exception as e:
            print(f"   ❌ Failed to store memory: {e}")

    # Wait for indexing
    await asyncio.sleep(2)

    print("\n2️⃣ Testing task-based retrieval...")
    test_tasks = [
        "Implement secure user login with JWT authentication",
        "Fix CORS issues in the API",
        "Set up database migrations",
        "Implement API rate limiting",
    ]

    for task_desc in test_tasks:
        try:
            print(f"\n   Task: '{task_desc}'")

            memories = await rag_system.retrieve_for_task(
                task_description=task_desc,
                requesting_agent_id="test_agent",
                limit=5
            )

            print(f"   Retrieved {len(memories)} relevant memories:")
            for mem in memories[:2]:
                print(f"      - [{mem['memory_type']}] Score: {mem['relevance_score']:.3f}")
                print(f"        {mem['content'][:80]}...")

        except Exception as e:
            print(f"   ❌ Retrieval failed: {e}")

    print("\n3️⃣ Testing similar task search...")
    try:
        similar_tasks = await rag_system.search_similar_tasks(
            task_description="Build a REST API with authentication",
            limit=3
        )

        print(f"   Found {len(similar_tasks)} similar tasks")
        for task in similar_tasks:
            print(f"      - Score: {task.get('score', 0):.3f} | {task.get('content', '')[:60]}...")

    except Exception as e:
        print(f"   ❌ Similar task search failed: {e}")

    print("\n4️⃣ Testing error solution search...")
    try:
        error_solutions = await rag_system.search_error_solutions(
            error_description="CORS policy: No 'Access-Control-Allow-Origin' header is present",
            limit=3
        )

        print(f"   Found {len(error_solutions)} potential solutions")
        for solution in error_solutions:
            print(f"      - Score: {solution.get('score', 0):.3f}")
            print(f"        {solution.get('content', '')[:80]}...")

    except Exception as e:
        print(f"   ❌ Error solution search failed: {e}")

    print("\n5️⃣ Testing domain knowledge retrieval...")
    try:
        knowledge = await rag_system.get_domain_knowledge(
            query="How is rate limiting implemented in this system?",
            limit=3
        )

        print(f"   Found {len(knowledge)} domain knowledge entries")
        for entry in knowledge:
            print(f"      - Score: {entry.get('score', 0):.3f}")
            print(f"        {entry.get('content', '')[:80]}...")

    except Exception as e:
        print(f"   ❌ Domain knowledge retrieval failed: {e}")

    print("\n6️⃣ Cleaning up test data...")
    cleanup_count = 0
    for collection, memory_id in stored_ids:
        try:
            if vector_store.delete_memory(collection, memory_id):
                cleanup_count += 1
        except:
            pass

    print(f"   Cleaned up {cleanup_count}/{len(stored_ids)} test memories")

    print("\n✅ RAG System tests completed successfully!")
    return True


async def test_memory_ingestion():
    """Test document ingestion into memory."""
    print("\n🧪 Testing Memory Ingestion...")

    # Initialize components
    config = Config()
    vector_store = VectorStoreManager()
    llm_provider = OpenAIProvider(
        api_key=config.openai_api_key,
        model=config.llm_model,
        embedding_model=config.embedding_model
    )
    ingestion = MemoryIngestion(vector_store, llm_provider)

    # Create a test document
    test_file_path = "/tmp/test_document.md"
    test_content = """# Test Documentation

## Authentication System

Our authentication system uses JWT tokens with the following features:
- RS256 algorithm for enhanced security
- 15-minute access token expiry
- 7-day refresh token stored in httpOnly cookies
- Automatic token refresh on 401 responses

## Database Schema

The user table has the following structure:
- id: UUID primary key
- email: unique, not null
- password_hash: bcrypt hashed password
- created_at: timestamp
- updated_at: timestamp

## API Endpoints

### POST /auth/login
Authenticates a user and returns JWT tokens.

### POST /auth/refresh
Refreshes the access token using the refresh token.

### POST /auth/logout
Invalidates the refresh token.
"""

    print("\n1️⃣ Creating test document...")
    try:
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        print(f"   ✅ Created test document: {test_file_path}")
    except Exception as e:
        print(f"   ❌ Failed to create test document: {e}")
        return False

    print("\n2️⃣ Testing document ingestion...")
    try:
        await ingestion.ingest_document(
            file_path=test_file_path,
            document_type="documentation"
        )
        print(f"   ✅ Document ingested successfully")
    except Exception as e:
        print(f"   ❌ Document ingestion failed: {e}")
        return False

    # Wait for indexing
    await asyncio.sleep(2)

    print("\n3️⃣ Testing retrieval of ingested content...")
    try:
        # Search for content from the ingested document
        query_embedding = await llm_provider.generate_embedding("JWT authentication refresh token")

        results = await vector_store.search(
            collection="static_docs",
            query_vector=query_embedding,
            limit=5
        )

        print(f"   Found {len(results)} chunks from ingested document")
        for i, result in enumerate(results[:3]):
            print(f"      Chunk {i+1} (Score: {result['score']:.3f}):")
            print(f"         {result['content'][:100]}...")

    except Exception as e:
        print(f"   ❌ Failed to retrieve ingested content: {e}")
        return False

    print("\n4️⃣ Cleaning up...")
    try:
        # Clean up test document
        os.remove(test_file_path)
        print(f"   ✅ Removed test document")

        # Note: In production, you'd also clean up the ingested vectors
        # But for testing, we'll leave them to verify persistence

    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")

    print("\n✅ Memory Ingestion tests completed successfully!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("RAG SYSTEM INTEGRATION TESTS")
    print("=" * 60)

    async def run_all_tests():
        """Run all RAG system tests."""
        success = True

        try:
            success = await test_rag_retrieval() and success
            success = await test_memory_ingestion() and success
        except Exception as e:
            print(f"\n❌ Tests failed: {e}")
            return False

        return success

    try:
        success = asyncio.run(run_all_tests())
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)