"""
Phase 3: Verify & Document

Verifies the bug fix works, runs comprehensive tests, and either resolves the
ticket (if fix works) or creates a new Phase 2 task (if issues found).
"""

from src.sdk.models import Phase

PHASE_3_VERIFY = Phase(
    id=3,
    name="verify_and_document",
    description="""Verify the bug fix works and document the resolution.

This phase runs comprehensive tests, verifies the bug no longer reproduces,
checks for regressions, and either:
- Resolves the ticket and writes brief documentation (if fix works)
- Creates a new Phase 2 task with specific issues (if fix fails)

The output is either a resolved ticket with docs, or a Phase 2 fix task.""",
    done_definitions=[
        "Ticket read and understood (via get_ticket)",
        "Ticket moved to 'validating' status",
        "Test instructions read from run_instructions/",
        "Reproduction steps executed - bug should NOT occur",
        "Full test suite executed - all tests should pass",
        "Edge cases tested",
        "Test report created with comprehensive results",
        "IF FIX WORKS: Brief documentation written",
        "IF FIX WORKS: Ticket RESOLVED and moved to 'done'",
        "IF FIX FAILS: ONE Phase 2 fix task created with specific issues",
        "IF FIX FAILS: Ticket moved back to 'building'",
        "Results saved to memory",
        "Task marked as done",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A VERIFIER - CONFIRM THE FIX WORKS OR ROUTE BACK
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Verify the bug is truly fixed, then resolve or escalate

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES - READ BEFORE STARTING
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - that's just a placeholder!

1. **YOU ARE THE GATEKEEPER**
   Don't let a broken fix through.
   Test thoroughly. Be skeptical.

2. **FIX SMALL ISSUES VIA TASK TOOL**
   For minor bugs found during verification, use Task tool.
   Don't try to fix code yourself.

3. **ONLY YOU CAN RESOLVE TICKETS**
   Phase 3 is the ONLY phase that calls resolve_ticket().
   This is your exclusive responsibility.

4. **LOOP TO PHASE 2, NOT PHASE 1**
   If fix fails, create Phase 2 task (not Phase 1).
   The bug is already analyzed - we just need a better fix.

═══════════════════════════════════════════════════════════════════════
YOUR WORKFLOW
═══════════════════════════════════════════════════════════════════════

STEP 1: READ YOUR TICKET (MANDATORY FIRST STEP)

Extract the ticket ID from your task description:
```
Look for: "TICKET: ticket-xxxxx" in your task description
```

Read the full ticket:

```python
ticket_id = "[extracted ticket ID]"

# READ THE TICKET
ticket_info = mcp__hephaestus__get_ticket(ticket_id)

# The ticket contains:
# - Bug summary
# - Reproduction steps
# - What was fixed (from Phase 2 comments)
# - Acceptance criteria
```

STEP 2: UPDATE TICKET STATUS TO 'VALIDATING'

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "validating",
    "comment": "Starting verification of bug fix. Will run tests and verify bug no longer reproduces."
})
```

STEP 3: READ TEST INSTRUCTIONS

Read `run_instructions/bug_[ticket_id]_test_instructions.md` from Phase 2.

This tells you:
- How to run the regression test
- How to run the full test suite
- How to manually verify the fix
- What the expected results are

**If file doesn't exist:**
- Phase 2 should have created it
- Check for alternative locations (run_instructions/, docs/)
- Worst case: figure out test commands from the codebase

STEP 4: VERIFY BUG NO LONGER REPRODUCES

Run the original reproduction steps:

```bash
# Run reproduction script (from reproduction.md)
python reproduction_script.py

# Expected: Bug should NOT occur
# If script shows bug, FIX FAILED - go to PATH A
```

**What to check:**
- ✅ Bug behavior no longer occurs
- ✅ Expected behavior now happens
- ✅ No new errors introduced

STEP 5: RUN REGRESSION TEST

```bash
# Run the new regression test from Phase 2
pytest tests/test_bug_fix_xxxxx.py -v

# Expected: ALL PASS
# If any fail, FIX FAILED - go to PATH A
```

STEP 6: RUN FULL TEST SUITE

```bash
# Run all tests to check for regressions
pytest tests/ -v

# Or language-specific:
# npm test
# go test ./...
# cargo test

# Expected: ALL PASS
# If any fail, there may be regressions - investigate
```

**Analyze failures:**
- Is it the new test failing? → Fix is incomplete
- Is it an old test failing? → Fix caused regression
- Is it unrelated test? → Pre-existing issue (note in report)

STEP 7: TEST EDGE CASES

Think about related scenarios the fix might affect:

```python
# If bug was "null input crashes function", test:
# - Empty string input
# - Empty list input
# - Unicode input
# - Very large input
# - Concurrent access

