"""Service for generating and comparing embeddings for task deduplication."""

import numpy as np
import openai
from typing import List, Dict, Any, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.core.simple_config import get_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and comparing embeddings."""

    def __init__(self, openai_api_key: str):
        """Initialize the embedding service.

        Args:
            openai_api_key: OpenAI API key for generating embeddings
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.config = get_config()
        self.model = self.config.task_embedding_model
        logger.info(f"Initialized EmbeddingService with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(
            (openai.APIError, openai.APIConnectionError, openai.RateLimitError)
        ),
        reraise=True,
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI's text-embedding model.

        Retries up to 3 times with exponential backoff for API errors.

        Args:
            text: Text to generate embedding for

        Returns:
            List of floats representing the embedding vector

        Raises:
            Exception: If embedding generation fails after retries
        """
        try:
            # Truncate text if too long (max ~8000 tokens for most models)
            max_chars = 30000  # Conservative limit
            if len(text) > max_chars:
                logger.warning(f"Text truncated from {len(text)} to {max_chars} characters")
                text = text[:max_chars]

            response = self.client.embeddings.create(
                model=self.model, input=text, encoding_format="float"
            )

            embedding = response.data[0].embedding
            logger.info(f"Generated embedding with dimension: {len(embedding)}")
            return embedding

        except (openai.APIError, openai.APIConnectionError, openai.RateLimitError) as e:
            logger.warning(f"OpenAI API error (will retry): {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity score between -1 and 1
        """
        # Handle edge cases
        if not vec1 or not vec2:
            logger.warning("Empty vector provided for similarity calculation")
            return 0.0

        if len(vec1) != len(vec2):
            logger.warning(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")
            return 0.0

        try:
            # Convert to numpy arrays for efficient computation
            arr1 = np.array(vec1, dtype=np.float32)
            arr2 = np.array(vec2, dtype=np.float32)

            # Calculate norms
            norm_a = np.linalg.norm(arr1)
            norm_b = np.linalg.norm(arr2)

            # Handle zero vectors
            if norm_a == 0 or norm_b == 0:
                logger.warning("Zero vector provided for similarity calculation")
                return 0.0

            # Calculate cosine similarity
            similarity = np.dot(arr1, arr2) / (norm_a * norm_b)

            # Ensure result is in valid range (floating point errors can cause slight overflow)
            similarity = np.clip(similarity, -1.0, 1.0)

            return float(similarity)

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def calculate_batch_similarities(
        self, query_embedding: List[float], embeddings: List[List[float]]
    ) -> List[float]:
        """Calculate cosine similarities between a query and multiple embeddings efficiently.

        Args:
            query_embedding: Query embedding vector
            embeddings: List of embedding vectors to compare against

        Returns:
            List of similarity scores
        """
        if not embeddings:
            return []

        try:
            # Convert to numpy arrays
            query_arr = np.array(query_embedding, dtype=np.float32)
            embeddings_arr = np.array(embeddings, dtype=np.float32)

            # Normalize query
            query_norm = np.linalg.norm(query_arr)
            if query_norm == 0:
                return [0.0] * len(embeddings)
            query_normalized = query_arr / query_norm

            # Normalize embeddings
            norms = np.linalg.norm(embeddings_arr, axis=1)
            # Avoid division by zero
            norms[norms == 0] = 1.0
            embeddings_normalized = embeddings_arr / norms[:, np.newaxis]

            # Calculate dot products (cosine similarities)
            similarities = np.dot(embeddings_normalized, query_normalized)

            # Clip to valid range and convert to list
            similarities = np.clip(similarities, -1.0, 1.0)
            return similarities.tolist()

        except Exception as e:
            logger.error(f"Error in batch similarity calculation: {e}")
            # Fallback to individual calculations
            return [self.calculate_cosine_similarity(query_embedding, emb) for emb in embeddings]

    async def generate_ticket_embedding(
        self, title: str, description: str, tags: List[str]
    ) -> List[float]:
        """
        Generate weighted embedding for ticket content.

        Weighting strategy:
        - Title: 2x weight (repeat title twice in input)
        - Description: 1x weight
        - Tags: 1.5x weight (repeat tags approximately 1.5x)

        Args:
            title: Ticket title
            description: Ticket description
            tags: List of tags

        Returns:
            Embedding vector (dimension depends on configured model)
        """
        # Combine with weights
        # Title gets 2x weight, tags get ~1.5x weight
        tag_text = " ".join(tags)
        weighted_text = f"{title} {title} {description} {tag_text} {tag_text}"

        logger.debug(f"Generating weighted ticket embedding (title 2x, tags 1.5x)")
        return await self.generate_embedding(weighted_text)

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector (same dimension as ticket embeddings)
        """
        logger.debug(f"Generating query embedding for: {query[:100]}...")
        return await self.generate_embedding(query)
