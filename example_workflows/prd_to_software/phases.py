"""
PRD to Software Builder Workflow - Python Phase Definitions (3-Phase Model)

This workflow takes a PRD (Product Requirements Document) and builds working software.
It's fully generic and works for any type of software project: web apps, CLIs, libraries,
microservices, mobile backends, etc.

The workflow consists of 3 consolidated phases:
1. Phase 1: Requirements Analysis (analyzes PRD, creates tickets with blocking relationships)
2. Phase 2: Plan & Implementation (designs AND implements each component in one agent)
3. Phase 3: Validate & Document (tests code, fixes small bugs, writes docs if tests pass)

The workflow is self-building: agents spawn tasks based on what they discover, creating
a dynamic tree of parallel work that converges on a complete, tested, documented system.

Usage:
    from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG, PRD_LAUNCH_TEMPLATE
    sdk = HephaestusSDK(
        phases=PRD_PHASES,
        workflow_config=PRD_WORKFLOW_CONFIG,
        ...
    )
"""

# Import phase definitions
from example_workflows.prd_to_software.phase_1_requirements_analysis import PHASE_1_REQUIREMENTS_ANALYSIS
from example_workflows.prd_to_software.phase_2_plan_and_implementation import PHASE_2_PLAN_AND_IMPLEMENTATION
from example_workflows.prd_to_software.phase_3_validate_and_document import PHASE_3_VALIDATE_AND_DOCUMENT

# Import workflow configuration
from example_workflows.prd_to_software.board_config import PRD_WORKFLOW_CONFIG

# Import launch template components
from src.sdk.models import LaunchTemplate, LaunchParameter

# Export phase list
PRD_PHASES = [
    PHASE_1_REQUIREMENTS_ANALYSIS,
    PHASE_2_PLAN_AND_IMPLEMENTATION,
    PHASE_3_VALIDATE_AND_DOCUMENT,
]

# Launch Template - defines the form users fill out to start this workflow
PRD_LAUNCH_TEMPLATE = LaunchTemplate(
    parameters=[
        LaunchParameter(
            name="project_name",
            label="Project Name",
            type="text",
            required=True,
            description="Name of the project you're building (e.g., 'Personal Task Manager')"
        ),
        LaunchParameter(
            name="project_type",
            label="Project Type",
            type="dropdown",
            required=True,
            options=["Web Application", "CLI Tool", "Library/SDK", "API/Microservice", "Mobile Backend", "Other"],
            description="What type of software are you building?"
        ),
        LaunchParameter(
            name="prd_content",
            label="PRD Content",
            type="textarea",
            required=True,
            description="Paste the full Product Requirements Document here"
        ),
        LaunchParameter(
            name="tech_preferences",
            label="Technology Preferences",
            type="text",
            required=False,
            description="Optional: Preferred tech stack (e.g., 'FastAPI, React, SQLite')"
        ),
        LaunchParameter(
            name="additional_context",
            label="Additional Context",
            type="textarea",
            required=False,
            description="Optional: Any additional context or constraints for the project"
        ),
    ],
    phase_1_task_prompt="""Phase 1: Requirements Analysis - {project_name}

**Project Type:** {project_type}
**Technology Preferences:** {tech_preferences}

**Additional Context:**
{additional_context}

---

## Product Requirements Document

{prd_content}

---

## Your Task

You are analyzing the PRD above for "{project_name}".

1. Carefully read and understand all requirements in the PRD
2. Identify ALL major components/modules needed to build this system
3. Create a Kanban ticket for EACH component using create_ticket()
   - Set proper blocking relationships (e.g., database blocks API, API blocks frontend)
   - Include clear acceptance criteria in each ticket
4. Create Phase 2 design & implementation tasks for each component using create_task()
   - Each Phase 2 task should reference its corresponding ticket
   - Include relevant PRD sections in the task description
5. Mark your task as done when all tickets and Phase 2 tasks are created

IMPORTANT: The PRD content above is the COMPLETE requirements document. Do not look for external files.
""",
)

# Export workflow configuration (already imported from board_config)
__all__ = ['PRD_PHASES', 'PRD_WORKFLOW_CONFIG', 'PRD_LAUNCH_TEMPLATE']
