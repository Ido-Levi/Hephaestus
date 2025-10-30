"""Service for detecting duplicate and related tasks based on embeddings."""

from typing import Dict, List, Optional, Any, Tuple
import logging
import json
from sqlalchemy.orm import Session
from src.core.database import Task, DatabaseManager
from src.services.embedding_service import EmbeddingService
from src.core.simple_config import get_config

logger = logging.getLogger(__name__)


class TaskSimilarityService:
    """Service for detecting duplicate and related tasks."""

    def __init__(self, db_manager: DatabaseManager, embedding_service: EmbeddingService):
        """Initialize the task similarity service.

        Args:
            db_manager: Database manager for accessing tasks
            embedding_service: Service for generating and comparing embeddings
        """
        self.db_manager = db_manager
        self.embedding_service = embedding_service
        self.config = get_config()
        logger.info(
            f"Initialized TaskSimilarityService with thresholds: "
            f"duplicate={self.config.task_similarity_threshold}, "
            f"related={self.config.task_related_threshold}"
        )

    async def check_for_duplicates(
        self,
        task_description: str,
        task_embedding: List[float],
        phase_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if task is duplicate or related to existing tasks.

        Args:
            task_description: Description of the new task
            task_embedding: Embedding vector of the new task
            phase_id: Phase ID of the new task (only check duplicates within same phase)

        Returns:
            Dictionary containing:
                - is_duplicate: Whether task is a duplicate
                - duplicate_of: ID of the original task if duplicate
                - duplicate_description: Description of the original task
                - related_tasks: List of related task IDs
                - related_tasks_details: Details of related tasks
                - max_similarity: Maximum similarity score found
        """
        session = self.db_manager.get_session()
        try:
            # Build query for existing tasks
            query = session.query(Task).filter(
                Task.embedding != None,
                Task.status.notin_(['failed', 'duplicated'])
            )

            # If phase_id is provided, only check tasks within the same phase
            # This ensures tasks from different phases are never considered duplicates
            if phase_id is not None:
                query = query.filter(Task.phase_id == phase_id)
                logger.info(f"Checking for duplicates within phase: {phase_id}")
            else:
                # If no phase_id, only check tasks without a phase
                query = query.filter(Task.phase_id == None)
                logger.info("Checking for duplicates among tasks without phase")

            existing_tasks = query.all()

            logger.debug(f"Comparing against {len(existing_tasks)} existing tasks")

            if not existing_tasks:
                return {
                    'is_duplicate': False,
                    'duplicate_of': None,
                    'duplicate_description': None,
                    'related_tasks': [],
                    'related_tasks_details': [],
                    'max_similarity': 0.0
                }

            # Prepare embeddings for batch comparison
            existing_embeddings = []
            valid_tasks = []
            for task in existing_tasks:
                if task.embedding:
                    # Handle JSON stored embeddings
                    if isinstance(task.embedding, str):
                        try:
                            embedding = json.loads(task.embedding)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse embedding for task {task.id}")
                            continue
                    else:
                        embedding = task.embedding

                    existing_embeddings.append(embedding)
                    valid_tasks.append(task)

            if not valid_tasks:
                return {
                    'is_duplicate': False,
                    'duplicate_of': None,
                    'duplicate_description': None,
                    'related_tasks': [],
                    'related_tasks_details': [],
                    'max_similarity': 0.0
                }

            # Calculate similarities in batch for efficiency
            similarities = self.embedding_service.calculate_batch_similarities(
                task_embedding,
                existing_embeddings
            )

            # Find duplicate and related tasks
            duplicate_task = None
            max_similarity = 0.0
            related_tasks = []

            for task, similarity in zip(valid_tasks, similarities):
                if similarity > max_similarity:
                    max_similarity = similarity
                    if similarity > self.config.task_similarity_threshold:
                        duplicate_task = task

                # Check for related tasks (not duplicates)
                if (similarity > self.config.task_related_threshold and
                    similarity <= self.config.task_similarity_threshold):
                    related_tasks.append({
                        'task_id': task.id,
                        'description': task.enriched_description or task.raw_description,
                        'similarity': similarity,
                        'status': task.status,
                        'created_at': task.created_at.isoformat() if task.created_at else None
                    })

            # Sort related tasks by similarity (highest first)
            related_tasks.sort(key=lambda x: x['similarity'], reverse=True)

            # Limit to top 10 related tasks
            related_tasks = related_tasks[:10]

            result = {
                'is_duplicate': duplicate_task is not None,
                'duplicate_of': duplicate_task.id if duplicate_task else None,
                'duplicate_description': (
                    duplicate_task.enriched_description or duplicate_task.raw_description
                ) if duplicate_task else None,
                'related_tasks': [t['task_id'] for t in related_tasks],
                'related_tasks_details': related_tasks,
                'max_similarity': max_similarity
            }

            if result['is_duplicate']:
                logger.info(
                    f"Found duplicate task: {result['duplicate_of']} "
                    f"with similarity {max_similarity:.3f} in phase {phase_id}"
                )
            elif max_similarity > self.config.task_similarity_threshold:
                logger.info(
                    f"High similarity ({max_similarity:.3f}) found but not in same phase "
                    f"(current phase: {phase_id})"
                )
            elif result['related_tasks']:
                logger.info(f"Found {len(result['related_tasks'])} related tasks")

            return result

        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            # Return safe default on error
            return {
                'is_duplicate': False,
                'duplicate_of': None,
                'duplicate_description': None,
                'related_tasks': [],
                'related_tasks_details': [],
                'max_similarity': 0.0,
                'error': str(e)
            }
        finally:
            session.close()

    async def store_task_embedding(
        self,
        task_id: str,
        embedding: List[float],
        related_task_ids: Optional[List[str]] = None,
        related_tasks_details: Optional[List[Dict[str, Any]]] = None,
        duplicate_of: Optional[str] = None,
        similarity_score: Optional[float] = None
    ):
        """Store embedding and relationship information for a task.

        Args:
            task_id: ID of the task
            embedding: Embedding vector to store
            related_task_ids: List of related task IDs (deprecated, use related_tasks_details)
            related_tasks_details: List of dicts with task_id and similarity
            duplicate_of: ID of the original task if this is a duplicate
            similarity_score: Similarity score to the original task
        """
        session = self.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                # Store embedding as JSON
                task.embedding = embedding

                # Store relationships with similarity scores
                if related_tasks_details:
                    # Store as list of dicts with id and similarity
                    task.related_task_ids = [
                        {"id": t["task_id"], "similarity": t["similarity"]}
                        for t in related_tasks_details
                    ]
                elif related_task_ids:
                    # Fallback for backward compatibility
                    task.related_task_ids = related_task_ids

                if duplicate_of:
                    task.duplicate_of_task_id = duplicate_of
                    task.similarity_score = similarity_score

                session.commit()
                logger.debug(f"Stored embedding for task {task_id}")
            else:
                logger.warning(f"Task {task_id} not found when storing embedding")

        except Exception as e:
            logger.error(f"Error storing task embedding: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    async def get_task_relationships(self, task_id: str) -> Dict[str, Any]:
        """Get duplicate and related task information for a task.

        Args:
            task_id: ID of the task

        Returns:
            Dictionary containing duplicate and related task information
        """
        session = self.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                return {'error': 'Task not found'}

            result = {
                'task_id': task_id,
                'is_duplicate': task.duplicate_of_task_id is not None,
                'duplicate_of': task.duplicate_of_task_id,
                'similarity_score': task.similarity_score,
                'related_tasks': []
            }

            # Get details of duplicate task if exists
            if task.duplicate_of_task_id:
                original = session.query(Task).filter_by(id=task.duplicate_of_task_id).first()
                if original:
                    result['duplicate_details'] = {
                        'id': original.id,
                        'description': original.enriched_description or original.raw_description,
                        'status': original.status,
                        'created_at': original.created_at.isoformat() if original.created_at else None
                    }

            # Get details of related tasks
            if task.related_task_ids:
                related_ids = task.related_task_ids
                if isinstance(related_ids, str):
                    try:
                        related_ids = json.loads(related_ids)
                    except json.JSONDecodeError:
                        related_ids = []

                for related_id in related_ids:
                    related_task = session.query(Task).filter_by(id=related_id).first()
                    if related_task:
                        result['related_tasks'].append({
                            'id': related_task.id,
                            'description': (
                                related_task.enriched_description or
                                related_task.raw_description
                            ),
                            'status': related_task.status
                        })

            return result

        except Exception as e:
            logger.error(f"Error getting task relationships: {e}")
            return {'error': str(e)}
        finally:
            session.close()

    async def find_similar_tasks(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Find tasks similar to a query string.

        Args:
            query: Query string to search for
            limit: Maximum number of results
            threshold: Minimum similarity threshold

        Returns:
            List of similar tasks with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_service.generate_embedding(query)

            session = self.db_manager.get_session()
            try:
                # Get all tasks with embeddings
                tasks = session.query(Task).filter(
                    Task.embedding != None,
                    Task.status != 'duplicated'
                ).all()

                if not tasks:
                    return []

                # Calculate similarities
                results = []
                for task in tasks:
                    if task.embedding:
                        # Parse embedding if stored as string
                        if isinstance(task.embedding, str):
                            try:
                                embedding = json.loads(task.embedding)
                            except json.JSONDecodeError:
                                continue
                        else:
                            embedding = task.embedding

                        similarity = self.embedding_service.calculate_cosine_similarity(
                            query_embedding,
                            embedding
                        )

                        if similarity >= threshold:
                            results.append({
                                'task_id': task.id,
                                'description': task.enriched_description or task.raw_description,
                                'similarity': similarity,
                                'status': task.status,
                                'created_at': task.created_at.isoformat() if task.created_at else None
                            })

                # Sort by similarity and limit results
                results.sort(key=lambda x: x['similarity'], reverse=True)
                return results[:limit]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error finding similar tasks: {e}")
            return []