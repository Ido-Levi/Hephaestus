"""Configuration management for Hephaestus."""

from typing import Optional, Literal
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, SecretStr


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    provider: Literal["openai", "anthropic"] = Field(
        default="openai",
        description="LLM provider to use",
    )
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        env="OPENAI_API_KEY",
        description="OpenAI API key",
    )
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None,
        env="ANTHROPIC_API_KEY",
        description="Anthropic API key",
    )
    model: str = Field(
        default="gpt-4-turbo-preview",
        description="Model to use for task enrichment and monitoring",
    )
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="Model to use for embeddings",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses",
    )
    max_tokens: int = Field(
        default=16000,
        description="Maximum tokens for LLM responses",
    )

    # Remove validators for now - they're causing issues with nested config

    class Config:
        env_prefix = "LLM_"


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    database_path: Path = Field(
        default=Path("./hephaestus.db"),
        description="Path to SQLite database",
    )
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL",
    )
    qdrant_collection_prefix: str = Field(
        default="hephaestus",
        description="Prefix for Qdrant collection names",
    )

    class Config:
        env_prefix = ""


class MCPConfig(BaseSettings):
    """MCP server configuration."""

    host: str = Field(
        default="0.0.0.0",
        description="Host to bind MCP server",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port for MCP server",
    )
    api_key_header: str = Field(
        default="X-Agent-ID",
        description="Header name for agent API key",
    )
    enable_cors: bool = Field(
        default=True,
        description="Enable CORS for MCP server",
    )
    websocket_enabled: bool = Field(
        default=True,
        description="Enable WebSocket support",
    )

    class Config:
        env_prefix = "MCP_"


class MonitoringConfig(BaseSettings):
    """Monitoring configuration."""

    interval_seconds: int = Field(
        default=60,
        ge=10,
        description="Monitoring loop interval in seconds",
    )
    max_health_check_failures: int = Field(
        default=3,
        ge=1,
        description="Maximum health check failures before intervention",
    )
    agent_timeout_minutes: int = Field(
        default=30,
        ge=5,
        description="Maximum time for an agent to complete a task",
    )
    max_concurrent_agents: int = Field(
        default=10,
        ge=1,
        description="Maximum number of concurrent agents",
    )
    tmux_output_lines: int = Field(
        default=200,
        ge=50,
        description="Number of tmux output lines to analyze",
    )
    stuck_detection_minutes: int = Field(
        default=5,
        ge=1,
        description="Minutes of inactivity before agent is considered stuck",
    )

    class Config:
        env_prefix = "MONITORING_"


class AgentConfig(BaseSettings):
    """Agent configuration."""

    default_cli_tool: Literal["claude", "codex"] = Field(
        default="claude",
        description="Default CLI tool for agents",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retries for agent creation",
    )
    health_check_interval: int = Field(
        default=300,
        ge=60,
        description="Health check interval in seconds",
    )
    system_prompt_max_length: int = Field(
        default=4000,
        description="Maximum length for system prompts",
    )
    tmux_session_prefix: str = Field(
        default="hep_agent",
        description="Prefix for tmux session names",
    )

    class Config:
        env_prefix = "AGENT_"


class MemoryConfig(BaseSettings):
    """Memory and RAG configuration."""

    max_context_memories: int = Field(
        default=20,
        ge=5,
        description="Maximum memories to include in context",
    )
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for memory retrieval",
    )
    recency_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Weight for recency in memory ranking",
    )
    relevance_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for relevance in memory ranking",
    )
    similarity_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for similarity in memory ranking",
    )
    chunk_size: int = Field(
        default=500,
        ge=100,
        description="Token size for document chunking",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        description="Token overlap between chunks",
    )

    # Validator removed - causing issues

    class Config:
        env_prefix = "MEMORY_"


class Settings(BaseSettings):
    """Main settings combining all configurations."""

    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

    # General settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )
    docs_path: Path = Field(
        default=Path("./docs"),
        description="Path to documentation folder for ingestion",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment and files."""
        # Load dotenv explicitly
        from dotenv import load_dotenv
        load_dotenv()
        return cls()


# Global settings instance
settings = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global settings
    if settings is None:
        settings = Settings.load()
    return settings


def reload_settings():
    """Reload settings from environment."""
    global settings
    settings = Settings.load()
    return settings