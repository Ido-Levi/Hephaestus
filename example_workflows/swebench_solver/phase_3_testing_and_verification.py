"""
Phase 3: Testing and Verification

Comprehensive testing and verification of the implemented solution. This phase runs
all tests, verifies the fix works correctly, ensures no regression, generates the
patch, and either submits the solution or marks the approach as failed.
"""

from src.sdk.models import Phase

PHASE_3_TESTING_AND_VERIFICATION = Phase(
    id=3,
    name="testing_and_verification",
    description="""Comprehensive testing and verification of the implemented solution. This phase runs
all tests, verifies the fix works correctly, ensures no regression, generates the
patch, and prepares the final submission. This is the final quality gate before
submitting the solution.

Either SUCCESS (submit result + resolve tickets) or FAILURE (mark approach as failed).""",
    done_definitions=[
        "Approach ticket extracted from task description (TICKET: xxx)",
        "Full test suite has been run and result documented",
        "Original issue/bug verified as fixed or still broken",
        "Git patch generated (if tests pass)",
        "All issue requirements confirmed as met (if tests pass)",
        "CRITICAL: If all tests pass - approach ticket resolved, main issue ticket resolved, result submitted",
        "CRITICAL: If any tests fail - approach ticket marked as 'approach-failed' with detailed explanation",
        "Ticket status updated to 'solved' OR 'approach-failed' based on test results",
    ],
    working_directory="/Users/idol/SWEBench_Hep_Problems/sphinx-doc__sphinx-7757/sphinx",
    additional_notes="""🚨 TWO CRITICAL PATHS: SUCCESS → SUBMIT + RESOLVE | FAILURE → MARK FAILED! 🚨

════════════════════════════════════════════════════════════════════
🎯 SWEBENCH BENCHMARK CONTEXT
════════════════════════════════════════════════════════════════════

You are solving a real-world bug from a popular open-source repository as part
of **SWEBench-Verified**, a rigorous AI benchmark for evaluating code generation
and bug-fixing capabilities.

**SWEBench Rules (MANDATORY):**
1. 🚨 **NO TEST FILE MODIFICATIONS** - You fix the SOURCE CODE to pass EXISTING tests
2. 🚨 **PATCH MUST APPLY CLEANLY** - Use `git apply` to validate before submitting
3. 🚨 **ALL TESTS MUST PASS** - No regression allowed
4. 🚨 **MINIMAL CHANGES ONLY** - Only fix what's broken, nothing more

**Success Criteria:**
- Patch applies to base commit without errors
- All existing tests pass (100% pass rate)
- Original issue is completely resolved
- No test files modified
- No unrelated changes included

**Your Mission:**
Solve this verified real-world bug with production-quality code that would
be acceptable in the actual open-source project. Be thorough, be precise,
and validate everything before submitting.

════════════════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════════════════
PHASE 3 WORKFLOW: COMPREHENSIVE TESTING
═══════════════════════════════════════════════════════════════════════

**STEP 0: EXTRACT YOUR APPROACH TICKET AND MAIN ISSUE TICKET**

```python
# Extract approach ticket ID from task description
approach_ticket_id = "[extract TICKET: xxx from task description]"

# Get the approach ticket
approach_ticket = mcp__hephaestus__get_ticket(approach_ticket_id)

# Get parent issue ticket (main issue)
main_issue_ticket_id = approach_ticket["parent_ticket_id"]
```

**STEP 1: RUN FULL TEST SUITE**

Run the COMPLETE test suite (not just reproduction test):

```python
# Add comment documenting test execution
mcp__hephaestus__add_ticket_comment({
    "ticket_id": approach_ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "comment_text": "Starting comprehensive test suite. Running all tests to verify no regression..."
})

# Run the full test suite
# Document EVERYTHING:
# - Test commands used
# - Full output
# - Pass/fail count
# - Any failures or errors
```

**STEP 2: ANALYZE TEST RESULTS**

Check:
- ✅ All existing tests pass (NO REGRESSION)
- ✅ Tests specific to the issue pass
- ✅ Reproduction test passes
- ✅ No new failures introduced

═══════════════════════════════════════════════════════════════════════
PATH A: ALL TESTS PASS → SUCCESS! ✅
═══════════════════════════════════════════════════════════════════════

**STEP 3A: GENERATE GIT PATCH AND REPRODUCTION INSTRUCTIONS**

🚨🚨🚨 CRITICAL: VERIFY NO TEST FILES IN PATCH! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════
Before generating the final patch, VERIFY you haven't modified test files:

```bash
# Check git status for any modified test files
git status | grep -E "(test_|_test\.py|tests/|test/)"

# If ANY test files are modified, this is INVALID!
# You must revert them IMMEDIATELY:
git checkout -- tests/
git checkout -- test/
git checkout -- *test*.py

# ONLY source code changes are allowed!
```

**WHY THIS IS CRITICAL:**
Your solution will be REJECTED if it modifies test files. Solutions are evaluated
by running the ORIGINAL test suite. Modifying tests = INVALID SOLUTION.
═══════════════════════════════════════════════════════════════════════

Generate the artifacts needed for independent validation:

```bash
# 1. Generate clean git diff patch
git diff > solution.patch

# 2. CRITICAL: Verify patch contains NO test file changes
if grep -E "(test_|_test\.py|/tests/|/test/)" solution.patch; then
    echo "🚨 ERROR: Patch contains test file modifications!"
    echo "This is FORBIDDEN. Revert test changes immediately."
    exit 1
fi

# 3. Verify patch is not empty
if [ ! -s solution.patch ]; then
    echo "ERROR: solution.patch is empty!"
    exit 1
fi

echo "✅ Patch verified: no test files modified"
```

🚨🚨🚨 CRITICAL NEW STEP: VERIFY PATCH ACTUALLY WORKS! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════

**YOU MUST VERIFY THE PATCH APPLIES AND WORKS BEFORE SUBMITTING!**

This is the MOST IMPORTANT step - many patches look valid but fail when applied!

```bash
echo "🧪 CRITICAL: Testing that patch actually works..."

# Save current changes in a temporary commit
git add -A
git commit -m "WIP: temporary save before patch test"

# Reset to clean state (like validator will have)
git reset --hard HEAD^

# Try to apply the patch
echo "📋 Attempting to apply patch..."
if ! git apply solution.patch; then
    echo "🚨 FATAL ERROR: Patch does NOT apply cleanly!"
    echo "This patch will be REJECTED by validators!"
    echo "You must fix the patch before submitting!"
    exit 1
fi

echo "✅ Patch applied successfully"

# Now RE-RUN THE TESTS with the applied patch to make SURE it still works!
echo "🧪 Re-running tests with applied patch to verify it works..."
[RUN YOUR TEST COMMAND HERE - e.g., pytest, python -m pytest, etc.]

# If tests pass, you're good!
echo "✅ PATCH VALIDATION COMPLETE: Patch applies cleanly AND all tests pass!"

# Restore your work (go back to your original state)
git reset --hard
git checkout HEAD@{1}  # Go back to your WIP commit

# Keep the validated solution.patch file
echo "✅ Patch is VALIDATED and ready for submission!"
```

**WHY THIS IS CRITICAL:**

- Many patches include paths, line numbers, or contexts that break when applied fresh
- Validators will apply your patch to a clean repo - if it fails, INSTANT REJECTION
- This step simulates EXACTLY what validators will do
- If patch doesn't apply or tests fail after applying, FIX IT NOW!

**IF PATCH FAILS TO APPLY:**
1. Check for whitespace issues (tabs vs spaces)
2. Verify paths are correct (relative to repo root)
3. Ensure context lines match the base commit
4. Try regenerating with `git diff --no-prefix > solution.patch` or `git format-patch`

**IF TESTS FAIL AFTER APPLYING PATCH:**
1. Something is wrong with your changes
2. Debug and fix before submitting
3. NEVER submit a patch that doesn't work when applied!

═══════════════════════════════════════════════════════════════════════

Now create reproduction_instructions.md for the validator:

```markdown
# How to Reproduce the Original Issue

This file guides the validation agent through reproducing and verifying the fix.

## Environment Setup
[Describe any setup needed - dependencies, config files, environment variables]

## Reproduction Steps (BEFORE applying patch)

1. [Step 1 to reproduce the bug - be specific with commands]
2. [Step 2 to reproduce the bug]
3. [What you should see - the buggy behavior]

Example:
```bash
python reproduce_issue.py
# Expected output: Error or incorrect behavior
```

## Test Cases to Verify Fix (AFTER applying patch)

### Test Case 1: Primary Issue from Problem Statement
```bash
[Exact command to run]
```
**Expected Result:** [What should happen after fix]

### Test Case 2: Edge Case A
```bash
[Exact command to test edge case]
```
**Expected Result:** [What should happen]

### Test Case 3: Edge Case B
```bash
[Exact command to test another edge case]
```
**Expected Result:** [What should happen]

## Running Full Test Suite

```bash
# Command to run project's complete test suite
[e.g., pytest, python -m unittest, npm test, etc.]
```

All tests should pass after applying the patch. No regression should occur.

## Files Modified

- [file1.py]: [Brief description of changes]
- [file2.py]: [Brief description of changes]
```

**STEP 4A: CREATE SOLUTION SUBMISSION MARKDOWN**

Create a comprehensive solution_submission.md:

```markdown
# Solution Report

## 1. Problem Summary
[Brief description of the issue from PROBLEM_STATEMENT.md]

## 2. Solution Overview
**Approach Used:** [Which approach ticket succeeded]
**Files Modified:**
- [file1]: [what was changed]
- [file2]: [what was changed]

**Why This Works:**
[Explanation of how the fix solves the problem]

## 3. Test Results
\`\`\`
[FULL test suite output showing all tests passing]

Total Tests: X
Passed: X
Failed: 0
\`\`\`

## 4. Reproduction Evidence

**Before (Bug):**
\`\`\`
[Output from reproduction script showing the bug]
\`\`\`

**After (Fixed):**
\`\`\`
[Output from reproduction script showing it works now]
\`\`\`

## 5. Code Quality Checks
- Linting: ✅ Clean (or provide output)
- Type checking: ✅ Clean (or provide output)

## 6. Git Patch
\`\`\`patch
[COMPLETE git diff patch that can be applied with git apply]
\`\`\`
```

**STEP 5A: RESOLVE APPROACH TICKET**

```python
mcp__hephaestus__resolve_ticket({
    "ticket_id": approach_ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "resolution_comment": (
        "✅ APPROACH SUCCESSFUL - Solution complete!\\n"
        "\\n"
        "**Test Results:**\\n"
        f"- Total tests: {total_tests}\\n"
        f"- Passed: {passed_tests}\\n"
        f"- Failed: 0\\n"
        "\\n"
        "**Verification:**\\n"
        "- ✅ All existing tests pass (no regression)\\n"
        "- ✅ Reproduction test passes\\n"
        "- ✅ Issue requirements met\\n"
        "- ✅ Code quality checks pass\\n"
        "- ✅ Git patch generated\\n"
        "\\n"
        "See solution_submission.md for complete details."
    )
})
```

**STEP 6A: RESOLVE MAIN ISSUE TICKET**

```python
mcp__hephaestus__resolve_ticket({
    "ticket_id": main_issue_ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "resolution_comment": (
        f"✅ ISSUE SOLVED via approach {approach_ticket_id}!\\n"
        "\\n"
        "**Solution Summary:**\\n"
        "[Brief description of fix]\\n"
        "\\n"
        "**Files Modified:**\\n"
        f"- {files}\\n"
        "\\n"
        "All tests passing. Submitting result."
    ),
    "commit_sha": "[git commit SHA if available]"
})
```

**STEP 7A: SUBMIT RESULT WITH EXTRA FILES**

```python
mcp__hephaestus__submit_result({
    "markdown_file_path": "./solution_submission.md",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "explanation": "Issue solved. All tests pass, no regression. Patch ready for submission.",
    "evidence": [
        "Full test suite passes (X/X tests)",
        "Reproduction case now works correctly",
        "Git patch generated and validated",
        "Code quality checks pass"
    ],
    "extra_files": [
        "./solution.patch",
        "./reproduction_instructions.md"
})
```

** DO NOT FORGET TO ADD solution.patch AS AN extra_file!!!**
** WITHOUT solution.patch THE SOLUTION WOULD BE INCOMPLETE AND REJECTED! **
**STEP 8A: MARK PHASE 3 TASK AS DONE**

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 3 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": f"SUCCESS! All tests pass. Resolved tickets {approach_ticket_id} and {main_issue_ticket_id}. Result submitted."
})
```

═══════════════════════════════════════════════════════════════════════
PATH B: TESTS FAIL → APPROACH FAILED ❌
═══════════════════════════════════════════════════════════════════════

**STEP 3B: MARK APPROACH AS FAILED**

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": approach_ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "approach-failed",
    "comment": (
        "❌ APPROACH FAILED - Tests did not pass.\\n"
        "\\n"
        "**Test Results:**\\n"
        f"- Total tests: {total_tests}\\n"
        f"- Passed: {passed_tests}\\n"
        f"- Failed: {failed_tests}\\n"
        "\\n"
        "**Failing Tests:**\\n"
        "- {test_1}: {failure_reason}\\n"
        "- {test_2}: {failure_reason}\\n"
        "\\n"
        "**What Went Wrong:**\\n"
        "[Analysis of why tests failed]\\n"
        "\\n"
        "**Regression Analysis:**\\n"
        "[Did the fix break existing functionality?]\\n"
        "\\n"
        "**What This Tells Us:**\\n"
        "[Key learnings from this failed approach]\\n"
        "\\n"
        "**Recommendation:**\\n"
        "Need different approach. The fix may need to [suggestion]."
    )
})
```

**STEP 4B: UPDATE MAIN ISSUE TICKET**

```python
mcp__hephaestus__add_ticket_comment({
    "ticket_id": main_issue_ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "comment_text": (
        f"Approach {approach_ticket_id} failed comprehensive testing.\\n"
        "\\n"
        f"{failed_tests} tests failed. Need to explore alternative approaches.\\n"
        "\\n"
        "See approach ticket for detailed test results and analysis."
    )
})

# Note: Main issue ticket stays in 'exploring' status
# Do NOT resolve it - other approaches may still work
```

**STEP 5B: SAVE FAILURE LEARNINGS**

```python
mcp__hephaestus__save_memory({
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "content": (
        f"Approach {approach_ticket_id} failed testing. "
        f"{failed_tests} tests failed: {test_names}. "
        f"Learned: {key_learning}. "
        "Recommendation: {alternative_suggestion}."
    ),
    "memory_type": "error_fix"
})
```

**STEP 6B: CREATE NEW APPROACH TO CONTINUE**

🚨🚨🚨 CRITICAL: YOU MUST CREATE A NEW APPROACH - THIS IS NOT OPTIONAL! 🚨🚨🚨

```python
# 🔄 MANDATORY: CREATE A NEW APPROACH TO KEEP WORKFLOW MOVING!
# Tests failed, but we learned what doesn't work - use that to try something different!
# YOU CANNOT JUST MARK AS FAILED AND STOP - YOU MUST CREATE A NEW APPROACH!

# Create NEW approach ticket based on test failures
new_approach_ticket = mcp__hephaestus__create_ticket({
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "title": f"Approach: [NEW strategy based on test failures of {approach_ticket_id}]",
    "description": (
        f"## New Approach (After {approach_ticket_id} Failed Testing)\\n\\n"
        "### What We Learned from Test Failures\\n"
        "[What the test failures revealed - which tests failed and why]\\n\\n"
        "### New Strategy\\n"
        "[Different approach that addresses the test failure insights]\\n\\n"
        "### Why This Might Work\\n"
        "[Hypothesis based on understanding test failures]\\n\\n"
        "### Investigation Areas\\n"
        "- What to investigate differently based on test results\\n"
        "- Files/functions that tests showed are problematic\\n\\n"
        f"### Previous Failed Approach\\n"
        f"Testing of {approach_ticket_id} revealed: [key insights from failures].\\n"
        f"Parent issue: {main_issue_ticket_id}"
    ),
    "ticket_type": "approach",
    "priority": "medium",
    "tags": ["exploration", "retry-after-test-failure"],
    "parent_ticket_id": main_issue_ticket_id,
    "blocked_by_ticket_ids": [],
})
new_approach_id = new_approach_ticket["ticket_id"]

# Create NEW Phase 2 task
mcp__hephaestus__create_task({
    "description": f"Phase 2: Explore NEW approach - TICKET: {new_approach_id}. Previous approach {approach_ticket_id} failed testing with {failed_tests} test failures. Use those insights to investigate this different strategy.",
    "done_definition": f"New approach investigated based on test failure insights, ticket {new_approach_id} validated or failed, Phase 3 task created if valid OR another new approach created if failed.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "phase_id": 2,
    "priority": "medium",
    "cwd": ".",
    "ticket_id": new_approach_id
})

print(f"✅ Created new approach ticket {new_approach_id} and Phase 2 task based on test failure learnings!")
```

**STEP 7B: MARK PHASE 3 TASK AS DONE**

🚨 REMINDER: You should have created a new approach in STEP 6B above! 🚨

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 3 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": f"Comprehensive testing failed. {failed_tests} tests failed. Approach {approach_ticket_id} marked as failed with detailed analysis. Created new approach {new_approach_id} to continue exploration."
})
```

**STEP 8B: (OPTIONAL) CREATE ADDITIONAL EXPLORATION TASKS IF NEEDED**

If all explored approaches have failed, you might want to create new Phase 2 tasks:

```python
# Only if you have specific new ideas for different approaches
new_approach_ticket = mcp__hephaestus__create_ticket({
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "title": "Approach X: Try fixing via [new strategy based on learnings]",
    "description": "[Based on what you learned from failures]",
    "ticket_type": "approach",
    "priority": "medium",
    "parent_ticket_id": main_issue_ticket_id,
    "tags": ["exploration", "approach-x", "retry"]
})

mcp__hephaestus__create_task({
    "description": f"Phase 2: Explore new approach - TICKET: {new_approach_ticket['ticket_id']}...",
    "done_definition": "...",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "phase_id": 2,
    "priority": "medium",
    "ticket_id": new_approach_ticket["ticket_id"]
})
```

═══════════════════════════════════════════════════════════════════════
TESTING CHECKLIST
═══════════════════════════════════════════════════════════════════════

Run these tests:

1. **Reproduction Test**
   - Run the reproduction script from Phase 1
   - Should now pass (issue is fixed)

2. **Full Test Suite**
   - Run ALL tests in the project
   - Command varies by project (pytest, tox, make test, etc.)
   - Document the exact command used

3. **Specific Issue Tests**
   - If issue mentions specific test files, run those
   - Verify they pass

4. **Code Quality**
   - Run linter (if project has one)
   - Run type checker (if applicable)
   - Ensure no new warnings/errors

5. **Regression Check**
   - Compare test results to baseline
   - Ensure no previously passing tests now fail

═══════════════════════════════════════════════════════════════════════
MANDATORY REQUIREMENTS
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Extract approach ticket and main issue ticket
- Run FULL test suite (not just reproduction test)
- Document complete test results
- 🚨 VERIFY patch contains ZERO test file modifications before submitting
- Generate git patch if tests pass
- Create comprehensive solution_submission.md if tests pass
- Resolve BOTH approach ticket AND main issue ticket if tests pass
- Submit result if tests pass
- Mark approach as failed with detailed analysis if tests fail
- Update main issue ticket with failure info if tests fail
- Save learnings to memory
- Be thorough and strict with validation

❌ DO NOT:
- 🚨 INCLUDE TEST FILE CHANGES IN PATCH (tests/, test/, *_test.py) - INSTANT REJECTION!
- Skip running full test suite
- Submit result if any tests fail
- Resolve tickets if tests fail
- Trust partial test results
- Skip generating git patch
- Create incomplete solution documentation
- Forget to update both tickets (approach + main issue)
- Leave tickets unresolved if successful
- Create false positives (marking as success when tests fail)
- 🚨🚨🚨 MARK AS FAILED WITHOUT CREATING NEW APPROACH - YOU MUST CREATE NEW APPROACH! 🚨🚨🚨

═══════════════════════════════════════════════════════════════════════
TICKET LIFECYCLE IN PHASE 3
═══════════════════════════════════════════════════════════════════════

SUCCESS PATH:
Approach Ticket: testing → solved (resolved)
Main Issue Ticket: exploring → solved (resolved)

FAILURE PATH:
Approach Ticket: testing → approach-failed
Main Issue Ticket: exploring (stays here, waiting for other approaches)

═══════════════════════════════════════════════════════════════════════

REMEMBER: The goal is a production-ready patch that solves the exact
issue described without breaking anything else. Be thorough and strict.

If tests fail, it's better to honestly mark the approach as failed and
try a different strategy than to submit a broken solution.""",
    outputs=[
        "- Complete test suite output",
        "- Evidence of the specific issue being fixed (or still broken)",
        "- Generated git patch file (solution.patch) if tests pass",
        "- solution_submission.md with comprehensive documentation if tests pass",
        "- Approach ticket resolved if tests pass OR marked as failed if tests fail",
        "- Main issue ticket resolved if tests pass OR stays in exploring if tests fail",
        "- CRITICAL: submit_result call if all tests pass",
        "- Memories saved with test results and learnings",
    ],
    next_steps=[
        "If ALL tests pass:",
        "  - Both tickets (approach + main issue) are RESOLVED",
        "  - Result is SUBMITTED",
        "  - Workflow stops (on_result_found: stop_all)",
        "  - Issue is SOLVED! ✅",
        "",
        "If ANY tests fail:",
        "  - Approach ticket marked as 'approach-failed'",
        "  - Main issue ticket stays in 'exploring'",
        "  - Other parallel approaches may still succeed",
        "  - If all approaches fail, may need new Phase 2 exploration tasks",
        "  - Workflow continues until a solution is found or all approaches exhausted",
    ],
)
