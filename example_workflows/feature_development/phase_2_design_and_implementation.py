"""
Phase 2: Design & Implementation

Implements ONE work item from a single ticket, following existing code patterns.
Creates a Phase 3 validation task when done.
"""

from src.sdk.models import Phase

PHASE_2_DESIGN_AND_IMPLEMENTATION = Phase(
    id=2,
    name="design_and_implementation",
    description="""Implement ONE work item following existing code patterns.

This phase handles a SINGLE ticket/work item (not the entire feature). It:
1. Reads the ticket to understand scope
2. Studies existing code patterns
3. Implements the work item
4. Adds tests for the work item
5. Creates ONE Phase 3 validation task for this ticket

Multiple Phase 2 tasks may run in parallel for different work items.""",
    done_definitions=[
        "Ticket read and moved to 'implementing' status",
        "Existing code patterns understood",
        "Work item implemented following existing patterns",
        "Tests added for the work item",
        "Implementation self-tested (basic functionality verified)",
        "Ticket moved to 'implemented' status",
        "ONE Phase 3 validation task created with same ticket ID",
        "Implementation decisions saved to memory",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A FEATURE BUILDER - IMPLEMENT ONE WORK ITEM
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Implement ONE work item from your ticket following existing patterns

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL: YOU ARE IMPLEMENTING ONE WORK ITEM, NOT THE ENTIRE FEATURE!
═══════════════════════════════════════════════════════════════════════

Your task description contains "TICKET: ticket-xxxxx".
That ticket represents ONE work item (e.g., "Backend API" or "Frontend Components").

You are NOT implementing the entire feature - just YOUR work item.
Other Phase 2 agents handle other work items in parallel.

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL: FOLLOW EXISTING CODE PATTERNS!
═══════════════════════════════════════════════════════════════════════

**This is NOT a greenfield project!**

You MUST:
- ✅ Read existing code BEFORE writing new code
- ✅ Follow existing naming conventions
- ✅ Use existing utilities and helpers
- ✅ Match existing code style
- ✅ Integrate with existing architecture

You must NOT:
- ❌ Create new architectural patterns
- ❌ Add new frameworks without justification
- ❌ Ignore existing utilities
- ❌ Use different naming conventions

═══════════════════════════════════════════════════════════════════════
⚠️ WORKFLOW RULES
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**

1. **READ YOUR TICKET FIRST**
   Extract "TICKET: ticket-xxxxx" from your task description.
   The ticket describes YOUR specific work item.

2. **ONE TICKET = ONE WORK ITEM**
   Your ticket is ONE piece of the feature, not the whole thing.

3. **CREATE ONE PHASE 3 TASK**
   When done, create ONE Phase 3 task with the SAME ticket ID.

4. **ONLY PHASE 3 RESOLVES TICKETS**
   You move tickets to 'implemented', NOT 'done'.

═══════════════════════════════════════════════════════════════════════

STEP 0: READ YOUR TICKET

```python
# Extract ticket ID from your task description
ticket_id = "[extracted ticket ID]"

# Read the full ticket to understand YOUR work item
ticket_info = get_ticket(ticket_id)

# The ticket tells you:
# - What specific work item to implement
# - Files to modify/create
# - Acceptance criteria
# - Dependencies (what this is blocked by)

# Move to 'implementing' status
change_ticket_status(
    ticket_id=ticket_id,
    agent_id="[YOUR AGENT ID]",
    new_status="implementing",
    comment="Starting implementation of this work item."
)
```

═══════════════════════════════════════════════════════════════════════

STEP 1: STUDY EXISTING CODE (CRITICAL!)

**Before writing ANY code, read the existing codebase:**

1. **Read similar features:**
   - How are existing features structured?
   - What patterns do they follow?

2. **Study the target files:**
   - Read the files you'll modify
   - Note import patterns, naming, style

3. **Check for utilities:**
   - Are there helper functions you should use?
   - Are there base classes to extend?

```python
save_memory(
    content="[Work Item] patterns: [describe patterns found]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 2: IMPLEMENT THE WORK ITEM

**Follow existing patterns!**

1. **Use existing utilities:**
   ```python
   # DON'T create new utilities if they exist
   from existing.utils import helper_function
   ```

2. **Match naming conventions:**
   ```python
   # Match what exists in the codebase
   ```

3. **Follow existing structure:**
   ```python
   # If other features have models.py, services.py, api.py
   # YOUR work item should follow the same structure
   ```

═══════════════════════════════════════════════════════════════════════

STEP 3: ADD TESTS

**Add tests following existing test patterns:**

1. Find where existing tests are located
2. Match the testing framework and style
3. Create tests for YOUR work item

```python
# tests/test_[work_item].py
def test_work_item_basic():
    # Test basic functionality
    pass

def test_work_item_edge_case():
    # Test edge cases
    pass
```

═══════════════════════════════════════════════════════════════════════

STEP 4: SELF-VALIDATE

**Before creating Phase 3 task, verify your work:**

1. **Code compiles/runs:**
   ```bash
   python -c "from src.feature import *"  # No import errors
   ```

2. **Basic functionality works:**
   - Quick test that the work item actually works

3. **Your tests pass:**
   ```bash
   pytest tests/test_[work_item].py -v
   ```

═══════════════════════════════════════════════════════════════════════

STEP 5: UPDATE TICKET AND CREATE PHASE 3 TASK

```python
# Move YOUR ticket to 'implemented'
change_ticket_status(
    ticket_id=ticket_id,
    agent_id="[YOUR AGENT ID]",
    new_status="implemented",
    comment="Work item implemented. Tests added. Ready for validation."
)

# Create ONE Phase 3 task for YOUR ticket
create_task(
    description=f"Phase 3: Validate [Work Item Name] - TICKET: {ticket_id}. Run tests for this work item. Verify it integrates correctly. Check for regressions in related areas.",
    done_definition=f"Work item validated. Tests pass. No regressions. Ticket {ticket_id} resolved and moved to 'done'.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=3,
    priority="medium",
    ticket_id=ticket_id  # SAME ticket ID!
)
```

═══════════════════════════════════════════════════════════════════════

STEP 6: MARK YOUR TASK AS DONE

```python
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary="Work item [name] implemented following existing patterns. Added [N] files, modified [M] files. Tests added. Ticket moved to 'implemented'. Phase 3 task created."
)
```

═══════════════════════════════════════════════════════════════════════
REMEMBER
═══════════════════════════════════════════════════════════════════════

- You handle ONE work item (from ONE ticket)
- Other Phase 2 agents handle other work items in parallel
- Follow existing code patterns
- Create ONE Phase 3 task with the SAME ticket ID
- Phase 3 will validate and resolve the ticket
""",
    outputs=[
        "Work item implementation integrated with existing code",
        "Tests for the work item",
        "Ticket moved to 'implemented' status",
        "ONE Phase 3 validation task created with same ticket ID",
    ],
    next_steps=[
        "Phase 3 will validate this work item",
        "Phase 3 will run tests and check for regressions",
        "Phase 3 will resolve the ticket when validation passes",
        "Other work items proceed independently via their own Phase 2/3 tasks",
    ],
)
