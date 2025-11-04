"""
Bug Fixing Workflow - Phase Definitions

This file imports all phase definitions and workflow configuration for easy access.
Each phase is defined in its own file for better organization.

Usage:
    from example_workflows.swebench_solver.phases import SWEBENCH_PHASES, SWEBENCH_WORKFLOW_CONFIG
    sdk = HephaestusSDK(
        phases=SWEBENCH_PHASES,
        workflow_config=SWEBENCH_WORKFLOW_CONFIG,
        ...
    )
"""

from example_workflows.swebench_solver.phase_1_issue_analysis_and_reproduction import (
    PHASE_1_ISSUE_ANALYSIS_AND_REPRODUCTION,
)
from example_workflows.swebench_solver.phase_2_exploration_and_implementation import (
    PHASE_2_EXPLORATION_AND_IMPLEMENTATION,
)
from example_workflows.swebench_solver.phase_3_testing_and_verification import (
    PHASE_3_TESTING_AND_VERIFICATION,
)
from example_workflows.swebench_solver.board_config import SWEBENCH_WORKFLOW_CONFIG

# Export all phases in order
SWEBENCH_PHASES = [
    PHASE_1_ISSUE_ANALYSIS_AND_REPRODUCTION,
    PHASE_2_EXPLORATION_AND_IMPLEMENTATION,
    PHASE_3_TESTING_AND_VERIFICATION,
]

# Export workflow config (includes ticket tracking board configuration)
__all__ = ["SWEBENCH_PHASES", "SWEBENCH_WORKFLOW_CONFIG"]
