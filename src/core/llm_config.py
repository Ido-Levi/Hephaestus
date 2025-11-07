"""LLM configuration management for multi-provider support."""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import yaml
import os

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class ModelInfo(BaseModel):
    """Model information for OpenRouter."""
    provider: Optional[str] = None
    model: str


class ProviderConfig(BaseModel):
    """Provider configuration."""
    api_key_env: str
    base_url: Optional[str] = None
    models: List[Union[str, Dict[str, str]]]
    # Azure-specific fields
    api_version: Optional[str] = None  # For Azure OpenAI (e.g., "2024-02-01")
    # Google Vertex AI-specific fields (for future use)
    project_id: Optional[str] = None
    location: Optional[str] = None  # e.g., "us-central1"


class ModelAssignment(BaseModel):
    """Model assignment for a component."""
    provider: str
    model: str
    openrouter_provider: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000


class MultiProviderLLMConfig(BaseModel):
    """Multi-provider LLM configuration."""
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model to use"
    )
    embedding_provider: str = Field(
        default="openai",
        description="Provider for embeddings (openai, azure_openai, google_ai)"
    )
    providers: Dict[str, ProviderConfig] = Field(
        default_factory=dict,
        description="Provider configurations"
    )
    model_assignments: Dict[str, ModelAssignment] = Field(
        default_factory=dict,
        description="Model assignments per component"
    )


