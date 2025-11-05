"""Unit tests for multi-provider LLM functionality."""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_config import (
    SimpleConfig,
    MultiProviderLLMConfig,
    ModelAssignment,
    ProviderConfig
)
from src.interfaces.langchain_llm_client import (
    LangChainLLMClient,
    ComponentType
)
from src.interfaces.multi_provider_llm import MultiProviderLLM


class TestLLMConfig:
    """Test configuration management."""

    def test_load_config(self, tmp_path):
        """Test loading configuration from YAML."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
llm:
  embedding_model: "text-embedding-3-small"
  providers:
    openai:
      api_key_env: "OPENAI_API_KEY"
      models:
        - "gpt-5-nano"
    groq:
      api_key_env: "GROQ_API_KEY"
      models:
        - "llama3-8b-8192"
  model_assignments:
    task_enrichment:
      provider: "openai"
      model: "gpt-5-nano"
      temperature: 0.7
      max_tokens: 2000
""")

        config = SimpleConfig(str(config_file))
        llm_config = config.get_llm_config()

        assert llm_config.embedding_model == "text-embedding-3-small"
        assert "openai" in llm_config.providers
        assert "groq" in llm_config.providers
        assert "task_enrichment" in llm_config.model_assignments

        task_assignment = llm_config.model_assignments["task_enrichment"]
        assert task_assignment.provider == "openai"
        assert task_assignment.model == "gpt-5-nano"
        assert task_assignment.temperature == 0.7

    def test_validate_config_strict(self, tmp_path):
        """Test strict validation raises errors for missing API keys."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
llm:
  providers:
    openai:
      api_key_env: "NONEXISTENT_KEY"
      models: ["gpt-5-nano"]
  model_assignments:
    task_enrichment:
      provider: "openai"
      model: "gpt-5-nano"
""")

        config = SimpleConfig(str(config_file))

        with pytest.raises(ValueError) as excinfo:
            config.validate(strict=True)
        assert "Missing API keys" in str(excinfo.value)

    def test_validate_config_non_strict(self, tmp_path, caplog):
        """Test non-strict validation logs warnings for missing API keys."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
llm:
  providers:
    openai:
      api_key_env: "NONEXISTENT_KEY"
      models: ["gpt-5-nano"]
  model_assignments:
    task_enrichment:
      provider: "openai"
      model: "gpt-5-nano"
""")

        config = SimpleConfig(str(config_file))
        config.validate(strict=False)  # Should not raise

        # Check that warning was logged
        assert "Some API keys are missing" in caplog.text

    def test_openrouter_provider_config(self, tmp_path):
        """Test OpenRouter configuration with provider parameter."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
llm:
  providers:
    openrouter:
      api_key_env: "OPENROUTER_API_KEY"
      base_url: "https://openrouter.ai/api/v1"
      models:
        - provider: "cerebras"
          model: "openai/gpt-oss-120b"
  model_assignments:
    guardian_analysis:
      provider: "openrouter"
      openrouter_provider: "cerebras"
      model: "openai/gpt-oss-120b"
      temperature: 0.5
      max_tokens: 3000
""")

        config = SimpleConfig(str(config_file))
        llm_config = config.get_llm_config()

        guardian_assignment = llm_config.model_assignments["guardian_analysis"]
        assert guardian_assignment.provider == "openrouter"
        assert guardian_assignment.openrouter_provider == "cerebras"
        assert guardian_assignment.model == "openai/gpt-oss-120b"


