"""Vector store management for RAG system using Qdrant."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector storage and retrieval using Qdrant."""

    # Collection definitions with their vector dimensions
    COLLECTIONS = {
        "agent_memories": {
            "size": None,  # Will be set to embedding_dimension
            "description": "Real-time agent discoveries and learnings",
        },
        "static_docs": {
            "size": None,
            "description": "Documentation files and static knowledge",
        },
        "task_completions": {
            "size": None,
            "description": "Historical task data and outcomes",
        },
        "error_solutions": {
            "size": None,
            "description": "Known error patterns and fixes",
        },
        "domain_knowledge": {
            "size": None,
            "description": "CVEs, CWEs, standards, and domain-specific knowledge",
        },
        "project_context": {
            "size": None,
            "description": "Current project state and goals",
        },
        "ticket_embeddings": {
            "size": None,
            "description": "Ticket tracking system embeddings for semantic search",
        },
    }

    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_prefix: str = "hephaestus", embedding_dimension: int = 768):
        """Initialize Qdrant client and collections.

        Args:
            qdrant_url: URL of the Qdrant server
            collection_prefix: Prefix for collection names
            embedding_dimension: Dimension of embedding vectors
        """
        self.client = QdrantClient(url=qdrant_url)
        self.collection_prefix = collection_prefix
        self.embedding_dimension = embedding_dimension
        self._initialize_collections()

    def _get_collection_name(self, collection: str) -> str:
        """Get the full collection name with prefix."""
        return f"{self.collection_prefix}_{collection}"

    def _initialize_collections(self):
        """Initialize all required collections in Qdrant."""
        for collection_name, config in self.COLLECTIONS.items():
            # Set the size to the embedding dimension
            config["size"] = self.embedding_dimension
            full_name = self._get_collection_name(collection_name)
            try:
                # Check if collection exists by listing all collections
                collections = self.client.get_collections()
                exists = any(c.name == full_name for c in collections.collections)

                if exists:
                    logger.info(f"Collection '{full_name}' already exists")
                else:
                    # Create collection if it doesn't exist
                    self.client.create_collection(
                        collection_name=full_name,
                        vectors_config=VectorParams(
                            size=config["size"],
                            distance=Distance.COSINE,
                        ),
                    )
                    logger.info(f"Created collection '{full_name}': {config['description']}")
            except Exception as e:
                # If listing fails, try to create anyway
                try:
                    self.client.create_collection(
                        collection_name=full_name,
                        vectors_config=VectorParams(
                            size=config["size"],
                            distance=Distance.COSINE,
                        ),
                    )
                    logger.info(f"Created collection '{full_name}': {config['description']}")
                except:
                    # Collection likely already exists
                    logger.debug(f"Collection '{full_name}' initialization handled")

    async def store_memory(
        self,
        collection: str,
        memory_id: str,
        embedding: List[float],
        content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """Store a memory in the specified collection.

        Args:
            collection: Collection name (without prefix)
            memory_id: Unique identifier for the memory
            embedding: Vector embedding of the content
            content: The actual content
            metadata: Additional metadata

        Returns:
            Success status
        """
        if collection not in self.COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")

        full_name = self._get_collection_name(collection)

        # Prepare the point (Qdrant accepts UUIDs as strings directly)
        point = PointStruct(
            id=memory_id,  # Can be a UUID string
            vector=embedding,
            payload={
                "content": content,
                "memory_id": memory_id,  # Store the original ID in payload
                "timestamp": datetime.utcnow().isoformat(),
                **metadata,
            },
        )

        try:
            self.client.upsert(
                collection_name=full_name,
                points=[point],
            )
            logger.debug(f"Stored memory {memory_id} in collection {full_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to store memory {memory_id}: {e}")
            return False

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in a collection.

        Args:
            collection: Collection name (without prefix)
            query_vector: Query embedding vector
            limit: Maximum number of results
            filters: Optional filters for metadata
            score_threshold: Minimum similarity score

        Returns:
            List of search results with content and metadata
        """
        if collection not in self.COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")

        full_name = self._get_collection_name(collection)

        # Build filter if provided
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )
            if conditions:
                qdrant_filter = Filter(must=conditions)

        try:
            results = self.client.search(
                collection_name=full_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=qdrant_filter,
                score_threshold=score_threshold,
                with_payload=True,
            )

            return [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "metadata": {
                        k: v for k, v in result.payload.items() if k != "content"
                    },
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Search failed in collection {full_name}: {e}")
            return []

    async def search_all_collections(
        self,
        query_vector: List[float],
        limit_per_collection: int = 5,
        total_limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search across all collections and aggregate results.

        Args:
            query_vector: Query embedding vector
            limit_per_collection: Max results from each collection
            total_limit: Total maximum results

        Returns:
            Aggregated and ranked results from all collections
        """
        all_results = []

        for collection_name in self.COLLECTIONS.keys():
            results = await self.search(
                collection=collection_name,
                query_vector=query_vector,
                limit=limit_per_collection,
            )

            # Add collection source to metadata
            for result in results:
                result["collection"] = collection_name
                all_results.append(result)

        # Sort by score and limit total results
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:total_limit]

    def delete_memory(self, collection: str, memory_id: str) -> bool:
        """Delete a memory from a collection.

        Args:
            collection: Collection name (without prefix)
            memory_id: ID of the memory to delete

        Returns:
            Success status
        """
        if collection not in self.COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")

        full_name = self._get_collection_name(collection)

        try:
            self.client.delete(
                collection_name=full_name,
                points_selector=[memory_id],
            )
            logger.debug(f"Deleted memory {memory_id} from collection {full_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics for a collection.

        Args:
            collection: Collection name (without prefix)

        Returns:
            Collection statistics
        """
        if collection not in self.COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")

        full_name = self._get_collection_name(collection)

        try:
            # Use count method instead of get_collection to avoid parsing issues
            count = self.client.count(collection_name=full_name)
            return {
                "name": collection,
                "vectors_count": count.count if hasattr(count, 'count') else 0,
                "indexed_vectors_count": count.count if hasattr(count, 'count') else 0,
                "status": "green",
            }
        except Exception as e:
            # Suppress verbose error logging for stats
            return {
                "name": collection,
                "vectors_count": 0,
                "status": "green"
            }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections.

        Returns:
            Dictionary of collection statistics
        """
        stats = {}
        for collection_name in self.COLLECTIONS.keys():
            stats[collection_name] = self.get_collection_stats(collection_name)
        return stats