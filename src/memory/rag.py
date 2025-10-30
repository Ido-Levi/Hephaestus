"""RAG (Retrieval Augmented Generation) system for Hephaestus."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from src.memory.vector_store import VectorStoreManager
from src.interfaces import LLMProviderInterface

logger = logging.getLogger(__name__)


class RAGSystem:
    """Retrieval system for cross-agent knowledge sharing."""

    def __init__(
        self,
        vector_store: VectorStoreManager,
        llm_provider: LLMProviderInterface,
    ):
        """Initialize RAG system.

        Args:
            vector_store: Vector store manager
            llm_provider: LLM provider for embeddings
        """
        self.vector_store = vector_store
        self.llm_provider = llm_provider

    async def retrieve_for_task(
        self,
        task_description: str,
        requesting_agent_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for a task.

        Args:
            task_description: Description of the task
            requesting_agent_id: ID of requesting agent
            limit: Maximum number of memories to retrieve

        Returns:
            List of relevant memories with metadata
        """
        logger.debug(f"Retrieving memories for task: {task_description[:100]}...")

        try:
            # Generate embedding for the task description
            query_embedding = await self.llm_provider.generate_embedding(task_description)

            # Search across all relevant collections
            all_results = await self.vector_store.search_all_collections(
                query_vector=query_embedding,
                limit_per_collection=5,
                total_limit=limit,
            )

            # Rerank results based on multiple factors
            ranked_results = self._rerank_results(all_results, task_description)

            # Format results for consumption
            formatted_results = []
            for result in ranked_results[:limit]:
                formatted_results.append({
                    "content": result["content"],
                    "source_collection": result.get("collection", "unknown"),
                    "source_agent": result["metadata"].get("agent_id", "system"),
                    "memory_type": result["metadata"].get("memory_type", "general"),
                    "relevance_score": result["score"],
                    "timestamp": result["metadata"].get("timestamp"),
                    "related_files": result["metadata"].get("related_files", []),
                })

            logger.info(f"Retrieved {len(formatted_results)} memories for task")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []

    async def search_similar_tasks(
        self,
        task_description: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for similar past tasks.

        Args:
            task_description: Description to search for
            limit: Maximum results

        Returns:
            List of similar tasks
        """
        try:
            # Generate embedding
            embedding = await self.llm_provider.generate_embedding(task_description)

            # Search in task_completions collection
            results = await self.vector_store.search(
                collection="task_completions",
                query_vector=embedding,
                limit=limit,
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search similar tasks: {e}")
            return []

    async def search_error_solutions(
        self,
        error_description: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for solutions to similar errors.

        Args:
            error_description: Error to search for
            limit: Maximum results

        Returns:
            List of potential solutions
        """
        try:
            # Generate embedding
            embedding = await self.llm_provider.generate_embedding(error_description)

            # Search in error_solutions collection
            results = await self.vector_store.search(
                collection="error_solutions",
                query_vector=embedding,
                limit=limit,
                score_threshold=0.7,
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search error solutions: {e}")
            return []

    async def get_domain_knowledge(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get relevant domain knowledge.

        Args:
            query: Query string
            limit: Maximum results

        Returns:
            List of domain knowledge entries
        """
        try:
            # Generate embedding
            embedding = await self.llm_provider.generate_embedding(query)

            # Search in domain_knowledge collection
            results = await self.vector_store.search(
                collection="domain_knowledge",
                query_vector=embedding,
                limit=limit,
            )

            return results

        except Exception as e:
            logger.error(f"Failed to get domain knowledge: {e}")
            return []

    def _rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
    ) -> List[Dict[str, Any]]:
        """Rerank search results based on multiple factors.

        Args:
            results: Raw search results
            query: Original query

        Returns:
            Reranked results
        """
        scored_results = []

        for result in results:
            # Calculate scores
            vector_score = result["score"]
            recency_score = self._calculate_recency_score(
                result["metadata"].get("timestamp")
            )
            type_relevance = self._get_type_relevance_score(
                result["metadata"].get("memory_type"),
                result.get("collection"),
            )

            # Calculate weighted final score
            final_score = (
                vector_score * 0.5 +  # Similarity weight
                recency_score * 0.2 +  # Recency weight
                type_relevance * 0.3  # Type relevance weight
            )

            result["final_score"] = final_score
            scored_results.append(result)

        # Sort by final score
        scored_results.sort(key=lambda x: x["final_score"], reverse=True)
        return scored_results

    def _calculate_recency_score(self, timestamp: Optional[str]) -> float:
        """Calculate recency score for a memory.

        Args:
            timestamp: ISO format timestamp

        Returns:
            Recency score (0-1)
        """
        if not timestamp:
            return 0.5  # Default for missing timestamps

        try:
            memory_time = datetime.fromisoformat(timestamp)
            age = datetime.utcnow() - memory_time

            # Score based on age (newer is better)
            if age < timedelta(hours=1):
                return 1.0
            elif age < timedelta(days=1):
                return 0.9
            elif age < timedelta(days=7):
                return 0.7
            elif age < timedelta(days=30):
                return 0.5
            else:
                return 0.3

        except:
            return 0.5

    def _get_type_relevance_score(
        self,
        memory_type: Optional[str],
        collection: Optional[str],
    ) -> float:
        """Get relevance score based on memory type and collection.

        Args:
            memory_type: Type of memory
            collection: Source collection

        Returns:
            Relevance score (0-1)
        """
        # Prioritize certain types and collections
        high_priority = {
            "error_solutions": 0.9,
            "task_completions": 0.8,
            "learning": 0.8,
            "error_fix": 0.9,
        }

        medium_priority = {
            "agent_memories": 0.6,
            "discovery": 0.6,
            "decision": 0.5,
        }

        # Check collection first
        if collection in high_priority:
            return high_priority[collection]

        # Then check memory type
        if memory_type in high_priority:
            return high_priority[memory_type]

        if collection in medium_priority:
            return medium_priority[collection]

        if memory_type in medium_priority:
            return medium_priority[memory_type]

        return 0.4  # Default relevance


class MemoryIngestion:
    """Handle ingestion of various content into memory."""

    def __init__(
        self,
        vector_store: VectorStoreManager,
        llm_provider: LLMProviderInterface,
    ):
        """Initialize memory ingestion.

        Args:
            vector_store: Vector store manager
            llm_provider: LLM provider for embeddings
        """
        self.vector_store = vector_store
        self.llm_provider = llm_provider

    async def ingest_document(
        self,
        file_path: str,
        document_type: str = "documentation",
    ):
        """Ingest a document into memory.

        Args:
            file_path: Path to document
            document_type: Type of document
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Chunk the document
            chunks = self._chunk_document(content, max_tokens=500, overlap=50)

            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.llm_provider.generate_embedding(chunk)

                # Store in vector database
                memory_id = f"{file_path}_{i}"
                await self.vector_store.store_memory(
                    collection="static_docs",
                    memory_id=memory_id,
                    embedding=embedding,
                    content=chunk,
                    metadata={
                        "file_path": file_path,
                        "document_type": document_type,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                )

            logger.info(f"Ingested document {file_path} in {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to ingest document {file_path}: {e}")

    def _chunk_document(
        self,
        content: str,
        max_tokens: int = 500,
        overlap: int = 50,
    ) -> List[str]:
        """Chunk a document into smaller pieces.

        Args:
            content: Document content
            max_tokens: Maximum tokens per chunk
            overlap: Token overlap between chunks

        Returns:
            List of chunks
        """
        # Simple word-based chunking (in production, use proper tokenizer)
        words = content.split()
        chunks = []

        # Approximate tokens as words for simplicity
        chunk_size = max_tokens
        step = chunk_size - overlap

        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

            # Stop if we've reached the end
            if i + chunk_size >= len(words):
                break

        return chunks