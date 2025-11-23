# Bug Fix Workflow
#
# A 3-phase workflow for systematic bug fixing:
# 1. Reproduce & Analyze - Understand and reproduce the bug
# 2. Implement Fix - Create minimal fix with regression test
# 3. Verify & Document - Confirm fix works, write brief docs
#
# Usage:
#     from example_workflows.bug_fix.phases import (
#         BUG_FIX_PHASES,
#         BUG_FIX_WORKFLOW_CONFIG,
#         BUG_FIX_LAUNCH_TEMPLATE
#     )

from example_workflows.bug_fix.phases import (
    BUG_FIX_PHASES,
    BUG_FIX_WORKFLOW_CONFIG,
    BUG_FIX_LAUNCH_TEMPLATE,
)

__all__ = ['BUG_FIX_PHASES', 'BUG_FIX_WORKFLOW_CONFIG', 'BUG_FIX_LAUNCH_TEMPLATE']
