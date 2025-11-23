"""
Documentation Generation Workflow - Python Phase Definitions

This workflow generates comprehensive documentation for existing codebases. It:
1. Discovers what needs to be documented (or focuses on specific areas if requested)
2. Generates documentation for each component/area in parallel

Works well after running index_repo to leverage existing codebase memories.

Usage:
    from example_workflows.documentation_generation.phases import (
        DOC_GEN_PHASES,
        DOC_GEN_CONFIG,
        DOC_GEN_LAUNCH_TEMPLATE,
    )

    doc_gen_definition = WorkflowDefinition(
        id="doc-gen",
        name="Documentation Generation",
        phases=DOC_GEN_PHASES,
        config=DOC_GEN_CONFIG,
        launch_template=DOC_GEN_LAUNCH_TEMPLATE,
    )

    sdk = HephaestusSDK(workflow_definitions=[doc_gen_definition])
"""

# Import phase definitions
from example_workflows.documentation_generation.phase_1_documentation_discovery import PHASE_1_DOCUMENTATION_DISCOVERY
from example_workflows.documentation_generation.phase_2_documentation_generation import PHASE_2_DOCUMENTATION_GENERATION

# Import SDK models
from src.sdk.models import WorkflowConfig, LaunchTemplate, LaunchParameter

# Export phase list
DOC_GEN_PHASES = [
    PHASE_1_DOCUMENTATION_DISCOVERY,
    PHASE_2_DOCUMENTATION_GENERATION,
]

# Workflow configuration
# Simple 3-column board for documentation progress
DOC_GEN_CONFIG = WorkflowConfig(
    has_result=False,  # No formal result submission - all tickets resolved = complete
    enable_tickets=True,
    board_config={
        "columns": [
            {"id": "to_document", "name": "📋 To Document", "order": 1, "color": "#94a3b8"},
            {"id": "documenting", "name": "✍️ Documenting", "order": 2, "color": "#f59e0b"},
            {"id": "done", "name": "✅ Done", "order": 3, "color": "#22c55e"},
        ],
        "ticket_types": ["documentation", "update", "new"],
        "default_ticket_type": "documentation",
        "initial_status": "to_document",
        "auto_assign": True,
        "require_comments_on_status_change": True,
        "allow_reopen": True,
        "track_time": True,
    },
)

# Launch template - documentation request form
DOC_GEN_LAUNCH_TEMPLATE = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="documentation_scope",
            label="What to Document",
            type="textarea",
            required=True,
            description="What should be documented? Examples: 'Everything - create full documentation suite', 'API endpoints only', 'The authentication system', 'Getting started guide'"
        ),
        LaunchParameter(
            name="target_audience",
            label="Target Audience",
            type="select",
            required=False,
            default="developers",
            options=["developers", "end-users", "administrators", "contributors", "all"],
            description="Who will read this documentation? This affects the technical depth and explanations."
        ),
    ],
    phase_1_task_prompt="""Phase 1: Documentation Discovery

**Documentation Scope:**
{documentation_scope}

**Target Audience:** {target_audience}

---

## Your Task

You are discovering what documentation to create for an existing codebase.

**CRITICAL: Follow the component-based approach!**

1. **Understand the documentation request**
   - "Everything" → Document all major components
   - Specific request → Focus only on that area

2. **Check for existing codebase memories**
   - If index_repo was run, use those memories!
   - Saves time and provides rich context

3. **Check the docs/ folder**
   - What documentation already exists?
   - What needs updating vs creating from scratch?

4. **Identify documentation areas** (for "everything" requests):
   - Overview/README
   - Getting Started
   - Architecture
   - API Reference (if applicable)
   - Configuration
   - Components Guide
   - Contributing

5. **Create ONE ticket per documentation area**
   - Use markdown in ticket descriptions
   - Include target file path (e.g., `docs/api-reference.md`)
   - Note if updating existing or creating new

6. **Create ONE Phase 2 task per ticket** (1:1 relationship!)
   - Each task includes "TICKET: [ticket_id]"
   - Phase 2 agents write the actual documentation

**IMPORTANT:**
- Group logically - don't create too many small tickets
- Check existing docs - UPDATE don't overwrite
- All docs go under docs/ folder
- Verify 1:1 ticket-to-task relationship before marking done
""",
)

# Export all
__all__ = [
    "DOC_GEN_PHASES",
    "DOC_GEN_CONFIG",
    "DOC_GEN_LAUNCH_TEMPLATE",
    "PHASE_1_DOCUMENTATION_DISCOVERY",
    "PHASE_2_DOCUMENTATION_GENERATION",
]
