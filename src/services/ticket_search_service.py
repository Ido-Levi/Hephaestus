"""Service for searching tickets using hybrid (semantic + keyword) approach."""

import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, MatchAny
from sqlalchemy.sql import text

from src.core.database import get_db, Ticket, TicketComment
from src.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class TicketSearchService:
    """Service for comprehensive ticket search (semantic + keyword)."""

    # Qdrant client singleton
    _qdrant_client = None
    _embedding_service = None

    @classmethod
    def _get_qdrant_client(cls) -> QdrantClient:
        """Get or create Qdrant client."""
        if cls._qdrant_client is None:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            cls._qdrant_client = QdrantClient(url=qdrant_url)
        return cls._qdrant_client

    @classmethod
    def _get_embedding_service(cls) -> EmbeddingService:
        """Get or create embedding service."""
        if cls._embedding_service is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            cls._embedding_service = EmbeddingService(openai_api_key)
        return cls._embedding_service

    @staticmethod
    async def semantic_search(
        query_text: str, workflow_id: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using Qdrant vector similarity.

        Gracefully degrades to keyword search if Qdrant is unavailable.

        Args:
            query_text: Natural language search query
            workflow_id: Workflow to search within
            limit: Max number of results
            filters: Optional filters (status, priority, type, etc.)

        Returns:
            List of ticket search results with relevance scores
        """
        try:
            # Generate embedding for query
            embedding_service = TicketSearchService._get_embedding_service()
            query_embedding = await embedding_service.generate_query_embedding(query_text)

            # Build Qdrant filter
            filter_conditions = [
                FieldCondition(key="workflow_id", match=MatchValue(value=workflow_id))
            ]

            # Add optional filters
            if filters:
                if "status" in filters:
                    if isinstance(filters["status"], list):
                        filter_conditions.append(
                            FieldCondition(key="status", match=MatchAny(any=filters["status"]))
                        )
                    else:
                        filter_conditions.append(
                            FieldCondition(key="status", match=MatchValue(value=filters["status"]))
                        )

                if "priority" in filters:
                    if isinstance(filters["priority"], list):
                        filter_conditions.append(
                            FieldCondition(key="priority", match=MatchAny(any=filters["priority"]))
                        )
                    else:
                        filter_conditions.append(
                            FieldCondition(
                                key="priority", match=MatchValue(value=filters["priority"])
                            )
                        )

                if "ticket_type" in filters:
                    if isinstance(filters["ticket_type"], list):
                        filter_conditions.append(
                            FieldCondition(
                                key="ticket_type", match=MatchAny(any=filters["ticket_type"])
                            )
                        )
                    else:
                        filter_conditions.append(
                            FieldCondition(
                                key="ticket_type", match=MatchValue(value=filters["ticket_type"])
                            )
                        )

                if "assigned_agent_id" in filters:
                    filter_conditions.append(
                        FieldCondition(
                            key="assigned_agent_id",
                            match=MatchValue(value=filters["assigned_agent_id"]),
                        )
                    )

                if "is_blocked" in filters:
                    filter_conditions.append(
                        FieldCondition(
                            key="is_blocked", match=MatchValue(value=filters["is_blocked"])
                        )
                    )

            qdrant_filter = Filter(must=filter_conditions)

            # Execute vector search
            qdrant_client = TicketSearchService._get_qdrant_client()
            search_results = qdrant_client.search(
                collection_name="hephaestus_ticket_embeddings",
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=limit,
                score_threshold=0.3,  # Lower threshold for better recall (cosine similarity)
            )

            # Format results
            results = []
            for result in search_results:
                results.append(
                    {
                        "ticket_id": result.payload["ticket_id"],
                        "title": result.payload["title"],
                        "description": result.payload["description"],
                        "status": result.payload["status"],
                        "priority": result.payload["priority"],
                        "ticket_type": result.payload["ticket_type"],
                        "relevance_score": result.score,
                        "matched_in": ["semantic"],
                        "preview": result.payload["description"][:200] + "..."
                        if len(result.payload["description"]) > 200
                        else result.payload["description"],
                        "created_at": result.payload["created_at"],
                        "assigned_agent_id": result.payload.get("assigned_agent_id"),
                        "tags": result.payload.get("tags", []),
                    }
                )

            logger.info(f"Semantic search returned {len(results)} results")
            return results

        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to keyword-only search: {e}")
            # Gracefully degrade to keyword search
            try:
                return await TicketSearchService.keyword_search(
                    keywords=query_text, workflow_id=workflow_id, limit=limit, filters=filters
                )
            except Exception as fallback_error:
                logger.error(f"Keyword fallback search also failed: {fallback_error}")
                return []

    @staticmethod
    async def keyword_search(
        keywords: str, workflow_id: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Keyword-based search using SQLite FTS5.

        Args:
            keywords: Search keywords
            workflow_id: Workflow to search within
            limit: Max number of results
            filters: Optional filters

        Returns:
            List of ticket search results with rank scores
        """
        try:
            with get_db() as db:
                # Build FTS5 query
                # Use FTS5 MATCH syntax
                fts_query = keywords

                # Query FTS5 with JOIN to tickets table
                sql = text(
                    """
                    SELECT
                        t.id as ticket_id,
                        t.title,
                        t.description,
                        t.status,
                        t.priority,
                        t.ticket_type,
                        t.created_at,
                        t.assigned_agent_id,
                        t.tags,
                        fts.rank as relevance_score
                    FROM ticket_fts fts
                    JOIN tickets t ON fts.ticket_id = t.id
                    WHERE fts.ticket_fts MATCH :query
                      AND t.workflow_id = :workflow_id
                    ORDER BY fts.rank
                    LIMIT :limit
                """
                )

                result = db.execute(
                    sql, {"query": fts_query, "workflow_id": workflow_id, "limit": limit}
                )

                rows = result.fetchall()

                # Apply additional filters if provided
                results = []
                for row in rows:
                    # Check filters
                    if filters:
                        if "status" in filters:
                            if isinstance(filters["status"], list):
                                if row.status not in filters["status"]:
                                    continue
                            elif row.status != filters["status"]:
                                continue

                        if "priority" in filters:
                            if isinstance(filters["priority"], list):
                                if row.priority not in filters["priority"]:
                                    continue
                            elif row.priority != filters["priority"]:
                                continue

                        if "ticket_type" in filters:
                            if isinstance(filters["ticket_type"], list):
                                if row.ticket_type not in filters["ticket_type"]:
                                    continue
                            elif row.ticket_type != filters["ticket_type"]:
                                continue

                    results.append(
                        {
                            "ticket_id": row.ticket_id,
                            "title": row.title,
                            "description": row.description,
                            "status": row.status,
                            "priority": row.priority,
                            "ticket_type": row.ticket_type,
                            "relevance_score": abs(float(row.relevance_score))
                            if row.relevance_score
                            else 0.0,  # FTS5 rank is negative
                            "matched_in": ["keyword"],
                            "preview": row.description[:200] + "..."
                            if len(row.description) > 200
                            else row.description,
                            "created_at": row.created_at.isoformat() + "Z"
                            if hasattr(row.created_at, "isoformat")
                            else str(row.created_at),
                            "assigned_agent_id": row.assigned_agent_id,
                            "tags": json.loads(row.tags) if row.tags else [],
                        }
                    )

                logger.info(f"Keyword search returned {len(results)} results")
                return results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    @staticmethod
    async def hybrid_search(
        query: str,
        workflow_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        include_comments: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic (70%) + keyword (30%) with RRF.

        This is the DEFAULT search mode.

        Args:
            query: Search query (natural language)
            workflow_id: Workflow to search within
            limit: Max number of results
            filters: Optional filters
            include_comments: Whether to search comments too

        Returns:
            List of ticket search results sorted by combined relevance
        """
        start_time = time.time()

        # Execute both searches
        semantic_results = await TicketSearchService.semantic_search(
            query_text=query,
            workflow_id=workflow_id,
            limit=limit * 2,  # Get more to merge
            filters=filters,
        )

        keyword_results = await TicketSearchService.keyword_search(
            keywords=query, workflow_id=workflow_id, limit=limit * 2, filters=filters
        )

        # Merge using Reciprocal Rank Fusion (RRF)
        # combined_score = (semantic_score * 0.7) + (keyword_score * 0.3)
        ticket_scores = {}

        # Add semantic scores (70% weight)
        for idx, result in enumerate(semantic_results):
            ticket_id = result["ticket_id"]
            # RRF: score = 1 / (k + rank), k=60 is standard
            rrf_score = 1.0 / (60 + idx + 1)
            ticket_scores[ticket_id] = {
                "semantic_score": rrf_score * 0.7,
                "keyword_score": 0.0,
                "data": result,
            }

        # Add keyword scores (30% weight)
        for idx, result in enumerate(keyword_results):
            ticket_id = result["ticket_id"]
            rrf_score = 1.0 / (60 + idx + 1)

            if ticket_id in ticket_scores:
                ticket_scores[ticket_id]["keyword_score"] = rrf_score * 0.3
                # Merge matched_in
                ticket_scores[ticket_id]["data"]["matched_in"] = ["semantic", "keyword"]
            else:
                ticket_scores[ticket_id] = {
                    "semantic_score": 0.0,
                    "keyword_score": rrf_score * 0.3,
                    "data": result,
                }

        # Calculate combined scores and sort
        merged_results = []
        for ticket_id, scores in ticket_scores.items():
            combined_score = scores["semantic_score"] + scores["keyword_score"]
            result_data = scores["data"]
            result_data["relevance_score"] = combined_score
            merged_results.append(result_data)

        # Sort by combined score (descending)
        merged_results.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Return top limit results
        final_results = merged_results[:limit]

        search_time_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Hybrid search for '{query[:50]}...' in workflow {workflow_id}: "
            f"{len(final_results)} results in {search_time_ms}ms "
            f"(from {len(semantic_results)} semantic + {len(keyword_results)} keyword)"
        )
        return final_results

    @staticmethod
    async def find_related_tickets(ticket_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find semantically similar tickets for duplicate detection and context.

        Args:
            ticket_id: Ticket to find related tickets for
            limit: Max number of related tickets

        Returns:
            List of related tickets with similarity scores
        """
        try:
            # Get ticket embedding from database
            with get_db() as db:
                ticket = db.query(Ticket).filter_by(id=ticket_id).first()
                if not ticket:
                    logger.warning(f"Ticket not found: {ticket_id}")
                    return []

                if not ticket.embedding:
                    logger.warning(f"Ticket {ticket_id} has no embedding")
                    return []

                query_embedding = ticket.embedding

            # Search in Qdrant for similar tickets (exclude this ticket)
            qdrant_client = TicketSearchService._get_qdrant_client()

            # Build filter to exclude this ticket
            filter_conditions = [
                FieldCondition(key="workflow_id", match=MatchValue(value=ticket.workflow_id))
            ]

            search_results = qdrant_client.search(
                collection_name="hephaestus_ticket_embeddings",
                query_vector=query_embedding,
                query_filter=Filter(must=filter_conditions),
                limit=limit + 1,  # +1 because we'll filter out the query ticket
            )

            # Format results and classify relation type
            results = []
            for result in search_results:
                # Skip the query ticket itself
                if result.payload["ticket_id"] == ticket_id:
                    continue

                # Classify relation type based on similarity score
                if result.score >= 0.9:
                    relation_type = "duplicate"
                elif result.score >= 0.7:
                    relation_type = "related"
                elif result.score >= 0.5:
                    relation_type = "similar"
                else:
                    continue  # Skip low similarity

                results.append(
                    {
                        "ticket_id": result.payload["ticket_id"],
                        "title": result.payload["title"],
                        "similarity_score": result.score,
                        "relation_type": relation_type,
                        "status": result.payload["status"],
                        "priority": result.payload["priority"],
                    }
                )

            logger.info(f"Found {len(results)} related tickets for {ticket_id}")
            return results[:limit]

        except Exception as e:
            logger.error(f"Find related tickets failed: {e}")
            return []

    @staticmethod
    async def index_ticket(
        ticket_id: str,
        title: str,
        description: str,
        comments: List[str],
        workflow_id: str,
        ticket_type: str,
        priority: str,
        status: str,
        tags: List[str],
        created_at: str,
        updated_at: str,
        created_by_agent_id: str,
        assigned_agent_id: Optional[str],
        is_blocked: bool,
    ) -> str:
        """
        Index ticket in Qdrant vector store.

        Args:
            All ticket metadata for payload

        Returns:
            Embedding ID (Qdrant point ID)
        """
        try:
            # Generate embedding
            embedding_service = TicketSearchService._get_embedding_service()
            embedding = await embedding_service.generate_ticket_embedding(
                title=title, description=description, tags=tags
            )

            # Prepare payload
            payload = {
                "ticket_id": ticket_id,
                "workflow_id": workflow_id,
                "title": title,
                "description": description,
                "ticket_type": ticket_type,
                "priority": priority,
                "status": status,
                "tags": tags,
                "created_at": created_at,
                "updated_at": updated_at,
                "created_by_agent_id": created_by_agent_id,
                "assigned_agent_id": assigned_agent_id,
                "comment_texts": comments,
                "is_blocked": is_blocked,
            }

            # Store in Qdrant
            qdrant_client = TicketSearchService._get_qdrant_client()

            # Use ticket_id as the point ID
            # Strip "ticket-" prefix to get pure UUID for Qdrant (Qdrant only accepts UUIDs without prefix)
            point_id = ticket_id.replace("ticket-", "")
            point = PointStruct(id=point_id, vector=embedding, payload=payload)

            qdrant_client.upsert(collection_name="hephaestus_ticket_embeddings", points=[point])

            logger.info(f"Indexed ticket {ticket_id} in Qdrant with point_id {point_id}")
            return point_id

        except Exception as e:
            logger.error(f"Failed to index ticket {ticket_id}: {e}")
            raise

    @staticmethod
    async def reindex_ticket(ticket_id: str) -> str:
        """
        Regenerate and update embedding for existing ticket.

        Called when title/description changes or every 5 comments.

        Args:
            ticket_id: Ticket to reindex

        Returns:
            New embedding ID
        """
        try:
            # Fetch ticket from database and extract all needed data while in session
            with get_db() as db:
                ticket = db.query(Ticket).filter_by(id=ticket_id).first()
                if not ticket:
                    raise ValueError(f"Ticket not found: {ticket_id}")

                # Get comments
                comments = (
                    db.query(TicketComment)
                    .filter_by(ticket_id=ticket_id)
                    .order_by(TicketComment.created_at.desc())
                    .limit(5)
                    .all()
                )

                comment_texts = [c.comment_text for c in comments]

                # Extract all ticket data while still in session
                title = ticket.title
                description = ticket.description
                tags = ticket.tags or []
                workflow_id = ticket.workflow_id
                ticket_type = ticket.ticket_type
                priority = ticket.priority
                status = ticket.status
                created_at = ticket.created_at.isoformat() + "Z"
                updated_at = ticket.updated_at.isoformat() + "Z"
                created_by_agent_id = ticket.created_by_agent_id
                assigned_agent_id = ticket.assigned_agent_id
                is_blocked = bool(ticket.blocked_by_ticket_ids and len(ticket.blocked_by_ticket_ids) > 0)

            # Generate new embedding
            embedding_service = TicketSearchService._get_embedding_service()
            embedding = await embedding_service.generate_ticket_embedding(
                title=title, description=description, tags=tags
            )

            # Update in Qdrant
            qdrant_client = TicketSearchService._get_qdrant_client()

            payload = {
                "ticket_id": ticket_id,
                "workflow_id": workflow_id,
                "title": title,
                "description": description,
                "ticket_type": ticket_type,
                "priority": priority,
                "status": status,
                "tags": tags,
                "created_at": created_at,
                "updated_at": updated_at,
                "created_by_agent_id": created_by_agent_id,
                "assigned_agent_id": assigned_agent_id,
                "comment_texts": comment_texts,
                "is_blocked": is_blocked,
            }

            # Strip "ticket-" prefix to get pure UUID for Qdrant
            point_id = ticket_id.replace("ticket-", "")
            point = PointStruct(id=point_id, vector=embedding, payload=payload)

            qdrant_client.upsert(collection_name="hephaestus_ticket_embeddings", points=[point])

            # Update ticket record in database
            with get_db() as db:
                ticket = db.query(Ticket).filter_by(id=ticket_id).first()
                ticket.embedding = embedding
                ticket.embedding_id = point_id
                ticket.updated_at = datetime.utcnow()
                db.commit()

            logger.info(f"Reindexed ticket {ticket_id} with point_id {point_id}")
            return point_id

        except Exception as e:
            logger.error(f"Failed to reindex ticket {ticket_id}: {e}")
            raise
