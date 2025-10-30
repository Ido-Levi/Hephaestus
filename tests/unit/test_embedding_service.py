"""Unit tests for the EmbeddingService."""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from src.services.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for EmbeddingService."""

    @pytest.fixture
    def embedding_service(self):
        """Create an EmbeddingService instance for testing."""
        with patch('src.services.embedding_service.openai.OpenAI'):
            service = EmbeddingService("test-api-key")
            return service

    @pytest.fixture
    def sample_embedding(self):
        """Generate a sample embedding vector."""
        # Create a normalized random vector
        vec = np.random.randn(3072)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_service, sample_embedding):
        """Test successful embedding generation returns correct dimension."""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=sample_embedding)]
        embedding_service.client.embeddings.create = MagicMock(return_value=mock_response)

        # Generate embedding
        result = await embedding_service.generate_embedding("Test task description")

        # Verify
        assert len(result) == 3072
        assert result == sample_embedding
        embedding_service.client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-large",
            input="Test task description",
            encoding_format="float"
        )

    @pytest.mark.asyncio
    async def test_generate_embedding_with_long_text(self, embedding_service, sample_embedding):
        """Test that long text is truncated properly."""
        # Create very long text
        long_text = "x" * 50000

        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=sample_embedding)]
        embedding_service.client.embeddings.create = MagicMock(return_value=mock_response)

        # Generate embedding
        result = await embedding_service.generate_embedding(long_text)

        # Verify text was truncated
        call_args = embedding_service.client.embeddings.create.call_args
        assert len(call_args[1]['input']) == 30000  # Max chars limit
        assert len(result) == 3072

    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, embedding_service):
        """Test error handling for API failures."""
        # Mock API error
        embedding_service.client.embeddings.create = MagicMock(
            side_effect=Exception("API Error")
        )

        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            await embedding_service.generate_embedding("Test text")
        assert "API Error" in str(exc_info.value)

    def test_cosine_similarity_identical_vectors(self, embedding_service):
        """Test cosine similarity of identical vectors returns 1.0."""
        vec = [1.0, 2.0, 3.0, 4.0, 5.0]
        similarity = embedding_service.calculate_cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self, embedding_service):
        """Test cosine similarity of orthogonal vectors returns 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = embedding_service.calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity) < 1e-6

    def test_cosine_similarity_opposite_vectors(self, embedding_service):
        """Test cosine similarity of opposite vectors returns -1.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        similarity = embedding_service.calculate_cosine_similarity(vec1, vec2)
        assert abs(similarity + 1.0) < 1e-6

    def test_cosine_similarity_empty_vectors(self, embedding_service):
        """Test handling of empty vectors."""
        similarity = embedding_service.calculate_cosine_similarity([], [])
        assert similarity == 0.0

        similarity = embedding_service.calculate_cosine_similarity([1, 2, 3], [])
        assert similarity == 0.0

    def test_cosine_similarity_different_dimensions(self, embedding_service):
        """Test handling of vectors with different dimensions."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        similarity = embedding_service.calculate_cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_cosine_similarity_zero_vectors(self, embedding_service):
        """Test handling of zero vectors."""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        similarity = embedding_service.calculate_cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_calculate_batch_similarities_empty(self, embedding_service):
        """Test batch similarity calculation with empty embeddings."""
        query = [1.0, 2.0, 3.0]
        similarities = embedding_service.calculate_batch_similarities(query, [])
        assert similarities == []

    def test_calculate_batch_similarities_single(self, embedding_service):
        """Test batch similarity calculation with single embedding."""
        query = [1.0, 0.0, 0.0]
        embeddings = [[1.0, 0.0, 0.0]]
        similarities = embedding_service.calculate_batch_similarities(query, embeddings)
        assert len(similarities) == 1
        assert abs(similarities[0] - 1.0) < 1e-6

    def test_calculate_batch_similarities_multiple(self, embedding_service):
        """Test batch similarity calculation with multiple embeddings."""
        query = [1.0, 0.0, 0.0]
        embeddings = [
            [1.0, 0.0, 0.0],   # Identical
            [0.0, 1.0, 0.0],   # Orthogonal
            [-1.0, 0.0, 0.0],  # Opposite
            [0.7071, 0.7071, 0.0]  # 45 degrees
        ]
        similarities = embedding_service.calculate_batch_similarities(query, embeddings)

        assert len(similarities) == 4
        assert abs(similarities[0] - 1.0) < 1e-6      # Identical
        assert abs(similarities[1] - 0.0) < 1e-6      # Orthogonal
        assert abs(similarities[2] - (-1.0)) < 1e-6   # Opposite
        assert abs(similarities[3] - 0.7071) < 1e-3   # 45 degrees

    def test_calculate_batch_similarities_normalization(self, embedding_service):
        """Test that batch similarities are properly normalized."""
        query = [2.0, 0.0, 0.0]  # Not normalized
        embeddings = [
            [3.0, 0.0, 0.0],   # Not normalized but same direction
            [0.0, 5.0, 0.0],   # Different direction, not normalized
        ]
        similarities = embedding_service.calculate_batch_similarities(query, embeddings)

        # Should still get correct cosine similarities
        assert abs(similarities[0] - 1.0) < 1e-6  # Same direction
        assert abs(similarities[1] - 0.0) < 1e-6  # Orthogonal

    def test_calculate_batch_similarities_with_zero_vector(self, embedding_service):
        """Test batch calculation handles zero vectors gracefully."""
        query = [1.0, 2.0, 3.0]
        embeddings = [
            [1.0, 2.0, 3.0],
            [0.0, 0.0, 0.0],  # Zero vector
            [2.0, 4.0, 6.0],
        ]
        similarities = embedding_service.calculate_batch_similarities(query, embeddings)

        assert len(similarities) == 3
        assert abs(similarities[0] - 1.0) < 1e-6  # Identical
        assert similarities[1] == 0.0  # Zero vector
        assert abs(similarities[2] - 1.0) < 1e-6  # Same direction

    @patch('src.services.embedding_service.logger')
    def test_calculate_batch_similarities_error_fallback(self, mock_logger, embedding_service):
        """Test that batch calculation falls back to individual on error."""
        query = [1.0, 0.0]

        # Mock numpy to raise error
        with patch('numpy.array', side_effect=Exception("Numpy error")):
            embeddings = [[1.0, 0.0], [0.0, 1.0]]
            similarities = embedding_service.calculate_batch_similarities(query, embeddings)

            # Should still get results from fallback
            assert len(similarities) == 2
            assert abs(similarities[0] - 1.0) < 1e-6
            assert abs(similarities[1] - 0.0) < 1e-6

            # Should log error
            mock_logger.error.assert_called()