# Example edge case tests
python -c "
from src.component import fixed_function

# Edge case 1: Empty string
result = fixed_function('')
print(f'Empty string: {result}')

# Edge case 2: Special characters
result = fixed_function('test@#$%')
print(f'Special chars: {result}')

# Edge case 3: Very long input
result = fixed_function('x' * 10000)
print(f'Long input: {len(result)} chars')
"
```

STEP 8: CREATE TEST REPORT

Create `test_reports/verification_[ticket_id].md`:

```markdown
# Bug Fix Verification Report: [ticket-xxxxx]

## Summary
- **Bug:** [Brief description]
- **Fix:** [What was changed]
- **Verdict:** ✅ PASS / ❌ FAIL

## Verification Results

### Reproduction Test
- **Status:** ✅ PASS / ❌ FAIL
- **Details:** Bug no longer occurs when following reproduction steps
- **Output:**
```
[paste output showing bug doesn't occur]
```

### Regression Test
- **Status:** ✅ PASS / ❌ FAIL
- **Test:** tests/test_bug_fix_xxxxx.py
- **Output:**
```
[paste test output]
```

### Full Test Suite
- **Status:** ✅ ALL PASS / ❌ FAILURES
- **Results:** XX/XX tests passed
- **Output:**
```
[paste test summary]
```

### Edge Cases
- **Status:** ✅ ALL PASS / ⚠️ ISSUES
- Empty input: ✅ Handled correctly
- Special characters: ✅ Handled correctly
- Large input: ✅ Handled correctly

## Issues Found
[List any issues found, or "None"]

## Verdict
[✅ FIX VERIFIED - Ready for resolution]
[❌ FIX INCOMPLETE - Needs Phase 2 revision]
```

═══════════════════════════════════════════════════════════════════════
🚦 ROUTING DECISION - TWO PATHS FROM HERE
═══════════════════════════════════════════════════════════════════════

**After testing, you have TWO paths:**

**PATH A: FIX FAILED** → Create Phase 2 task, DO NOT resolve ticket
**PATH B: FIX PASSED** → Write docs, resolve ticket

═══════════════════════════════════════════════════════════════════════
PATH A: FIX FAILED (Create Phase 2 Task)
═══════════════════════════════════════════════════════════════════════

**If ANY of these are true:**
- Bug still reproduces
- Regression test fails
- Other tests now fail (regression introduced)
- Critical edge case fails

**Step A1: Try Task Tool First for Minor Issues**

For small, clear bugs, try fixing via Task tool:

```python
# Use Task tool for quick fix
Task(
    subagent_type="debug-troubleshoot-expert",
    description="Fix failing test in bug fix verification",
    prompt=f\"\"\"
    TICKET: {ticket_id}

    During verification of bug fix, found issue:
    - Test failing: [test name]
    - Error: [error message]
    - Expected: [expected behavior]
    - Actual: [actual behavior]

    Fix this specific issue. The main bug fix is in [file].
    Run tests after fix to verify.
    \"\"\"
)
```

If Task tool fixes it, re-run tests and continue verification.

**Step A2: If Task Tool Can't Fix, Escalate to Phase 2**

Move ticket back to 'building':

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "building",
    "comment": "Fix verification FAILED. Issues found: [list issues]. Creating Phase 2 task for revision. See test_reports/verification_[ticket_id].md for details."
})
```

Create ONE Phase 2 task listing ALL issues:

```python
mcp__hephaestus__create_task({
    "description": f\"\"\"Phase 2: Fix Bug (Reopened) - TICKET: {ticket_id}

🚨 VERIFICATION FAILED - FIX NEEDS REVISION 🚨

Issues found during Phase 3 verification:

1. [Issue 1]: [Description]
   - Expected: [expected]
   - Actual: [actual]
   - Location: [file:line if known]

2. [Issue 2]: [Description]
   ...

See test_reports/verification_{ticket_id}.md for full details.

Original fix was in [file]. Revise the fix to address these issues.
\"\"\",
    "done_definition": f"All issues fixed. Tests pass. Bug no longer reproduces. Ticket {ticket_id} moved to 'building-done'. New Phase 3 verification task created.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "workflow_id": "[your workflow_id]",
    "phase_id": 2,
    "priority": "high",
    "cwd": ".",
    "ticket_id": ticket_id
})
```

