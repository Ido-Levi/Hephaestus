"""
Phase 2: Implement Fix

Implements the bug fix based on Phase 1's analysis. Creates minimal, focused
changes with regression tests, then hands off to Phase 3 for verification.
"""

from src.sdk.models import Phase

PHASE_2_FIX = Phase(
    id=2,
    name="implement_fix",
    description="""Implement the bug fix with minimal, focused changes.

This phase reads the ticket and reproduction from Phase 1, implements a fix,
writes a regression test, validates the fix works, and hands off to Phase 3.

The output is working code that fixes the bug, with tests to prevent regression.""",
    done_definitions=[
        "Ticket read and understood (via get_ticket)",
        "Ticket moved to 'building' status",
        "reproduction.md reviewed and understood",
        "Bug location identified in codebase",
        "Fix implemented with MINIMAL, focused changes",
        "Regression test written that would FAIL without the fix",
        "All existing tests still pass",
        "Self-validation completed (bug no longer reproduces)",
        "Test instructions documented in run_instructions/",
        "Ticket moved to 'building-done' status",
        "ONE Phase 3 verification task created with ticket ID",
        "Fix approach saved to memory",
        "Task marked as done",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A BUG FIXER - IMPLEMENT A MINIMAL, FOCUSED FIX
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Fix the bug with minimal changes, add regression test

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES - READ BEFORE STARTING
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - that's just a placeholder!
   Your actual agent ID is in your task context.

1. **READ THE TICKET FIRST**
   The ticket contains ALL the information you need.
   Don't start coding until you fully understand the bug.

2. **MINIMAL CHANGES ONLY**
   Fix the bug and NOTHING else.
   Don't refactor. Don't "improve" nearby code.
   Every line you change is a line that could break something.

3. **REGRESSION TEST IS MANDATORY**
   You MUST write a test that would FAIL on the old code.
   This prevents the bug from ever coming back.

4. **VALIDATE BEFORE HANDOFF**
   Run your fix. Verify the bug is gone.
   Don't hand broken code to Phase 3.

═══════════════════════════════════════════════════════════════════════
YOUR WORKFLOW
═══════════════════════════════════════════════════════════════════════

STEP 1: READ YOUR TICKET (MANDATORY FIRST STEP)

Extract the ticket ID from your task description:
```
Look for: "TICKET: ticket-xxxxx" in your task description
```

Then read the full ticket:

```python
ticket_id = "[extracted ticket ID]"

# READ THE TICKET - This is MANDATORY!
ticket_info = mcp__hephaestus__get_ticket(ticket_id)

# The ticket contains:
# - Bug summary
# - Expected vs actual behavior
# - Reproduction steps
# - Root cause analysis (file, function, line)
# - Fix hypothesis
# - Acceptance criteria
```

**🎯 THE TICKET IS YOUR SCOPE - FIX ONLY WHAT IT DESCRIBES!**

STEP 2: UPDATE TICKET STATUS TO 'BUILDING'

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "building",
    "comment": "Starting bug fix implementation. Reviewed ticket and reproduction.md."
})
```

STEP 3: REVIEW REPRODUCTION

Read `reproduction.md` created by Phase 1:
- Understand the exact steps to trigger the bug
- Note the expected vs actual behavior
- Review the root cause analysis

**Run the reproduction to see the bug yourself:**
```bash
# Run the reproduction script
python reproduction_script.py

# Or follow the manual steps
# You should see the bug occur
```

STEP 4: LOCATE THE BUG

The ticket tells you where to look. Navigate there:

```python
# From ticket:
# Affected File: src/component/module.py
# Affected Function: process_data()
# Line: 45-52

# Read the file and understand the bug
# Trace through the code logic
# Verify the root cause hypothesis is correct
```

**If the root cause analysis is WRONG:**
- Document what's actually wrong
- Update your understanding
- Proceed with the correct fix

STEP 5: IMPLEMENT THE FIX

**🚨 GOLDEN RULE: MINIMAL CHANGES ONLY! 🚨**

```python
# ❌ BAD: Refactoring while fixing
def process_data(data):
    # Completely rewrote this function while fixing the bug
    # Added logging, changed variable names, restructured logic
    # 150 lines changed
    pass

