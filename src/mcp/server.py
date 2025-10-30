"""MCP Server implementation for Hephaestus."""

from typing import Dict, Any, Optional, List
import json
import uuid
import logging
import os
import time
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import asyncio

from src.core.simple_config import get_config
from src.core.database import DatabaseManager, Task, Agent, Memory, Phase, ValidationReview, AgentResult, WorkflowResult, Workflow, get_db
from src.core.worktree_manager import WorktreeManager
from src.interfaces import get_cli_agent
from src.memory.vector_store import VectorStoreManager
from src.agents.manager import AgentManager
from src.memory.rag import RAGSystem
from src.mcp.api import create_frontend_routes
from src.phases import PhaseManager
from src.auth.auth_api import router as auth_router
from src.services.workflow_result_service import WorkflowResultService
from src.services.result_validator_service import ResultValidatorService
from src.services.embedding_service import EmbeddingService
from src.services.task_similarity_service import TaskSimilarityService
from src.services.queue_service import QueueService
from src.services.ticket_service import TicketService
from src.services.ticket_history_service import TicketHistoryService
from src.services.ticket_search_service import TicketSearchService

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hephaestus MCP Server",
    description="Model Context Protocol server for AI agent orchestration",
    version="1.0.0",
)

# Add CORS middleware
config = get_config()
if config.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Request/Response Models
class CreateTaskRequest(BaseModel):
    """Request model for creating a task."""

    task_description: str = Field(..., description="Raw task description")
    done_definition: str = Field(..., description="What constitutes completion")
    ai_agent_id: str = Field(..., description="ID of requesting agent")
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high)$")
    parent_task_id: Optional[str] = Field(default=None, description="Parent task ID for sub-tasks")
    phase_id: Optional[str] = Field(default=None, description="Phase ID for workflow-based tasks")
    phase_order: Optional[int] = Field(default=None, description="Phase order number (alternative to phase_id)")
    cwd: Optional[str] = Field(default=None, description="Working directory for the task")
    ticket_id: Optional[str] = Field(default=None, description="Associated ticket ID (required when ticket tracking enabled)")


class CreateTaskResponse(BaseModel):
    """Response model for task creation."""

    task_id: str
    enriched_description: str
    assigned_agent_id: str
    estimated_completion_time: int  # minutes
    status: str


class UpdateTaskStatusRequest(BaseModel):
    """Request model for updating task status."""

    task_id: str
    status: str = Field(..., pattern="^(done|failed)$")
    summary: str = Field(..., description="What was accomplished")
    key_learnings: List[str] = Field(..., description="Important discoveries")
    code_changes: Optional[List[str]] = Field(default=None, description="Files modified/created")
    failure_reason: Optional[str] = Field(default=None, description="Required if status is 'failed'")


class UpdateTaskStatusResponse(BaseModel):
    """Response model for task status update."""

    success: bool
    message: str
    termination_scheduled: bool


class SaveMemoryRequest(BaseModel):
    """Request model for saving memory."""

    ai_agent_id: str
    memory_content: str
    memory_type: str = Field(
        ...,
        pattern="^(error_fix|discovery|decision|learning|warning|codebase_knowledge)$"
    )
    related_files: Optional[List[str]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)


class SaveMemoryResponse(BaseModel):
    """Response model for memory saving."""

    memory_id: str
    indexed: bool
    similar_memories: Optional[List[str]] = Field(default=None)


class ReportResultsRequest(BaseModel):
    """Request model for reporting task results."""

    task_id: str = Field(..., description="ID of the task")
    markdown_file_path: str = Field(..., description="Path to markdown file with results")
    result_type: str = Field(
        ...,
        pattern="^(implementation|analysis|fix|design|test|documentation)$",
        description="Type of result"
    )
    summary: str = Field(..., description="Brief summary of the result")


class ReportResultsResponse(BaseModel):
    """Response model for result reporting."""

    status: str = Field(..., description="stored or error")
    result_id: str = Field(..., description="ID of the stored result")
    task_id: str = Field(..., description="ID of the task")
    agent_id: str = Field(..., description="ID of the agent")
    verification_status: str = Field(..., description="Verification status")
    created_at: str = Field(..., description="ISO timestamp of creation")


class GiveValidationReviewRequest(BaseModel):
    """Request model for validation review submission."""

    task_id: str = Field(..., description="ID of task being validated")
    validator_agent_id: str = Field(..., description="ID of validator agent")
    validation_passed: bool = Field(..., description="Whether validation passed")
    feedback: str = Field(..., description="Detailed feedback")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence supporting decision")
    recommendations: List[str] = Field(default_factory=list, description="Follow-up task recommendations")


class GiveValidationReviewResponse(BaseModel):
    """Response model for validation review."""

    status: str = Field(..., description="completed, needs_work, or error")
    message: str = Field(..., description="Status message")
    iteration: Optional[int] = Field(default=None, description="Current iteration number")


class SubmitResultRequest(BaseModel):
    """Request model for submitting workflow results."""

    markdown_file_path: str = Field(..., description="Path to markdown file with result evidence")
    explanation: str = Field(..., description="Brief explanation of what was accomplished")
    evidence: Optional[List[str]] = Field(default=None, description="List of evidence supporting completion")


class SubmitResultResponse(BaseModel):
    """Response model for result submission."""

    status: str = Field(..., description="submitted, rejected, or error")
    result_id: Optional[str] = Field(default=None, description="ID of the submitted result")
    workflow_id: str = Field(..., description="ID of the workflow")
    agent_id: str = Field(..., description="ID of the agent")
    validation_triggered: bool = Field(..., description="Whether validation was triggered")
    message: str = Field(..., description="Status message")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp of creation")


class SubmitResultValidationRequest(BaseModel):
    """Request model for result validation submission."""

    result_id: str = Field(..., description="ID of result being validated")
    validation_passed: bool = Field(..., description="Whether validation passed")
    feedback: str = Field(..., description="Detailed validation feedback")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence supporting decision")


class SubmitResultValidationResponse(BaseModel):
    """Response model for result validation."""

    status: str = Field(..., description="completed, workflow_terminated, or error")
    message: str = Field(..., description="Status message")
    workflow_action_taken: Optional[str] = Field(default=None, description="Action taken on workflow")
    result_id: str = Field(..., description="ID of the validated result")


class BroadcastMessageRequest(BaseModel):
    """Request model for broadcasting a message to all agents."""

    message: str = Field(..., description="Message content to broadcast")


# Ticket Tracking System Request/Response Models
class CreateTicketRequest(BaseModel):
    """Request model for creating a ticket."""

    workflow_id: Optional[str] = Field(default=None, description="ID of the workflow (auto-detected from agent's task if not provided)")
    title: str = Field(..., min_length=3, max_length=500, description="Short, descriptive title")
    description: str = Field(..., min_length=10, description="Detailed description")
    ticket_type: str = Field(default="task", description="Type of ticket (bug, feature, improvement, task, spike)")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$", description="Priority level")
    initial_status: Optional[str] = Field(default=None, description="Initial status (if None, uses board_config.initial_status)")
    assigned_agent_id: Optional[str] = Field(default=None, description="Optional agent to assign to")
    parent_ticket_id: Optional[str] = Field(default=None, description="Parent ticket ID for sub-tickets")
    blocked_by_ticket_ids: List[str] = Field(default_factory=list, description="List of ticket IDs blocking this ticket")
    tags: List[str] = Field(default_factory=list, description="List of tags for categorization")
    related_task_ids: List[str] = Field(default_factory=list, description="List of related task IDs")


class CreateTicketResponse(BaseModel):
    """Response model for ticket creation."""

    success: bool
    ticket_id: str
    status: str
    message: str
    embedding_created: bool
    similar_tickets: List[Dict[str, Any]] = Field(default_factory=list)


class UpdateTicketRequest(BaseModel):
    """Request model for updating a ticket."""

    ticket_id: str = Field(..., description="ID of the ticket to update")
    updates: Dict[str, Any] = Field(..., description="Fields to update")
    update_comment: Optional[str] = Field(default=None, description="Optional comment explaining changes")


class UpdateTicketResponse(BaseModel):
    """Response model for ticket update."""

    success: bool
    ticket_id: str
    fields_updated: List[str]
    message: str
    embedding_updated: bool


class ChangeTicketStatusRequest(BaseModel):
    """Request model for changing ticket status."""

    ticket_id: str = Field(..., description="ID of the ticket")
    new_status: str = Field(..., description="New status to move to")
    comment: str = Field(..., min_length=10, description="Required comment explaining status change")
    commit_sha: Optional[str] = Field(default=None, description="Optional commit SHA to link")


class ChangeTicketStatusResponse(BaseModel):
    """Response model for status change."""

    success: bool
    ticket_id: str
    old_status: str
    new_status: str
    message: str
    blocked: bool = False
    blocking_ticket_ids: List[str] = Field(default_factory=list)


class AddCommentRequest(BaseModel):
    """Request model for adding a comment to a ticket."""

    ticket_id: str = Field(..., description="ID of the ticket")
    comment_text: str = Field(..., min_length=1, description="The comment text")
    comment_type: str = Field(default="general", description="Type of comment (general, status_change, blocker, resolution)")
    mentions: List[str] = Field(default_factory=list, description="List of mentioned agent/ticket IDs")
    attachments: List[str] = Field(default_factory=list, description="List of file paths")


class AddCommentResponse(BaseModel):
    """Response model for adding a comment."""

    success: bool
    comment_id: str
    ticket_id: str
    message: str


class SearchTicketsRequest(BaseModel):
    """Request model for searching tickets."""

    workflow_id: Optional[str] = Field(default=None, description="ID of the workflow (auto-detected from agent's task if not provided)")
    query: str = Field(..., min_length=3, description="Search query (natural language)")
    search_type: str = Field(default="hybrid", pattern="^(semantic|keyword|hybrid)$", description="Search type (default: hybrid)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Optional filters (status, priority, type, etc.)")
    limit: int = Field(default=10, ge=1, le=50, description="Max number of results")
    include_comments: bool = Field(default=True, description="Search in comments too")


class TicketSearchResult(BaseModel):
    """Individual ticket search result."""

    ticket_id: str
    title: str
    description: str
    status: str
    priority: str
    ticket_type: str
    relevance_score: float
    matched_in: List[str] = Field(default_factory=list)
    preview: str
    created_at: str
    assigned_agent_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SearchTicketsResponse(BaseModel):
    """Response model for ticket search."""

    success: bool
    query: str
    results: List[TicketSearchResult]
    total_found: int
    search_time_ms: float


class TicketStats(BaseModel):
    """Ticket statistics for a workflow."""

    total_tickets: int
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_agent: Dict[str, int] = Field(default_factory=dict)
    blocked_count: int = 0
    resolved_count: int = 0
    avg_comments_per_ticket: float = 0.0
    avg_commits_per_ticket: float = 0.0
    created_today: int = 0
    completed_today: int = 0
    velocity_last_7_days: int = 0


class TicketStatsResponse(BaseModel):
    """Response model for ticket statistics."""

    success: bool
    workflow_id: str
    stats: TicketStats
    board_config: Optional[dict] = None