class TestLangChainLLMClient:
    """Test LangChain LLM client."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return MultiProviderLLMConfig(
            embedding_model="text-embedding-3-small",
            providers={
                "openai": ProviderConfig(
                    api_key_env="OPENAI_API_KEY",
                    models=["gpt-5-nano"]
                ),
                "groq": ProviderConfig(
                    api_key_env="GROQ_API_KEY",
                    models=["openai/gpt-oss-120b", "llama3-8b-8192"]
                ),
                "openrouter": ProviderConfig(
                    api_key_env="OPENROUTER_API_KEY",
                    base_url="https://openrouter.ai/api/v1",
                    models=[{"provider": "cerebras", "model": "openai/gpt-oss-120b"}]
                )
            },
            model_assignments={
                "task_enrichment": ModelAssignment(
                    provider="openai",
                    model="gpt-5-nano",
                    temperature=0.7,
                    max_tokens=2000
                ),
                "agent_monitoring": ModelAssignment(
                    provider="groq",
                    model="openai/gpt-oss-120b",
                    temperature=0.3,
                    max_tokens=2000
                ),
                "guardian_analysis": ModelAssignment(
                    provider="openrouter",
                    openrouter_provider="cerebras",
                    model="openai/gpt-oss-120b",
                    temperature=0.5,
                    max_tokens=3000
                )
            }
        )

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-openai-key",
        "GROQ_API_KEY": "test-groq-key",
        "OPENROUTER_API_KEY": "test-openrouter-key"
    })
    def test_initialize_models(self, mock_config):
        """Test model initialization."""
        with patch('src.interfaces.langchain_llm_client.ChatOpenAI') as MockOpenAI, \
             patch('src.interfaces.langchain_llm_client.ChatGroq') as MockGroq, \
             patch('src.interfaces.langchain_llm_client.OpenAIEmbeddings') as MockEmbeddings:

            client = LangChainLLMClient(mock_config)

            # Check embedding model initialized
            MockEmbeddings.assert_called_once_with(
                model="text-embedding-3-small",
                openai_api_key="test-openai-key"
            )

            # Check models created for each component
            assert len(client._models) > 0

    def test_get_model_for_component(self, mock_config):
        """Test getting model for specific component."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GROQ_API_KEY": "test-key",
            "OPENROUTER_API_KEY": "test-key"
        }):
            with patch('src.interfaces.langchain_llm_client.ChatOpenAI'), \
                 patch('src.interfaces.langchain_llm_client.ChatGroq'):

                client = LangChainLLMClient(mock_config)

                # Test getting model for task enrichment
                model = client._get_model_for_component(ComponentType.TASK_ENRICHMENT)
                assert model is not None

    def test_get_model_name(self, mock_config):
        """Test getting model name for component."""
        client = LangChainLLMClient(mock_config)

        # Test OpenAI model
        name = client.get_model_name(ComponentType.TASK_ENRICHMENT)
        assert name == "gpt-5-nano"

        # Test Groq model
        name = client.get_model_name(ComponentType.AGENT_MONITORING)
        assert name == "openai/gpt-oss-120b"

        # Test OpenRouter with provider
        name = client.get_model_name(ComponentType.GUARDIAN_ANALYSIS)
        assert name == "openai/gpt-oss-120b (via cerebras)"

    @pytest.mark.asyncio
    async def test_generate_embedding(self, mock_config):
        """Test embedding generation."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            mock_embeddings = AsyncMock()
            mock_embeddings.aembed_query.return_value = [0.1] * 1536

            with patch('src.interfaces.langchain_llm_client.OpenAIEmbeddings',
                      return_value=mock_embeddings):
                client = LangChainLLMClient(mock_config)
                client._embedding_model = mock_embeddings

                embedding = await client.generate_embedding("test text")

                assert len(embedding) == 1536
                mock_embeddings.aembed_query.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_fallback_behavior(self, mock_config):
        """Test fallback behavior when model unavailable."""
        # Remove all API keys
        with patch.dict(os.environ, {}, clear=True):
            client = LangChainLLMClient(mock_config)

            # Should return default values when models not available
            result = await client.enrich_task(
                "Test task",
                "Task done",
                ["context"]
            )

            assert result["enriched_description"] == "Test task"
            assert result["completion_criteria"] == ["Task done"]
            assert result["estimated_complexity"] == 5


class TestMultiProviderLLM:
    """Test multi-provider LLM interface."""

    @pytest.fixture
    def mock_client(self):
        """Create mock LangChain client."""
        client = Mock(spec=LangChainLLMClient)
        client.enrich_task = AsyncMock(return_value={
            "enriched_description": "Enriched task",
            "completion_criteria": ["Done"],
            "estimated_complexity": 5
        })
        client.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        client.analyze_agent_state = AsyncMock(return_value={
            "state": "healthy",
            "decision": "continue"
        })
        client.analyze_agent_trajectory = AsyncMock(return_value={
            "trajectory_aligned": True,
            "alignment_score": 0.8
        })
        client.analyze_system_coherence = AsyncMock(return_value={
            "coherence_score": 0.9
        })
        client.generate_agent_prompt = AsyncMock(return_value="Agent prompt")
        client.get_model_name = Mock(return_value="test-model")
        return client

    @pytest.mark.asyncio
    async def test_enrich_task(self, mock_client, tmp_path):
        """Test task enrichment."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("llm: {}")

        with patch('src.interfaces.multi_provider_llm.LangChainLLMClient',
                  return_value=mock_client):
            llm = MultiProviderLLM(str(config_file))

            result = await llm.enrich_task(
                "Test task",
                "Done definition",
                ["context"],
                "phase context"
            )

            assert result["enriched_description"] == "Enriched task"
            mock_client.enrich_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding(self, mock_client, tmp_path):
        """Test embedding generation."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("llm: {}")

        with patch('src.interfaces.multi_provider_llm.LangChainLLMClient',
                  return_value=mock_client):
            llm = MultiProviderLLM(str(config_file))

            embedding = await llm.generate_embedding("test text")

            assert len(embedding) == 1536
            mock_client.generate_embedding.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_analyze_agent_state(self, mock_client, tmp_path):
        """Test agent state analysis."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("llm: {}")

        with patch('src.interfaces.multi_provider_llm.LangChainLLMClient',
                  return_value=mock_client):
            llm = MultiProviderLLM(str(config_file))

            result = await llm.analyze_agent_state(
                "agent output",
                {"task": "info"},
                "project context"
            )

            assert result["state"] == "healthy"
            assert result["decision"] == "continue"
            mock_client.analyze_agent_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_trajectory(self, mock_client, tmp_path):
        """Test trajectory analysis."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("llm: {}")

        with patch('src.interfaces.multi_provider_llm.LangChainLLMClient',
                  return_value=mock_client):
            llm = MultiProviderLLM(str(config_file))

            result = await llm.analyze_agent_trajectory(
                "output",
                {},
                [],
                {}
            )

            assert result["trajectory_aligned"] is True
            assert result["alignment_score"] == 0.8
            mock_client.analyze_agent_trajectory.assert_called_once()

    def test_get_model_for_component(self, mock_client, tmp_path):
        """Test getting model for specific component."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("llm: {}")

        with patch('src.interfaces.multi_provider_llm.LangChainLLMClient',
                  return_value=mock_client):
            llm = MultiProviderLLM(str(config_file))

            model_name = llm.get_model_for_component("task_enrichment")
            assert model_name == "test-model"