# ✅ GOOD: Minimal fix
def process_data(data):
    # Original code unchanged except for the fix

    # BUG FIX: Added null check to prevent AttributeError
    # See ticket-xxxxx for details
    if data is None:
        return []

    # Rest of original code unchanged
    return data.items()
```

**Fix Guidelines:**
- Change only what's necessary to fix the bug
- Add a comment explaining the fix (reference ticket ID)
- Don't rename variables, don't reformat, don't refactor
- If you MUST change something else, document why
- Ensure backward compatibility

STEP 6: WRITE REGRESSION TEST

**🚨 MANDATORY: Write a test that would FAIL without your fix! 🚨**

```python
# tests/test_bug_fix_[ticket_id].py
# or add to existing test file

import pytest
from src.component.module import process_data

class TestBugFixTicketXXXXX:
    \"\"\"
    Regression tests for ticket-xxxxx: [Bug title]

    Bug: [Brief description]
    Root cause: [What was wrong]
    Fix: [What was changed]
    \"\"\"

    def test_process_data_handles_none_input(self):
        \"\"\"
        Regression test: process_data should handle None input gracefully.

        Before fix: Raised AttributeError: 'NoneType' has no attribute 'items'
        After fix: Returns empty list for None input

        Ticket: ticket-xxxxx
        \"\"\"
        # This test would FAIL on the old code
        result = process_data(None)

        # After fix, should return empty list
        assert result == []

    def test_process_data_still_works_with_valid_input(self):
        \"\"\"Verify fix did not break normal functionality.\"\"\"
        result = process_data({"key": "value"})
        assert result == [("key", "value")]
```

**Test Requirements:**
- Test MUST fail on old code (pre-fix)
- Test MUST pass on new code (post-fix)
- Test should be clearly labeled as regression test
- Reference the ticket ID in docstring
- Also verify fix didn't break existing functionality

STEP 7: RUN ALL TESTS

```bash
# Run the new regression test
pytest tests/test_bug_fix_xxxxx.py -v

# Run ALL tests to ensure nothing broke
pytest tests/ -v

# Expected: ALL tests pass, including new regression test
```

**If tests fail:**
- If YOUR regression test fails → fix isn't working, go back to Step 5
- If OTHER tests fail → your fix broke something, adjust the fix
- Don't proceed until ALL tests pass

STEP 8: VERIFY BUG IS FIXED

Run the original reproduction steps:

```bash
# Run reproduction script
python reproduction_script.py

# Expected: Bug should NOT occur anymore
# The script should show success, not the error
```

**If bug still occurs:**
- Your fix is incomplete
- Go back to Step 5 and improve the fix

STEP 9: CREATE TEST INSTRUCTIONS

Create `run_instructions/bug_[ticket_id]_test_instructions.md`:

```markdown
# Test Instructions: Bug Fix [ticket-xxxxx]

## Bug Fixed
[Brief description of the bug that was fixed]

## Prerequisites
- Python 3.x
- Dependencies: `pip install -r requirements.txt`
- [Any other setup needed]

## Running Tests

### Regression Test (New)
```bash
# This test specifically validates the bug fix
pytest tests/test_bug_fix_xxxxx.py -v

# Expected: PASS
```

### Full Test Suite
```bash
# Ensure fix didn't break anything
pytest tests/ -v

# Expected: ALL PASS
```

### Manual Verification
```bash
# Run original reproduction steps
python reproduction_script.py

# Expected: Bug no longer occurs
# Should see: [expected output]
```

## What Was Fixed
- **File:** [path/to/file.py]
- **Function:** [function_name()]
- **Change:** [Brief description of the fix]