class GetTicketsRequest(BaseModel):
    """Request model for getting/listing tickets."""

    workflow_id: str = Field(..., description="ID of the workflow")
    status: Optional[str] = Field(default=None, description="Filter by status")
    ticket_type: Optional[str] = Field(default=None, description="Filter by type")
    priority: Optional[str] = Field(default=None, description="Filter by priority")
    assigned_agent_id: Optional[str] = Field(default=None, description="Filter by assigned agent")
    include_completed: bool = Field(default=True, description="Include completed tickets")
    limit: int = Field(default=50, ge=1, le=200, description="Max number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    sort_by: str = Field(default="created_at", pattern="^(created_at|updated_at|priority|status)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class TicketDetail(BaseModel):
    """Detailed ticket information."""

    id: str  # Primary ticket ID
    ticket_id: str  # Alias for backwards compatibility
    workflow_id: str
    title: str
    description: str
    ticket_type: str
    priority: str
    status: str
    created_by_agent_id: str
    assigned_agent_id: Optional[str] = None
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    comment_count: int = 0
    commit_count: int = 0
    is_blocked: bool = False
    blocked_by_ticket_ids: List[str] = Field(default_factory=list)
    is_resolved: bool = False


class GetTicketsResponse(BaseModel):
    """Response model for get tickets."""

    success: bool
    tickets: List[TicketDetail]
    total_count: int
    has_more: bool


class ResolveTicketRequest(BaseModel):
    """Request model for resolving a ticket."""

    ticket_id: str = Field(..., description="ID of the ticket to resolve")
    resolution_comment: str = Field(..., min_length=10, description="Comment explaining resolution")
    commit_sha: Optional[str] = Field(default=None, description="Commit that resolved the ticket")


class ResolveTicketResponse(BaseModel):
    """Response model for resolve ticket."""

    success: bool
    ticket_id: str
    message: str
    unblocked_tickets: List[str] = Field(default_factory=list)


class LinkCommitRequest(BaseModel):
    """Request model for linking a commit to a ticket."""

    ticket_id: str = Field(..., description="ID of the ticket")
    commit_sha: str = Field(..., description="Git commit SHA")
    commit_message: Optional[str] = Field(default=None, description="Commit message (auto-fetched if not provided)")


class LinkCommitResponse(BaseModel):
    """Response model for link commit."""

    success: bool
    ticket_id: str
    commit_sha: str
    message: str


class RequestTicketClarificationRequest(BaseModel):
    """Request model for ticket clarification."""

    ticket_id: str = Field(..., description="ID of the ticket needing clarification")
    conflict_description: str = Field(..., min_length=20, description="Clear description of the conflict or issue")
    context: str = Field(default="", description="Additional context relevant to the clarification")
    potential_solutions: List[str] = Field(default_factory=list, description="List of potential solutions being considered")


class RequestTicketClarificationResponse(BaseModel):
    """Response model for ticket clarification."""

    success: bool
    ticket_id: str
    clarification: str  # Markdown-formatted detailed response
    comment_id: str  # ID of the comment where clarification was stored
    message: str


class FileDiff(BaseModel):
    """File diff information for commit."""

    path: str
    status: str  # modified, added, deleted, renamed
    insertions: int
    deletions: int
    diff: str  # Unified diff content
    language: str  # For syntax highlighting
    old_path: Optional[str] = None  # For renamed files


class CommitDiffResponse(BaseModel):
    """Response model for commit diff."""

    success: bool
    commit_sha: str
    commit_message: str
    author: str
    commit_timestamp: str
    files_changed: int
    total_insertions: int
    total_deletions: int
    total_files: int
    files: List[FileDiff]


class BroadcastMessageResponse(BaseModel):
    """Response model for message broadcast."""

    success: bool = Field(..., description="Whether broadcast was successful")
    recipient_count: int = Field(..., description="Number of agents message was sent to")
    message: str = Field(..., description="Status message")


class SendMessageRequest(BaseModel):
    """Request model for sending a direct message to an agent."""

    recipient_agent_id: str = Field(..., description="ID of the agent to send message to")
    message: str = Field(..., description="Message content")


class SendMessageResponse(BaseModel):
    """Response model for direct message."""

    success: bool = Field(..., description="Whether message was sent successfully")
    message: str = Field(..., description="Status message")


# Server state
class ServerState:
    """Global server state."""

    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.vector_store: Optional[VectorStoreManager] = None
        self.llm_provider = None
        self.agent_manager: Optional[AgentManager] = None
        self.rag_system: Optional[RAGSystem] = None
        self.phase_manager: Optional[PhaseManager] = None
        self.worktree_manager: Optional[WorktreeManager] = None
        self.result_validator_service: Optional[ResultValidatorService] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.task_similarity_service: Optional[TaskSimilarityService] = None
        self.queue_service: Optional[QueueService] = None
        self.active_websockets: List[WebSocket] = []
        self.sse_queues: List[asyncio.Queue] = []
        self.background_queue_processor_task: Optional[asyncio.Task] = None
        self.shutdown_event: asyncio.Event = asyncio.Event()

    async def initialize(self):
        """Initialize server components."""
        config = get_config()

        # Initialize database
        self.db_manager = DatabaseManager(str(config.database_path))
        self.db_manager.create_tables()

        # Initialize vector store
        self.vector_store = VectorStoreManager(
            qdrant_url=config.qdrant_url,
            collection_prefix=config.qdrant_collection_prefix,
        )

        # Initialize LLM provider using get_llm_provider()
        # This automatically handles multi-provider config or falls back to legacy single-provider
        from src.interfaces.llm_interface import get_llm_provider
        self.llm_provider = get_llm_provider()

        # Initialize phase manager first (needed by agent manager)
        self.phase_manager = PhaseManager(
            db_manager=self.db_manager
        )

        # Initialize worktree manager
        self.worktree_manager = WorktreeManager(
            db_manager=self.db_manager
        )

        # Initialize agent manager with phase manager
        self.agent_manager = AgentManager(
            db_manager=self.db_manager,
            llm_provider=self.llm_provider,
            phase_manager=self.phase_manager,
        )

        # Initialize RAG system
        self.rag_system = RAGSystem(
            vector_store=self.vector_store,
            llm_provider=self.llm_provider,
        )

        # Initialize result validator service
        self.result_validator_service = ResultValidatorService(
            db_manager=self.db_manager,
            phase_manager=self.phase_manager,
        )

        # Initialize embedding and similarity services (only if OpenAI is configured and dedup enabled)
        if config.openai_api_key and config.task_dedup_enabled:
            self.embedding_service = EmbeddingService(config.openai_api_key)
            self.task_similarity_service = TaskSimilarityService(
                self.db_manager,
                self.embedding_service
            )
            logger.info("Task deduplication service initialized")
        else:
            if not config.openai_api_key:
                logger.warning("OpenAI API key not configured - task deduplication disabled")
            if not config.task_dedup_enabled:
                logger.info("Task deduplication disabled by configuration")

        # Initialize queue service
        self.queue_service = QueueService(
            db_manager=self.db_manager,
            max_concurrent_agents=config.max_concurrent_agents
        )
        logger.info(f"Queue service initialized with max_concurrent_agents={config.max_concurrent_agents}")

        logger.info("Server state initialized successfully")

    async def broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected WebSocket and SSE clients."""
        disconnected = []
        for websocket in self.active_websockets:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)

        # Remove disconnected clients
        for ws in disconnected:
            self.active_websockets.remove(ws)

        # Send to SSE clients
        for queue in self.sse_queues:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("SSE queue full, skipping event")


# Initialize server state
server_state = ServerState()


def get_single_active_workflow() -> Optional[str]:
    """
    Get the ID of the single active workflow in the system.

    Returns:
        workflow_id if exactly one workflow exists, None otherwise
    """
    try:
        with get_db() as session:
            workflows = session.query(Workflow).filter(
                Workflow.status.in_(["active", "paused"])
            ).all()

            if len(workflows) == 1:
                return workflows[0].id
            elif len(workflows) == 0:
                logger.warning("No active workflows found in the system")
                return None
            else:
                logger.warning(f"Multiple workflows found ({len(workflows)}), cannot auto-select")
                return None
    except Exception as e:
        logger.error(f"Error getting single active workflow: {e}")
        return None


@app.on_event("startup")
async def startup_event():
    """Initialize server on startup."""
    logger.info("Starting Hephaestus MCP Server...")
    await server_state.initialize()

    # Add frontend API routes
    api_router = create_frontend_routes(server_state.db_manager, server_state.agent_manager, server_state.phase_manager)
    app.include_router(api_router)

    # Add authentication routes
    app.include_router(auth_router)

    # Load phases if folder is specified
    import os
    from pathlib import Path

    logger.info("=== PHASE LOADING DEBUG ===")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Environment variables starting with HEPHAESTUS: {[k for k in os.environ.keys() if 'HEPHAESTUS' in k]}")

    phases_folder = os.environ.get("HEPHAESTUS_PHASES_FOLDER")
    logger.info(f"HEPHAESTUS_PHASES_FOLDER value: '{phases_folder}'")

    if phases_folder:
        logger.info(f"Attempting to load workflow phases from: {phases_folder}")

        # Check if folder exists
        full_path = Path(phases_folder)
        if not full_path.is_absolute():
            full_path = Path(os.getcwd()) / phases_folder

        logger.info(f"Full path to phases folder: {full_path}")
        logger.info(f"Folder exists: {full_path.exists()}")
        logger.info(f"Is directory: {full_path.is_dir() if full_path.exists() else 'N/A'}")

        if full_path.exists() and full_path.is_dir():
            # List files in directory
            files = list(full_path.glob("*.yaml"))
            logger.info(f"YAML files found: {len(files)}")
            for f in files:
                logger.info(f"  - {f.name}")

        try:
            from src.phases import PhaseLoader
            logger.info("PhaseLoader imported successfully")

            # Load phases from folder
            logger.info(f"Calling PhaseLoader.load_phases_from_folder('{phases_folder}')")
            workflow_def = PhaseLoader.load_phases_from_folder(phases_folder)
            logger.info(f"Loaded workflow '{workflow_def.name}' with {len(workflow_def.phases)} phases")

            # Load phases configuration (for ticket tracking, result handling, etc.)
            logger.info(f"Loading phases_config.yaml from '{phases_folder}'")
            phases_config = PhaseLoader.load_phases_config(phases_folder)
            logger.info(f"Loaded phases config: enable_tickets={phases_config.enable_tickets}, has_result={phases_config.has_result}")

            # Initialize workflow in database
            logger.info("Initializing workflow in database...")
            workflow_id = server_state.phase_manager.initialize_workflow(workflow_def, phases_config)
            logger.info(f"Initialized workflow with ID: {workflow_id}")

            # Log phase names
            logger.info("Loaded phases:")
            for phase in workflow_def.phases:
                logger.info(f"  Phase {phase.order}: {phase.name}")
                logger.info(f"    - Description: {phase.description[:100]}...")
                logger.info(f"    - Done definitions: {len(phase.done_definitions)} items")

        except ImportError as e:
            logger.error(f"Failed to import PhaseLoader: {e}")
            import traceback
            logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(f"Failed to load phases: {e}")
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            # Don't fail server startup, just run without phases
    else:
        logger.info("No phases folder specified - running in standard mode")
        logger.info("To load phases, set HEPHAESTUS_PHASES_FOLDER environment variable")

    logger.info("=== END PHASE LOADING DEBUG ===")

    # Start background queue processor
    logger.info("Starting background queue processor...")
    server_state.background_queue_processor_task = asyncio.create_task(background_queue_processor())
    logger.info("Background queue processor task created")

    logger.info("Server started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Hephaestus MCP Server...")

    # Stop background queue processor
    logger.info("Stopping background queue processor...")
    server_state.shutdown_event.set()
    if server_state.background_queue_processor_task:
        try:
            await asyncio.wait_for(server_state.background_queue_processor_task, timeout=5.0)
            logger.info("Background queue processor stopped")
        except asyncio.TimeoutError:
            logger.warning("Background queue processor did not stop gracefully, cancelling...")
            server_state.background_queue_processor_task.cancel()

    # Close all WebSocket connections
    for ws in server_state.active_websockets:
        await ws.close()


def verify_agent_id(agent_id: str = Header(None, alias="X-Agent-ID")) -> str:
    """Verify agent ID from header."""
    if not agent_id:
        raise HTTPException(status_code=401, detail="Agent ID required in X-Agent-ID header")
    return agent_id


async def process_queue():
    """Process the next queued task by creating an agent for it.

    Only creates an agent if we're under the max concurrent agent limit.
    """
    try:
        # Check if we should queue (i.e., at capacity)
        if server_state.queue_service.should_queue_task():
            logger.debug("At capacity - not processing queue")
            return

        # Get next task from queue
        next_task = server_state.queue_service.get_next_queued_task()

        if not next_task:
            logger.debug("No queued tasks to process")
            return

        logger.info(f"Processing queued task {next_task.id} (priority={next_task.priority}, boosted={next_task.priority_boosted})")

        # Dequeue the task
        server_state.queue_service.dequeue_task(next_task.id)

        # BUG FIX: Check if task needs enrichment (was blocked on creation and skipped enrichment)
        # Tasks created with placeholder "[Processing] ..." need real LLM enrichment
        needs_enrichment = not next_task.enriched_description or next_task.enriched_description.startswith("[Processing]")
        logger.info(f"[QUEUE_ENRICHMENT] Task {next_task.id} enrichment check:")
        logger.info(f"[QUEUE_ENRICHMENT]   - enriched_description exists: {bool(next_task.enriched_description)}")
        logger.info(f"[QUEUE_ENRICHMENT]   - enriched_description value: {next_task.enriched_description[:100] if next_task.enriched_description else 'NULL'}")
        logger.info(f"[QUEUE_ENRICHMENT]   - starts with [Processing]: {next_task.enriched_description.startswith('[Processing]') if next_task.enriched_description else False}")
        logger.info(f"[QUEUE_ENRICHMENT]   - NEEDS ENRICHMENT: {needs_enrichment}")

        if needs_enrichment:
            logger.info(f"[QUEUE_ENRICHMENT] ========== STARTING ENRICHMENT PIPELINE FOR TASK {next_task.id} ==========")
            logger.info(f"[QUEUE_ENRICHMENT] Task phase_id (from DB): {next_task.phase_id} (type: {type(next_task.phase_id).__name__})")
            logger.info(f"[QUEUE_ENRICHMENT] Task raw_description: {next_task.raw_description[:200]}")

            # Get phase context for enrichment
            # CRITICAL: phase_id might be an integer (phase order) or UUID string
            phase_context_str = ""
            workflow_id = None
            phase_id_uuid = None

            if next_task.phase_id and server_state.phase_manager:
                # BUG FIX: Convert phase order number to UUID (same logic as process_task_async)
                logger.info(f"[QUEUE_ENRICHMENT] Converting phase_id to UUID if needed")
                logger.info(f"[QUEUE_ENRICHMENT]   - Original phase_id: {next_task.phase_id}")
                logger.info(f"[QUEUE_ENRICHMENT]   - Is digit check: {str(next_task.phase_id).isdigit()}")

                if str(next_task.phase_id).isdigit():
                    # phase_id is a phase order number - convert to UUID
                    logger.info(f"[QUEUE_ENRICHMENT] phase_id={next_task.phase_id} is an ORDER number - converting to UUID")
                    phase_id_uuid = server_state.phase_manager.get_phase_for_task(
                        phase_id=None,
                        order=int(next_task.phase_id),
                        requesting_agent_id="system"
                    )
                    logger.info(f"[QUEUE_ENRICHMENT] ✓ Converted phase order {next_task.phase_id} → UUID: {phase_id_uuid}")
                else:
                    # phase_id is already a UUID
                    logger.info(f"[QUEUE_ENRICHMENT] phase_id={next_task.phase_id} is a UUID - using directly")
                    phase_id_uuid = next_task.phase_id

                logger.info(f"[QUEUE_ENRICHMENT] Fetching phase context for UUID: {phase_id_uuid}")
                phase_context = server_state.phase_manager.get_phase_context(phase_id_uuid)
                if phase_context:
                    phase_context_str = phase_context.to_prompt_context()
                    workflow_id = phase_context.workflow_id
                    logger.info(f"[QUEUE_ENRICHMENT] ✓ Got phase context (length={len(phase_context_str)}, workflow_id={workflow_id})")
                    logger.info(f"[QUEUE_ENRICHMENT] Phase context preview: {phase_context_str[:300]}")
                else:
                    logger.warning(f"[QUEUE_ENRICHMENT] ✗ No phase context returned for phase UUID={phase_id_uuid}")
            else:
                logger.warning(f"[QUEUE_ENRICHMENT] ✗ Skipping phase context (phase_id={next_task.phase_id}, phase_manager={bool(server_state.phase_manager)})")

            # BUG FIX: If we don't have workflow_id from phase, try to get it from single active workflow
            if not workflow_id:
                logger.info(f"[QUEUE_ENRICHMENT] No workflow_id from phase context - trying get_single_active_workflow()")
                workflow_id = get_single_active_workflow()
                if workflow_id:
                    logger.info(f"[QUEUE_ENRICHMENT] ✓ Got workflow_id from single active workflow: {workflow_id}")
                else:
                    logger.warning(f"[QUEUE_ENRICHMENT] ✗ Could not get workflow_id from single active workflow")

            # Retrieve RAG memories for enrichment
            logger.info(f"[QUEUE_ENRICHMENT] Retrieving RAG memories for enrichment")
            context_memories_for_enrichment = await server_state.rag_system.retrieve_for_task(
                task_description=next_task.raw_description,
                requesting_agent_id="system",
            )
            logger.info(f"[QUEUE_ENRICHMENT] ✓ Retrieved {len(context_memories_for_enrichment)} memories from RAG")

            # Get project context for enrichment
            logger.info(f"[QUEUE_ENRICHMENT] Getting project context")
            project_context_for_enrichment = await server_state.agent_manager.get_project_context()
            logger.info(f"[QUEUE_ENRICHMENT] ✓ Got project context (length={len(project_context_for_enrichment)})")

            if phase_context_str:
                project_context_for_enrichment = f"{project_context_for_enrichment}\n\n{phase_context_str}"
                logger.info(f"[QUEUE_ENRICHMENT] ✓ Added phase context to project context (total length={len(project_context_for_enrichment)})")

            # Enrich task using LLM
            logger.info(f"[QUEUE_ENRICHMENT] Calling LLM for task enrichment")
            logger.info(f"[QUEUE_ENRICHMENT]   - task_description: {next_task.raw_description[:100]}")
            logger.info(f"[QUEUE_ENRICHMENT]   - done_definition: {next_task.done_definition}")
            logger.info(f"[QUEUE_ENRICHMENT]   - context memories: {len(context_memories_for_enrichment)} items")
            logger.info(f"[QUEUE_ENRICHMENT]   - phase_context provided: {bool(phase_context_str)}")

            context_strings = [mem.get("content", "") for mem in context_memories_for_enrichment]
            enriched_task = await server_state.llm_provider.enrich_task(
                task_description=next_task.raw_description,
                done_definition=next_task.done_definition or "Task completed successfully",
                context=context_strings,
                phase_context=phase_context_str if phase_context_str else None,
            )
            logger.info(f"[QUEUE_ENRICHMENT] ✓ LLM enrichment complete!")
            logger.info(f"[QUEUE_ENRICHMENT] Enriched description: {enriched_task['enriched_description'][:200]}")
            logger.info(f"[QUEUE_ENRICHMENT] Estimated complexity: {enriched_task.get('estimated_complexity', 'N/A')}")

            # Update task with enriched data
            logger.info(f"[QUEUE_ENRICHMENT] Updating task in database")
            session = server_state.db_manager.get_session()
            try:
                task = session.query(Task).filter_by(id=next_task.id).first()
                if task:
                    task.enriched_description = enriched_task["enriched_description"]
                    task.estimated_complexity = enriched_task.get("estimated_complexity", 5)
                    logger.info(f"[QUEUE_ENRICHMENT] ✓ Set enriched_description and estimated_complexity")

                    # BUG FIX: Update phase_id to UUID if we converted it from order
                    if phase_id_uuid and phase_id_uuid != next_task.phase_id:
                        logger.info(f"[QUEUE_ENRICHMENT] Updating phase_id from order {next_task.phase_id} to UUID {phase_id_uuid}")
                        task.phase_id = phase_id_uuid
                        next_task.phase_id = phase_id_uuid  # Update in-memory object too
                        logger.info(f"[QUEUE_ENRICHMENT] ✓ Updated phase_id to UUID in database")

                    # BUG FIX: Always set workflow_id (to match process_task_async behavior)
                    if workflow_id:
                        task.workflow_id = workflow_id
                        logger.info(f"[QUEUE_ENRICHMENT] ✓ Set workflow_id: {workflow_id}")
                    else:
                        logger.warning(f"[QUEUE_ENRICHMENT] ✗ No workflow_id to set")

                    # Check if phase has validation enabled
                    if phase_id_uuid:
                        from src.core.database import Phase
                        phase = session.query(Phase).filter_by(id=phase_id_uuid).first()
                        if phase and phase.validation:
                            if phase.validation.get("enabled", True):
                                task.validation_enabled = True
                                logger.info(f"[QUEUE_ENRICHMENT] ✓ Inherited validation from phase (enabled=True)")
                            else:
                                logger.info(f"[QUEUE_ENRICHMENT] Phase validation explicitly disabled")
                        else:
                            logger.info(f"[QUEUE_ENRICHMENT] No validation config in phase")

                    session.commit()
                    logger.info(f"[QUEUE_ENRICHMENT] ✓ Database commit successful")

                    # Store enriched_task dict for passing to create_agent_for_task
                    next_task.enriched_description = enriched_task["enriched_description"]
                    next_task._enriched_task_dict = enriched_task  # Store full dict
                    logger.info(f"[QUEUE_ENRICHMENT] ✓ Stored full enriched_task dict for agent creation")
                    logger.info(f"[QUEUE_ENRICHMENT] ========== ENRICHMENT PIPELINE COMPLETE FOR TASK {next_task.id} ==========")
                else:
                    logger.error(f"[QUEUE_ENRICHMENT] ✗ Task {next_task.id} not found in database!")
            finally:
                session.close()
        else:
            logger.info(f"[QUEUE_ENRICHMENT] Task {next_task.id} already enriched - skipping enrichment pipeline")

        # BUG FIX: Refresh task from database first to get enriched_description for RAG retrieval
        session_pre = server_state.db_manager.get_session()
        try:
            refreshed_task_pre = session_pre.query(Task).filter_by(id=next_task.id).first()
            task_description_for_rag = refreshed_task_pre.enriched_description or refreshed_task_pre.raw_description
        finally:
            session_pre.close()

        # Get project context
        logger.info(f"[QUEUE_AGENT_CREATE] Getting project context for task {next_task.id}")
        project_context = await server_state.agent_manager.get_project_context()
        logger.info(f"[QUEUE_AGENT_CREATE] ✓ Got project context (length={len(project_context)})")

        # Get phase context if applicable
        # BUG FIX: Convert phase order to UUID (same as enrichment above)
        phase_id_for_agent = None
        if next_task.phase_id and server_state.phase_manager:
            logger.info(f"[QUEUE_AGENT_CREATE] Converting phase_id for agent creation")
            logger.info(f"[QUEUE_AGENT_CREATE]   - phase_id from task: {next_task.phase_id}")

            if str(next_task.phase_id).isdigit():
                logger.info(f"[QUEUE_AGENT_CREATE] phase_id={next_task.phase_id} is ORDER - converting to UUID")
                phase_id_for_agent = server_state.phase_manager.get_phase_for_task(
                    phase_id=None,
                    order=int(next_task.phase_id),
                    requesting_agent_id="system"
                )
                logger.info(f"[QUEUE_AGENT_CREATE] ✓ Converted order {next_task.phase_id} → UUID: {phase_id_for_agent}")
            else:
                logger.info(f"[QUEUE_AGENT_CREATE] phase_id={next_task.phase_id} is UUID - using directly")
                phase_id_for_agent = next_task.phase_id

            logger.info(f"[QUEUE_AGENT_CREATE] Fetching phase context for agent with UUID: {phase_id_for_agent}")
            phase_context = server_state.phase_manager.get_phase_context(phase_id_for_agent)
            if phase_context:
                project_context = f"{project_context}\n\n{phase_context.to_prompt_context()}"
                logger.info(f"[QUEUE_AGENT_CREATE] ✓ Added phase context to project context (total={len(project_context)})")
            else:
                logger.warning(f"[QUEUE_AGENT_CREATE] ✗ No phase context for UUID: {phase_id_for_agent}")

        # Retrieve relevant memories (using enriched description if available)
        logger.info(f"[QUEUE_AGENT_CREATE] Retrieving RAG memories")
        context_memories = await server_state.rag_system.retrieve_for_task(
            task_description=task_description_for_rag,
            requesting_agent_id="system",
        )
        logger.info(f"[QUEUE_AGENT_CREATE] ✓ Retrieved {len(context_memories)} memories")

        # Determine working directory
        working_directory = None
        if phase_id_for_agent:
            logger.info(f"[QUEUE_AGENT_CREATE] Querying database for phase working directory")
            session = server_state.db_manager.get_session()
            try:
                from src.core.database import Phase

                # DEBUG: Show what's in the Phase table
                logger.info(f"[QUEUE_AGENT_CREATE] DEBUG: Querying Phase table with UUID: {phase_id_for_agent}")
                all_phases = session.query(Phase.id, Phase.name, Phase.order).all()
                logger.info(f"[QUEUE_AGENT_CREATE] DEBUG: All phases in DB: {all_phases}")

                phase = session.query(Phase).filter_by(id=phase_id_for_agent).first()
                if phase:
                    logger.info(f"[QUEUE_AGENT_CREATE] ✓ Found phase: {phase.name}, working_dir: {phase.working_directory}")
                    if phase.working_directory:
                        working_directory = phase.working_directory
                else:
                    logger.warning(f"[QUEUE_AGENT_CREATE] ✗ No phase found with UUID: {phase_id_for_agent}")
            finally:
                session.close()
        if not working_directory:
            working_directory = os.getcwd()
            logger.info(f"[QUEUE_AGENT_CREATE] Using default working directory: {working_directory}")

        # BUG FIX: Refresh task from database to get updated enriched_description
        # The next_task object is stale if enrichment just ran
        logger.info(f"[QUEUE_AGENT_CREATE] Refreshing task from database")
        session = server_state.db_manager.get_session()
        try:
            refreshed_task = session.query(Task).filter_by(id=next_task.id).first()
            if refreshed_task:
                logger.info(f"[QUEUE_AGENT_CREATE] ✓ Refreshed task from DB")
                logger.info(f"[QUEUE_AGENT_CREATE]   - enriched_description: {refreshed_task.enriched_description[:100] if refreshed_task.enriched_description else 'NULL'}")
                logger.info(f"[QUEUE_AGENT_CREATE]   - phase_id: {refreshed_task.phase_id}")

                # BUG FIX: Use the UUID phase_id for the temp task, not the order number
                # Create temp task object with fresh data (like normal flow does)
                temp_task = Task(
                    id=refreshed_task.id,
                    raw_description=refreshed_task.raw_description,
                    enriched_description=refreshed_task.enriched_description,
                    done_definition=refreshed_task.done_definition,
                    phase_id=phase_id_for_agent or refreshed_task.phase_id,  # Use UUID if converted
                    created_by_agent_id=refreshed_task.created_by_agent_id,
                )
                task_for_agent = temp_task
                logger.info(f"[QUEUE_AGENT_CREATE] ✓ Created temp task object for agent (phase_id={temp_task.phase_id})")
            else:
                # Fallback to next_task if refresh failed
                logger.warning(f"[QUEUE_AGENT_CREATE] ✗ Could not refresh task from DB - using stale task")
                task_for_agent = next_task
        finally:
            session.close()

        # BUG FIX: Prepare enriched_data dict to match process_task_async exactly
        # If we just ran enrichment, use the full dict; otherwise create minimal dict
        logger.info(f"[QUEUE_AGENT_CREATE] Preparing enriched_data for agent")
        if hasattr(next_task, '_enriched_task_dict'):
            # Enrichment just ran - use full dict from LLM
            enriched_data_for_agent = next_task._enriched_task_dict
            logger.info(f"[QUEUE_AGENT_CREATE] ✓ Using full enriched_task dict from LLM")
        else:
            # Task was already enriched - create minimal dict with enriched_description
            enriched_data_for_agent = {
                "enriched_description": task_for_agent.enriched_description,
                "estimated_complexity": task_for_agent.estimated_complexity or 5,
            }
            logger.info(f"[QUEUE_AGENT_CREATE] ✓ Created minimal enriched_data dict")

        logger.info(f"[QUEUE_AGENT_CREATE] Creating agent for task {next_task.id}")
        logger.info(f"[QUEUE_AGENT_CREATE]   - task enriched_description: {task_for_agent.enriched_description[:100] if task_for_agent.enriched_description else 'NULL'}")
        logger.info(f"[QUEUE_AGENT_CREATE]   - task phase_id: {task_for_agent.phase_id}")
        logger.info(f"[QUEUE_AGENT_CREATE]   - project_context length: {len(project_context)}")
        logger.info(f"[QUEUE_AGENT_CREATE]   - memories count: {len(context_memories)}")
        logger.info(f"[QUEUE_AGENT_CREATE]   - working_directory: {working_directory}")

        # Create agent for the task (using refreshed task data and full enriched_data)
        agent = await server_state.agent_manager.create_agent_for_task(
            task=task_for_agent,
            enriched_data=enriched_data_for_agent,
            memories=context_memories,
            project_context=project_context,
            working_directory=working_directory,
        )

        logger.info(f"[QUEUE_AGENT_CREATE] ✓✓✓ AGENT CREATED SUCCESSFULLY: {agent.id} for task {next_task.id} ✓✓✓")

        # Update task status
        session = server_state.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=next_task.id).first()
            if task:
                task.assigned_agent_id = agent.id
                task.status = "assigned"
                task.started_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

        # Broadcast update
        await server_state.broadcast_update({
            "type": "task_dequeued",
            "task_id": next_task.id,
            "agent_id": agent.id,
            "description": (next_task.enriched_description or next_task.raw_description)[:200],
        })

        logger.info(f"Created agent {agent.id} for queued task {next_task.id}")

    except Exception as e:
        logger.error(f"Failed to process queue: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def background_queue_processor():
    """Background task that processes the queue every minute.

    This ensures that queued tasks (especially newly unblocked ones)
    don't get stuck waiting for another event to trigger queue processing.
    """
    logger.info("Background queue processor started")

    while not server_state.shutdown_event.is_set():
        try:
            # Check if there are any queued tasks
            queue_status = server_state.queue_service.get_queue_status()
            queued_count = queue_status.get("queued_tasks_count", 0)

            if queued_count > 0:
                logger.info(f"[BACKGROUND_QUEUE] Found {queued_count} queued task(s), processing queue...")
                await process_queue()
            else:
                logger.debug("[BACKGROUND_QUEUE] No queued tasks, skipping")

        except Exception as e:
            logger.error(f"[BACKGROUND_QUEUE] Error in background queue processor: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Wait 60 seconds before next check
        try:
            await asyncio.wait_for(server_state.shutdown_event.wait(), timeout=60.0)
            # If we get here, shutdown was signaled
            break
        except asyncio.TimeoutError:
            # Timeout is expected - continue the loop
            pass

    logger.info("Background queue processor stopped")


# API Endpoints
@app.post("/create_task", response_model=CreateTaskResponse)
async def create_task(
    request: CreateTaskRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Create a new task with automatic enrichment and agent assignment."""
    logger.info(f"Creating task from agent {agent_id}: {request.task_description[:100]}...")

    try:
        # Check if ticket tracking is enabled and ticket_id is required
        # EXCEPTION: SDK agents (main-session-agent or agents with 'sdk'/'main' in ID)
        # can create tasks without ticket_id as they are often the ticket creators

        # Check if ticket tracking is enabled in the system (any board config exists)
        session = server_state.db_manager.get_session()
        try:
            from src.core.database import BoardConfig
            # Check if there are any board configs (indicating ticket tracking is active)
            has_ticket_tracking = session.query(BoardConfig).first() is not None

            # If ticket tracking is enabled globally, require ticket_id from MCP agents
            if has_ticket_tracking and not request.ticket_id:
                # Check if this is an SDK agent (allowed to create tasks without tickets)
                is_sdk_agent = (
                    agent_id == "main-session-agent" or
                    "sdk" in agent_id.lower() or
                    "main" in agent_id.lower()
                )

                if not is_sdk_agent:
                    session.close()
                    raise HTTPException(
                        status_code=400,
                        detail="Ticket tracking is enabled. MCP agents MUST provide ticket_id. "
                               "Create a ticket first using create_ticket, then use that ticket_id here. "
                               "Only SDK/root agents can create tasks without tickets."
                    )
        finally:
            if session.is_active:
                session.close()

        # Generate task ID immediately
        task_id = str(uuid.uuid4())

        # Create initial task in database with pending status
        session = server_state.db_manager.get_session()
        task = Task(
            id=task_id,
            raw_description=request.task_description,
            enriched_description=f"[Processing] {request.task_description}",  # Placeholder
            done_definition=request.done_definition,
            status="pending",
            priority=request.priority,
            parent_task_id=request.parent_task_id,
            created_by_agent_id=agent_id,
            phase_id=request.phase_id,
            workflow_id=None,
            estimated_complexity=5,  # Default value
            ticket_id=request.ticket_id,  # Store associated ticket ID
        )
        session.add(task)
        session.commit()
        session.close()

        # Check if task's ticket is blocked
        if request.ticket_id:
            from src.services.task_blocking_service import TaskBlockingService

            blocking_info = TaskBlockingService.check_task_blocked(task_id)

            if blocking_info["is_blocked"]:
                # Ticket is blocked - mark task as blocked immediately
                logger.info(
                    f"Task {task_id} associated with blocked ticket {request.ticket_id}. "
                    f"Marking task as 'blocked'. Blocked by: {blocking_info['blocking_ticket_ids']}"
                )

                session = server_state.db_manager.get_session()
                try:
                    task_obj = session.query(Task).filter_by(id=task_id).first()
                    if task_obj:
                        task_obj.status = "blocked"

                        blocker_titles = [t["title"] for t in blocking_info["blocking_tickets"]]
                        task_obj.completion_notes = f"Blocked by tickets: {', '.join(blocker_titles)}"

                        session.commit()
                finally:
                    session.close()

                # Broadcast blocked status
                await server_state.broadcast_update({
                    "type": "task_blocked",
                    "task_id": task_id,
                    "description": request.task_description[:200],
                    "blocking_tickets": blocking_info["blocking_ticket_ids"],
                })

                # Return immediately - don't process this task further
                return {
                    "task_id": task_id,
                    "enriched_description": request.task_description,  # Use raw description for blocked tasks
                    "assigned_agent_id": "none",  # No agent assigned for blocked tasks
                    "estimated_completion_time": 0,  # No estimate for blocked tasks
                    "status": "blocked",
                }

        # Process the rest asynchronously
        async def process_task_async():
            try:
                # 1. Determine phase if workflow is active
                logger.info(f"=== TASK CREATION PHASE DEBUG for task {task_id} ===")
                logger.info(f"Request phase_id: {request.phase_id}")
                logger.info(f"Request phase_order: {request.phase_order}")
                logger.info(f"Server phase_manager: {server_state.phase_manager}")
                logger.info(f"Server phase_manager.workflow_id: {getattr(server_state.phase_manager, 'workflow_id', 'NOT SET')}")
                logger.debug(f"Server phase_manager.active_workflow: {getattr(server_state.phase_manager, 'active_workflow', 'NOT SET')}...")

                # Use the phase_id from the request first, then fallback to phase_manager
                phase_id = request.phase_id
                workflow_id = None
                phase_context_str = ""

                if server_state.phase_manager.workflow_id:
                    logger.info(f"Workflow is active with ID: {server_state.phase_manager.workflow_id}")

                    # Handle phase identification - request.phase_id might be a phase order number, not UUID
                    if request.phase_id and str(request.phase_id).isdigit():
                        # request.phase_id is actually a phase order number
                        logger.info(f"phase_id appears to be an order number: {request.phase_id}")
                        phase_id = server_state.phase_manager.get_phase_for_task(
                            phase_id=None,
                            order=int(request.phase_id),
                            requesting_agent_id=agent_id
                        )
                        logger.info(f"get_phase_for_task returned phase_id: {phase_id} for order: {request.phase_id}")
                    elif request.phase_id:
                        # request.phase_id is a UUID string
                        logger.info(f"phase_id appears to be a UUID: {request.phase_id}")
                        phase_id = request.phase_id
                    else:
                        # No phase specified, get current phase
                        logger.info(f"No explicit phase_id in request, calling get_phase_for_task")
                        phase_id = server_state.phase_manager.get_phase_for_task(
                            phase_id=None,
                            order=request.phase_order,
                            requesting_agent_id=agent_id
                        )
                        logger.info(f"get_phase_for_task returned: {phase_id}")

                    if phase_id:
                        logger.info(f"Getting phase context for phase_id: {phase_id}")
                        # Get phase context for enrichment
                        phase_context = server_state.phase_manager.get_phase_context(phase_id)
                        logger.debug(f"get_phase_context returned: {phase_context}")
                        if phase_context:
                            logger.info(f"Phase context found, generating prompt context")
                            phase_context_str = phase_context.to_prompt_context()
                            workflow_id = phase_context.workflow_id
                            logger.info(f"Generated context length: {len(phase_context_str)}, workflow_id: {workflow_id}")
                        else:
                            logger.warning(f"No phase context returned for phase_id: {phase_id}")
                    else:
                        logger.warning(f"No phase_id determined for task")
                else:
                    logger.warning(f"No active workflow in phase_manager")

                logger.info(f"Final values: phase_id={phase_id}, workflow_id={workflow_id}, context_length={len(phase_context_str)}")
                logger.info(f"=== END TASK CREATION PHASE DEBUG ===")

                # 2. Determine working directory (priority: request > phase > server)
                working_directory = request.cwd  # From request
                if not working_directory and phase_id:
                    # Get phase working directory
                    session = server_state.db_manager.get_session()
                    phase = session.query(Phase).filter_by(id=phase_id).first()
                    if phase and phase.working_directory:
                        working_directory = phase.working_directory
                    session.close()
                if not working_directory:
                    working_directory = os.getcwd()  # Server's current directory

                # 3. Retrieve relevant context from RAG
                context_memories = await server_state.rag_system.retrieve_for_task(
                    task_description=request.task_description,
                    requesting_agent_id=agent_id,
                )

                # 4. Get project context
                project_context = await server_state.agent_manager.get_project_context()

                # Add phase context to project context
                if phase_context_str:
                    project_context = f"{project_context}\n\n{phase_context_str}"

                # 5. Enrich task using LLM
                context_strings = [mem.get("content", "") for mem in context_memories]
                enriched_task = await server_state.llm_provider.enrich_task(
                    task_description=request.task_description,
                    done_definition=request.done_definition,
                    context=context_strings,
                    phase_context=phase_context_str if phase_context_str else None,
                )

                # 6. Update task with enriched data
                session = server_state.db_manager.get_session()
                task = session.query(Task).filter_by(id=task_id).first()
                if task:
                    task.enriched_description = enriched_task["enriched_description"]
                    task.phase_id = phase_id
                    task.workflow_id = workflow_id
                    task.estimated_complexity = enriched_task.get("estimated_complexity", 5)

                    # Check if phase has validation enabled and inherit it
                    if phase_id:
                        phase = session.query(Phase).filter_by(id=phase_id).first()
                        if phase and phase.validation:
                            # Check if validation is explicitly disabled
                            if phase.validation.get("enabled", True):  # Default to True if not specified
                                task.validation_enabled = True
                                logger.info(f"Task {task_id} inheriting validation from phase {phase.name}")
                            else:
                                logger.info(f"Task {task_id} validation explicitly disabled in phase {phase.name}")

                    session.commit()

                    # Store task data before closing session
                    task_data = {
                        "id": task_id,
                        "raw_description": request.task_description,
                        "enriched_description": enriched_task["enriched_description"],
                        "done_definition": request.done_definition,
                        "phase_id": phase_id,
                    }
                    session.close()

                    # 6.5 Check for duplicates if deduplication is enabled
                    duplicate_info = None
                    if (server_state.embedding_service and
                        server_state.task_similarity_service and
                        get_config().task_dedup_enabled):

                        try:
                            # Generate embedding for enriched description
                            task_embedding = await server_state.embedding_service.generate_embedding(
                                enriched_task["enriched_description"]
                            )

                            # Check for duplicates within the same phase
                            duplicate_info = await server_state.task_similarity_service.check_for_duplicates(
                                enriched_task["enriched_description"],
                                task_embedding,
                                phase_id=phase_id  # Only check duplicates within same phase
                            )

                            if duplicate_info['is_duplicate']:
                                # Update task as duplicate
                                session = server_state.db_manager.get_session()
                                task = session.query(Task).filter_by(id=task_id).first()
                                if task:
                                    task.status = 'duplicated'
                                    task.duplicate_of_task_id = duplicate_info['duplicate_of']
                                    task.similarity_score = duplicate_info['max_similarity']
                                    session.commit()
                                session.close()

                                # Log the duplicate detection
                                logger.warning(
                                    f"Task {task_id} detected as duplicate of {duplicate_info['duplicate_of']} "
                                    f"with similarity {duplicate_info['max_similarity']:.3f}"
                                )

                                # Return early (don't create agent for duplicates)
                                return

                            # Store embedding and related tasks (not a duplicate)
                            await server_state.task_similarity_service.store_task_embedding(
                                task_id,
                                task_embedding,
                                related_tasks_details=duplicate_info.get('related_tasks_details', [])
                            )

                            if duplicate_info.get('related_tasks'):
                                logger.info(
                                    f"Task {task_id} has {len(duplicate_info['related_tasks'])} related tasks"
                                )

                        except Exception as e:
                            logger.error(f"Failed to check for duplicates: {e}")
                            # Continue without deduplication on error

                    # 6.5 Check if we should queue the task
                    if server_state.queue_service.should_queue_task():
                        # At capacity - enqueue the task
                        server_state.queue_service.enqueue_task(task_id)

                        # Get queue status for broadcasting
                        queue_status = server_state.queue_service.get_queue_status()

                        # Broadcast queued status
                        await server_state.broadcast_update({
                            "type": "task_queued",
                            "task_id": task_id,
                            "description": enriched_task["enriched_description"][:200],
                            "queue_position": queue_status.get("queued_tasks_count", 0),
                            "slots_available": queue_status.get("slots_available", 0),
                        })

                        logger.info(f"Task {task_id} queued (at capacity: {queue_status['active_agents']}/{queue_status['max_concurrent_agents']} agents)")
                        return  # Don't create agent yet

                    # 7. Create agent for the task (using task data, not the ORM object)
                    # Create a temporary task object for the agent manager
                    logger.info(f"[CREATE_TASK] Creating agent for task {task_id}")
                    logger.info(f"[CREATE_TASK] Task was created by agent: {agent_id}")

                    temp_task = Task(
                        id=task_id,
                        raw_description=task_data["raw_description"],
                        enriched_description=task_data["enriched_description"],
                        done_definition=task_data["done_definition"],
                        phase_id=task_data["phase_id"],
                        created_by_agent_id=agent_id,  # Important: Set the parent agent ID
                    )

                    logger.info(f"[CREATE_TASK] temp_task.created_by_agent_id = {temp_task.created_by_agent_id}")

                    agent = await server_state.agent_manager.create_agent_for_task(
                        task=temp_task,
                        enriched_data=enriched_task,
                        memories=context_memories,
                        project_context=project_context,
                        working_directory=working_directory,
                    )

                    # Store agent ID immediately (before session issues)
                    agent_id_str = str(agent.id) if agent else None

                    # 8. Update task with assigned agent in a new session
                    session = server_state.db_manager.get_session()
                    task = session.query(Task).filter_by(id=task_id).first()
                    if task:
                        task.assigned_agent_id = agent_id_str
                        task.status = "assigned"
                        task.started_at = datetime.utcnow()
                        session.commit()
                    session.close()

                    # 9. Broadcast update via WebSocket
                    await server_state.broadcast_update({
                        "type": "task_created",
                        "task_id": task_id,
                        "agent_id": agent_id_str,
                        "description": enriched_task["enriched_description"][:200],
                    })

                    logger.info(f"Task {task_id} processed successfully in background")
                else:
                    logger.error(f"Task {task_id} not found after creation")

            except Exception as e:
                logger.error(f"Failed to process task {task_id} in background: {e}")
                # Update task status to failed
                session = server_state.db_manager.get_session()
                task = session.query(Task).filter_by(id=task_id).first()
                if task:
                    task.status = "failed"
                    task.failure_reason = str(e)
                    session.commit()
                session.close()

        # Start processing in the background without waiting
        import asyncio
        asyncio.create_task(process_task_async())

        # Return immediately with pending status
        return CreateTaskResponse(
            task_id=task_id,
            enriched_description=f"[Processing] {request.task_description}",
            assigned_agent_id="pending",
            estimated_completion_time=25,
            status="pending",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update_task_status", response_model=UpdateTaskStatusResponse)
async def update_task_status(
    request: UpdateTaskStatusRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Update task status when complete or failed."""
    logger.info(f"Updating task {request.task_id} status to {request.status}")

    try:
        session = server_state.db_manager.get_session()

        # 1. Verify task exists and agent owns it
        task = session.query(Task).filter_by(id=request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.assigned_agent_id != agent_id:
            raise HTTPException(status_code=403, detail="Agent not authorized for this task")

        # 2. Save learnings as memories
        for learning in request.key_learnings:
            # Generate embedding
            embedding = await server_state.llm_provider.generate_embedding(learning)

            # Save to vector store
            memory_id = str(uuid.uuid4())
            await server_state.vector_store.store_memory(
                collection="agent_memories",
                memory_id=memory_id,
                embedding=embedding,
                content=learning,
                metadata={
                    "agent_id": agent_id,
                    "task_id": request.task_id,
                    "memory_type": "learning",
                    "code_changes": request.code_changes,
                },
            )

            # Save to database
            memory = Memory(
                id=memory_id,
                agent_id=agent_id,
                content=learning,
                memory_type="learning",
                embedding_id=memory_id,
                related_task_id=request.task_id,
                related_files=request.code_changes,
            )
            session.add(memory)

        # 3. Check if task has results reported
        if request.status == "done" and not task.has_results:
            logger.warning(f"Task {request.task_id} completed without formal results reported")

        # 4. Check if task has validation enabled
        validation_spawned = False
        if request.status == "done" and task.validation_enabled:
            # Agent claims done but needs validation
            task.status = "under_review"
            task.validation_iteration += 1
            task.completion_notes = request.summary

            # Capture task attributes before async function (to avoid detached instance issues)
            task_validation_iteration = task.validation_iteration
            task_workflow_id = task.workflow_id

            session.commit()

            # Mark original agent as kept alive for validation (do this immediately)
            agent = session.query(Agent).filter_by(id=agent_id).first()
            if agent:
                agent.kept_alive_for_validation = True
                session.commit()

            # Process validation spawning asynchronously (like create_task)
            async def spawn_validation_async():
                try:
                    logger.info(f"Starting validation process for task {request.task_id}")

                    # Commit agent's work for validation (using worktree manager)
                    commit_sha = None
                    if hasattr(server_state, 'worktree_manager'):
                        try:
                            commit_result = server_state.worktree_manager.commit_for_validation(
                                agent_id=agent_id,
                                iteration=task_validation_iteration
                            )
                            commit_sha = commit_result.get("commit_sha")
                        except Exception as e:
                            logger.warning(f"Failed to create validation commit: {e}")

                    # Spawn validator agent
                    from src.validation.validator_agent import spawn_validator_agent
                    validator_id = await spawn_validator_agent(
                        validation_type="task",
                        target_id=request.task_id,
                        workflow_id=task_workflow_id,
                        commit_sha=commit_sha or "HEAD",
                        db_manager=server_state.db_manager,
                        worktree_manager=getattr(server_state, 'worktree_manager', None),
                        agent_manager=server_state.agent_manager,
                        original_agent_id=agent_id
                    )

                    # Update task status to validation in progress
                    session = server_state.db_manager.get_session()
                    try:
                        task = session.query(Task).filter_by(id=request.task_id).first()
                        if task:
                            task.status = "validation_in_progress"
                            session.commit()
                            logger.info(f"Task {request.task_id} validation spawned successfully, validator: {validator_id}")
                        else:
                            logger.error(f"Task {request.task_id} not found during validation update")
                    finally:
                        session.close()

                    # Broadcast validation started
                    await server_state.broadcast_update({
                        "type": "validation_started",
                        "task_id": request.task_id,
                        "validator_id": validator_id,
                        "original_agent_id": agent_id,
                    })

                except Exception as e:
                    logger.error(f"Failed to spawn validation for task {request.task_id}: {e}")
                    # Update task status to failed validation
                    session = server_state.db_manager.get_session()
                    try:
                        task = session.query(Task).filter_by(id=request.task_id).first()
                        if task:
                            task.status = "failed"
                            task.failure_reason = f"Validation spawning failed: {str(e)}"
                            session.commit()

                        # Terminate the agent since validation failed and process queue
                        await server_state.agent_manager.terminate_agent(agent_id)
                        await process_queue()
                    finally:
                        session.close()

            # Start validation process in background
            asyncio.create_task(spawn_validation_async())
            validation_spawned = True

        else:
            # No validation or task failed - proceed normally
            task.status = request.status
            task.completed_at = datetime.utcnow()
            task.completion_notes = request.summary

            if request.status == "failed":
                task.failure_reason = request.failure_reason

            session.commit()

            # If task completed successfully without validation, merge to parent
            merge_commit_sha = None
            if request.status == "done" and hasattr(server_state, 'worktree_manager'):
                try:
                    merge_result = server_state.worktree_manager.merge_to_parent(agent_id)
                    merge_commit_sha = merge_result.get("commit_sha") if isinstance(merge_result, dict) else None
                    logger.info(f"Merged completed work to parent (no validation): {merge_result}")
                except Exception as e:
                    logger.warning(f"Failed to merge completed work to parent: {e}")

                # Auto-link commit to ticket if task has ticket_id
                if task.ticket_id and merge_commit_sha:
                    try:
                        logger.info(f"Auto-linking commit {merge_commit_sha} to ticket {task.ticket_id}")

                        # Link the merge commit to the ticket
                        await TicketService.link_commit(
                            ticket_id=task.ticket_id,
                            agent_id=agent_id,
                            commit_sha=merge_commit_sha,
                            commit_message=f"Task {request.task_id} completed and merged",
                            link_method="auto_task_completion"
                        )

                        logger.info(f"Commit {merge_commit_sha} linked to ticket {task.ticket_id}")

                        # Broadcast commit linked to ticket
                        await server_state.broadcast_update({
                            "type": "ticket_commit_linked",
                            "ticket_id": task.ticket_id,
                            "task_id": request.task_id,
                            "agent_id": agent_id,
                            "commit_sha": merge_commit_sha
                        })

                    except Exception as e:
                        logger.error(f"Failed to auto-link commit to ticket: {e}")
                        # Don't fail the task if ticket operations fail

            # 4. Schedule agent termination and queue processing (only if no validation)
            async def terminate_and_process_queue():
                await server_state.agent_manager.terminate_agent(agent_id)
                await process_queue()

            asyncio.create_task(terminate_and_process_queue())

        # 5. Broadcast update
        await server_state.broadcast_update({
            "type": "task_completed",
            "task_id": request.task_id,
            "agent_id": agent_id,
            "status": request.status,
            "summary": request.summary[:200],
        })

        session.close()

        # Return appropriate response based on whether validation was spawned
        if validation_spawned:
            return UpdateTaskStatusResponse(
                success=True,
                message="Task submitted for validation. A validation agent has been spawned - please wait for validation results.",
                termination_scheduled=False,  # Agent kept alive for validation feedback
            )
        else:
            return UpdateTaskStatusResponse(
                success=True,
                message=f"Task {request.status} successfully",
                termination_scheduled=True,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/save_memory", response_model=SaveMemoryResponse)
async def save_memory(
    request: SaveMemoryRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Store important discoveries and learnings."""
    logger.info(f"Saving memory from agent {agent_id}: {request.memory_content[:100]}...")

    try:
        # Generate memory ID immediately
        memory_id = str(uuid.uuid4())

        # Create initial memory record in database
        session = server_state.db_manager.get_session()
        memory = Memory(
            id=memory_id,
            agent_id=agent_id,
            content=request.memory_content,
            memory_type=request.memory_type,
            embedding_id=None,  # Will be updated after processing
            tags=request.tags,
            related_files=request.related_files,
        )
        session.add(memory)
        session.commit()
        session.close()

        # Process the embedding and deduplication asynchronously
        async def process_memory_async():
            try:
                # 1. Generate embedding
                embedding = await server_state.llm_provider.generate_embedding(request.memory_content)

                # 2. Check for similar memories
                similar = await server_state.vector_store.search(
                    collection="agent_memories",
                    query_vector=embedding,
                    limit=5,
                    score_threshold=0.95,  # High threshold for deduplication
                )

                # 3. If not duplicate, store in vector database
                if not similar or similar[0]["score"] < 0.95:
                    # Store in vector database
                    success = await server_state.vector_store.store_memory(
                        collection="agent_memories",
                        memory_id=memory_id,
                        embedding=embedding,
                        content=request.memory_content,
                        metadata={
                            "agent_id": agent_id,
                            "memory_type": request.memory_type,
                            "related_files": request.related_files,
                            "tags": request.tags,
                        },
                    )

                    # Update memory with embedding ID
                    session = server_state.db_manager.get_session()
                    memory = session.query(Memory).filter_by(id=memory_id).first()
                    if memory:
                        memory.embedding_id = memory_id if success else None
                        session.commit()
                    session.close()

                    logger.info(f"Memory {memory_id} indexed successfully in background")
                else:
                    # Memory is too similar to existing one - mark as duplicate
                    session = server_state.db_manager.get_session()
                    memory = session.query(Memory).filter_by(id=memory_id).first()
                    if memory:
                        # Mark as duplicate by adding a reference to the original
                        memory.tags = (memory.tags or []) + [f"duplicate_of:{similar[0]['id']}"]
                        session.commit()
                    session.close()
                    logger.info(f"Memory {memory_id} marked as duplicate of {similar[0]['id']}")

            except Exception as e:
                logger.error(f"Failed to process memory {memory_id} in background: {e}")
                # Update memory with error status
                session = server_state.db_manager.get_session()
                memory = session.query(Memory).filter_by(id=memory_id).first()
                if memory:
                    memory.tags = (memory.tags or []) + [f"indexing_error:{str(e)[:50]}"]
                    session.commit()
                session.close()

        # Start background processing
        asyncio.create_task(process_memory_async())

        # Return immediately with memory ID
        return SaveMemoryResponse(
            memory_id=memory_id,
            indexed=True,  # Optimistically return true (indexing happens async)
            similar_memories=None,  # Can't provide this synchronously anymore
        )

    except Exception as e:
        logger.error(f"Failed to save memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/report_results", response_model=ReportResultsResponse)
async def report_results(
    request: ReportResultsRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Submit formal results for a completed task."""
    logger.info(f"Agent {agent_id} reporting results for task {request.task_id}")

    try:
        # Import the result service
        from src.services.result_service import ResultService

        # Create the result
        result = ResultService.create_result(
            agent_id=agent_id,
            task_id=request.task_id,
            markdown_file_path=request.markdown_file_path,
            result_type=request.result_type,
            summary=request.summary,
        )

        # Broadcast update
        await server_state.broadcast_update({
            "type": "results_reported",
            "task_id": request.task_id,
            "agent_id": agent_id,
            "result_id": result["result_id"],
            "summary": request.summary[:200],
        })

        return ReportResultsResponse(
            status=result["status"],
            result_id=result["result_id"],
            task_id=result["task_id"],
            agent_id=result["agent_id"],
            verification_status=result["verification_status"],
            created_at=result["created_at"],
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to report results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/give_validation_review", response_model=GiveValidationReviewResponse)
async def give_validation_review(
    request: GiveValidationReviewRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Submit validation review for a task."""
    logger.info(f"Validation review from {agent_id}: task={request.task_id}, passed={request.validation_passed}")

    try:
        session = server_state.db_manager.get_session()

        # 1. Verify caller is a validator agent
        agent = session.query(Agent).filter_by(id=agent_id).first()
        if not agent or agent.agent_type != "validator":
            raise HTTPException(status_code=403, detail="Only validator agents can submit reviews")

        # 2. Get task
        task = session.query(Task).filter_by(id=request.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        original_agent_id = task.assigned_agent_id

        # 3. Create validation review record
        review = ValidationReview(
            id=str(uuid.uuid4()),
            task_id=request.task_id,
            validator_agent_id=agent_id,
            iteration_number=task.validation_iteration,
            validation_passed=request.validation_passed,
            feedback=request.feedback,
            evidence=request.evidence,
            recommendations=request.recommendations
        )
        session.add(review)

        if request.validation_passed:
            # 4a. Validation successful
            task.status = "done"
            task.review_done = True
            task.completed_at = datetime.utcnow()

            # Update verification status of results if they exist
            if task.has_results:
                from src.services.result_service import ResultService
                results = ResultService.get_results_for_task(request.task_id)
                for result_info in results:
                    try:
                        ResultService.verify_result(
                            result_id=result_info["result_id"],
                            validation_review_id=review.id,
                            verified=True
                        )
                    except Exception as e:
                        logger.warning(f"Failed to verify result {result_info['result_id']}: {e}")

            # Create recommended follow-up tasks
            if request.recommendations:
                for rec in request.recommendations:
                    follow_up_task = Task(
                        id=str(uuid.uuid4()),
                        raw_description=rec,
                        done_definition="Complete as described",
                        parent_task_id=request.task_id,
                        created_by_agent_id=agent_id,
                        priority="medium",
                        status="pending"
                    )
                    session.add(follow_up_task)

            session.commit()

            # Merge agent's work to parent (if using worktrees)
            if hasattr(server_state, 'worktree_manager') and original_agent_id:
                try:
                    merge_result = server_state.worktree_manager.merge_to_parent(original_agent_id)
                    logger.info(f"Merged validated work: {merge_result}")
                except Exception as e:
                    logger.warning(f"Failed to merge validated work: {e}")

            # Terminate both original and validator agents, then process queue
            async def terminate_both_and_process_queue():
                await server_state.agent_manager.terminate_agent(original_agent_id)
                await server_state.agent_manager.terminate_agent(agent_id)
                await process_queue()

            asyncio.create_task(terminate_both_and_process_queue())

            # Broadcast success
            await server_state.broadcast_update({
                "type": "validation_passed",
                "task_id": request.task_id,
                "agent_id": original_agent_id,
                "validator_id": agent_id,
                "iteration": task.validation_iteration
            })

            return GiveValidationReviewResponse(
                status="completed",
                message="Validation passed, task completed",
                iteration=task.validation_iteration
            )

        else:
            # 4b. Validation failed - send feedback to original agent
            task.status = "needs_work"
            task.last_validation_feedback = request.feedback
            session.commit()

            # Send feedback to the still-running agent
            from src.validation.validator_agent import send_feedback_to_agent
            feedback_sent = send_feedback_to_agent(
                agent_id=original_agent_id,
                feedback=request.feedback,
                iteration=task.validation_iteration
            )

            if not feedback_sent:
                logger.error(f"Failed to send feedback to agent {original_agent_id}")

            # Terminate validator (its job is done) and process queue
            async def terminate_validator_and_process_queue():
                await server_state.agent_manager.terminate_agent(agent_id)
                await process_queue()

            asyncio.create_task(terminate_validator_and_process_queue())

            # Broadcast validation failure
            await server_state.broadcast_update({
                "type": "validation_failed",
                "task_id": request.task_id,
                "agent_id": original_agent_id,
                "validator_id": agent_id,
                "iteration": task.validation_iteration
            })

            return GiveValidationReviewResponse(
                status="needs_work",
                message="Validation failed, feedback sent to agent",
                iteration=task.validation_iteration
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process validation review: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.post("/submit_result", response_model=SubmitResultResponse)
async def submit_result(
    request: SubmitResultRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Submit a workflow result for validation."""
    try:
        logger.info(f"Agent {agent_id} submitting result: {request.explanation}")

        # Get agent's task to determine workflow_id
        session = server_state.db_manager.get_session()
        try:
            agent = session.query(Agent).filter_by(id=agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

            # Find the agent's assigned task
            task = session.query(Task).filter_by(assigned_agent_id=agent_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"No task found for agent: {agent_id}")

            workflow_id = task.workflow_id
            if not workflow_id:
                raise HTTPException(status_code=400, detail=f"Task {task.id} has no workflow_id")

            logger.info(f"Derived workflow_id {workflow_id} from agent {agent_id}'s task {task.id}")

        finally:
            session.close()

        # Submit the result
        result = WorkflowResultService.submit_result(
            agent_id=agent_id,
            workflow_id=workflow_id,
            markdown_file_path=request.markdown_file_path,
            explanation=request.explanation,
            evidence=request.evidence,
        )

        # Create AgentResult entry for tracking
        session = server_state.db_manager.get_session()
        try:
            # Get the task to link AgentResult
            task = session.query(Task).filter_by(assigned_agent_id=agent_id).first()
            if task:
                with open(request.markdown_file_path, 'r') as f:
                    markdown_content = f.read()

                agent_result = AgentResult(
                    id=f"agent-result-{uuid.uuid4()}",
                    agent_id=agent_id,
                    task_id=task.id,
                    markdown_content=markdown_content,
                    markdown_file_path=request.markdown_file_path,
                    result_type="implementation",  # Default to implementation for workflow results
                    summary=request.explanation or "Workflow result submitted",
                    created_at=datetime.utcnow()
                )
                session.add(agent_result)
                session.commit()
                logger.info(f"Created AgentResult {agent_result.id} for workflow result {result['result_id']}")
        except Exception as e:
            logger.warning(f"Failed to create AgentResult entry: {e}")
            session.rollback()
        finally:
            session.close()

        # Create commit for result submission
        commit_sha = None
        if hasattr(server_state, 'worktree_manager'):
            try:
                commit_result = server_state.worktree_manager.commit_for_validation(
                    agent_id=agent_id,
                    iteration=1,  # Results are always first iteration
                    message="Result submitted for workflow validation"
                )
                commit_sha = commit_result.get("commit_sha")
                logger.info(f"Created commit {commit_sha} for result submission by agent {agent_id}")
            except Exception as e:
                logger.warning(f"Failed to create result submission commit: {e}")

        # Check if validation should be triggered
        should_validate, criteria = server_state.result_validator_service.should_spawn_validator(
            workflow_id
        )

        validation_triggered = False
        if should_validate and criteria:
            # Spawn validator asynchronously using unified validator system
            async def spawn_validator_async():
                try:
                    from src.validation.validator_agent import spawn_validator_agent
                    validator_id = await spawn_validator_agent(
                        validation_type="result",
                        target_id=result["result_id"],
                        workflow_id=workflow_id,
                        commit_sha=commit_sha or "HEAD",
                        db_manager=server_state.db_manager,
                        worktree_manager=getattr(server_state, 'worktree_manager', None),
                        agent_manager=server_state.agent_manager,
                        criteria=criteria,
                        original_agent_id=agent_id
                    )
                    logger.info(f"Spawned result validator {validator_id} for result {result['result_id']}")
                except Exception as e:
                    logger.error(f"Failed to spawn result validator: {e}")

            asyncio.create_task(spawn_validator_async())
            validation_triggered = True

        # Broadcast result submission
        await server_state.broadcast_update({
            "type": "result_submitted",
            "result_id": result["result_id"],
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "validation_triggered": validation_triggered,
        })

        return SubmitResultResponse(
            status=result["status"],
            result_id=result["result_id"],
            workflow_id=workflow_id,
            agent_id=agent_id,
            validation_triggered=validation_triggered,
            message="Result submitted successfully" + (" and validation triggered" if validation_triggered else ""),
            created_at=result["created_at"],
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit_result_validation", response_model=SubmitResultValidationResponse)
async def submit_result_validation(
    request: SubmitResultValidationRequest,
):
    """Submit validation review for a workflow result (validator agents only)."""
    try:
        logger.info(f"Processing validation for result {request.result_id}")

        # Get the workflow result to find the validator agent
        session = server_state.db_manager.get_session()
        try:
            result = session.query(WorkflowResult).filter_by(id=request.result_id).first()
            if not result:
                raise HTTPException(status_code=404, detail=f"Result {request.result_id} not found")

            # The validator agent should be the one that currently has this result assigned
            # We can find it by looking for the most recent result_validator agent for this workflow
            validator_agent = session.query(Agent).filter(
                Agent.agent_type == "result_validator"
            ).order_by(Agent.created_at.desc()).first()

            if not validator_agent:
                raise HTTPException(status_code=500, detail="No validator agent found for this validation")

            agent_id = validator_agent.id
            logger.info(f"Using validator agent {agent_id} for result {request.result_id}")
        finally:
            session.close()

        # Process validation outcome
        outcome = server_state.result_validator_service.process_validation_outcome(
            result_id=request.result_id,
            passed=request.validation_passed,
            feedback=request.feedback,
            evidence=request.evidence,
            validator_agent_id=agent_id
        )

        # Handle workflow actions
        workflow_action_taken = None
        if "terminate_workflow" in outcome["next_actions"]:
            # Import termination handler when needed
            from src.workflow.termination_handler import WorkflowTerminationHandler
            termination_handler = WorkflowTerminationHandler(
                db_manager=server_state.db_manager,
                agent_manager=server_state.agent_manager
            )

            await termination_handler.terminate_workflow(outcome["workflow_id"])
            workflow_action_taken = "workflow_terminated"
            logger.info(f"Terminated workflow {outcome['workflow_id']} due to validated result")

        elif "continue_workflow" in outcome["next_actions"]:
            workflow_action_taken = "workflow_continues"
            logger.info(f"Workflow {outcome['workflow_id']} continues after validated result")

        # Terminate validator agent and process queue
        async def terminate_result_validator_and_process_queue():
            await server_state.agent_manager.terminate_agent(agent_id)
            await process_queue()

        asyncio.create_task(terminate_result_validator_and_process_queue())

        # Broadcast validation result
        await server_state.broadcast_update({
            "type": "result_validation_completed",
            "result_id": request.result_id,
            "workflow_id": outcome["workflow_id"],
            "validation_passed": request.validation_passed,
            "validator_agent_id": agent_id,
            "workflow_action": workflow_action_taken,
        })

        status = "workflow_terminated" if workflow_action_taken == "workflow_terminated" else "completed"
        message = f"Validation {'passed' if request.validation_passed else 'failed'}"
        if workflow_action_taken == "workflow_terminated":
            message += " - workflow terminated"
        elif workflow_action_taken == "workflow_continues":
            message += " - workflow continues"

        return SubmitResultValidationResponse(
            status=status,
            message=message,
            workflow_action_taken=workflow_action_taken,
            result_id=request.result_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process result validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflows/{workflow_id}/results")
async def get_workflow_results(
    workflow_id: str,
    requesting_agent_id: str = Header(None, alias="X-Agent-ID"),
):
    """Get all results for a specific workflow."""
    try:
        results = WorkflowResultService.get_workflow_results(workflow_id)
        return results
    except Exception as e:
        logger.error(f"Failed to get workflow results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/broadcast_message", response_model=BroadcastMessageResponse)
async def broadcast_message(
    request: BroadcastMessageRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Broadcast a message to all active agents except the sender.

    This allows agents to communicate with each other by sending messages
    that will be delivered to all other active agents in the system.
    """
    logger.info(f"Agent {agent_id[:8]} broadcasting message: {request.message[:100]}...")

    try:
        # Use agent manager to broadcast the message
        recipient_count = await server_state.agent_manager.broadcast_message_to_all_agents(
            sender_agent_id=agent_id,
            message=request.message
        )

        # Broadcast update via WebSocket
        await server_state.broadcast_update({
            "type": "agent_broadcast",
            "sender_agent_id": agent_id,
            "recipient_count": recipient_count,
            "message_preview": request.message[:100],
        })

        return BroadcastMessageResponse(
            success=True,
            recipient_count=recipient_count,
            message=f"Message broadcast to {recipient_count} agent(s)"
        )

    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send_message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Send a direct message to a specific agent.

    This allows agents to communicate directly with each other by sending
    targeted messages to specific agents.
    """
    logger.info(f"Agent {agent_id[:8]} sending message to {request.recipient_agent_id[:8]}: {request.message[:100]}...")

    try:
        # Use agent manager to send the direct message
        success = await server_state.agent_manager.send_direct_message(
            sender_agent_id=agent_id,
            recipient_agent_id=request.recipient_agent_id,
            message=request.message
        )

        if not success:
            return SendMessageResponse(
                success=False,
                message=f"Failed to send message - recipient agent {request.recipient_agent_id[:8]} may not exist or is terminated"
            )

        # Broadcast update via WebSocket
        await server_state.broadcast_update({
            "type": "agent_direct_message",
            "sender_agent_id": agent_id,
            "recipient_agent_id": request.recipient_agent_id,
            "message_preview": request.message[:100],
        })

        return SendMessageResponse(
            success=True,
            message=f"Message sent to agent {request.recipient_agent_id[:8]}"
        )

    except Exception as e:
        logger.error(f"Failed to send direct message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TICKET TRACKING SYSTEM ENDPOINTS ====================

@app.post("/api/tickets/create", response_model=CreateTicketResponse)
async def create_ticket_endpoint(
    request: CreateTicketRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Create a new ticket in the workflow tracking system."""
    logger.info(f"[TICKET_CREATE] ========== START ==========")
    logger.info(f"[TICKET_CREATE] Agent: {agent_id}")
    logger.info(f"[TICKET_CREATE] Title: {request.title}")
    logger.info(f"[TICKET_CREATE] Type: {request.ticket_type}, Priority: {request.priority}")
    logger.info(f"[TICKET_CREATE] Workflow_ID provided: {request.workflow_id}")
    logger.info(f"[TICKET_CREATE] Tags: {request.tags}")

    try:
        # Auto-detect workflow_id from agent's current task if not provided
        workflow_id = request.workflow_id
        if not workflow_id:
            logger.info(f"[TICKET_CREATE] No workflow_id provided, attempting auto-detection...")

            # Try to get from agent's current task first
            with get_db() as session:
                agent = session.query(Agent).filter_by(id=agent_id).first()
                logger.info(f"[TICKET_CREATE] Agent lookup: found={agent is not None}")
                if agent:
                    logger.info(f"[TICKET_CREATE] Agent.current_task_id: {agent.current_task_id}")

                if agent and agent.current_task_id:
                    task = session.query(Task).filter_by(id=agent.current_task_id).first()
                    logger.info(f"[TICKET_CREATE] Task lookup: found={task is not None}")
                    if task:
                        logger.info(f"[TICKET_CREATE] Task.workflow_id: {task.workflow_id}")

                    if task and task.workflow_id:
                        workflow_id = task.workflow_id
                        logger.info(f"[TICKET_CREATE] ✅ Auto-detected workflow_id from task: {workflow_id}")

            # If still no workflow_id, try to get the single active workflow
            if not workflow_id:
                logger.info(f"[TICKET_CREATE] Could not detect from task, trying single active workflow...")
                workflow_id = get_single_active_workflow()
                if workflow_id:
                    logger.info(f"[TICKET_CREATE] ✅ Using single active workflow: {workflow_id}")
                else:
                    logger.error(f"[TICKET_CREATE] ❌ No single active workflow found")
                    raise HTTPException(
                        status_code=400,
                        detail="Could not determine workflow_id: no active workflows found or multiple workflows exist. "
                               "Please ensure you have exactly one active workflow."
                    )
        else:
            logger.info(f"[TICKET_CREATE] Using provided workflow_id: {workflow_id}")

        logger.info(f"[TICKET_CREATE] Calling TicketService.create_ticket with workflow_id={workflow_id}")
        result = await TicketService.create_ticket(
            workflow_id=workflow_id,
            agent_id=agent_id,
            title=request.title,
            description=request.description,
            ticket_type=request.ticket_type,
            priority=request.priority,
            initial_status=request.initial_status,
            assigned_agent_id=request.assigned_agent_id,
            parent_ticket_id=request.parent_ticket_id,
            blocked_by_ticket_ids=request.blocked_by_ticket_ids,
            tags=request.tags,
            related_task_ids=request.related_task_ids,
        )

        logger.info(f"[TICKET_CREATE] ✅ TicketService.create_ticket returned successfully")
        logger.info(f"[TICKET_CREATE] Result: {result}")
        logger.info(f"[TICKET_CREATE] Ticket ID: {result.get('ticket_id')}")

        # Broadcast update
        logger.info(f"[TICKET_CREATE] Broadcasting update...")
        await server_state.broadcast_update({
            "type": "ticket_created",
            "ticket_id": result["ticket_id"],
            "workflow_id": workflow_id,
            "agent_id": agent_id,
            "title": request.title,
        })
        logger.info(f"[TICKET_CREATE] Broadcast complete")

        logger.info(f"[TICKET_CREATE] Creating response object...")
        response = CreateTicketResponse(**result)
        logger.info(f"[TICKET_CREATE] Response created: {response}")
        logger.info(f"[TICKET_CREATE] ========== SUCCESS ==========")
        return response

    except HTTPException:
        # Re-raise HTTPException without modification to preserve status code
        raise
    except ValueError as e:
        logger.error(f"[TICKET_CREATE] ❌ ValueError: {e}")
        logger.error(f"[TICKET_CREATE] ========== FAILED (ValueError) ==========")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[TICKET_CREATE] ❌ Unexpected error: {type(e).__name__}: {e}")
        logger.error(f"[TICKET_CREATE] ========== FAILED (Exception) ==========")
        import traceback
        logger.error(f"[TICKET_CREATE] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/update", response_model=UpdateTicketResponse)
async def update_ticket_endpoint(
    request: UpdateTicketRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Update ticket fields (excluding status changes)."""
    logger.info(f"Agent {agent_id} updating ticket {request.ticket_id}")

    try:
        result = await TicketService.update_ticket(
            ticket_id=request.ticket_id,
            agent_id=agent_id,
            updates=request.updates,
            update_comment=request.update_comment,
        )

        # Broadcast update
        await server_state.broadcast_update({
            "type": "ticket_updated",
            "ticket_id": request.ticket_id,
            "agent_id": agent_id,
            "fields_updated": result["fields_updated"],
        })

        return UpdateTicketResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error updating ticket: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/change-status", response_model=ChangeTicketStatusResponse)
async def change_ticket_status_endpoint(
    request: ChangeTicketStatusRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Move ticket to a different status column."""
    logger.info(f"Agent {agent_id} changing status of ticket {request.ticket_id} to {request.new_status}")

    try:
        result = await TicketService.change_status(
            ticket_id=request.ticket_id,
            agent_id=agent_id,
            new_status=request.new_status,
            comment=request.comment,
            commit_sha=request.commit_sha,
        )

        # Broadcast update
        await server_state.broadcast_update({
            "type": "ticket_status_changed",
            "ticket_id": request.ticket_id,
            "agent_id": agent_id,
            "old_status": result["old_status"],
            "new_status": result["new_status"],
            "blocked": result["blocked"],
        })

        return ChangeTicketStatusResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error changing ticket status: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to change ticket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/comment", response_model=AddCommentResponse)
async def add_comment_endpoint(
    request: AddCommentRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Add a comment to a ticket."""
    logger.info(f"Agent {agent_id} adding comment to ticket {request.ticket_id}")

    try:
        result = await TicketService.add_comment(
            ticket_id=request.ticket_id,
            agent_id=agent_id,
            comment_text=request.comment_text,
            comment_type=request.comment_type,
            mentions=request.mentions,
            attachments=request.attachments,
        )

        # Broadcast update
        await server_state.broadcast_update({
            "type": "ticket_comment_added",
            "ticket_id": request.ticket_id,
            "agent_id": agent_id,
            "comment_id": result["comment_id"],
        })

        return AddCommentResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error adding comment: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickets/{ticket_id}")
async def get_ticket_endpoint(
    ticket_id: str,
    agent_id: str = Header(None, alias="X-Agent-ID"),
):
    """Get full ticket details including comments and history.

    Args:
        ticket_id: The exact ticket ID to fetch (e.g., ticket-c368a0d1-cbd7-4231-a374-0a3a7374064e)
        agent_id: Optional agent ID for logging purposes
    """
    logger.info(f"Agent {agent_id or 'anonymous'} fetching ticket {ticket_id}")

    try:
        ticket = await TicketService.get_ticket(ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket not found: {ticket_id}")

        return ticket

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/search", response_model=SearchTicketsResponse)
async def search_tickets_endpoint(
    request: SearchTicketsRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """
    Search tickets using hybrid (semantic + keyword) search by default.

    Supports three search modes:
    - "semantic": Vector similarity only
    - "keyword": SQLite FTS5 only
    - "hybrid": Combined (70% semantic + 30% keyword) - DEFAULT
    """
    logger.info(f"Agent {agent_id} searching tickets: query='{request.query}', type={request.search_type}")

    try:
        # Auto-detect workflow_id from agent's current task if not provided
        workflow_id = request.workflow_id
        if not workflow_id:
            # Try to get from agent's current task first
            with get_db() as session:
                agent = session.query(Agent).filter_by(id=agent_id).first()
                if agent and agent.current_task_id:
                    task = session.query(Task).filter_by(id=agent.current_task_id).first()
                    if task and task.workflow_id:
                        workflow_id = task.workflow_id
                        logger.info(f"Auto-detected workflow_id {workflow_id} from agent's task {task.id}")

            # If still no workflow_id, try to get the single active workflow
            if not workflow_id:
                logger.info(f"Could not detect workflow_id from task, trying single active workflow...")
                workflow_id = get_single_active_workflow()
                if workflow_id:
                    logger.info(f"Using single active workflow: {workflow_id}")
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not determine workflow_id: no active workflows found or multiple workflows exist. "
                               "Please ensure you have exactly one active workflow."
                    )

        start_time = time.time()

        if request.search_type == "semantic":
            results = await TicketSearchService.semantic_search(
                query_text=request.query,
                workflow_id=workflow_id,
                limit=request.limit,
                filters=request.filters
            )
        elif request.search_type == "keyword":
            results = await TicketSearchService.keyword_search(
                keywords=request.query,
                workflow_id=workflow_id,
                limit=request.limit,
                filters=request.filters
            )
        else:  # hybrid (default)
            results = await TicketSearchService.hybrid_search(
                query=request.query,
                workflow_id=workflow_id,
                limit=request.limit,
                filters=request.filters,
                include_comments=request.include_comments
            )

        search_time_ms = (time.time() - start_time) * 1000

        return SearchTicketsResponse(
            success=True,
            query=request.query,
            results=[TicketSearchResult(**r) for r in results],
            total_found=len(results),
            search_time_ms=search_time_ms
        )

    except Exception as e:
        logger.error(f"Ticket search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickets/stats/{workflow_id}", response_model=TicketStatsResponse)
async def get_ticket_stats_endpoint(
    workflow_id: str,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Retrieve aggregate statistics for workflow tickets."""
    logger.info(f"Agent {agent_id} fetching ticket stats for workflow {workflow_id}")

    try:
        from src.core.database import Ticket, TicketComment, TicketCommit, BoardConfig
        from sqlalchemy import func

        session = server_state.db_manager.get_session()
        try:
            # Get board config for this workflow
            board_config = session.query(BoardConfig).filter_by(workflow_id=workflow_id).first()
            logger.info(f"BoardConfig found: {board_config is not None}, workflow_id: {workflow_id}")

            # Total tickets
            total_tickets = session.query(func.count(Ticket.id)).filter_by(workflow_id=workflow_id).scalar()

            # By status
            by_status = {}
            status_counts = session.query(
                Ticket.status, func.count(Ticket.id)
            ).filter_by(workflow_id=workflow_id).group_by(Ticket.status).all()
            for status, count in status_counts:
                by_status[status] = count

            # By type
            by_type = {}
            type_counts = session.query(
                Ticket.ticket_type, func.count(Ticket.id)
            ).filter_by(workflow_id=workflow_id).group_by(Ticket.ticket_type).all()
            for ticket_type, count in type_counts:
                by_type[ticket_type] = count

            # By priority
            by_priority = {}
            priority_counts = session.query(
                Ticket.priority, func.count(Ticket.id)
            ).filter_by(workflow_id=workflow_id).group_by(Ticket.priority).all()
            for priority, count in priority_counts:
                by_priority[priority] = count

            # By agent
            by_agent = {}
            agent_counts = session.query(
                Ticket.assigned_agent_id, func.count(Ticket.id)
            ).filter_by(workflow_id=workflow_id).filter(
                Ticket.assigned_agent_id.isnot(None)
            ).group_by(Ticket.assigned_agent_id).all()
            for agent_id_val, count in agent_counts:
                by_agent[agent_id_val] = count

            # Blocked count
            tickets_list = session.query(Ticket).filter_by(workflow_id=workflow_id).all()
            blocked_count = sum(1 for t in tickets_list if t.blocked_by_ticket_ids and len(t.blocked_by_ticket_ids) > 0)

            # Resolved count
            resolved_count = session.query(func.count(Ticket.id)).filter_by(
                workflow_id=workflow_id, is_resolved=True
            ).scalar()

            # Average comments per ticket
            total_comments = session.query(func.count(TicketComment.id)).join(
                Ticket, TicketComment.ticket_id == Ticket.id
            ).filter(Ticket.workflow_id == workflow_id).scalar()
            avg_comments = total_comments / total_tickets if total_tickets > 0 else 0.0

            # Average commits per ticket
            total_commits = session.query(func.count(TicketCommit.id)).join(
                Ticket, TicketCommit.ticket_id == Ticket.id
            ).filter(Ticket.workflow_id == workflow_id).scalar()
            avg_commits = total_commits / total_tickets if total_tickets > 0 else 0.0

            # Created today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            created_today = session.query(func.count(Ticket.id)).filter(
                Ticket.workflow_id == workflow_id,
                Ticket.created_at >= today_start
            ).scalar()

            # Completed today
            completed_today = session.query(func.count(Ticket.id)).filter(
                Ticket.workflow_id == workflow_id,
                Ticket.completed_at >= today_start
            ).scalar() if Ticket.completed_at else 0

            # Velocity last 7 days (tickets completed in last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            velocity_last_7_days = session.query(func.count(Ticket.id)).filter(
                Ticket.workflow_id == workflow_id,
                Ticket.is_resolved == True,
                Ticket.resolved_at >= seven_days_ago
            ).scalar()

            stats = TicketStats(
                total_tickets=total_tickets or 0,
                by_status=by_status,
                by_type=by_type,
                by_priority=by_priority,
                by_agent=by_agent,
                blocked_count=blocked_count,
                resolved_count=resolved_count or 0,
                avg_comments_per_ticket=avg_comments or 0.0,
                avg_commits_per_ticket=avg_commits or 0.0,
                created_today=created_today or 0,
                completed_today=completed_today or 0,
                velocity_last_7_days=velocity_last_7_days or 0
            )

            # Convert board_config to dict if it exists
            board_config_dict = None
            if board_config:
                board_config_dict = {
                    "name": board_config.name,
                    "columns": board_config.columns,
                    "ticket_types": board_config.ticket_types,
                    "default_ticket_type": board_config.default_ticket_type,
                    "initial_status": board_config.initial_status,
                    "auto_assign": board_config.auto_assign if hasattr(board_config, 'auto_assign') else False,
                    "allow_reopen": board_config.allow_reopen if hasattr(board_config, 'allow_reopen') else True,
                    "track_time": board_config.track_time if hasattr(board_config, 'track_time') else False,
                }

            return TicketStatsResponse(
                success=True,
                workflow_id=workflow_id,
                stats=stats,
                board_config=board_config_dict
            )

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to get ticket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tickets", response_model=GetTicketsResponse)
async def get_tickets_endpoint(
    agent_id: str = Header(..., alias="X-Agent-ID"),
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    ticket_type: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_agent_id: Optional[str] = None,
    include_completed: bool = True,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """Get/list tickets with filtering and pagination."""

    try:
        # Auto-detect workflow_id from agent's current task if not provided
        if not workflow_id:
            # Try to get from agent's current task first
            with get_db() as session:
                agent = session.query(Agent).filter_by(id=agent_id).first()
                if agent and agent.current_task_id:
                    task = session.query(Task).filter_by(id=agent.current_task_id).first()
                    if task and task.workflow_id:
                        workflow_id = task.workflow_id
                        logger.info(f"Auto-detected workflow_id {workflow_id} from agent's task {task.id}")

            # If still no workflow_id, try to get the single active workflow
            if not workflow_id:
                logger.info(f"Could not detect workflow_id from task, trying single active workflow...")
                workflow_id = get_single_active_workflow()
                if workflow_id:
                    logger.info(f"Using single active workflow: {workflow_id}")
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not determine workflow_id: no active workflows found or multiple workflows exist. "
                               "Please ensure you have exactly one active workflow."
                    )

        logger.info(f"Agent {agent_id} fetching tickets for workflow {workflow_id}")

        # Build filters dict, only including non-None values
        filters = {}
        if status is not None:
            filters["status"] = status
        if ticket_type is not None:
            filters["ticket_type"] = ticket_type
        if priority is not None:
            filters["priority"] = priority
        if assigned_agent_id is not None:
            filters["assigned_agent_id"] = assigned_agent_id
        if not include_completed:
            filters["include_completed"] = include_completed

        result = await TicketService.get_tickets_by_workflow(
            workflow_id=workflow_id,
            filters=filters,
        )

        # Result is a list of ticket dicts
        tickets = [TicketDetail(**t) for t in result]

        return GetTicketsResponse(
            success=True,
            tickets=tickets,
            total_count=len(tickets),
            has_more=False,  # TODO: Implement pagination in service
        )

    except Exception as e:
        logger.error(f"Failed to get tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/resolve", response_model=ResolveTicketResponse)
async def resolve_ticket_endpoint(
    request: ResolveTicketRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Mark ticket as resolved and automatically unblock dependent tickets."""
    logger.info(f"Agent {agent_id} resolving ticket {request.ticket_id}")

    try:
        result = await TicketService.resolve_ticket(
            ticket_id=request.ticket_id,
            agent_id=agent_id,
            resolution_comment=request.resolution_comment,
            commit_sha=request.commit_sha,
        )

        # Broadcast update
        await server_state.broadcast_update({
            "type": "ticket_resolved",
            "ticket_id": request.ticket_id,
            "agent_id": agent_id,
            "unblocked_tickets": result["unblocked_tickets"],
        })

        return ResolveTicketResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error resolving ticket: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resolve ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/link-commit", response_model=LinkCommitResponse)
async def link_commit_endpoint(
    request: LinkCommitRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Manually link a git commit to a ticket."""
    logger.info(f"Agent {agent_id} linking commit {request.commit_sha} to ticket {request.ticket_id}")

    try:
        result = await TicketService.link_commit(
            ticket_id=request.ticket_id,
            agent_id=agent_id,
            commit_sha=request.commit_sha,
            commit_message=request.commit_message,
            link_method="manual",
        )

        # Broadcast update
        await server_state.broadcast_update({
            "type": "commit_linked",
            "ticket_id": request.ticket_id,
            "agent_id": agent_id,
            "commit_sha": request.commit_sha,
        })

        return LinkCommitResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error linking commit: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to link commit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tickets/request-clarification", response_model=RequestTicketClarificationResponse)
async def request_ticket_clarification_endpoint(
    request: RequestTicketClarificationRequest,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """
    Request LLM-powered clarification for a ticket with conflicting/unclear requirements.

    This endpoint prevents infinite task creation loops by providing agents with
    clear, LLM-arbitrated guidance when they encounter ambiguity or conflicts.

    Process:
    1. Gathers comprehensive context (ticket details, 60 recent tickets, 60 recent tasks)
    2. Calls LLM with structured reasoning prompt
    3. Returns detailed markdown guidance
    4. Stores clarification as ticket comment for audit trail
    """
    logger.info(f"[CLARIFICATION] ========== START ==========")
    logger.info(f"[CLARIFICATION] Agent {agent_id[:8]} requesting clarification for ticket {request.ticket_id}")
    logger.info(f"[CLARIFICATION] Conflict: {request.conflict_description[:100]}...")

    try:
        with get_db() as db:
            # 1. Validate ticket exists
            ticket = db.query(Ticket).filter_by(id=request.ticket_id).first()
            if not ticket:
                logger.error(f"[CLARIFICATION] Ticket not found: {request.ticket_id}")
                raise HTTPException(status_code=404, detail=f"Ticket not found: {request.ticket_id}")

            logger.info(f"[CLARIFICATION] Ticket found: {ticket.title}")

            # 2. Gather context - Latest 60 tickets
            recent_tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).limit(60).all()
            tickets_context = [
                {
                    "ticket_id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "ticket_type": t.ticket_type
                }
                for t in recent_tickets
            ]
            logger.info(f"[CLARIFICATION] Gathered {len(tickets_context)} recent tickets for context")

            # 3. Gather context - Latest 60 tasks
            recent_tasks = db.query(Task).order_by(Task.created_at.desc()).limit(60).all()
            tasks_context = [
                {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status,
                    "phase_id": t.phase_id
                }
                for t in recent_tasks
            ]
            logger.info(f"[CLARIFICATION] Gathered {len(tasks_context)} recent tasks for context")

            # 4. Prepare ticket details
            ticket_details = {
                "ticket_id": ticket.id,
                "title": ticket.title,
                "description": ticket.description,
                "status": ticket.status,
                "priority": ticket.priority,
                "ticket_type": ticket.ticket_type,
                "assigned_agent_id": ticket.assigned_agent_id,
                "tags": ticket.tags or []
            }

        # 5. Call LLM for clarification
        logger.info(f"[CLARIFICATION] Calling LLM arbitrator with full context...")
        logger.info(f"[CLARIFICATION] Potential solutions provided: {len(request.potential_solutions)}")

        clarification_markdown = await server_state.llm_provider.resolve_ticket_clarification(
            ticket_id=request.ticket_id,
            conflict_description=request.conflict_description,
            context=request.context,
            potential_solutions=request.potential_solutions,
            ticket_details=ticket_details,
            related_tickets=tickets_context,
            active_tasks=tasks_context
        )

        logger.info(f"[CLARIFICATION] ✅ LLM arbitration complete, {len(clarification_markdown)} chars")

        # 6. Store clarification as ticket comment
        comment_text = f"""## 🤖 AUTOMATED CLARIFICATION REQUEST

**Agent**: `{agent_id}`
**Conflict Description**: {request.conflict_description}

---

{clarification_markdown}

---

*This clarification was automatically generated by the Hephaestus arbitration system.*
"""

        comment_result = await TicketService.add_comment(
            ticket_id=request.ticket_id,
            agent_id=agent_id,
            comment_text=comment_text,
            comment_type="clarification",
            mentions=[],
            attachments=[]
        )

        logger.info(f"[CLARIFICATION] ✅ Stored as comment {comment_result['comment_id']}")
        logger.info(f"[CLARIFICATION] ========== SUCCESS ==========")

        # Broadcast update
        await server_state.broadcast_update({
            "type": "ticket_clarification_requested",
            "ticket_id": request.ticket_id,
            "agent_id": agent_id,
            "comment_id": comment_result['comment_id'],
        })

        return RequestTicketClarificationResponse(
            success=True,
            ticket_id=request.ticket_id,
            clarification=clarification_markdown,
            comment_id=comment_result['comment_id'],
            message="Clarification generated and stored successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CLARIFICATION] ❌ Error: {e}", exc_info=True)
        logger.error(f"[CLARIFICATION] ========== FAILED ==========")
        raise HTTPException(status_code=500, detail=f"Failed to generate clarification: {str(e)}")


@app.get("/api/tickets/commit-diff/{commit_sha}", response_model=CommitDiffResponse)
async def get_commit_diff_endpoint(
    commit_sha: str,
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Get detailed git diff for a commit (for Git Diff Window in UI)."""
    logger.info(f"Agent {agent_id} fetching commit diff for {commit_sha}")

    try:
        import subprocess
        import re

        # Get the configured main repo path
        config = get_config()
        main_repo_path = str(config.main_repo_path)

        # Helper function to detect language from file extension
        def detect_language(file_path: str) -> str:
            ext_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".tsx": "tsx",
                ".jsx": "jsx",
                ".go": "go",
                ".rs": "rust",
                ".java": "java",
                ".c": "c",
                ".cpp": "cpp",
                ".h": "c",
                ".hpp": "cpp",
                ".md": "markdown",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".json": "json",
                ".sql": "sql",
                ".sh": "bash",
            }
            ext = os.path.splitext(file_path)[1].lower()
            return ext_map.get(ext, "text")

        # Get commit metadata from the correct repository
        cmd = ["git", "show", "--format=%H|%an|%at|%s", "-s", commit_sha]
        result = subprocess.run(cmd, cwd=main_repo_path, capture_output=True, text=True, check=True)

        if result.returncode != 0:
            raise HTTPException(status_code=404, detail=f"Commit not found: {commit_sha}")

        parts = result.stdout.strip().split("|", 3)
        commit_hash = parts[0] if len(parts) > 0 else commit_sha
        author = parts[1] if len(parts) > 1 else "unknown"
        timestamp_unix = int(parts[2]) if len(parts) > 2 else 0
        message = parts[3] if len(parts) > 3 else "No message"

        timestamp = datetime.fromtimestamp(timestamp_unix).isoformat() if timestamp_unix > 0 else datetime.utcnow().isoformat()

        # Get file stats from the correct repository
        cmd = ["git", "diff", "--numstat", f"{commit_sha}^", commit_sha]
        result = subprocess.run(cmd, cwd=main_repo_path, capture_output=True, text=True, check=True)

        files_data = []
        total_insertions = 0
        total_deletions = 0

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue

            insertions = int(parts[0]) if parts[0].isdigit() else 0
            deletions = int(parts[1]) if parts[1].isdigit() else 0
            file_path = parts[2]

            total_insertions += insertions
            total_deletions += deletions

            # Get unified diff for this file from the correct repository
            cmd_diff = ["git", "diff", f"{commit_sha}^", commit_sha, "--", file_path]
            diff_result = subprocess.run(cmd_diff, cwd=main_repo_path, capture_output=True, text=True)

            # Determine file status
            status = "modified"
            old_path = None
            if "new file mode" in diff_result.stdout:
                status = "added"
            elif "deleted file mode" in diff_result.stdout:
                status = "deleted"
            elif "rename from" in diff_result.stdout:
                status = "renamed"
                rename_match = re.search(r"rename from (.+)", diff_result.stdout)
                if rename_match:
                    old_path = rename_match.group(1)

            files_data.append(FileDiff(
                path=file_path,
                status=status,
                insertions=insertions,
                deletions=deletions,
                diff=diff_result.stdout,
                language=detect_language(file_path),
                old_path=old_path,
            ))

        return CommitDiffResponse(
            success=True,
            commit_sha=commit_hash,
            commit_message=message,
            author=author,
            commit_timestamp=timestamp,
            files_changed=len(files_data),
            total_insertions=total_insertions,
            total_deletions=total_deletions,
            total_files=len(files_data),
            files=files_data,
        )

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get commit diff: {e}")
    except Exception as e:
        logger.error(f"Failed to get commit diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows")
async def get_workflows_endpoint(
    agent_id: str = Header(..., alias="X-Agent-ID"),
):
    """Get all workflows."""
    logger.info(f"Agent {agent_id} fetching workflows")

    try:
        session = server_state.db_manager.get_session()
        try:
            workflows = session.query(Workflow).all()

            return [
                {
                    "id": w.id,
                    "name": w.name,
                    "status": w.status,
                    "phases_folder_path": w.phases_folder_path,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                }
                for w in workflows
            ]
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to fetch workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/terminate_agent")
async def terminate_agent_endpoint(
    agent_id: str = Body(..., embed=True),
    reason: str = Body(default="Manual termination", embed=True),
):
    """Manually terminate an agent from the UI.

    This endpoint allows users to forcefully terminate running agents.
    After termination, the queue is processed to start the next queued task if any.
    """
    logger.info(f"Manual termination request for agent {agent_id}: {reason}")

    try:
        session = server_state.db_manager.get_session()
        try:
            # Verify agent exists
            agent = session.query(Agent).filter_by(id=agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            if agent.status == "terminated":
                raise HTTPException(status_code=400, detail=f"Agent {agent_id} is already terminated")

            # Get the agent's task if any
            task = None
            if agent.current_task_id:
                task = session.query(Task).filter_by(id=agent.current_task_id).first()

            # Terminate the agent and mark task as failed
            await server_state.agent_manager.terminate_agent(agent_id)

            if task:
                task.status = "failed"
                task.failure_reason = f"Manually terminated: {reason}"
                task.completed_at = datetime.utcnow()
                session.commit()

        finally:
            session.close()

        # Process queue after termination
        await process_queue()

        # Broadcast update
        await server_state.broadcast_update({
            "type": "agent_terminated_manually",
            "agent_id": agent_id,
            "reason": reason,
        })

        return {"success": True, "message": f"Agent {agent_id[:8]} terminated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to terminate agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bump_task_priority")
async def bump_task_priority_endpoint(
    task_id: str = Body(..., embed=True),
):
    """Bump a queued task and start it immediately, bypassing the agent limit.

    This allows urgent tasks to start even when at max capacity (e.g., 2/2 → 3/2).
    When agents complete, the system returns to the configured limit.
    """
    logger.info(f"Priority bump & start request for task {task_id}")

    try:
        session = server_state.db_manager.get_session()
        try:
            # Verify task exists and is queued
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            if task.status != "queued":
                raise HTTPException(
                    status_code=400,
                    detail=f"Task {task_id} is not queued (status: {task.status})"
                )

        finally:
            session.close()

        # Boost the task priority first
        success = server_state.queue_service.boost_task_priority(task_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to boost task priority")

        # Dequeue and start immediately (bypassing limit)
        session = server_state.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()

            # Dequeue the task
            server_state.queue_service.dequeue_task(task_id)

            # Get project context
            project_context = await server_state.agent_manager.get_project_context()

            # Get phase context if applicable
            if task.phase_id and server_state.phase_manager:
                phase_context = server_state.phase_manager.get_phase_context(task.phase_id)
                if phase_context:
                    project_context = f"{project_context}\n\n{phase_context.to_prompt_context()}"

            # Retrieve relevant memories
            context_memories = await server_state.rag_system.retrieve_for_task(
                task_description=task.enriched_description or task.raw_description,
                requesting_agent_id="system",
            )

            # Determine working directory
            working_directory = None
            if task.phase_id:
                from src.core.database import Phase
                phase = session.query(Phase).filter_by(id=task.phase_id).first()
                if phase and phase.working_directory:
                    working_directory = phase.working_directory
            if not working_directory:
                working_directory = os.getcwd()

        finally:
            session.close()

        # Create agent immediately (bypassing agent limit)
        agent = await server_state.agent_manager.create_agent_for_task(
            task=task,
            enriched_data={"enriched_description": task.enriched_description},
            memories=context_memories,
            project_context=project_context,
            working_directory=working_directory,
        )

        # Update task status
        session = server_state.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                task.assigned_agent_id = agent.id
                task.status = "assigned"
                task.started_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

        # Broadcast update
        await server_state.broadcast_update({
            "type": "task_priority_bumped",
            "task_id": task_id,
            "agent_id": agent.id,
        })

        logger.info(f"Task {task_id} bumped and agent {agent.id} created (bypassing limit)")

        return {
            "success": True,
            "message": f"Task {task_id[:8]} started immediately (bypassing agent limit)",
            "agent_id": agent.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bump and start task: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cancel_queued_task")
async def cancel_queued_task_endpoint(
    task_id: str = Body(..., embed=True),
):
    """Cancel a queued task and remove it from the queue.

    The task will be marked as failed and removed from the queue.
    """
    logger.info(f"Cancel request for queued task {task_id}")

    try:
        session = server_state.db_manager.get_session()
        try:
            # Verify task exists and is queued
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            if task.status != "queued":
                raise HTTPException(
                    status_code=400,
                    detail=f"Task {task_id} is not queued (status: {task.status})"
                )

            # Mark task as failed
            task.status = "failed"
            task.failure_reason = "Cancelled by user from queue"
            task.completed_at = datetime.utcnow()
            session.commit()

        finally:
            session.close()

        # Remove from queue
        server_state.queue_service.dequeue_task(task_id)

        # Broadcast update
        await server_state.broadcast_update({
            "type": "task_cancelled",
            "task_id": task_id,
        })

        logger.info(f"Task {task_id} cancelled and removed from queue")

        return {
            "success": True,
            "message": f"Task {task_id[:8]} cancelled and removed from queue",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel queued task: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/restart_task")
async def restart_task_endpoint(
    task_id: str = Body(..., embed=True),
):
    """Restart a completed or failed task.

    This will:
    - Clear completion data (failure_reason, completion_notes, completed_at)
    - Clear trajectory data (guardian analyses, steering interventions)
    - Reset task to pending/queued status
    - Create new agent or queue based on capacity
    """
    logger.info(f"Restart request for task {task_id}")

    try:
        session = server_state.db_manager.get_session()
        try:
            # Verify task exists and is done/failed
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            if task.status not in ["done", "failed"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only restart completed or failed tasks (current status: {task.status})"
                )

            # Get agent ID before clearing (to delete trajectory data)
            old_agent_id = task.assigned_agent_id

            # Clear completion data
            task.status = "pending"
            task.assigned_agent_id = None
            task.started_at = None
            task.completed_at = None
            task.completion_notes = None
            task.failure_reason = None
            session.commit()

        finally:
            session.close()

        # Clear trajectory data for old agent
        if old_agent_id:
            session = server_state.db_manager.get_session()
            try:
                from src.core.database import GuardianAnalysis, SteeringIntervention

                # Delete guardian analyses
                session.query(GuardianAnalysis).filter_by(agent_id=old_agent_id).delete()

                # Delete steering interventions
                session.query(SteeringIntervention).filter_by(agent_id=old_agent_id).delete()

                session.commit()
                logger.info(f"Cleared trajectory data for agent {old_agent_id}")

            finally:
                session.close()

        # Check if we should queue or create agent immediately
        should_queue = server_state.queue_service.should_queue_task()

        if should_queue:
            # Queue the task
            server_state.queue_service.enqueue_task(task_id)
            logger.info(f"Task {task_id} restarted and queued")

            # Broadcast update
            await server_state.broadcast_update({
                "type": "task_restarted",
                "task_id": task_id,
                "status": "queued",
            })

            return {
                "success": True,
                "message": f"Task {task_id[:8]} restarted and added to queue",
                "status": "queued",
            }
        else:
            # Create agent immediately
            session = server_state.db_manager.get_session()
            try:
                task = session.query(Task).filter_by(id=task_id).first()

                # Get project context
                project_context = await server_state.agent_manager.get_project_context()

                # Get phase context if applicable
                if task.phase_id and server_state.phase_manager:
                    phase_context = server_state.phase_manager.get_phase_context(task.phase_id)
                    if phase_context:
                        project_context = f"{project_context}\n\n{phase_context.to_prompt_context()}"

                # Retrieve relevant memories
                context_memories = await server_state.rag_system.retrieve_for_task(
                    task_description=task.enriched_description or task.raw_description,
                    requesting_agent_id="system",
                )

                # Determine working directory
                working_directory = None
                if task.phase_id:
                    from src.core.database import Phase
                    phase = session.query(Phase).filter_by(id=task.phase_id).first()
                    if phase and phase.working_directory:
                        working_directory = phase.working_directory
                if not working_directory:
                    working_directory = os.getcwd()

            finally:
                session.close()

            # Create agent for the task
            agent = await server_state.agent_manager.create_agent_for_task(
                task=task,
                enriched_data={"enriched_description": task.enriched_description},
                memories=context_memories,
                project_context=project_context,
                working_directory=working_directory,
            )

            # Update task status
            session = server_state.db_manager.get_session()
            try:
                task = session.query(Task).filter_by(id=task_id).first()
                if task:
                    task.assigned_agent_id = agent.id
                    task.status = "assigned"
                    task.started_at = datetime.utcnow()
                    session.commit()
            finally:
                session.close()

            logger.info(f"Task {task_id} restarted with new agent {agent.id}")

            # Broadcast update
            await server_state.broadcast_update({
                "type": "task_restarted",
                "task_id": task_id,
                "agent_id": agent.id,
                "status": "assigned",
            })

            return {
                "success": True,
                "message": f"Task {task_id[:8]} restarted with new agent",
                "agent_id": agent.id,
                "status": "assigned",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restart task: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue_status")
async def get_queue_status_endpoint():
    """Get current queue status information.

    Returns information about active agents, queued tasks, and available slots.
    """
    try:
        status = server_state.queue_service.get_queue_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent_status")
async def get_agent_status(
    agent_id: Optional[str] = None,
    requesting_agent_id: str = Header(None, alias="X-Agent-ID"),
):
    """Get status of specific agent or all agents."""
    try:
        session = server_state.db_manager.get_session()

        if agent_id:
            agent = session.query(Agent).filter_by(id=agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")

            result = {
                "id": agent.id,
                "status": agent.status,
                "current_task_id": agent.current_task_id,
                "last_activity": agent.last_activity.isoformat() if agent.last_activity else None,
                "health_check_failures": agent.health_check_failures,
            }
        else:
            # Get all active agents
            agents = session.query(Agent).filter(
                Agent.status != "terminated"
            ).all()

            result = [
                {
                    "id": agent.id,
                    "status": agent.status,
                    "current_task_id": agent.current_task_id,
                    "last_activity": agent.last_activity.isoformat() if agent.last_activity else None,
                }
                for agent in agents
            ]

        session.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task_progress")
async def get_task_progress(
    task_id: Optional[str] = None,
    requesting_agent_id: str = Header(None, alias="X-Agent-ID"),
):
    """Get progress of specific task or all active tasks."""
    try:
        session = server_state.db_manager.get_session()

        if task_id:
            task = session.query(Task).filter_by(id=task_id).first()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            result = {
                "id": task.id,
                "status": task.status,
                "description": task.enriched_description or task.raw_description,
                "assigned_agent_id": task.assigned_agent_id,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "phase_id": task.phase_id,
                "workflow_id": task.workflow_id,
            }

            # Add phase information if available
            if task.phase_id:
                phase = session.query(Phase).filter_by(id=task.phase_id).first()
                if phase:
                    result["phase_name"] = phase.name
                    result["phase_order"] = phase.order
        else:
            # Get all active tasks
            tasks = session.query(Task).filter(
                Task.status.in_(["pending", "assigned", "in_progress"])
            ).all()

            result = []
            for task in tasks:
                task_data = {
                    "id": task.id,
                    "status": task.status,
                    "description": (task.enriched_description or task.raw_description)[:200],
                    "assigned_agent_id": task.assigned_agent_id,
                    "phase_id": task.phase_id,
                    "workflow_id": task.workflow_id,
                }

                # Add phase information if available
                if task.phase_id:
                    phase = session.query(Phase).filter_by(id=task.phase_id).first()
                    if phase:
                        task_data["phase_name"] = phase.name
                        task_data["phase_order"] = phase.order

                result.append(task_data)

        session.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    server_state.active_websockets.append(websocket)

    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({"type": "echo", "data": data})

    except WebSocketDisconnect:
        server_state.active_websockets.remove(websocket)
        logger.info("WebSocket client disconnected")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# OAuth endpoints for MCP compatibility with Dynamic Client Registration
@app.get("/.well-known/oauth-authorization-server")
async def oauth_server_metadata():
    """OAuth server metadata with DCR support."""
    return {
        "issuer": "http://localhost:8000",
        "authorization_endpoint": "http://localhost:8000/oauth/authorize",
        "token_endpoint": "http://localhost:8000/oauth/token",
        "registration_endpoint": "http://localhost:8000/oauth/register",  # DCR endpoint
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],  # PKCE support
        "token_endpoint_auth_methods_supported": ["none"],
        "revocation_endpoint": "http://localhost:8000/oauth/revoke",
        "scopes_supported": ["openid", "profile", "email"],
    }


@app.get("/.well-known/openid-configuration")
async def openid_config():
    """OpenID configuration - tells Claude no auth needed."""
    return {
        "issuer": "http://localhost:8000",
        "authorization_endpoint": "http://localhost:8000/authorize",
        "token_endpoint": "http://localhost:8000/token",
        "userinfo_endpoint": "http://localhost:8000/userinfo",
        "response_types_supported": ["none"],
        "grant_types_supported": ["none"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["none"],
    }


# Store registered clients (in production, use a database)
registered_clients = {}


@app.post("/oauth/register")
async def register_client(request: Dict[str, Any]):
    """Dynamic Client Registration endpoint (RFC 7591)."""
    import secrets

    client_id = f"client_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)

    # Store client registration
    registered_clients[client_id] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": request.get("client_name", "Claude"),
        "redirect_uris": request.get("redirect_uris", ["https://claude.ai/api/mcp/auth_callback"]),
        "grant_types": request.get("grant_types", ["authorization_code"]),
        "response_types": request.get("response_types", ["code"]),
        "scope": request.get("scope", "openid profile email"),
        "token_endpoint_auth_method": request.get("token_endpoint_auth_method", "none"),
    }

    # Return client registration response
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "client_secret_expires_at": 0,  # Never expires
        "redirect_uris": registered_clients[client_id]["redirect_uris"],
        "grant_types": registered_clients[client_id]["grant_types"],
        "response_types": registered_clients[client_id]["response_types"],
        "client_name": registered_clients[client_id]["client_name"],
        "scope": registered_clients[client_id]["scope"],
        "token_endpoint_auth_method": registered_clients[client_id]["token_endpoint_auth_method"],
    }


@app.get("/oauth/authorize")
async def authorize_get(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "openid profile email",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
):
    """Authorization endpoint - auto-approves for local use."""
    import secrets

    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)

    # Build redirect URL with code
    redirect_url = f"{redirect_uri}?code={auth_code}"
    if state:
        redirect_url += f"&state={state}"

    # Return HTML that auto-redirects (simulating user approval)
    html_content = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url={redirect_url}">
    </head>
    <body>
        <p>Authorizing... Redirecting to Claude...</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/oauth/authorize")
async def authorize_post(request: Dict[str, Any]):
    """Authorization endpoint POST - for form submissions."""
    return await authorize_get(
        client_id=request.get("client_id"),
        redirect_uri=request.get("redirect_uri"),
        response_type=request.get("response_type", "code"),
        scope=request.get("scope", "openid profile email"),
        state=request.get("state"),
        code_challenge=request.get("code_challenge"),
        code_challenge_method=request.get("code_challenge_method"),
    )


@app.post("/oauth/token")
async def token(request: Dict[str, Any] = Body(...)):
    """Token endpoint - returns access token."""
    import secrets

    # For simplicity, always return a valid token (no real auth)
    return {
        "access_token": f"access_{secrets.token_urlsafe(32)}",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": f"refresh_{secrets.token_urlsafe(32)}",
        "scope": request.get("scope", "openid profile email"),
    }


@app.post("/oauth/revoke")
async def revoke_token(request: Dict[str, Any]):
    """Token revocation endpoint."""
    # For local use, just return success
    return {"revoked": True}


@app.get("/userinfo")
async def userinfo():
    """Fake userinfo endpoint."""
    return {
        "sub": "local-user",
        "name": "Local User",
        "preferred_username": "local",
    }


@app.get("/")
async def root():
    """Root endpoint with MCP protocol info."""
    return {
        "name": "Hephaestus MCP Server",
        "version": "1.0.0",
        "protocol_version": "1.0",
        "description": "Model Context Protocol server for AI agent orchestration",
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": False,
            "auth": {
                "type": "none",
                "required": False
            }
        },
        "endpoints": [
            "/create_task",
            "/update_task_status",
            "/save_memory",
            "/agent_status",
            "/task_progress",
            "/health",
            "/ws",
            "/sse",
            "/tools",
            "/resources",
        ],
    }


# MCP Protocol endpoints
@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "create_task",
                "description": "Create a new task for an autonomous agent",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_description": {"type": "string"},
                        "done_definition": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["task_description", "done_definition"]
                }
            },
            {
                "name": "save_memory",
                "description": "Save a memory to the knowledge base",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "memory_type": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["content", "memory_type"]
                }
            },
            {
                "name": "get_task_status",
                "description": "Get status of all tasks",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }


@app.post("/tools/execute")
async def execute_tool(request: Dict[str, Any]):
    """Execute an MCP tool."""
    tool_name = request.get("tool")
    arguments = request.get("arguments", {})

    if tool_name == "create_task":
        # Forward to create_task endpoint
        return await create_task(
            CreateTaskRequest(
                task_description=arguments.get("task_description"),
                done_definition=arguments.get("done_definition"),
                ai_agent_id="mcp-claude",
                priority=arguments.get("priority", "medium")
            ),
            agent_id="mcp-claude"
        )
    elif tool_name == "save_memory":
        # Forward to save_memory endpoint
        return await save_memory(
            SaveMemoryRequest(
                content=arguments.get("content"),
                memory_type=arguments.get("memory_type", "discovery"),
                tags=arguments.get("tags", []),
                related_files=arguments.get("related_files", [])
            ),
            agent_id="mcp-claude"
        )
    elif tool_name == "get_task_status":
        return await task_progress()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")


@app.get("/resources")
async def list_resources():
    """List available MCP resources."""
    session = server_state.db_manager.get_session()
    try:
        tasks = session.query(Task).filter(Task.status != "done").all()
        return {
            "resources": [
                {
                    "uri": f"task://{task.id}",
                    "name": f"Task: {task.id[:8]}",
                    "description": (task.enriched_description or task.raw_description)[:100],
                    "mimeType": "application/json"
                }
                for task in tasks
            ]
        }
    finally:
        session.close()


@app.get("/resources/{resource_uri:path}")
async def get_resource(resource_uri: str):
    """Get a specific MCP resource."""
    if resource_uri.startswith("task://"):
        task_id = resource_uri.replace("task://", "")
        session = server_state.db_manager.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                return {
                    "uri": resource_uri,
                    "content": {
                        "id": task.id,
                        "description": task.enriched_description or task.raw_description,
                        "status": task.status,
                        "assigned_agent": task.assigned_agent_id,
                        "created_at": task.created_at.isoformat() if task.created_at else None
                    }
                }
            else:
                raise HTTPException(status_code=404, detail="Task not found")
        finally:
            session.close()
    else:
        raise HTTPException(status_code=404, detail="Resource not found")


@app.get("/sse")
async def sse_endpoint():
    """Server-Sent Events endpoint for Claude MCP integration."""
    async def event_generator():
        """Generate SSE events."""
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Connected to Hephaestus MCP Server', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

        # Create a queue for this SSE connection
        event_queue = asyncio.Queue(maxsize=100)
        server_state.sse_queues.append(event_queue)

        try:
            while True:
                # Wait for events to send
                try:
                    # Check for events with timeout to send keepalive
                    event = await asyncio.wait_for(event_queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive event every 30 seconds
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
        except asyncio.CancelledError:
            # Clean up when connection is closed
            if event_queue in server_state.sse_queues:
                server_state.sse_queues.remove(event_queue)
            raise
        finally:
            # Ensure cleanup
            if event_queue in server_state.sse_queues:
                server_state.sse_queues.remove(event_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )