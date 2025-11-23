"""
Feature Development Workflow - Python Phase Definitions

This workflow adds features to existing codebases. It:
1. Analyzes the feature request, breaks it into work items, creates tickets with blocking
2. Implements each work item following existing patterns (parallel Phase 2 tasks)
3. Validates each work item and resolves its ticket (parallel Phase 3 tasks)

Key difference from PRD workflow: Works with EXISTING code, not greenfield.

Usage:
    from example_workflows.feature_development.phases import (
        FEATURE_DEV_PHASES,
        FEATURE_DEV_CONFIG,
        FEATURE_DEV_LAUNCH_TEMPLATE,
    )

    feature_dev_definition = WorkflowDefinition(
        id="feature-dev",
        name="Feature Development",
        phases=FEATURE_DEV_PHASES,
        config=FEATURE_DEV_CONFIG,
        launch_template=FEATURE_DEV_LAUNCH_TEMPLATE,
    )

    sdk = HephaestusSDK(workflow_definitions=[feature_dev_definition])
"""

# Import phase definitions
from example_workflows.feature_development.phase_1_feature_analysis import PHASE_1_FEATURE_ANALYSIS
from example_workflows.feature_development.phase_2_design_and_implementation import PHASE_2_DESIGN_AND_IMPLEMENTATION
from example_workflows.feature_development.phase_3_validate_and_integrate import PHASE_3_VALIDATE_AND_INTEGRATE

# Import SDK models
from src.sdk.models import WorkflowConfig, LaunchTemplate, LaunchParameter

# Export phase list
FEATURE_DEV_PHASES = [
    PHASE_1_FEATURE_ANALYSIS,
    PHASE_2_DESIGN_AND_IMPLEMENTATION,
    PHASE_3_VALIDATE_AND_INTEGRATE,
]

# Workflow configuration
# Feature development with 6-column board to track work item progress
FEATURE_DEV_CONFIG = WorkflowConfig(
    has_result=False,  # No formal result submission - all tickets resolved = complete
    enable_tickets=True,
    board_config={
        "columns": [
            {"id": "backlog", "name": "📋 Backlog", "order": 1, "color": "#94a3b8"},
            {"id": "implementing", "name": "🔨 Implementing", "order": 2, "color": "#f59e0b"},
            {"id": "implemented", "name": "✅ Implemented", "order": 3, "color": "#10b981"},
            {"id": "testing", "name": "🧪 Testing", "order": 4, "color": "#8b5cf6"},
            {"id": "done", "name": "🎉 Done", "order": 5, "color": "#22c55e"},
        ],
        "ticket_types": ["feature", "enhancement", "bug-fix"],
        "default_ticket_type": "feature",
        "initial_status": "backlog",
        "auto_assign": True,
        "require_comments_on_status_change": True,
        "allow_reopen": True,
        "track_time": True,
    },
)

# Launch template - simple form for feature requests
FEATURE_DEV_LAUNCH_TEMPLATE = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="feature_description",
            label="Feature Description",
            type="textarea",
            required=True,
            description="Describe the feature you want to add. Be specific about what it should do, expected behavior, and any requirements."
        ),
        LaunchParameter(
            name="target_area",
            label="Target Area (Optional)",
            type="text",
            required=False,
            default="",
            description="Which part of the codebase? (e.g., 'authentication', 'API', 'frontend', 'database')"
        ),
        LaunchParameter(
            name="additional_context",
            label="Additional Context (Optional)",
            type="textarea",
            required=False,
            default="",
            description="Any additional context, constraints, examples, or references that might help"
        ),
    ],
    phase_1_task_prompt="""Phase 1: Feature Analysis & Planning

**Feature Description:**
{feature_description}

**Target Area (if specified):** {target_area}

**Additional Context:**
{additional_context}

---

## Your Task

You are analyzing a feature request for an EXISTING codebase.

**CRITICAL: Break the feature into WORK ITEMS with proper planning!**

1. Understand the feature request thoroughly
2. Check for existing codebase memories (from index_repo workflow if run)
3. If no memories exist, do a quick codebase scan
4. **Break the feature into 2-5 logical work items** (backend, frontend, tests, etc.)
5. **Determine implementation order and blocking relationships**
6. **Create ONE ticket per work item** with `blocked_by_ticket_ids` for dependencies
7. **Create ONE Phase 2 task per ticket** (1:1 relationship!)
8. Save all discoveries to memory

**IMPORTANT:**
- DO NOT create one ticket for the entire feature!
- Backend work items typically have no blockers
- Frontend work items are typically blocked by backend
- Test work items are typically blocked by implementation
- Verify 1:1 ticket-to-task relationship before marking done

Example breakdown:
- Ticket 1: "Feature: [Name] - Backend API" (no blockers)
- Ticket 2: "Feature: [Name] - Frontend" (blocked by Ticket 1)
- Ticket 3: "Feature: [Name] - Tests" (blocked by Ticket 1, 2)
""",
)

# Export all
__all__ = [
    "FEATURE_DEV_PHASES",
    "FEATURE_DEV_CONFIG",
    "FEATURE_DEV_LAUNCH_TEMPLATE",
    "PHASE_1_FEATURE_ANALYSIS",
    "PHASE_2_DESIGN_AND_IMPLEMENTATION",
    "PHASE_3_VALIDATE_AND_INTEGRATE",
]