## Test Results (Phase 2 Execution)
- Regression test: ✅ PASS
- Full suite: ✅ XX/XX tests pass
- Manual verification: ✅ Bug no longer reproduces
```

STEP 10: SAVE FIX TO MEMORY

```python
mcp__hephaestus__save_memory({
    "content": f"Bug fix for ticket-{ticket_id}: [bug description]. Fixed by [what was changed] in [file:line]. Regression test at tests/test_bug_fix_{ticket_id}.py.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "memory_type": "learning"
})

# If you learned something useful about the codebase
mcp__hephaestus__save_memory({
    "content": "[Component] requires [pattern/check] when handling [scenario]. Missing this causes [problem].",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "memory_type": "codebase_knowledge"
})
```

STEP 11: MOVE TICKET TO 'BUILDING-DONE'

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "building-done",
    "comment": "Bug fix implemented. Regression test added. All tests passing. Ready for Phase 3 verification."
})
```

STEP 12: CREATE PHASE 3 VERIFICATION TASK

```python
mcp__hephaestus__create_task({
    "description": f"Phase 3: Verify Bug Fix - TICKET: {ticket_id}. Verify fix works, run full test suite, check for regressions. Fix: [brief description of fix]. Test instructions at run_instructions/bug_{ticket_id}_test_instructions.md.",
    "done_definition": f"Bug fix verified. All tests pass. No regressions. Brief documentation written. Ticket {ticket_id} resolved and moved to 'done'.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "workflow_id": "[your workflow_id]",
    "phase_id": 3,
    "priority": "high",
    "cwd": ".",
    "ticket_id": ticket_id  # Pass the ticket ID forward!
})
```

STEP 13: MARK YOUR TASK AS DONE

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 2 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": f"Bug fixed in [file]. Added regression test. All tests passing. Ticket moved to 'building-done'. Phase 3 verification task created.",
    "key_learnings": [
        "Fix: [what was changed]",
        "Root cause: [confirmed cause]",
        "Test: [test file/name]"
    ]
})
```

═══════════════════════════════════════════════════════════════════════
SPECIAL CASE: REOPENED BUG (FROM PHASE 3)
═══════════════════════════════════════════════════════════════════════

If your task description contains:
- "Reopened from Phase 3"
- "Fix failed verification"
- "Additional bugs found"

Then you're fixing a bug that Phase 3 found issues with.

**In this case:**
1. Read the UPDATED ticket (it has new information from Phase 3)
2. Read the test report from Phase 3 (mentioned in task)
3. Focus on fixing the specific issues Phase 3 identified
4. DON'T recreate reproduction.md (it already exists)
5. Update your regression test if needed
6. Proceed with normal Steps 5-13

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Read the ticket FIRST
- Make MINIMAL changes to fix the bug
- Add clear comments referencing the ticket
- Write regression test that would FAIL without fix
- Run ALL tests before handoff
- Verify bug no longer reproduces
- Create test instructions file
- Create Phase 3 verification task

❌ DO NOT:
- Refactor unrelated code
- "Improve" code while you're there
- Change code style or formatting
- Rename variables or functions
- Skip the regression test
- Hand off without self-validation
- Create multiple Phase 3 tasks
- Forget to move ticket to 'building-done'
- Forget ticket_id in Phase 3 task

═══════════════════════════════════════════════════════════════════════
REMEMBER: The best bug fix is the smallest one that works.
Every extra line you change is a potential new bug.
═══════════════════════════════════════════════════════════════════════""",
    outputs=[
        "Fixed code with minimal, focused changes",
        "Regression test in tests/ that would fail without fix",
        "run_instructions/bug_[ticket_id]_test_instructions.md",
        "Memory entries about the fix",
        "ONE Phase 3 verification task with ticket ID",
    ],
    next_steps=[
        "Ticket moved to 'building-done', waiting for Phase 3",
        "Phase 3 will verify the fix comprehensively",
        "Phase 3 will move ticket: building-done → validating → done (or back to building if issues)",
        "If Phase 3 finds issues, they create new Phase 2 task (same ticket)",
    ],
)
