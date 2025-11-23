"""
Index Repo Workflow - Python Phase Definitions

This workflow scans a repository and extracts comprehensive knowledge into the memory system.
It's designed to run BEFORE other workflows (bug fix, feature development) to give agents
rich context about the codebase.

The workflow consists of 2 phases:
1. Phase 1: Initial Scan - Understand the repo, discover components, create Phase 2 tasks
2. Phase 2: Component Deep Dive - Thoroughly explore each component, save detailed memories

Usage:
    from example_workflows.index_repo.phases import INDEX_REPO_PHASES, INDEX_REPO_CONFIG, INDEX_REPO_LAUNCH_TEMPLATE

    index_repo_definition = WorkflowDefinition(
        id="index-repo",
        name="Index Repository",
        phases=INDEX_REPO_PHASES,
        config=INDEX_REPO_CONFIG,
        launch_template=INDEX_REPO_LAUNCH_TEMPLATE,
    )

    sdk = HephaestusSDK(workflow_definitions=[index_repo_definition])
"""

# Import phase definitions
from example_workflows.index_repo.phase_1_initial_scan import PHASE_1_INITIAL_SCAN
from example_workflows.index_repo.phase_2_component_deep_dive import PHASE_2_COMPONENT_DEEP_DIVE

# Import SDK models
from src.sdk.models import WorkflowConfig, LaunchTemplate, LaunchParameter

# Export phase list
INDEX_REPO_PHASES = [
    PHASE_1_INITIAL_SCAN,
    PHASE_2_COMPONENT_DEEP_DIVE,
]

# Workflow configuration
# Knowledge-extraction workflow with simple Kanban board for tracking exploration progress
INDEX_REPO_CONFIG = WorkflowConfig(
    has_result=False,  # No final deliverable - memories ARE the output
    enable_tickets=True,  # Track components on Kanban board
    board_config={
        "columns": [
            {"id": "discovered", "name": "🔍 Discovered", "order": 1, "color": "#94a3b8"},
            {"id": "exploring", "name": "🔬 Exploring", "order": 2, "color": "#f59e0b"},
            {"id": "indexed", "name": "✅ Indexed", "order": 3, "color": "#22c55e"},
        ],
        "ticket_types": ["component", "area"],
        "default_ticket_type": "component",
        "initial_status": "discovered",
        "auto_assign": True,
        "require_comments_on_status_change": True,
        "allow_reopen": False,  # No need to re-explore components
        "track_time": True,
    },
)

# Launch template - simple form with optional context
INDEX_REPO_LAUNCH_TEMPLATE = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="repo_context",
            label="Repository Context (Optional)",
            type="textarea",
            required=False,
            default="",
            description="Add any context about this repo that might help the exploration (e.g., 'This is a FastAPI backend for a todo app' or 'Focus on the authentication and API layers')"
        ),
    ],
    phase_1_task_prompt="""Phase 1: Initial Repository Scan

**Additional Context from User:**
{repo_context}

---

Your task:
1. Scan the repository to understand what it is and what it does
2. Read README, docs, and configuration files
3. Identify the tech stack (languages, frameworks, tools)
4. Map the directory structure
5. Discover all major components/modules
6. Save your findings to memory (use save_memory frequently!)
7. Create a Phase 2 deep-dive task for EACH component you discover
8. Mark your task as done with a summary of components found

Remember: Your memories will help other agents understand this codebase!
""",
)

# Export all
__all__ = [
    "INDEX_REPO_PHASES",
    "INDEX_REPO_CONFIG",
    "INDEX_REPO_LAUNCH_TEMPLATE",
    "PHASE_1_INITIAL_SCAN",
    "PHASE_2_COMPONENT_DEEP_DIVE",
]
