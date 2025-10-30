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
    from example_workflows.prd_to_software.phases import PRD_PHASES, PRD_WORKFLOW_CONFIG
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

# Export phase list
PRD_PHASES = [
    PHASE_1_REQUIREMENTS_ANALYSIS,
    PHASE_2_PLAN_AND_IMPLEMENTATION,
    PHASE_3_VALIDATE_AND_DOCUMENT,
]

# Export workflow configuration (already imported from board_config)
__all__ = ['PRD_PHASES', 'PRD_WORKFLOW_CONFIG']
