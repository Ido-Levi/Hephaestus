"""Main Hephaestus SDK client."""

import os
import time
import yaml
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.sdk.models import (
    Phase, TaskStatus, AgentStatus, Workflow, WorkflowResult,
    WorkflowConfig, WorkflowDefinition, WorkflowExecution
)
from src.sdk.config import HephaestusConfig
from src.sdk.process_manager import ProcessManager
from src.sdk.exceptions import (
    HephaestusStartupError,
    SDKNotRunningError,
    InvalidPhaseError,
    TaskCreationError,
    TaskNotFoundError,
    QdrantConnectionError,
)


class HephaestusSDK:
    """
    Main SDK client for Hephaestus AI agent orchestration system.

    Supports two modes:
    - Headless mode (default): Runs services in background, logs to files
    - TUI mode: Interactive terminal UI with forge ASCII art

    Phases can be defined as:
    - YAML directory: phases_dir parameter
    - Python objects: phases parameter (list of Phase objects)
    """

    def __init__(
        self,
        phases_dir: Optional[str] = None,
        phases: Optional[List[Phase]] = None,
        workflow_config: Optional[WorkflowConfig] = None,
        workflow_definitions: Optional[List[WorkflowDefinition]] = None,
        config: Optional[HephaestusConfig] = None,
        auto_start: bool = False,
        **config_kwargs,
    ):
        """
        Initialize the Hephaestus SDK.

        Args:
            phases_dir: Path to directory containing phase YAML files (deprecated, use workflow_definitions)
            phases: List of Phase objects (deprecated, use workflow_definitions)
            workflow_config: WorkflowConfig object for result handling (deprecated)
            workflow_definitions: List of WorkflowDefinition objects (preferred)
            config: Pre-configured HephaestusConfig object (optional)
            auto_start: Automatically start services on init
            **config_kwargs: Any HephaestusConfig field can be passed as keyword argument

        Examples:
            # Option 1: Multiple workflow definitions (preferred)
            sdk = HephaestusSDK(
                workflow_definitions=[
                    WorkflowDefinition(id="prd", name="PRD Builder", phases=PRD_PHASES, config=PRD_CONFIG),
                    WorkflowDefinition(id="bugfix", name="Bug Fix", phases=BUGFIX_PHASES, config=BUGFIX_CONFIG),
                ],
                llm_provider="openai",
            )

            # Option 2: Single workflow (backward compatible)
            sdk = HephaestusSDK(
                phases=[...],
                workflow_config=WorkflowConfig(has_result=True, ...),
                llm_provider="openai",
            )

            # Option 3: From YAML directory (backward compatible)
            sdk = HephaestusSDK(
                phases_dir="/path/to/phases",
            )
        """
        # Multi-workflow support
        self.definitions: Dict[str, WorkflowDefinition] = {}

        # Handle workflow_definitions (new preferred way)
        if workflow_definitions:
            for defn in workflow_definitions:
                self.definitions[defn.id] = defn
            # Use first definition's phases as the default phases_map for backward compatibility
            if workflow_definitions:
                first_def = workflow_definitions[0]
                self.phases_list = first_def.phases
                self.workflow_config = first_def.config
                self.phases_dir = None
        elif phases_dir is None and phases is None:
            raise ValueError("Either workflow_definitions, phases_dir, or phases must be provided")
        elif phases_dir is not None and phases is not None:
            raise ValueError("Cannot provide both phases_dir and phases")
        else:
            # Backward compatibility: create a "default" workflow definition
            self.phases_dir = phases_dir
            self.phases_list = phases
            self.workflow_config = workflow_config

        self.phases_map: Dict[int, Phase] = {}

        # Create or use config
        if config is not None:
            # Use provided config as base
            self.config = config
            # Override with any kwargs
            for key, value in config_kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    raise ValueError(f"Unknown config parameter: {key}")
        else:
            # Create new config from kwargs
            self.config = HephaestusConfig(**config_kwargs)

        # Validate config
        self.config.validate()

        # State
        self.running = False
        self.log_dir: Optional[Path] = None
        self.process_manager: Optional[ProcessManager] = None
        self.temp_phases_dir: Optional[Path] = None

        # Load phases
        self._load_phases()

        # Auto start if requested
        if auto_start:
            self.start()

    def _load_phases(self) -> None:
        """Load phases from directory or Python objects."""
        if self.phases_dir:
            # Load from YAML directory
            self._load_phases_from_yaml()
        elif self.phases_list:
            # Use Python objects
            self._load_phases_from_objects()

    def _load_phases_from_yaml(self) -> None:
        """Load phases from YAML files in directory."""
        phases_path = Path(self.phases_dir)

        if not phases_path.exists():
            raise ValueError(f"Phases directory does not exist: {self.phases_dir}")

        if not phases_path.is_dir():
            raise ValueError(f"Phases path is not a directory: {self.phases_dir}")

        # Find all YAML files matching pattern XX_*.yaml
        yaml_files = sorted(phases_path.glob("*_*.yaml"))

        if not yaml_files:
            raise ValueError(f"No phase YAML files found in: {self.phases_dir}")

        for yaml_file in yaml_files:
            # Extract phase ID from filename (e.g., "01_planning.yaml" -> 1)
            filename = yaml_file.stem
            parts = filename.split("_", 1)

            if len(parts) < 2:
                continue

            try:
                phase_id = int(parts[0])
            except ValueError:
                continue

            # Load YAML
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            # Parse into Phase object
            phase = Phase(
                id=phase_id,
                name=parts[1],
                description=data.get("description", ""),
                done_definitions=data.get("Done_Definitions", []),
                working_directory=data.get("working_directory", "."),
                additional_notes=data.get("Additional_Notes", ""),
                outputs=data.get("Outputs", []),
                next_steps=data.get("Next_Steps", []),
            )

            self.phases_map[phase_id] = phase

    def _load_phases_from_objects(self) -> None:
        """Load phases from Python objects."""
        for phase in self.phases_list:
            if not isinstance(phase, Phase):
                raise ValueError(f"Invalid phase object: {phase}")

            if phase.id in self.phases_map:
                raise ValueError(f"Duplicate phase ID: {phase.id}")

            self.phases_map[phase.id] = phase

    def _write_phases_to_temp_dir(self) -> Path:
        """Write phases and workflow config to temporary directory as YAML files."""
        temp_dir = Path(tempfile.mkdtemp(prefix="hephaestus_phases_"))

        # Custom YAML dumper to use literal style for multiline strings
        def str_representer(dumper, data):
            if "\n" in data:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        yaml.SafeDumper.add_representer(str, str_representer)

        # Write phase YAML files
        for phase_id, phase in self.phases_map.items():
            filename = f"{phase_id:02d}_{phase.name}.yaml"
            filepath = temp_dir / filename

            with open(filepath, "w") as f:
                # Use custom dumper with literal style for multiline strings
                yaml.dump(
                    phase.to_yaml_dict(),
                    f,
                    Dumper=yaml.SafeDumper,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

        # Write phases_config.yaml if workflow_config is provided
        if self.workflow_config:
            config_filepath = temp_dir / "phases_config.yaml"
            with open(config_filepath, "w") as f:
                yaml.dump(
                    self.workflow_config.to_yaml_dict(),
                    f,
                    Dumper=yaml.SafeDumper,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

        return temp_dir

    def _create_log_directory(self, log_dir: Optional[str] = None) -> Path:
        """Create log directory with timestamp."""
        if log_dir:
            log_path = Path(log_dir)
        else:
            # Default: ~/.hephaestus/logs/session-{timestamp}/
            home = Path.home()
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_path = home / ".hephaestus" / "logs" / f"session-{timestamp}"

        log_path.mkdir(parents=True, exist_ok=True)
        return log_path

    def _check_backend_health(self) -> bool:
        """Check if backend API is healthy."""
        try:
            response = requests.get(
                f"http://{self.config.mcp_host}:{self.config.mcp_port}/health",
                timeout=2,
            )
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except Exception:
            return False

    def _check_qdrant_health(self) -> bool:
        """Check if Qdrant is accessible."""
        try:
            # Qdrant health endpoint
            response = requests.get(f"{self.config.qdrant_url}/", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def start(
        self, timeout: int = 30, enable_tui: bool = False, log_dir: Optional[str] = None
    ) -> bool:
        """
        Start Hephaestus services.

        Args:
            timeout: Maximum seconds to wait for services to become healthy
            enable_tui: Enable TUI mode (default: False, headless)
            log_dir: Custom log directory (default: ~/.hephaestus/logs/session-{timestamp}/)

        Returns:
            True if all services are healthy

        Raises:
            HephaestusStartupError: If services don't become healthy within timeout
            QdrantConnectionError: If Qdrant is not accessible
        """
        if self.running:
            print("Hephaestus is already running")
            return True

        # Create log directory
        self.log_dir = self._create_log_directory(log_dir)

        # Write phases to temp directory if using Python objects
        if self.phases_list:
            self.temp_phases_dir = self._write_phases_to_temp_dir()
            self.config.phases_temp_dir = str(self.temp_phases_dir)
        else:
            # Use provided phases_dir
            self.config.phases_temp_dir = self.phases_dir

        if enable_tui:
            # Launch TUI mode
            self._start_with_tui(timeout)
        else:
            # Headless mode
            self._start_headless(timeout)

        return True

    def _start_headless(self, timeout: int):
        """Start in headless mode with console output."""
        # Check Qdrant first
        print(f"[Hephaestus] Checking Qdrant connectivity...")
        if not self._check_qdrant_health():
            raise QdrantConnectionError(
                f"Qdrant is not accessible at {self.config.qdrant_url}. "
                "Please ensure Qdrant is running (e.g., docker run -p 6333:6333 qdrant/qdrant)"
            )

        # Create process manager
        self.process_manager = ProcessManager(self.config, self.log_dir)

        # Print log directory
        print(f"\nLogs: {self.log_dir}/")
        print(f"  → backend.log")
        print(f"  → monitor.log\n")

        # Spawn processes
        print("[Hephaestus] Starting backend process...")
        self.process_manager.spawn_backend()

        print("[Hephaestus] Starting monitor process...")
        self.process_manager.spawn_monitor()

        # Poll backend health
        print("[Hephaestus] Waiting for services to become healthy...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._check_backend_health():
                print("[Hephaestus] ✓ Backend is healthy")
                break

            time.sleep(0.5)
        else:
            # Timeout
            self.process_manager.shutdown_all()
            raise HephaestusStartupError(
                f"Backend did not become healthy within {timeout} seconds. "
                f"Check logs at: {self.log_dir}/backend.log"
            )

        # Verify monitor process is running
        if not self.process_manager.is_process_alive("monitor"):
            self.process_manager.shutdown_all()
            raise HephaestusStartupError(
                f"Monitor process failed to start. "
                f"Check logs at: {self.log_dir}/monitor.log"
            )

        print("[Hephaestus] ✓ Monitor is running")

        # Register workflow definitions with backend
        self._register_workflow_definitions()

        # Start watchdog
        self.process_manager.start_watchdog()

        self.running = True
        print("\n[Hephaestus] ✓ All systems ready (headless mode)")

    def _register_workflow_definitions(self):
        """Register workflow definitions with the backend."""
        print(f"[SDK] _register_workflow_definitions called, definitions count: {len(self.definitions)}")
        if not self.definitions:
            print("[SDK] No definitions to register, returning early")
            return

        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/api/workflow-definitions"
        print(f"[SDK] Registering {len(self.definitions)} definitions to {url}")

        for def_id, defn in self.definitions.items():
            print(f"[SDK] Registering definition: {def_id}")
            # Convert Phase objects to dicts for the API
            phases_config = []
            for phase in defn.phases:
                phase_dict = {
                    "id": phase.id,
                    "name": phase.name,
                    "description": phase.description,
                    "done_definitions": phase.done_definitions,
                    "working_directory": phase.working_directory,
                }
                if phase.additional_notes:
                    phase_dict["additional_notes"] = phase.additional_notes
                if phase.outputs:
                    phase_dict["outputs"] = phase.outputs
                if phase.next_steps:
                    phase_dict["next_steps"] = phase.next_steps
                phases_config.append(phase_dict)

            # Convert WorkflowConfig to dict
            workflow_config = None
            if defn.config:
                workflow_config = {
                    "has_result": defn.config.has_result,
                    "enable_tickets": defn.config.enable_tickets,
                    "board_config": defn.config.board_config,
                    "result_criteria": defn.config.result_criteria,
                    "on_result_found": defn.config.on_result_found,
                }
            else:
                workflow_config = {}

            # Add launch_template to workflow_config if present
            if defn.launch_template:
                workflow_config["launch_template"] = defn.launch_template.to_dict()

            payload = {
                "id": def_id,
                "name": defn.name,
                "description": defn.description,
                "phases_config": phases_config,
                "workflow_config": workflow_config,
            }

            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                print(f"[SDK] ✓ Successfully registered definition: {def_id}")
            except Exception as e:
                print(f"[Warning] Failed to register workflow definition '{def_id}': {e}")

    def _start_with_tui(self, timeout: int):
        """Start with TUI interface."""
        from src.sdk.tui import HephaestusTUI

        # Create process manager
        self.process_manager = ProcessManager(self.config, self.log_dir)

        # Start services BEFORE launching TUI
        try:
            # Check Qdrant first
            if not self._check_qdrant_health():
                raise QdrantConnectionError(
                    f"Qdrant is not accessible at {self.config.qdrant_url}. "
                    "Please ensure Qdrant is running (docker run -p 6333:6333 qdrant/qdrant)."
                )

            # Spawn backend process
            self.process_manager.spawn_backend()

            # Spawn monitor process
            self.process_manager.spawn_monitor()

            # Poll backend health
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self._check_backend_health():
                    break
                time.sleep(0.5)
            else:
                self.process_manager.shutdown_all()
                raise HephaestusStartupError(
                    f"Backend did not become healthy within {timeout} seconds. "
                    f"Check logs at: {self.log_dir}/backend.log"
                )

            # Verify monitor
            if not self.process_manager.is_process_alive("monitor"):
                self.process_manager.shutdown_all()
                raise HephaestusStartupError(
                    f"Monitor process failed to start. "
                    f"Check logs at: {self.log_dir}/monitor.log"
                )

            # Start watchdog
            self.process_manager.start_watchdog()

            self.running = True

            # NOW launch the TUI (services are already running)
            tui_app = HephaestusTUI(sdk_instance=self, log_dir=str(self.log_dir))
            tui_app.run()  # Blocking until user quits

        except Exception as e:
            # Clean up on error
            if self.process_manager:
                self.process_manager.shutdown_all()
            raise

    def create_task(
        self,
        description: str,
        phase_id: int,
        priority: str = "medium",
        agent_id: str = "main-session-agent",
        ticket_id: str = None,
    ) -> str:
        """
        Create a new task.

        Args:
            description: Task description
            phase_id: Phase ID for the task
            priority: Task priority ("low", "medium", "high")
            agent_id: Agent ID creating the task
            ticket_id: Associated ticket ID (OPTIONAL - for SDK root tasks creating tickets)

        Returns:
            Task ID

        Raises:
            SDKNotRunningError: If SDK is not running
            InvalidPhaseError: If phase_id doesn't exist
            TaskCreationError: If task creation fails

        Note:
            SDK tasks (especially root tasks created by main-session-agent) typically
            do not need ticket_id as they are often the ticket creators themselves.
            This parameter is provided for consistency with the MCP interface.
        """
        if not self.running:
            raise SDKNotRunningError("SDK is not running. Call start() first.")

        if phase_id not in self.phases_map:
            raise InvalidPhaseError(
                f"Phase {phase_id} does not exist. Available phases: {list(self.phases_map.keys())}"
            )

        # Get the phase to extract done_definitions
        phase = self.phases_map[phase_id]

        # Construct done_definition from the phase's done_definitions list
        done_definition = "\n".join(f"- {item}" for item in phase.done_definitions)

        # Make request to backend
        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/create_task"

        payload = {
            "task_description": description,
            "done_definition": done_definition,
            "ai_agent_id": agent_id,
            "phase_id": str(phase_id),
            "priority": priority,
        }

        # Add ticket_id if provided
        if ticket_id:
            payload["ticket_id"] = ticket_id

        # Add required headers
        headers = {
            "Content-Type": "application/json",
            "X-Agent-ID": agent_id,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get("task_id")

        except Exception as e:
            raise TaskCreationError(f"Failed to create task: {e}")

    def get_task_status(self, task_id: str) -> TaskStatus:
        """
        Get status of a task.

        Args:
            task_id: Task ID

        Returns:
            TaskStatus object

        Raises:
            SDKNotRunningError: If SDK is not running
            TaskNotFoundError: If task doesn't exist
        """
        if not self.running:
            raise SDKNotRunningError("SDK is not running. Call start() first.")

        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/api/tasks/{task_id}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            return TaskStatus(
                id=data["id"],
                status=data["status"],
                description=data["description"],
                agent_id=data.get("agent_id"),
                phase_id=data.get("phase_id"),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                summary=data.get("summary"),
                priority=data.get("priority", "medium"),
            )

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise TaskNotFoundError(f"Task {task_id} not found")
            raise

    def get_tasks(
        self,
        status: Optional[str] = None,
        phase_id: Optional[int] = None,
    ) -> List[TaskStatus]:
        """
        Get list of tasks with optional filtering.

        Args:
            status: Filter by status ("pending", "in_progress", "done", "failed")
            phase_id: Filter by phase ID

        Returns:
            List of TaskStatus objects
        """
        if not self.running:
            raise SDKNotRunningError("SDK is not running. Call start() first.")

        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/api/tasks"

        params = {}
        if status:
            params["status"] = status
        if phase_id:
            params["phase_id"] = phase_id

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            tasks = []
            # The API returns a list directly, not wrapped in {"tasks": [...]}
            task_list = data if isinstance(data, list) else data.get("tasks", [])
            for task_data in task_list:
                tasks.append(
                    TaskStatus(
                        id=task_data["id"],
                        status=task_data["status"],
                        description=task_data["description"],
                        agent_id=task_data.get("agent_id"),
                        phase_id=task_data.get("phase_id"),
                        created_at=datetime.fromisoformat(task_data["created_at"]),
                        updated_at=datetime.fromisoformat(task_data["updated_at"]),
                        summary=task_data.get("summary"),
                        priority=task_data.get("priority", "medium"),
                    )
                )

            return tasks

        except Exception as e:
            print(f"Failed to get tasks: {e}")
            return []

    # ==================== Multi-Workflow Methods ====================

    def start_workflow(
        self,
        definition_id: str,
        description: str,
        working_directory: str = None,
        launch_params: Dict[str, Any] = None,
    ) -> str:
        """
        Start a new workflow execution from a registered definition.

        Args:
            definition_id: ID of the workflow definition to execute
            description: Description/name of this execution (e.g., "Build URL Shortener")
            working_directory: Working directory for this execution
            launch_params: Parameters from launch template to substitute into phases

        Returns:
            workflow_id of the new execution

        Raises:
            SDKNotRunningError: If SDK is not running
            ValueError: If definition_id doesn't exist
        """
        if not self.running:
            raise SDKNotRunningError("SDK is not running. Call start() first.")

        # Check if definition exists
        if definition_id not in self.definitions:
            raise ValueError(
                f"Definition '{definition_id}' not found. "
                f"Available: {list(self.definitions.keys())}"
            )

        # Make request to backend
        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/api/workflow-executions"

        payload = {
            "definition_id": definition_id,
            "description": description,
        }
        if working_directory:
            payload["working_directory"] = working_directory
        if launch_params:
            payload["launch_params"] = launch_params

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get("workflow_id")

        except requests.exceptions.HTTPError as e:
            # Try to get error details from response
            try:
                error_detail = response.json().get("detail", str(e))
            except:
                error_detail = response.text
            raise TaskCreationError(f"Failed to start workflow: {e} - Details: {error_detail}")
        except Exception as e:
            raise TaskCreationError(f"Failed to start workflow: {e}")

    def list_workflow_definitions(self) -> List[WorkflowDefinition]:
        """
        List all registered workflow definitions.

        Returns:
            List of WorkflowDefinition objects
        """
        return list(self.definitions.values())

    def list_workflow_executions(self, status: str = "all") -> List[WorkflowExecution]:
        """
        List all workflow executions.

        Args:
            status: Filter by status ("all", "active", "completed", "paused", "failed")

        Returns:
            List of WorkflowExecution objects

        Raises:
            SDKNotRunningError: If SDK is not running
        """
        if not self.running:
            raise SDKNotRunningError("SDK is not running. Call start() first.")

        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/api/workflow-executions"
        params = {"status": status} if status != "all" else {}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            executions = []

            workflow_list = data if isinstance(data, list) else data.get("workflows", [])
            for wf_data in workflow_list:
                executions.append(
                    WorkflowExecution(
                        id=wf_data["id"],
                        definition_id=wf_data.get("definition_id", "default"),
                        description=wf_data.get("description", ""),
                        status=wf_data["status"],
                        created_at=datetime.fromisoformat(wf_data["created_at"]),
                        active_tasks=wf_data.get("active_tasks", 0),
                        total_tasks=wf_data.get("total_tasks", 0),
                        done_tasks=wf_data.get("done_tasks", 0),
                        failed_tasks=wf_data.get("failed_tasks", 0),
                        active_agents=wf_data.get("active_agents", 0),
                        working_directory=wf_data.get("working_directory"),
                        definition_name=wf_data.get("name"),
                    )
                )

            return executions

        except Exception as e:
            print(f"Failed to list workflow executions: {e}")
            return []

    def get_workflow_execution(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """
        Get details of a specific workflow execution.

        Args:
            workflow_id: The workflow execution ID

        Returns:
            WorkflowExecution object or None if not found

        Raises:
            SDKNotRunningError: If SDK is not running
        """
        if not self.running:
            raise SDKNotRunningError("SDK is not running. Call start() first.")

        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/api/workflows/{workflow_id}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            wf_data = response.json()

            return WorkflowExecution(
                id=wf_data["id"],
                definition_id=wf_data.get("definition_id", "default"),
                description=wf_data.get("description", ""),
                status=wf_data["status"],
                created_at=datetime.fromisoformat(wf_data["created_at"]),
                active_tasks=wf_data.get("active_tasks", 0),
                total_tasks=wf_data.get("total_tasks", 0),
                done_tasks=wf_data.get("done_tasks", 0),
                failed_tasks=wf_data.get("failed_tasks", 0),
                active_agents=wf_data.get("active_agents", 0),
                working_directory=wf_data.get("working_directory"),
                definition_name=wf_data.get("name"),
            )

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            print(f"Failed to get workflow execution: {e}")
            return None

    def create_task_in_workflow(
        self,
        workflow_id: str,
        description: str,
        phase_id: int,
        priority: str = "medium",
        agent_id: str = "main-session-agent",
        done_definition: str = None,
        cwd: str = None,
        ticket_id: str = None,
    ) -> str:
        """
        Create a task in a specific workflow execution.

        This method allows creating tasks in any workflow execution, not just
        the default one.

        Args:
            workflow_id: The workflow execution ID
            description: Task description
            phase_id: Phase ID (order number) for the task
            priority: Task priority ("low", "medium", "high")
            agent_id: Agent ID creating the task
            done_definition: Custom done definition (uses phase default if None)
            cwd: Working directory for the task
            ticket_id: Associated ticket ID

        Returns:
            Task ID

        Raises:
            SDKNotRunningError: If SDK is not running
            TaskCreationError: If task creation fails
        """
        if not self.running:
            raise SDKNotRunningError("SDK is not running. Call start() first.")

        # Build done_definition from phase if not provided
        if done_definition is None and phase_id in self.phases_map:
            phase = self.phases_map[phase_id]
            done_definition = "\n".join(f"- {item}" for item in phase.done_definitions)
        elif done_definition is None:
            done_definition = "Task completed successfully"

        # Make request to backend
        url = f"http://{self.config.mcp_host}:{self.config.mcp_port}/create_task"

        payload = {
            "task_description": description,
            "done_definition": done_definition,
            "ai_agent_id": agent_id,
            "phase_id": str(phase_id),
            "priority": priority,
            "workflow_id": workflow_id,
        }

        if ticket_id:
            payload["ticket_id"] = ticket_id
        if cwd:
            payload["cwd"] = cwd

        headers = {
            "Content-Type": "application/json",
            "X-Agent-ID": agent_id,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get("task_id")

        except Exception as e:
            raise TaskCreationError(f"Failed to create task: {e}")

    def is_healthy(self) -> Dict[str, bool]:
        """
        Check health of all services.

        Returns:
            Dictionary with component health status
        """
        if not self.running or not self.process_manager:
            return {
                "backend_process": False,
                "monitor_process": False,
                "backend_api": False,
                "qdrant": False,
                "overall": False,
            }

        backend_process = self.process_manager.is_process_alive("backend")
        monitor_process = self.process_manager.is_process_alive("monitor")
        backend_api = self._check_backend_health()
        qdrant = self._check_qdrant_health()

        return {
            "backend_process": backend_process,
            "monitor_process": monitor_process,
            "backend_api": backend_api,
            "qdrant": qdrant,
            "overall": all([backend_process, monitor_process, backend_api, qdrant]),
        }

    def shutdown(self, graceful: bool = True, timeout: int = 10) -> None:
        """
        Shutdown all services.

        Args:
            graceful: Use graceful shutdown (SIGTERM) vs force kill (SIGKILL)
            timeout: Maximum seconds to wait for graceful shutdown
        """
        if not self.running:
            return

        print("\n[Hephaestus] Shutting down...")

        if self.process_manager:
            self.process_manager.shutdown_all(graceful=graceful, timeout=timeout)

        # Clean up temp phases directory
        if self.temp_phases_dir and self.temp_phases_dir.exists():
            shutil.rmtree(self.temp_phases_dir)

        self.running = False
        print("[Hephaestus] ✓ Shutdown complete")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False
