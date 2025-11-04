"""Simplified configuration for Hephaestus."""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Simple configuration class with YAML and environment variable support."""

    def __init__(self):
        # Load from YAML first
        self._load_yaml_config()

        # Then apply environment variable overrides
        self._load_env_overrides()

    def _load_yaml_config(self):
        """Load configuration from YAML file."""
        yaml_path = Path(os.getenv("HEPHAESTUS_CONFIG", "./hephaestus_config.yaml"))

        if yaml_path.exists():
            with open(yaml_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                self._apply_yaml_config(yaml_config)
        else:
            # Default values if no YAML found
            self._apply_defaults()

    def _apply_yaml_config(self, config: Dict[str, Any]):
        """Apply configuration from YAML dictionary."""
        # Server settings
        server = config.get('server', {})
        self.mcp_host = server.get('host', '0.0.0.0')
        self.mcp_port = server.get('port', 8000)
        self.enable_cors = server.get('enable_cors', True)

        # Paths settings
        paths = config.get('paths', {})
        self.database_path = Path(paths.get('database', './hephaestus.db'))
        self.phases_folder = paths.get('phases_folder', './sample-phases')
        self.worktree_base_path = Path(paths.get('worktree_base', '/tmp/hephaestus_worktrees'))
        self.project_root = Path(paths.get('project_root', str(Path.cwd())))

        # Git settings
        git = config.get('git', {})
        self.main_repo_path = Path(git.get('main_repo_path', str(Path.cwd())))
        self.base_branch = git.get('base_branch', 'main')  # Base branch/commit for merging
        self.worktree_branch_prefix = git.get('worktree_branch_prefix', 'agent-')
        self.auto_commit = git.get('auto_commit', True)
        self.conflict_resolution_strategy = git.get('conflict_resolution', 'newest_file_wins')

        # LLM settings
        llm = config.get('llm', {})
        # Use new default_* fields for fallback/legacy mode (replaces LLM_MODEL env var)
        self.llm_provider = llm.get('default_provider', 'openrouter')
        self.llm_model = llm.get('default_model', 'openai/gpt-oss-120b')
        self.default_openrouter_provider = llm.get('default_openrouter_provider', 'cerebras')
        self.default_temperature = llm.get('default_temperature', 0.7)
        self.default_max_tokens = llm.get('default_max_tokens', 4000)
        self.embedding_model = llm.get('embedding_model', 'text-embedding-3-large')
        self.system_prompt_max_length = llm.get('system_prompt_max_length', 8000)

        # Agent settings
        agents = config.get('agents', {})
        self.default_cli_tool = agents.get('default_cli_tool', 'claude')
        self.cli_model = agents.get('cli_model', 'sonnet')
        self.glm_api_token_env = agents.get('glm_api_token_env', 'GLM_API_TOKEN')
        self.tmux_session_prefix = agents.get('tmux_session_prefix', 'agent')
        self.agent_health_check_interval = agents.get('health_check_interval', 60)
        self.max_health_check_failures = agents.get('max_health_failures', 3)
        self.agent_termination_delay = agents.get('termination_delay', 5)

        # Vector store settings
        vector_store = config.get('vector_store', {})
        self.qdrant_url = vector_store.get('qdrant_url', 'http://localhost:6333')
        self.qdrant_collection_prefix = vector_store.get('collection_prefix', 'hephaestus')
        self.embedding_dimension = vector_store.get('embedding_dimension', 1536)

        # Monitoring settings
        monitoring = config.get('monitoring', {})
        self.monitoring_enabled = monitoring.get('enabled', True)
        self.monitoring_interval_seconds = monitoring.get('interval_seconds', 60)
        self.log_level = monitoring.get('log_level', 'INFO')
        self.log_format = monitoring.get('log_format', 'json')
        self.stuck_agent_threshold = monitoring.get('stuck_agent_threshold', 300)
        self.guardian_min_agent_age_seconds = monitoring.get('guardian_min_agent_age_seconds', 60)

        # MCP settings
        mcp = config.get('mcp', {})
        self.auth_required = mcp.get('auth_required', False)
        self.session_timeout = mcp.get('session_timeout', 3600)
        self.max_concurrent_agents = mcp.get('max_concurrent_agents', 10)

        # Task deduplication settings
        dedup = config.get('task_deduplication', {})
        self.task_dedup_enabled = dedup.get('enabled', True)
        self.task_similarity_threshold = dedup.get('similarity_threshold', 0.7)
        self.task_related_threshold = dedup.get('related_threshold', 0.4)
        self.task_embedding_model = dedup.get('embedding_model', 'text-embedding-3-large')
        self.task_embedding_dimension = dedup.get('embedding_dimension', 3072)
        self.task_dedup_batch_size = dedup.get('batch_size', 100)

        # Additional settings from original config
        self.agent_max_retries = 3
        self.tmux_output_lines = 200  # Used by Guardian/monitoring for performance (UI uses 2000)
        self.stuck_detection_minutes = 5
        self.agent_timeout_minutes = 30
        self.max_context_memories = 20
        self.similarity_threshold = 0.7

        # Worktree settings from original config
        self.max_worktrees = 50
        self.max_tree_depth = 10
        self.disk_space_threshold_gb = 10
        self.auto_merge_enabled = True
        self.prefer_child_on_tie = True
        self.require_manual_review = False
        self.log_all_resolutions = True
        self.worktree_auto_cleanup_enabled = True
        self.worktree_cleanup_interval_hours = 6
        self.worktree_retention_hours = {
            "merged": 1,
            "failed": 24,
            "abandoned": 6,
            "active": -1
        }
        self.auto_checkpoint_enabled = True
        self.checkpoint_interval_minutes = 30
        self.checkpoint_on_error = True
        self.checkpoint_before_child = True
        self.worktree_archive_prefix = "refs/archive/"
        self.archive_after_days = 7
        self.delete_archives_after_days = 30

        # General settings
        self.debug = False
        self.docs_path = Path("./docs")

        # Diagnostic agent settings
        diagnostic = config.get('diagnostic_agent', {})
        self.diagnostic_agent_enabled = diagnostic.get('enabled', True)
        self.diagnostic_cooldown_seconds = diagnostic.get('cooldown_seconds', 60)
        self.diagnostic_min_stuck_time_seconds = diagnostic.get('min_stuck_time_seconds', 60)
        self.diagnostic_max_agents_to_analyze = diagnostic.get('max_agents_to_analyze', 15)
        self.diagnostic_max_conductor_analyses = diagnostic.get('max_conductor_analyses', 5)
        self.diagnostic_max_tasks_per_run = diagnostic.get('max_tasks_per_run', 5)

    def _apply_defaults(self):
        """Apply default configuration values."""
        # Use same defaults as YAML loading
        self._apply_yaml_config({})

    def _load_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # LLM settings - only API keys from environment, all models from YAML
        if os.getenv("LLM_PROVIDER"):
            self.llm_provider = os.getenv("LLM_PROVIDER")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        # LLM_MODEL and EMBEDDING_MODEL are deprecated - all model config comes from YAML

        # Database settings
        if os.getenv("DATABASE_PATH"):
            self.database_path = Path(os.getenv("DATABASE_PATH"))
        if os.getenv("QDRANT_URL"):
            self.qdrant_url = os.getenv("QDRANT_URL")
        if os.getenv("QDRANT_COLLECTION_PREFIX"):
            self.qdrant_collection_prefix = os.getenv("QDRANT_COLLECTION_PREFIX")

        # MCP settings
        if os.getenv("MCP_HOST"):
            self.mcp_host = os.getenv("MCP_HOST")
        if os.getenv("MCP_PORT"):
            self.mcp_port = int(os.getenv("MCP_PORT"))

        # Monitoring settings
        if os.getenv("MONITORING_INTERVAL_SECONDS"):
            self.monitoring_interval_seconds = int(os.getenv("MONITORING_INTERVAL_SECONDS"))
        if os.getenv("MAX_HEALTH_CHECK_FAILURES"):
            self.max_health_check_failures = int(os.getenv("MAX_HEALTH_CHECK_FAILURES"))
        if os.getenv("AGENT_TIMEOUT_MINUTES"):
            self.agent_timeout_minutes = int(os.getenv("AGENT_TIMEOUT_MINUTES"))
        # Note: max_concurrent_agents is ONLY configurable via hephaestus_config.yaml or SDK
        # Not overridable by environment variables for consistency
        if os.getenv("GUARDIAN_MIN_AGENT_AGE_SECONDS"):
            self.guardian_min_agent_age_seconds = int(os.getenv("GUARDIAN_MIN_AGENT_AGE_SECONDS"))

        # Agent settings
        if os.getenv("DEFAULT_CLI_TOOL"):
            self.default_cli_tool = os.getenv("DEFAULT_CLI_TOOL")
        if os.getenv("CLI_MODEL"):
            self.cli_model = os.getenv("CLI_MODEL")
        if os.getenv("GLM_API_TOKEN_ENV"):
            self.glm_api_token_env = os.getenv("GLM_API_TOKEN_ENV")

        # Worktree settings
        if os.getenv("WORKTREE_BASE_PATH"):
            self.worktree_base_path = Path(os.getenv("WORKTREE_BASE_PATH"))
        if os.getenv("MAIN_REPO_PATH"):
            self.main_repo_path = Path(os.getenv("MAIN_REPO_PATH"))
        if os.getenv("GIT_BASE_BRANCH"):
            self.base_branch = os.getenv("GIT_BASE_BRANCH")
        if os.getenv("WORKTREE_MAX_COUNT"):
            self.max_worktrees = int(os.getenv("WORKTREE_MAX_COUNT"))
        if os.getenv("WORKTREE_MAX_DEPTH"):
            self.max_tree_depth = int(os.getenv("WORKTREE_MAX_DEPTH"))
        if os.getenv("WORKTREE_DISK_THRESHOLD_GB"):
            self.disk_space_threshold_gb = int(os.getenv("WORKTREE_DISK_THRESHOLD_GB"))

        # Worktree conflict resolution
        if os.getenv("WORKTREE_AUTO_MERGE"):
            self.auto_merge_enabled = os.getenv("WORKTREE_AUTO_MERGE").lower() == "true"
        if os.getenv("WORKTREE_CONFLICT_STRATEGY"):
            self.conflict_resolution_strategy = os.getenv("WORKTREE_CONFLICT_STRATEGY")
        if os.getenv("WORKTREE_PREFER_CHILD_ON_TIE"):
            self.prefer_child_on_tie = os.getenv("WORKTREE_PREFER_CHILD_ON_TIE").lower() == "true"
        if os.getenv("WORKTREE_LOG_RESOLUTIONS"):
            self.log_all_resolutions = os.getenv("WORKTREE_LOG_RESOLUTIONS").lower() == "true"

        # Worktree cleanup settings
        if os.getenv("WORKTREE_AUTO_CLEANUP"):
            self.worktree_auto_cleanup_enabled = os.getenv("WORKTREE_AUTO_CLEANUP").lower() == "true"
        if os.getenv("WORKTREE_CLEANUP_INTERVAL_HOURS"):
            self.worktree_cleanup_interval_hours = int(os.getenv("WORKTREE_CLEANUP_INTERVAL_HOURS"))
        if os.getenv("WORKTREE_RETENTION_MERGED"):
            self.worktree_retention_hours["merged"] = int(os.getenv("WORKTREE_RETENTION_MERGED"))
        if os.getenv("WORKTREE_RETENTION_FAILED"):
            self.worktree_retention_hours["failed"] = int(os.getenv("WORKTREE_RETENTION_FAILED"))
        if os.getenv("WORKTREE_RETENTION_ABANDONED"):
            self.worktree_retention_hours["abandoned"] = int(os.getenv("WORKTREE_RETENTION_ABANDONED"))

        # Worktree commit settings
        if os.getenv("WORKTREE_AUTO_CHECKPOINT"):
            self.auto_checkpoint_enabled = os.getenv("WORKTREE_AUTO_CHECKPOINT").lower() == "true"
        if os.getenv("WORKTREE_CHECKPOINT_INTERVAL"):
            self.checkpoint_interval_minutes = int(os.getenv("WORKTREE_CHECKPOINT_INTERVAL"))
        if os.getenv("WORKTREE_CHECKPOINT_ON_ERROR"):
            self.checkpoint_on_error = os.getenv("WORKTREE_CHECKPOINT_ON_ERROR").lower() == "true"
        if os.getenv("WORKTREE_CHECKPOINT_BEFORE_CHILD"):
            self.checkpoint_before_child = os.getenv("WORKTREE_CHECKPOINT_BEFORE_CHILD").lower() == "true"

        # Worktree branch settings
        if os.getenv("WORKTREE_BRANCH_PREFIX"):
            self.worktree_branch_prefix = os.getenv("WORKTREE_BRANCH_PREFIX")
        if os.getenv("WORKTREE_ARCHIVE_PREFIX"):
            self.worktree_archive_prefix = os.getenv("WORKTREE_ARCHIVE_PREFIX")
        if os.getenv("WORKTREE_ARCHIVE_AFTER_DAYS"):
            self.archive_after_days = int(os.getenv("WORKTREE_ARCHIVE_AFTER_DAYS"))
        if os.getenv("WORKTREE_DELETE_ARCHIVES_AFTER_DAYS"):
            self.delete_archives_after_days = int(os.getenv("WORKTREE_DELETE_ARCHIVES_AFTER_DAYS"))

        # General settings
        if os.getenv("DEBUG"):
            self.debug = os.getenv("DEBUG").lower() == "true"
        if os.getenv("LOG_LEVEL"):
            self.log_level = os.getenv("LOG_LEVEL")

        # Phases folder from environment
        if os.getenv("HEPHAESTUS_PHASES_FOLDER"):
            self.phases_folder = os.getenv("HEPHAESTUS_PHASES_FOLDER")

        # Task deduplication settings from environment
        if os.getenv("TASK_DEDUP_ENABLED"):
            self.task_dedup_enabled = os.getenv("TASK_DEDUP_ENABLED").lower() == "true"
        if os.getenv("TASK_SIMILARITY_THRESHOLD"):
            self.task_similarity_threshold = float(os.getenv("TASK_SIMILARITY_THRESHOLD"))
        if os.getenv("TASK_RELATED_THRESHOLD"):
            self.task_related_threshold = float(os.getenv("TASK_RELATED_THRESHOLD"))
        if os.getenv("TASK_EMBEDDING_MODEL"):
            self.task_embedding_model = os.getenv("TASK_EMBEDDING_MODEL")

        # Diagnostic agent settings from environment
        if os.getenv("DIAGNOSTIC_AGENT_ENABLED"):
            self.diagnostic_agent_enabled = os.getenv("DIAGNOSTIC_AGENT_ENABLED").lower() == "true"
        if os.getenv("DIAGNOSTIC_COOLDOWN_SECONDS"):
            self.diagnostic_cooldown_seconds = int(os.getenv("DIAGNOSTIC_COOLDOWN_SECONDS"))
        if os.getenv("DIAGNOSTIC_MIN_STUCK_TIME"):
            self.diagnostic_min_stuck_time_seconds = int(os.getenv("DIAGNOSTIC_MIN_STUCK_TIME"))

    def get_api_key(self):
        """Get the appropriate API key based on provider."""
        if self.llm_provider == "openai":
            return self.openai_api_key
        elif self.llm_provider == "anthropic":
            return self.anthropic_api_key
        return None

    def validate(self):
        """Validate configuration."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic provider")
        return True

    def to_env_dict(self) -> dict:
        """Export configuration as environment variables dict for subprocess.
        
        Returns:
            Dictionary of environment variables for spawned processes
        """
        env = {}
        
        # Database and storage paths
        if self.database_path:
            env["DATABASE_PATH"] = str(self.database_path)
        if self.qdrant_url:
            env["QDRANT_URL"] = self.qdrant_url
        if self.qdrant_collection_prefix:
            env["QDRANT_COLLECTION_PREFIX"] = self.qdrant_collection_prefix
        
        # Server settings  
        if self.mcp_host:
            env["MCP_HOST"] = self.mcp_host
        if self.mcp_port:
            env["MCP_PORT"] = str(self.mcp_port)
        
        # Worktree settings
        if self.worktree_base_path:
            env["WORKTREE_BASE_PATH"] = str(self.worktree_base_path)
        if hasattr(self, 'working_directory') and self.working_directory:
            env["WORKING_DIRECTORY"] = str(self.working_directory)
        
        return env


# Global config instance
_config = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config