class TestAzureOpenAIProvider:
    """Test Azure OpenAI provider integration."""

    def test_azure_openai_config_parsing(self, tmp_path):
        """Test Azure OpenAI configuration parsing."""
        config_file = tmp_path / "azure_config.yaml"
        config_file.write_text("""
llm:
  embedding_model: "text-embedding-3-large"
  embedding_provider: "azure_openai"
  providers:
    azure_openai:
      api_key_env: "AZURE_OPENAI_API_KEY"
      base_url: "https://test-resource.openai.azure.com"
      api_version: "2024-02-01"
      models:
        - "gpt-4"
        - "gpt-35-turbo"
  model_assignments:
    task_enrichment:
      provider: "azure_openai"
      model: "gpt-4"
      temperature: 0.7
      max_tokens: 4000
""")

        config = SimpleConfig(str(config_file))
        llm_config = config.get_llm_config()

        assert "azure_openai" in llm_config.providers
        azure_config = llm_config.providers["azure_openai"]
        assert azure_config.api_key_env == "AZURE_OPENAI_API_KEY"
        assert azure_config.base_url == "https://test-resource.openai.azure.com"
        assert azure_config.api_version == "2024-02-01"
        assert "gpt-4" in azure_config.models
        assert llm_config.embedding_provider == "azure_openai"

    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-azure-key"})
    @patch('src.interfaces.langchain_llm_client.AzureChatOpenAI')
    def test_azure_model_initialization(self, mock_azure_chat, tmp_path):
        """Test Azure OpenAI model initialization with correct parameters."""
        config_file = tmp_path / "azure_config.yaml"
        config_file.write_text("""
llm:
  providers:
    azure_openai:
      api_key_env: "AZURE_OPENAI_API_KEY"
      base_url: "https://test-resource.openai.azure.com"
      api_version: "2024-02-01"
      models: ["gpt-4"]
  model_assignments:
    task_enrichment:
      provider: "azure_openai"
      model: "gpt-4"
      temperature: 0.7
      max_tokens: 2000
""")

        config = SimpleConfig(str(config_file))
        client = LangChainLLMClient(config.get_llm_config())

        # Verify AzureChatOpenAI was called with correct parameters
        assert mock_azure_chat.called
        call_kwargs = mock_azure_chat.call_args.kwargs
        assert call_kwargs['model'] == "gpt-4"
        assert call_kwargs['azure_deployment'] == "gpt-4"
        assert call_kwargs['api_version'] == "2024-02-01"
        assert call_kwargs['azure_endpoint'] == "https://test-resource.openai.azure.com"
        assert call_kwargs['temperature'] == 0.7
        assert call_kwargs['max_tokens'] == 2000

    @patch.dict(os.environ, {"AZURE_OPENAI_API_KEY": "test-azure-key"})
    @patch('src.interfaces.langchain_llm_client.AzureOpenAIEmbeddings')
    def test_azure_embeddings_initialization(self, mock_azure_embeddings, tmp_path):
        """Test Azure OpenAI embeddings initialization."""
        config_file = tmp_path / "azure_config.yaml"
        config_file.write_text("""
llm:
  embedding_model: "text-embedding-3-large"
  embedding_provider: "azure_openai"
  providers:
    azure_openai:
      api_key_env: "AZURE_OPENAI_API_KEY"
      base_url: "https://test-resource.openai.azure.com"
      api_version: "2024-02-01"
      models: ["text-embedding-3-large"]
""")

        config = SimpleConfig(str(config_file))
        client = LangChainLLMClient(config.get_llm_config())

        # Verify AzureOpenAIEmbeddings was called
        assert mock_azure_embeddings.called
        call_kwargs = mock_azure_embeddings.call_args.kwargs
        assert call_kwargs['model'] == "text-embedding-3-large"
        assert call_kwargs['azure_deployment'] == "text-embedding-3-large"
        assert call_kwargs['azure_endpoint'] == "https://test-resource.openai.azure.com"
        assert call_kwargs['api_version'] == "2024-02-01"