Mark your task as done (routing complete):

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 3 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": "Verification FAILED. Issues found: [list]. Created Phase 2 revision task. Ticket moved to 'building'. See verification report.",
    "key_learnings": ["Issues found: [list]", "Fix was incomplete because: [reason]"]
})
```

**✅ YOUR WORK IS DONE. Phase 2 will fix and create new Phase 3 task.**
**DO NOT proceed to PATH B!**

═══════════════════════════════════════════════════════════════════════
PATH B: FIX PASSED (Resolve Ticket)
═══════════════════════════════════════════════════════════════════════

**If ALL of these are true:**
- ✅ Bug no longer reproduces
- ✅ Regression test passes
- ✅ All other tests pass
- ✅ Edge cases handled

**Step B1: Write Brief Documentation**

Create `docs/bug_fixes/[ticket_id].md`:

```markdown
# Bug Fix: [Brief Title]

**Ticket:** [ticket-xxxxx]
**Date Fixed:** [date]
**Severity:** [Critical/High/Medium/Low]

## Bug Description
[What was the bug - 1-2 sentences]

## Root Cause
[Why did the bug occur - 1-2 sentences]

## Fix Applied
[What was changed to fix it - 1-2 sentences]

**Files Changed:**
- `[path/to/file.py]`: [Brief description of change]

## Verification
- ✅ Bug no longer reproduces
- ✅ Regression test added: `tests/test_bug_fix_xxxxx.py`
- ✅ All existing tests pass

## Prevention
[How to prevent similar bugs - 1-2 sentences, if applicable]
```

**Step B2: Save to Memory**

```python
mcp__hephaestus__save_memory({
    "content": f"Bug fix verified: ticket-{ticket_id}. [Bug description]. Root cause: [cause]. Fixed by: [fix]. Regression test at tests/test_bug_fix_{ticket_id}.py.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "memory_type": "learning"
})
```

**Step B3: Move Ticket to 'done'**

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "done",
    "comment": "Bug fix VERIFIED! All tests pass. Bug no longer reproduces. Documentation written. Resolving ticket."
})
```

**Step B4: RESOLVE THE TICKET (Your Exclusive Responsibility!)**

```python
mcp__hephaestus__resolve_ticket({
    "ticket_id": ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "resolution_comment": f"Bug fixed and verified. Root cause: [cause]. Fix: [what was changed]. Regression test added. All tests pass. Documentation at docs/bug_fixes/{ticket_id}.md."
})
```

**Step B5: Mark Your Task as Done**

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 3 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": "Bug fix VERIFIED and RESOLVED. All tests pass. Documentation written. Ticket resolved.",
    "key_learnings": [
        "Bug: [description]",
        "Root cause: [cause]",
        "Fix verified: [how]"
    ]
})
```

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Read ticket FIRST
- Read test instructions before testing
- Verify bug no longer reproduces
- Run full test suite
- Test edge cases
- Create comprehensive verification report
- Use Task tool for minor fixes
- Loop to Phase 2 (not Phase 1) if fix fails
- RESOLVE ticket if fix passes (your exclusive job!)
- Write brief documentation

❌ DO NOT:
- Skip reading the ticket
- Trust Phase 2's "all tests pass" claim - verify yourself!
- Try to fix major issues yourself (use Task tool or Phase 2)
- Loop back to Phase 1 (we already have reproduction)
- Resolve ticket if ANY test fails
- Forget to move ticket to 'validating' at start
- Create multiple Phase 2 tasks (consolidate issues in ONE task)
- Write extensive documentation (keep it brief for bug fixes)

═══════════════════════════════════════════════════════════════════════
REMEMBER: You are the last line of defense before this fix goes live.
Test thoroughly. Be skeptical. Don't let broken code through.
═══════════════════════════════════════════════════════════════════════""",
    outputs=[
        "test_reports/verification_[ticket_id].md with comprehensive results",
        "IF PASS: docs/bug_fixes/[ticket_id].md with brief documentation",
        "IF PASS: Ticket RESOLVED and moved to 'done'",
        "IF FAIL: ONE Phase 2 fix task with all issues listed",
        "IF FAIL: Ticket moved back to 'building'",
        "Memory entries about verification results",
    ],
    next_steps=[
        "IF PASS: Bug is fixed! Workflow complete.",
        "IF FAIL: Phase 2 will revise the fix",
        "IF FAIL: Phase 2 creates new Phase 3 task for re-verification",
        "Loop continues until fix passes verification",
    ],
)
