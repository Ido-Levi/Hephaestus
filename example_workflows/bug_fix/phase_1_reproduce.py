"""
Phase 1: Reproduce & Analyze

Entry point for the Bug Fix workflow. Reads the bug report, creates reliable
reproduction steps, documents root cause hypothesis, and spawns Phase 2 fix task.
"""

from src.sdk.models import Phase

PHASE_1_REPRODUCE = Phase(
    id=1,
    name="reproduce_and_analyze",
    description="""Reproduce the bug and create a solid foundation for fixing it.

This phase is the entry point for bug fixing. It reads the bug report/issue,
creates reliable reproduction steps, forms a root cause hypothesis, and spawns
a Phase 2 task to implement the fix.

The output is a ticket tracking the bug and a Phase 2 task with all context needed.""",
    done_definitions=[
        "Bug report thoroughly read and understood",
        "Expected vs actual behavior clearly documented",
        "Reproduction steps created and VERIFIED to trigger the bug",
        "Root cause hypothesis documented with evidence",
        "reproduction.md file created with complete reproduction guide",
        "Bug ticket created with full details and proper severity",
        "ONE Phase 2 fix task created with ticket ID",
        "Key discoveries saved to memory for the hive mind",
        "Task marked as done",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A BUG ANALYST - REPRODUCE AND UNDERSTAND THE BUG
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Reproduce the bug, document it thoroughly, create ticket and fix task

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES - READ BEFORE STARTING
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - that's just a placeholder in examples!
   Your actual agent ID is in your task context.

   ❌ WRONG: `"agent_id": "agent-mcp"`
   ✅ RIGHT: `"agent_id": "[your actual agent ID from task context]"`

1. **VERIFY REPRODUCTION BEFORE CREATING TICKET**
   You MUST actually trigger the bug before documenting it.
   Don't just assume the reproduction steps work - RUN THEM!

2. **CREATE DETAILED TICKET**
   The ticket is the single source of truth for this bug.
   Phase 2 and Phase 3 agents will ONLY read the ticket to understand the bug.
   Make it comprehensive!

3. **ALWAYS MARK YOUR TASK AS DONE**
   After creating ticket and Phase 2 task, mark your task complete.

═══════════════════════════════════════════════════════════════════════
YOUR WORKFLOW
═══════════════════════════════════════════════════════════════════════

STEP 1: READ THE BUG REPORT

Your task description contains the bug report. Read it carefully.
Look for:
- What is the expected behavior?
- What is the actual behavior?
- Are there any reproduction steps provided?
- What is the severity/priority?
- Which component/area is affected?

If the bug report references external files (PROBLEM_STATEMENT.md, BUG_REPORT.md,
issue description), read those files too.

STEP 2: CREATE REPRODUCTION STEPS

Create a reliable way to trigger the bug. Options:

**For Code Bugs:**
```python
# reproduction_script.py
# This script reproduces bug #XXX

# Setup
from src.component import function_with_bug

# Trigger the bug
result = function_with_bug("input that causes bug")

# Expected: result should be "expected_value"
# Actual: result is "wrong_value" or raises Exception
print(f"Result: {result}")
print("BUG REPRODUCED!" if result != "expected_value" else "Bug NOT reproduced")
```

**For API Bugs:**
```bash
# Reproduction steps for API bug
curl -X POST http://localhost:8000/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"input": "value_that_triggers_bug"}'

# Expected: 200 OK with {"result": "expected"}
# Actual: 500 Internal Server Error or wrong response
```

**For UI Bugs:**
```markdown
1. Navigate to /page
2. Click on "Button X"
3. Enter "value" in input field
4. Click "Submit"
5. Expected: Success message appears
6. Actual: Error message or nothing happens
```

STEP 3: VERIFY REPRODUCTION WORKS

**🚨 MANDATORY: Actually run your reproduction steps! 🚨**

```bash
# Run the reproduction script
python reproduction_script.py

# Or run the curl command
# Or follow the manual steps

# VERIFY you see the bug occur
# If the bug doesn't occur, your reproduction is wrong - fix it!
```

**Expected outcome:** You should see the bug happen.
**If bug doesn't reproduce:** Investigate why. Maybe:
- Environment is different
- Steps are incomplete
- Bug was already fixed
- Bug is intermittent (document that!)

STEP 4: ANALYZE ROOT CAUSE

Now that you can reproduce, investigate WHY it happens:

```python
# Trace through the code
# 1. Find the function/component that fails
# 2. Read the code logic
# 3. Identify where the logic is wrong
# 4. Form a hypothesis about the fix

# Document your findings:
# - Affected file(s): src/component/module.py
# - Affected function(s): process_data()
# - Line number(s): 45-52
# - Root cause: Missing null check before accessing property
# - Hypothesis: Add null check at line 47
```

STEP 5: CREATE REPRODUCTION.MD

Create `reproduction.md` with complete documentation:

```markdown
# Bug Reproduction: [Brief Bug Title]

## Bug Summary
[1-2 sentences describing the bug]

## Expected Behavior
[What SHOULD happen]

## Actual Behavior
[What ACTUALLY happens - include error messages]

## Environment
- OS: [e.g., macOS 14.0, Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- Relevant dependencies: [e.g., FastAPI 0.104.0]

## Reproduction Steps

### Prerequisites
[Any setup needed before reproducing]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Reproduction Script (if applicable)
```python
[Your reproduction script]
```

### Reproduction Verified
- ✅ Bug successfully reproduced on [date]
- Output: [paste actual output showing the bug]

## Root Cause Analysis

### Affected Components
- File: [path/to/file.py]
- Function: [function_name()]
- Line(s): [line numbers]

### Root Cause
[Explanation of WHY the bug occurs]

### Fix Hypothesis
[What you think needs to change to fix it]

## Severity Assessment
- **Severity**: [Critical/High/Medium/Low]
- **Impact**: [Who/what is affected]
- **Urgency**: [Needs immediate fix / Can wait]
```

STEP 6: SAVE KEY DISCOVERIES TO MEMORY

```python
# Save reproduction knowledge
mcp__hephaestus__save_memory({
    "content": "Bug reproduction for [bug title]: [brief description]. Root cause: [cause]. Affected: [files/functions]. Reproduction at reproduction.md.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "memory_type": "discovery"
})

# Save codebase knowledge if you learned something
mcp__hephaestus__save_memory({
    "content": "Component [X] has issue with [Y] when [condition]. Located at [file:line].",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "memory_type": "codebase_knowledge"
})

# Save warning if critical
mcp__hephaestus__save_memory({
    "content": "WARNING: [Component] has [vulnerability/issue] - must be fixed before [deadline/release].",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "memory_type": "warning"
})
```

STEP 7: CREATE BUG TICKET

**🚨🚨🚨 CRITICAL: CREATE A DETAILED TICKET! 🚨🚨🚨**

The ticket is the ONLY information Phase 2 and Phase 3 agents will have!
Make it comprehensive!

```python
bug_ticket = mcp__hephaestus__create_ticket({
    "workflow_id": "[your workflow_id]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "title": "[Component]: [Brief bug description]",
    "description": (
        "## Bug: [Title]\\n\\n"
        "### Summary\\n"
        "[1-2 sentence summary of the bug]\\n\\n"
        "### Expected Behavior\\n"
        "[What should happen]\\n\\n"
        "### Actual Behavior\\n"
        "[What actually happens - include error messages]\\n\\n"
        "### Reproduction\\n"
        "See reproduction.md for full reproduction guide.\\n"
        "Quick reproduction:\\n"
        "1. [Step 1]\\n"
        "2. [Step 2]\\n"
        "3. [Step 3]\\n\\n"
        "### Root Cause Analysis\\n"
        "**Affected File(s):** [path/to/file.py]\\n"
        "**Affected Function(s):** [function_name()]\\n"
        "**Line(s):** [line numbers]\\n\\n"
        "**Root Cause:** [Explanation of why bug occurs]\\n\\n"
        "**Fix Hypothesis:** [What needs to change]\\n\\n"
        "### Severity\\n"
        "**Level:** [Critical/High/Medium/Low]\\n"
        "**Impact:** [Who/what is affected]\\n\\n"
        "### Acceptance Criteria\\n"
        "- [ ] Bug no longer reproduces with original reproduction steps\\n"
        "- [ ] Regression test added to prevent recurrence\\n"
        "- [ ] All existing tests still pass\\n"
        "- [ ] Fix is minimal and focused\\n"
    ),
    "ticket_type": "bug",
    "priority": "[critical/high/medium/low]",  # Match severity
    "tags": ["bug", "phase-2-pending", "[component-name]"],
    "blocked_by_ticket_ids": [],  # Usually bugs don't have blockers
})
bug_ticket_id = bug_ticket["ticket_id"]
```

STEP 8: CREATE PHASE 2 FIX TASK

```python
mcp__hephaestus__create_task({
    "description": f"Phase 2: Fix Bug - TICKET: {bug_ticket_id}. [Brief bug description]. Root cause: [cause]. Fix hypothesis: [hypothesis]. See reproduction.md for reproduction steps. Affected: [file:function:line].",
    "done_definition": f"Bug fixed with minimal changes. Regression test added. All tests passing. Ticket {bug_ticket_id} moved to 'building-done'. Phase 3 verification task created.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "workflow_id": "[your workflow_id]",
    "phase_id": 2,
    "priority": "[high/medium/low]",  # Match bug severity
    "cwd": ".",
    "ticket_id": bug_ticket_id
})
```

STEP 9: MARK YOUR TASK AS DONE

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 1 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": "Bug reproduced and documented. Root cause: [brief cause]. Created ticket and Phase 2 fix task. Reproduction at reproduction.md.",
    "key_learnings": [
        "Root cause: [what caused the bug]",
        "Affected: [component/file/function]",
        "Fix approach: [proposed fix]"
    ]
})
```

═══════════════════════════════════════════════════════════════════════
SPECIAL CASES
═══════════════════════════════════════════════════════════════════════

**IF BUG CANNOT BE REPRODUCED:**

1. Document everything you tried
2. Create ticket anyway with status note
3. Mark reproduction as "Unable to reproduce"
4. Still create Phase 2 task - they may have different environment

```python
# In ticket description, add:
"### ⚠️ Reproduction Status: UNABLE TO REPRODUCE\\n"
"Attempted reproduction on [date] with [environment].\\n"
"Steps tried:\\n"
"1. [What you tried]\\n"
"2. [What you tried]\\n"
"Bug did not occur. Possible reasons:\\n"
"- [Reason 1]\\n"
"- [Reason 2]\\n"
```

**IF BUG IS ALREADY FIXED:**

1. Verify the fix actually works
2. Check if there's a test covering it
3. If no test exists, still create Phase 2 task to add regression test
4. Document in ticket that bug appears fixed but needs test

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Actually reproduce the bug (don't assume!)
- Create comprehensive reproduction.md
- Document root cause with file/function/line
- Create detailed ticket with all context
- Save discoveries to memory
- Create ONE Phase 2 task
- Mark your task as done

❌ DO NOT:
- Implement the fix (that's Phase 2!)
- Write tests (that's Phase 2!)
- Create tickets without reproduction attempt
- Create vague ticket descriptions
- Skip the root cause analysis
- Forget to verify reproduction works
- Create multiple Phase 2 tasks (one is enough!)
- Forget to include ticket ID in Phase 2 task

═══════════════════════════════════════════════════════════════════════
REMEMBER: Your job is to make Phase 2's job easy. The better your
reproduction and analysis, the faster the bug gets fixed!
═══════════════════════════════════════════════════════════════════════""",
    outputs=[
        "reproduction.md with complete reproduction guide",
        "Bug ticket with full details in 'backlog' status",
        "ONE Phase 2 fix task with ticket ID",
        "Memory entries with key discoveries",
    ],
    next_steps=[
        "Phase 2 will implement the fix based on your analysis",
        "Phase 2 will move ticket: backlog → building → building-done",
        "Phase 3 will verify the fix works and write documentation",
    ],
)