class TestGoogleAIProvider:
    """Test Google AI Studio provider integration."""

    def test_google_ai_config_parsing(self, tmp_path):
        """Test Google AI configuration parsing."""
        config_file = tmp_path / "google_config.yaml"
        config_file.write_text("""
llm:
  embedding_model: "models/embedding-001"
  embedding_provider: "google_ai"
  providers:
    google_ai:
      api_key_env: "GOOGLE_API_KEY"
      models:
        - "gemini-2.5-flash"
        - "gemini-1.5-pro"
  model_assignments:
    task_enrichment:
      provider: "google_ai"
      model: "gemini-2.5-flash"
      temperature: 0.7
      max_tokens: 4000
""")

        config = SimpleConfig(str(config_file))
        llm_config = config.get_llm_config()

        assert "google_ai" in llm_config.providers
        google_config = llm_config.providers["google_ai"]
        assert google_config.api_key_env == "GOOGLE_API_KEY"
        assert "gemini-2.5-flash" in google_config.models
        assert llm_config.embedding_provider == "google_ai"
        assert llm_config.embedding_model == "models/embedding-001"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-google-key"})
    @patch('src.interfaces.langchain_llm_client.ChatGoogleGenerativeAI')
    def test_google_model_initialization(self, mock_google_chat, tmp_path):
        """Test Google AI model initialization with correct parameters."""
        config_file = tmp_path / "google_config.yaml"
        config_file.write_text("""
llm:
  providers:
    google_ai:
      api_key_env: "GOOGLE_API_KEY"
      models: ["gemini-2.5-flash"]
  model_assignments:
    task_enrichment:
      provider: "google_ai"
      model: "gemini-2.5-flash"
      temperature: 0.7
      max_tokens: 2000
""")

        config = SimpleConfig(str(config_file))
        client = LangChainLLMClient(config.get_llm_config())

        # Verify ChatGoogleGenerativeAI was called with correct parameters
        assert mock_google_chat.called
        call_kwargs = mock_google_chat.call_args.kwargs
        assert call_kwargs['model'] == "gemini-2.5-flash"
        assert call_kwargs['google_api_key'] == "test-google-key"
        assert call_kwargs['temperature'] == 0.7
        assert call_kwargs['max_tokens'] == 2000

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-google-key"})
    @patch('src.interfaces.langchain_llm_client.GoogleGenerativeAIEmbeddings')
    def test_google_embeddings_initialization(self, mock_google_embeddings, tmp_path):
        """Test Google AI embeddings initialization."""
        config_file = tmp_path / "google_config.yaml"
        config_file.write_text("""
llm:
  embedding_model: "models/embedding-001"
  embedding_provider: "google_ai"
  providers:
    google_ai:
      api_key_env: "GOOGLE_API_KEY"
      models: ["models/embedding-001"]
""")

        config = SimpleConfig(str(config_file))
        client = LangChainLLMClient(config.get_llm_config())

        # Verify GoogleGenerativeAIEmbeddings was called
        assert mock_google_embeddings.called
        call_kwargs = mock_google_embeddings.call_args.kwargs
        assert call_kwargs['model'] == "models/embedding-001"
        assert call_kwargs['google_api_key'] == "test-google-key"


