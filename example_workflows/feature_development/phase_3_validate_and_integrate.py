"""
Phase 3: Validate & Complete

Validates ONE work item, runs tests, checks for regressions, and resolves the ticket.
"""

from src.sdk.models import Phase

PHASE_3_VALIDATE_AND_INTEGRATE = Phase(
    id=3,
    name="validate_and_integrate",
    description="""Validate ONE work item and resolve its ticket.

This phase handles validation for a SINGLE ticket/work item. It:
1. Runs tests for the work item
2. Checks for regressions in related areas
3. Fixes bugs via Task tool if needed
4. Resolves the ticket when validation passes

Multiple Phase 3 tasks may run in parallel for different work items.""",
    done_definitions=[
        "Ticket read and moved to 'testing' status",
        "Tests for the work item executed and passing",
        "Related tests run to check for regressions",
        "Bugs fixed via Task tool (if found)",
        "IF critical bugs: Phase 2 fix task created, ticket back to 'implementing'",
        "IF all passes: Ticket RESOLVED and moved to 'done'",
        "Validation results saved to memory",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A VALIDATOR - TEST ONE WORK ITEM AND RESOLVE
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Validate ONE work item and resolve its ticket

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL: YOU ARE VALIDATING ONE WORK ITEM, NOT THE ENTIRE FEATURE!
═══════════════════════════════════════════════════════════════════════

Your task description contains "TICKET: ticket-xxxxx".
That ticket represents ONE work item that was implemented.

You validate and resolve just YOUR ticket.
Other Phase 3 agents handle other work items.

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL: CHECK FOR REGRESSIONS!
═══════════════════════════════════════════════════════════════════════

Don't just run the new tests - also run related existing tests!

The work item integrates with existing code.
Make sure it doesn't break anything.

═══════════════════════════════════════════════════════════════════════
⚠️ WORKFLOW RULES
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**

1. **READ YOUR TICKET FIRST**
   Extract "TICKET: ticket-xxxxx" from your task description.

2. **RUN TESTS FOR YOUR WORK ITEM + RELATED AREAS**
   Not just new tests - check for regressions too!

3. **✅ YOU RESOLVE YOUR TICKET**
   Phase 3 is the ONLY phase that resolves tickets!

4. **FIX BUGS VIA TASK TOOL**
   Don't try to fix complex bugs yourself.

═══════════════════════════════════════════════════════════════════════

STEP 0: READ YOUR TICKET AND UPDATE STATUS

```python
# Extract ticket ID from task description
ticket_id = "[extracted ticket ID]"

# Read the full ticket
ticket_info = get_ticket(ticket_id)

# Move to 'testing' status
change_ticket_status(
    ticket_id=ticket_id,
    agent_id="[YOUR AGENT ID]",
    new_status="testing",
    comment="Starting validation of this work item."
)
```

═══════════════════════════════════════════════════════════════════════

STEP 1: RUN TESTS FOR YOUR WORK ITEM

Run the tests that were added for this work item:

```bash
# Run tests for this specific work item
pytest tests/test_[work_item].py -v
```

All tests for your work item should pass.

═══════════════════════════════════════════════════════════════════════

STEP 2: CHECK FOR REGRESSIONS

**Run related tests to ensure nothing is broken:**

```bash
# Run tests for related components
pytest tests/test_[related].py -v

# Or run the full test suite if small
pytest tests/ -v
```

If existing tests fail, that's a regression caused by the work item.

═══════════════════════════════════════════════════════════════════════

STEP 3: FIX BUGS (IF NEEDED)

**If tests fail, fix via Task tool:**

```python
Task(
    subagent_type="debug-troubleshoot-expert",
    description="Fix bugs in work item",
    prompt=f\"\"\"Fix bugs found in work item validation:

TICKET: {ticket_id}

**Failing Tests:**
1. test_xxx - [error description]

Fix all issues and verify tests pass.
\"\"\"
)
```

After fixes, re-run tests to verify.

═══════════════════════════════════════════════════════════════════════

STEP 4: ROUTE BASED ON RESULTS

**PATH A: CRITICAL BUGS (Back to Phase 2)**

If fundamental issues require re-implementation:

```python
# Move ticket back to 'implementing'
change_ticket_status(
    ticket_id=ticket_id,
    agent_id="[YOUR AGENT ID]",
    new_status="implementing",
    comment="Critical bugs found. Needs Phase 2 fix."
)

# Create Phase 2 fix task
create_task(
    description=f"Phase 2: Fix critical bugs in [Work Item] - TICKET: {ticket_id}. Bugs: [list]. See failing tests.",
    done_definition=f"Bugs fixed. Tests passing. Ticket {ticket_id} moved to 'implemented'. Phase 3 retest task created.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=2,
    priority="high",
    ticket_id=ticket_id
)

# Mark your task done (you've routed correctly)
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary="Validation found critical bugs. Created Phase 2 fix task."
)
```

---

**PATH B: ALL TESTS PASS (Resolve ticket)**

If all tests pass, resolve the ticket:

```python
# Move ticket to 'done'
change_ticket_status(
    ticket_id=ticket_id,
    agent_id="[YOUR AGENT ID]",
    new_status="done",
    comment="Work item validated. All tests pass."
)

# RESOLVE the ticket
resolve_ticket(
    ticket_id=ticket_id,
    agent_id="[YOUR AGENT ID]",
    resolution_comment="Work item [name] validated. Tests pass. No regressions. Ready for use."
)

# Mark your task done
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary="Work item [name] validated. All tests pass. Ticket resolved."
)
```

═══════════════════════════════════════════════════════════════════════
REMEMBER
═══════════════════════════════════════════════════════════════════════

- You validate ONE work item (from ONE ticket)
- Run tests for your work item + check for regressions
- Fix bugs via Task tool
- If critical bugs: create Phase 2 fix task
- If all passes: RESOLVE the ticket (your exclusive responsibility!)
- Other work items are validated independently
""",
    outputs=[
        "Tests run for work item",
        "Regressions checked in related areas",
        "Bugs fixed (if found)",
        "IF critical bugs: Phase 2 fix task created",
        "IF all passes: Ticket RESOLVED and moved to 'done'",
    ],
    next_steps=[
        "Work item is complete when ticket is resolved",
        "Other work items proceed via their own Phase 3 tasks",
        "When all tickets are resolved, the feature is complete",
    ],
)