class SimpleConfig:
    """Simple configuration loader for YAML config."""

    def __init__(self, config_path: str = "./hephaestus_config.yaml"):
        """Initialize simple config loader.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._llm_config: Optional[MultiProviderLLMConfig] = None
        self.load_config()

    def load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

        # Parse LLM configuration
        if 'llm' in self._config:
            llm_data = self._config['llm']

            # Convert to proper format
            providers = {}
            if 'providers' in llm_data:
                for provider_name, provider_data in llm_data['providers'].items():
                    # Convert models list to proper format
                    models = []
                    for model in provider_data.get('models', []):
                        if isinstance(model, dict):
                            models.append(model)
                        else:
                            models.append(model)

                    # Allow environment variable to override base_url for openrouter
                    base_url = provider_data.get('base_url')
                    if provider_name == 'openrouter':
                        env_base_url = os.getenv('OPENROUTER_BASE_URL')
                        if env_base_url:
                            base_url = env_base_url

                    providers[provider_name] = ProviderConfig(
                        api_key_env=provider_data.get('api_key_env', f"{provider_name.upper()}_API_KEY"),
                        base_url=base_url,
                        models=models,
                        api_version=provider_data.get('api_version'),
                        project_id=provider_data.get('project_id'),
                        location=provider_data.get('location')
                    )

            # Convert model assignments
            model_assignments = {}
            if 'model_assignments' in llm_data:
                for component, assignment in llm_data['model_assignments'].items():
                    model_assignments[component] = ModelAssignment(**assignment)

            self._llm_config = MultiProviderLLMConfig(
                embedding_model=llm_data.get('embedding_model', 'text-embedding-3-small'),
                embedding_provider=llm_data.get('embedding_provider', 'openai'),
                providers=providers,
                model_assignments=model_assignments
            )

    def get_llm_config(self) -> MultiProviderLLMConfig:
        """Get LLM configuration.

        Returns:
            Multi-provider LLM configuration
        """
        if not self._llm_config:
            # Return default if not configured
            return MultiProviderLLMConfig()
        return self._llm_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def llm_provider(self) -> str:
        """Get default LLM provider (for backward compatibility)."""
        # Use task enrichment provider as default
        if self._llm_config and 'task_enrichment' in self._llm_config.model_assignments:
            return self._llm_config.model_assignments['task_enrichment'].provider
        return self.get('llm.provider', 'openai')

    @property
    def llm_model(self) -> str:
        """Get default LLM model (for backward compatibility)."""
        # Use task enrichment model as default
        if self._llm_config and 'task_enrichment' in self._llm_config.model_assignments:
            assignment = self._llm_config.model_assignments['task_enrichment']
            if assignment.openrouter_provider:
                return f"{assignment.openrouter_provider}/{assignment.model}"
            return assignment.model
        return self.get('llm.model', 'gpt-4-turbo-preview')

    @property
    def embedding_model(self) -> str:
        """Get embedding model."""
        if self._llm_config:
            return self._llm_config.embedding_model
        return self.get('llm.embedding_model', 'text-embedding-3-small')

    def validate(self, strict: bool = False):
        """Validate configuration.

        Args:
            strict: If True, raise error on missing API keys. If False, just log warnings.
        """
        import logging
        logger = logging.getLogger(__name__)

        # Check for required API keys based on configured providers
        if self._llm_config:
            missing_keys = []
            for component, assignment in self._llm_config.model_assignments.items():
                provider_config = self._llm_config.providers.get(assignment.provider)
                if provider_config:
                    api_key = os.getenv(provider_config.api_key_env)
                    if not api_key:
                        missing_keys.append(
                            f"{assignment.provider} for {component} "
                            f"(env var: {provider_config.api_key_env})"
                        )

            if missing_keys:
                if strict:
                    raise ValueError(
                        f"Missing API keys: {', '.join(missing_keys)}"
                    )
                else:
                    logger.warning(
                        f"Some API keys are missing: {', '.join(missing_keys)}. "
                        "Components using these providers will use fallback behavior."
                    )

    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """Get API key for a provider.

        Args:
            provider: Provider name (defaults to main provider)

        Returns:
            API key or None
        """
        if not provider:
            provider = self.llm_provider

        if self._llm_config and provider in self._llm_config.providers:
            provider_config = self._llm_config.providers[provider]
            return os.getenv(provider_config.api_key_env)

        # Fallback to legacy env vars
        if provider == 'openai':
            return os.getenv('OPENAI_API_KEY')
        elif provider == 'anthropic':
            return os.getenv('ANTHROPIC_API_KEY')
        elif provider == 'groq':
            return os.getenv('GROQ_API_KEY')
        elif provider == 'openrouter':
            return os.getenv('OPENROUTER_API_KEY')
        elif provider == 'azure_openai':
            return os.getenv('AZURE_OPENAI_API_KEY')
        elif provider == 'google_ai':
            return os.getenv('GOOGLE_API_KEY')

        return None

    # Additional properties for backward compatibility
    @property
    def database_path(self) -> str:
        """Get database path."""
        return self.get('paths.database', './hephaestus.db')

    @property
    def qdrant_url(self) -> str:
        """Get Qdrant URL."""
        return self.get('vector_store.qdrant_url', 'http://localhost:6333')

    @property
    def server_host(self) -> str:
        """Get server host."""
        return self.get('server.host', '0.0.0.0')

    @property
    def server_port(self) -> int:
        """Get server port."""
        return self.get('server.port', 8000)

    @property
    def monitoring_interval(self) -> int:
        """Get monitoring interval."""
        return self.get('monitoring.interval_seconds', 60)

    @property
    def tmux_session_prefix(self) -> str:
        """Get tmux session prefix."""
        return self.get('agents.tmux_session_prefix', 'hep_agent')

    @property
    def default_cli_tool(self) -> str:
        """Get default CLI tool."""
        return self.get('agents.default_cli_tool', 'claude')


# Global configuration instance
_config = None


def get_config(config_path: str = "./hephaestus_config.yaml") -> SimpleConfig:
    """Get or create global configuration instance.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration instance
    """
    global _config
    if _config is None:
        _config = SimpleConfig(config_path)
    return _config


def reload_config(config_path: str = "./hephaestus_config.yaml") -> SimpleConfig:
    """Reload configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        New configuration instance
    """
    global _config
    _config = SimpleConfig(config_path)
    return _config