class TestMultiProviderIntegration:
    """Test multi-provider integration scenarios."""

    @patch.dict(os.environ, {
        "AZURE_OPENAI_API_KEY": "azure-key",
        "GOOGLE_API_KEY": "google-key",
        "OPENAI_API_KEY": "openai-key"
    })
    @patch('src.interfaces.langchain_llm_client.AzureChatOpenAI')
    @patch('src.interfaces.langchain_llm_client.ChatGoogleGenerativeAI')
    @patch('src.interfaces.langchain_llm_client.OpenAIEmbeddings')
    def test_mixed_provider_routing(self, mock_openai_emb, mock_google, mock_azure, tmp_path):
        """Test that different components can use different providers simultaneously."""
        config_file = tmp_path / "mixed_config.yaml"
        config_file.write_text("""
llm:
  embedding_model: "text-embedding-3-small"
  embedding_provider: "openai"
  providers:
    openai:
      api_key_env: "OPENAI_API_KEY"
    azure_openai:
      api_key_env: "AZURE_OPENAI_API_KEY"
      base_url: "https://test.openai.azure.com"
      api_version: "2024-02-01"
    google_ai:
      api_key_env: "GOOGLE_API_KEY"
  model_assignments:
    task_enrichment:
      provider: "azure_openai"
      model: "gpt-4"
      temperature: 0.7
      max_tokens: 4000
    guardian_analysis:
      provider: "google_ai"
      model: "gemini-2.5-flash"
      temperature: 0.5
      max_tokens: 8000
""")

        config = SimpleConfig(str(config_file))
        client = LangChainLLMClient(config.get_llm_config())

        # Verify both chat providers were initialized
        assert mock_azure.called
        assert mock_google.called
        # Verify OpenAI embeddings was used
        assert mock_openai_emb.called

    def test_graceful_fallback_missing_keys(self, tmp_path, caplog):
        """Test system continues gracefully when provider keys are missing."""
        config_file = tmp_path / "missing_keys_config.yaml"
        config_file.write_text("""
llm:
  providers:
    azure_openai:
      api_key_env: "NONEXISTENT_AZURE_KEY"
      base_url: "https://test.openai.azure.com"
      api_version: "2024-02-01"
    google_ai:
      api_key_env: "NONEXISTENT_GOOGLE_KEY"
  model_assignments:
    task_enrichment:
      provider: "azure_openai"
      model: "gpt-4"
""")

        # Should not crash, just log warnings
        config = SimpleConfig(str(config_file))
        config.validate(strict=False)

        # Check warnings were logged
        assert "Some API keys are missing" in caplog.text or "API key not found" in caplog.text