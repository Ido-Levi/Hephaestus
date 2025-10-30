"""
SWEBench Solver Workflow - Python Phase Definitions

This file defines the phases for the SWEBench solver workflow as Python objects.
These can be loaded directly by the SDK without needing YAML files.

Usage:
    from example_workflows.swebench_solver.phases import SWEBENCH_PHASES, SWEBENCH_WORKFLOW_CONFIG
    sdk = HephaestusSDK(
        phases=SWEBENCH_PHASES,
        workflow_config=SWEBENCH_WORKFLOW_CONFIG,
        ...
    )
"""

from src.sdk.models import Phase, WorkflowConfig

# Phase definitions matching the YAML files exactly
SWEBENCH_PHASES = [
    Phase(
        id=1,
        name="issue_analysis_and_reproduction",
        description="""[This is Phase 1 - Created by Phase 0 initialization]
FOCUS: Reproduce the issue and create MULTIPLE Phase 2 exploration tasks.
Read PROBLEM_STATEMENT.md, reproduce the issue with clear steps, create reproduction
scripts, and spawn MULTIPLE Phase 2 tasks to explore different solution approaches.
DO NOT implement solutions - only reproduce and document the issue clearly.""",
        done_definitions=[
            "Problem statement from PROBLEM_STATEMENT.md has been thoroughly analyzed",
            "Issue has been successfully reproduced with clear, repeatable steps",
            "reproduction.md file created with exact commands to reproduce the issue",
            "Custom reproduction scripts created if needed (e.g., test_reproduction.py)",
            "Test commands documented and verified to show the issue",
            "CRITICAL: At least 2-3 Phase 2 tasks created to explore different solution approaches",
            "Each Phase 2 task explores a different potential fix location or approach",
        ],
        working_directory="/Users/idol/SWEBench_Hep_Problems/sphinx-doc__sphinx-7757/sphinx",
        additional_notes="""🚨 CRITICAL: YOUR MAIN GOAL IS REPRODUCTION + CREATING MULTIPLE P2 TASKS! 🚨

MANDATORY TASK CREATION:
═══════════════════════════════════════════════════════════════════════
You MUST create AT LEAST 2-3 Phase 2 tasks to explore different solutions:

Examples:
- "Phase 2: Explore fixing issue in [module A] by modifying [function X]"
- "Phase 2: Investigate alternative approach via [module B]"
- "Phase 2: Try fixing by adjusting [specific logic] in [file Y]"

Each with phase_id=2 and different exploration angles!
═══════════════════════════════════════════════════════════════════════

YOUR WORKFLOW:
1. Read PROBLEM_STATEMENT.md carefully
2. Reproduce the issue with minimal test case
3. Create reproduction.md with EXACT commands:
   ```bash
   cd /path/to/repo
   python test_script.py  # Shows the error
   ```
4. Write custom scripts if needed (test_reproduction.py)
5. Identify 2-3 DIFFERENT potential fix locations/approaches
6. Create a Phase 2 task for EACH approach

DO NOT:
- Write implementation guides (that's Phase 2's job)
- Try to fix the issue (Phase 3 does that)
- Create only one Phase 2 task (MUST be multiple!)

Start by carefully reading PROBLEM_STATEMENT.md. Extract:
1. What is broken or needs to be added
2. Expected behavior after the fix
3. Any specific test cases mentioned
4. Edge cases or special conditions
5. Related files or modules mentioned

For bugs, create a minimal reproduction script that demonstrates the issue.
This will be crucial for verifying your fix later.

Use save_memory to document:
- Key requirements from the issue
- Reproduction steps and results
- Initial hypotheses about the cause
- Test commands and their current output

Document everything in an issue_analysis.md file that will guide the next phases.""",
        outputs=[
            "- reproduction.md containing:",
            "  * Clear, step-by-step commands to reproduce the issue",
            "  * Expected vs actual behavior",
            "  * Exact error messages or incorrect outputs",
            "  * Test commands that demonstrate the problem",
            "- Custom reproduction scripts (e.g., test_reproduction.py) if needed",
            "- Multiple Phase 2 tasks exploring different solution approaches",
        ],
        next_steps=[
            "Create AT LEAST 2-3 Phase 2 tasks, each exploring a different potential solution.",
            "Pass along the reproduction.md file path to each task. Phase 2 tasks will each",
            "write their own implementation.md with their proposed solution approach.",
        ],
    ),
    Phase(
        id=2,
        name="codebase_investigation",
        description="""FOCUS: Explore ONE specific solution approach and write implementation.md.
Each Phase 2 task explores a DIFFERENT potential fix. Your job is to investigate
your assigned approach, find the exact code locations, and write a detailed
implementation.md file explaining EXACTLY how to fix the issue with your approach.""",
        done_definitions=[
            "Investigated the specific approach assigned in your task description",
            "Exact files and functions for YOUR approach identified",
            "implementation.md file created with step-by-step fix instructions",
            "Code snippets showing exactly what to change included",
            "Risks and dependencies for your approach documented",
            "A Phase 3 task created referencing your implementation.md",
        ],
        working_directory="/Users/idol/SWEBench_Hep_Problems/sphinx-doc__sphinx-7757/sphinx",
        additional_notes="""🎯 YOUR MISSION: Write implementation.md for YOUR specific approach!

CRITICAL: CREATE implementation.md FILE:
═══════════════════════════════════════════════════════════════════════
You MUST create an implementation.md file with:

1. **Approach**: Description of your specific solution approach
2. **Files to Modify**: List exact files and line numbers
3. **Changes Required**:
   ```python
   # Current code (line X-Y in file.py):
   def current_function():
       ...

   # Change to:
   def fixed_function():
       ...
   ```
4. **Why This Works**: Explanation of why your approach fixes the issue
5. **Risks**: Any potential side effects or concerns

THEN create ONE Phase 3 task:
"Phase 3: Implement fix using approach from implementation.md"
Include phase_id=3 and reference the implementation.md path!
═══════════════════════════════════════════════════════════════════════

Investigation Strategy:
1. Start from the reproduction case or test that demonstrates the issue
2. Trace through the code execution path
3. Find the exact functions/methods that need modification
4. Understand how similar issues are handled elsewhere
5. Check for existing tests that cover this area

Use various search strategies:
- grep/rg for error messages, function names, class names
- Look for test files related to the issue
- Check imports to understand dependencies
- Read docstrings and comments for context

IMPORTANT: Don't just find the general area - locate the EXACT lines of code
that need to be changed. Your implementation plan should be specific enough
that Phase 3 can execute it without additional searching.

Use save_memory to document:
- Exact file paths and line numbers
- Current implementation logic
- Why the current code is wrong/incomplete
- How to fix it following project patterns""",
        outputs=[
            "- implementation.md containing:",
            "  * Your specific approach description",
            "  * Exact files and line numbers to modify",
            "  * Before/after code snippets showing the changes",
            "  * Clear explanation of why this approach works",
            "  * Any risks or side effects identified",
            "- A single Phase 3 task to implement YOUR approach",
        ],
        next_steps=[
            "Create ONE Phase 3 task that will implement the solution from your implementation.md.",
            "The Phase 3 agent will follow your implementation.md exactly. If the implementation",
            "doesn't work, Phase 3 will create a new Phase 2 task to explore a different approach.",
        ],
    ),
    Phase(
        id=3,
        name="solution_implementation",
        description="""FOCUS: Implement the solution from implementation.md and test if it works.
Read the implementation.md file from Phase 2, follow the instructions exactly,
make the code changes, and test if they fix the issue. If not working, create
a new Phase 2 task to explore a different approach.""",
        done_definitions=[
            "implementation.md has been read and understood",
            "Code changes from implementation.md have been applied exactly",
            "Reproduction test has been run to check if issue is fixed",
            "If fix works: Phase 4 task created for comprehensive testing",
            "If fix doesn't work: New Phase 2 task created with different approach",
            "No unrelated changes made to the codebase",
        ],
        working_directory="/Users/idol/SWEBench_Hep_Problems/sphinx-doc__sphinx-7757/sphinx",
        additional_notes="""📋 FOLLOW implementation.md EXACTLY!

YOUR WORKFLOW:
═══════════════════════════════════════════════════════════════════════
1. READ implementation.md from your task description
2. APPLY the changes EXACTLY as specified
3. RUN the reproduction test from reproduction.md
4. CHECK if the issue is fixed:

IF FIXED ✅:
  - Create Phase 4 task: "Phase 4: Comprehensive testing of fix"
  - Include phase_id=4 and list of modified files

IF NOT FIXED ❌:
  - Create NEW Phase 2 task: "Phase 2: Explore alternative fix approach"
  - Include phase_id=2
  - Describe why current approach didn't work
  - Suggest different area to investigate

IMPORTANT:
- Do NOT try to debug or modify the approach yourself
- If it doesn't work, let Phase 2 explore a new approach
- Only make changes specified in implementation.md
═══════════════════════════════════════════════════════════════════════

Implementation Guidelines:

1. MINIMAL CHANGES ONLY:
   - Change only what's necessary to fix the issue
   - Don't refactor unrelated code
   - Don't update comments unless directly relevant
   - Don't change formatting of unmodified lines

2. FOLLOW PROJECT PATTERNS:
   - Match the existing code style exactly
   - Use the same naming conventions
   - Follow established error handling patterns
   - Maintain consistency with surrounding code

3. HANDLE EDGE CASES:
   - Address all cases mentioned in the issue
   - Consider boundary conditions
   - Ensure robust error handling
   - Don't introduce new failure modes

4. TEST AS YOU GO:
   - After each change, verify it doesn't break syntax
   - Run the specific test or reproduction case
   - Ensure the basic fix works before proceeding

5. DOCUMENT YOUR CHANGES:
   - Keep track of every file you modify
   - Note what each change does
   - Save memories about implementation decisions

IMPORTANT: Resist the urge to "improve" code beyond the issue requirements.
Your goal is a minimal, focused patch that solves exactly the stated problem.""",
        outputs=[
            "- Modified source files with the implementation from implementation.md",
            "- Test results showing if the fix works",
            "- EITHER:",
            "  * Phase 4 task if fix works",
            "  * New Phase 2 task if fix doesn't work",
        ],
        next_steps=[
            "- If fix works: Create Phase 4 task for comprehensive testing",
            "- If fix doesn't work: Create Phase 2 task to explore different approach",
            "- The description should reference which implementation.md was tried",
        ],
    ),
    Phase(
        id=4,
        name="testing_and_verification",
        description="""Comprehensive testing and verification of the implemented solution. This phase runs
all tests, verifies the fix works correctly, ensures no regression, generates the
patch, and prepares the final submission. This is the final quality gate before
submitting the solution.""",
        done_definitions=[
            "Full test suite has been run and ALL tests pass",
            "Original issue/bug is verified as fixed",
            "No regression in existing functionality",
            "Git patch generated and validated",
            "All issue requirements confirmed as met",
            "CRITICAL: If solution works, submit_result has been called with comprehensive evidence",
        ],
        working_directory="/Users/idol/SWEBench_Hep_Problems/sphinx-doc__sphinx-7757/sphinx",
        additional_notes="""🚨 TWO CRITICAL PATHS: SUCCESS → SUBMIT | FAILURE → NEW TASKS! 🚨

PATH 1 - SUCCESS (All tests pass):
═══════════════════════════════════════════════════════════════════════
USE submit_result with markdown containing:
1. Problem Summary
2. Solution Overview
3. Test Results (FULL output)
4. Git Patch (MANDATORY!)

PATH 2 - FAILURE (Tests fail or issue not fixed):
═══════════════════════════════════════════════════════════════════════
CREATE NEW EXPLORATION TASKS:

- Still not working? → Create NEW Phase 1 task:
  "Phase 1: Re-analyze issue with focus on [new area]" (phase_id=1)

- Need different approach? → Create NEW Phase 2 tasks:
  "Phase 2: Explore fixing via [different module]" (phase_id=2)
  "Phase 2: Try alternative approach using [different strategy]" (phase_id=2)

- Create MULTIPLE new directions to explore!

TESTING STEPS:
1. Run FULL test suite
2. Verify reproduction case is fixed
3. Check for regressions
4. If ALL pass → submit_result
5. If ANY fail → create new P1/P2 tasks for different approaches

IMPORTANT: Don't get stuck on one approach. If it's not working,
spawn new exploration tasks to try completely different solutions!""",
        outputs=[
            "- Complete test suite output showing all tests passing",
            "- Evidence of the specific issue being fixed",
            "- Generated git patch file (solution.patch)",
            "- solution_submission.md with comprehensive documentation",
            "- CRITICAL: submit_result call if solution is valid",
        ],
        next_steps=[
            "- If ALL tests pass and issue is fixed: submit_result immediately!",
            "- If tests fail: Create Phase 3 task to fix the implementation",
            "- If issue not fully fixed: Create appropriate phase task to address",
            "- Never leave a working solution unsubmitted!",
        ],
    ),
]

