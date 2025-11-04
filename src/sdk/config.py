"""Configuration management for the Hephaestus SDK."""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class HephaestusConfig:
    """Configuration for the Hephaestus SDK.

    Supports all fields from hephaestus_config.yaml for comprehensive configuration.
    """

    # Database
    database_path: str = "./hephaestus.db"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # LLM - Basic settings
    llm_provider: str = "anthropic"  # or "openai"
    llm_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # Server
    mcp_port: int = 8000
    mcp_host: str = "127.0.0.1"
    enable_cors: bool = True

    # Monitoring
    monitoring_interval: int = 60
    monitoring_enabled: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    stuck_agent_threshold: int = 300

    # Working directory
    working_directory: str = "."

    # Paths
    phases_temp_dir: Optional[str] = None
    phases_folder: Optional[str] = None
    worktree_base: str = "/tmp/hephaestus_worktrees"
    project_root: Optional[str] = None

    # Git Configuration
    main_repo_path: Optional[str] = None
    base_branch: str = "main"  # Base branch/commit for merging (can be branch name or commit SHA)
    worktree_branch_prefix: str = "agent-"
    auto_commit: bool = True
    conflict_resolution: str = "newest_file_wins"

    # Agent Configuration
    default_cli_tool: str = "claude"
    tmux_session_prefix: str = "agent"
    health_check_interval: int = 60
    max_health_failures: int = 3
    termination_delay: int = 5

    # Vector Store Configuration
    collection_prefix: str = "hephaestus"
    embedding_dimension: int = 1536
    embedding_model: str = "text-embedding-3-large"

    # MCP Server Configuration
    auth_required: bool = False
    session_timeout: int = 3600
    max_concurrent_agents: int = 10

    # Task Deduplication
    task_deduplication_enabled: bool = True
    similarity_threshold: float = 0.82
    related_threshold: float = 0.5
    dedup_batch_size: int = 100

    # Diagnostic Agent Configuration
    diagnostic_agent_enabled: bool = False
    diagnostic_cooldown_seconds: int = 60
    diagnostic_min_stuck_time_seconds: int = 60
    diagnostic_max_agents_to_analyze: int = 15
    diagnostic_max_conductor_analyses: int = 5
    diagnostic_max_tasks_per_run: int = 5

    # Advanced LLM Configuration
    llm_providers: Dict[str, Any] = field(default_factory=dict)
    model_assignments: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Load API keys from environment if not provided."""
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.openrouter_api_key:
            self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.groq_api_key:
            self.groq_api_key = os.getenv("GROQ_API_KEY")

        # Set default model based on provider
        if not self.llm_model:
            if self.llm_provider == "openai":
                self.llm_model = "gpt-5"
            elif self.llm_provider == "anthropic":
                self.llm_model = "claude-sonnet-4-5-20250929"

    def to_env_dict(self) -> Dict[str, str]:
        """Convert config to environment variable dictionary for backend processes.

        This passes ALL configuration settings to the backend via environment variables,
        matching the structure of hephaestus_config.yaml.
        """
        env = {
            # Database
            "DATABASE_PATH": self.database_path,

            # Qdrant / Vector Store
            "QDRANT_URL": self.qdrant_url,
            "VECTOR_STORE_COLLECTION_PREFIX": self.collection_prefix,
            "EMBEDDING_DIMENSION": str(self.embedding_dimension),
            "EMBEDDING_MODEL": self.embedding_model,

            # LLM
            "LLM_PROVIDER": self.llm_provider,
            "LLM_MODEL": self.llm_model or "",

            # Server
            "MCP_PORT": str(self.mcp_port),
            "MCP_HOST": self.mcp_host,
            "SERVER_ENABLE_CORS": str(self.enable_cors).lower(),

            # Monitoring
            "MONITORING_INTERVAL_SECONDS": str(self.monitoring_interval),
            "MONITORING_ENABLED": str(self.monitoring_enabled).lower(),
            "LOG_LEVEL": self.log_level,
            "LOG_FORMAT": self.log_format,
            "STUCK_AGENT_THRESHOLD": str(self.stuck_agent_threshold),

            # Paths
            "WORKING_DIRECTORY": self.working_directory,
            "WORKTREE_BASE": self.worktree_base,

            # Git Configuration
            "GIT_BASE_BRANCH": self.base_branch,
            "WORKTREE_BRANCH_PREFIX": self.worktree_branch_prefix,
            "AUTO_COMMIT": str(self.auto_commit).lower(),
            "CONFLICT_RESOLUTION": self.conflict_resolution,

            # Agent Configuration
            "DEFAULT_CLI_TOOL": self.default_cli_tool,
            "TMUX_SESSION_PREFIX": self.tmux_session_prefix,
            "HEALTH_CHECK_INTERVAL": str(self.health_check_interval),
            "MAX_HEALTH_FAILURES": str(self.max_health_failures),
            "TERMINATION_DELAY": str(self.termination_delay),

            # MCP Server Configuration
            "AUTH_REQUIRED": str(self.auth_required).lower(),
            "SESSION_TIMEOUT": str(self.session_timeout),
            "MAX_CONCURRENT_AGENTS": str(self.max_concurrent_agents),

            # Task Deduplication
            "TASK_DEDUPLICATION_ENABLED": str(self.task_deduplication_enabled).lower(),
            "SIMILARITY_THRESHOLD": str(self.similarity_threshold),
            "RELATED_THRESHOLD": str(self.related_threshold),
            "DEDUP_BATCH_SIZE": str(self.dedup_batch_size),

            # Diagnostic Agent Configuration
            "DIAGNOSTIC_AGENT_ENABLED": str(self.diagnostic_agent_enabled).lower(),
            "DIAGNOSTIC_COOLDOWN_SECONDS": str(self.diagnostic_cooldown_seconds),
            "DIAGNOSTIC_MIN_STUCK_TIME": str(self.diagnostic_min_stuck_time_seconds),
        }

        # API Keys (only if set)
        if self.openai_api_key:
            env["OPENAI_API_KEY"] = self.openai_api_key
        if self.anthropic_api_key:
            env["ANTHROPIC_API_KEY"] = self.anthropic_api_key
        if self.openrouter_api_key:
            env["OPENROUTER_API_KEY"] = self.openrouter_api_key
        if self.groq_api_key:
            env["GROQ_API_KEY"] = self.groq_api_key

        # Optional Paths
        if self.phases_temp_dir:
            env["HEPHAESTUS_PHASES_FOLDER"] = self.phases_temp_dir
        elif self.phases_folder:
            env["HEPHAESTUS_PHASES_FOLDER"] = self.phases_folder

        if self.project_root:
            env["PROJECT_ROOT"] = self.project_root

        if self.main_repo_path:
            env["MAIN_REPO_PATH"] = self.main_repo_path

        return env

    @property
    def api_base_url(self) -> str:
        """Get the full API base URL."""
        return f"http://{self.mcp_host}:{self.mcp_port}"

    def validate(self) -> None:
        """Validate configuration."""
        # Check API keys for simple providers
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set for OpenAI provider")

        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set for Anthropic provider")

        if self.llm_provider == "openrouter" and not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY must be set for OpenRouter provider")

        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set for Groq provider")

        # Check provider is valid
        valid_providers = ["openai", "anthropic", "openrouter", "groq"]
        if self.llm_provider not in valid_providers:
            raise ValueError(
                f"Invalid LLM provider: {self.llm_provider}. Must be one of {valid_providers}"
            )

        # Check port is valid
        if not (1024 <= self.mcp_port <= 65535):
            raise ValueError(f"Invalid MCP port: {self.mcp_port}. Must be 1024-65535")

        # Check thresholds are valid
        if not (0.0 <= self.similarity_threshold <= 1.0):
            raise ValueError(f"similarity_threshold must be between 0.0 and 1.0")

        if not (0.0 <= self.related_threshold <= 1.0):
            raise ValueError(f"related_threshold must be between 0.0 and 1.0")