# Workflow configuration for result handling
SWEBENCH_WORKFLOW_CONFIG = WorkflowConfig(
    has_result=True,
    result_criteria="""VALIDATION REQUIREMENTS FOR SWEBENCH SOLUTION ACCEPTANCE:

════════════════════════════════════════════════════════════════════
CRITICAL: A SOLUTION IS ONLY VALID IF ALL REQUIREMENTS ARE MET
════════════════════════════════════════════════════════════════════

1. **ISSUE REQUIREMENTS VERIFICATION** (MANDATORY)
   ✓ Every requirement from the problem statement is addressed
   ✓ Expected behavior exactly matches issue description
   ✓ All edge cases mentioned in the issue are handled correctly
   ✓ No unintended side effects introduced

2. **TEST SUITE VALIDATION** (MANDATORY)
   ✓ Full test suite runs successfully (provide complete output)
   ✓ ALL existing tests pass - NO REGRESSION allowed
   ✓ Tests specific to the issue pass (if they exist)
   ✓ Any new tests added for the fix also pass
   ✓ Include the exact test commands and their full output

3. **REPRODUCTION EVIDENCE** (MANDATORY)
   ✓ Original failing case now works correctly
   ✓ Before/after behavior clearly demonstrated
   ✓ Console output, error messages, or results showing the fix
   ✓ Step-by-step reproduction instructions included

4. **CODE QUALITY VERIFICATION** (MANDATORY)
   ✓ Changes follow project's coding conventions
   ✓ No linting errors or warnings introduced
   ✓ No type checking errors (if applicable)
   ✓ Code is clean, readable, and maintainable
   ✓ Only necessary changes included (no extra modifications)

5. **PATCH VALIDATION** (MANDATORY)
   ✓ Complete git patch included in submission
   ✓ Patch applies cleanly to the base commit
   ✓ Patch contains ONLY the necessary changes
   ✓ Patch format is correct and can be applied with git apply

════════════════════════════════════════════════════════════════════
REQUIRED SUBMISSION FORMAT:
════════════════════════════════════════════════════════════════════

The submission markdown file MUST include these sections:

## 1. Problem Summary
- Brief description of the issue
- Key requirements addressed

## 2. Solution Overview
- What was changed and why
- Files modified with brief explanations

## 3. Test Results
```
[FULL test suite output showing all tests passing]
```

## 4. Reproduction Evidence
- Before: [Show the failing case]
- After: [Show the working case]
- Include exact commands and outputs

## 5. Code Quality Checks
- Linting results (if applicable)
- Type checking results (if applicable)

## 6. Git Patch
```patch
[COMPLETE git diff patch that can be applied with git apply]
```

════════════════════════════════════════════════════════════════════
VALIDATION DECISION CRITERIA:
════════════════════════════════════════════════════════════════════

✅ APPROVE if and only if:
   - ALL mandatory requirements are met
   - Test suite fully passes with no regression
   - Patch is clean and minimal
   - Evidence clearly demonstrates the fix works

❌ REJECT if:
   - Any test fails or shows regression
   - Requirements not fully addressed
   - Patch includes unnecessary changes
   - Missing evidence of fix working
   - Code quality issues present

When validating:
1. First verify the patch applies cleanly
2. Check that all tests pass (no "trust" - verify the output)
3. Confirm the specific issue is fixed
4. Ensure no extra changes snuck in
5. Validate code quality and style

REMEMBER: The goal is a production-ready patch that solves the exact
issue described without breaking anything else. Be thorough and strict.""",
    on_result_found="stop_all",
)
