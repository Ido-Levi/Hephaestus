"""
Phase 1: Feature Analysis & Planning

Entry point for the Feature Development workflow. Analyzes the feature request,
discovers relevant parts of the existing codebase, breaks down the feature into
work items, and creates tickets with proper blocking relationships.
"""

from src.sdk.models import Phase

PHASE_1_FEATURE_ANALYSIS = Phase(
    id=1,
    name="feature_analysis",
    description="""Analyze the feature request, plan implementation, and create work item tickets.

This phase is the entry point for adding features to existing codebases. It:
1. Understands the feature request
2. Discovers relevant parts of the codebase (leveraging memories if available)
3. Breaks down the feature into logical work items
4. Creates ONE ticket per work item with blocking relationships
5. Creates ONE Phase 2 task per ticket (1:1 relationship)

Works for any type of existing software project.""",
    done_definitions=[
        "Feature request thoroughly analyzed and understood",
        "Existing codebase memories retrieved (if available from index_repo)",
        "If no memories: Quick codebase scan completed",
        "Tech stack and project structure understood",
        "Feature broken down into logical work items",
        "Implementation order and dependencies determined",
        "ONE ticket created per work item with proper blocked_by_ticket_ids",
        "ONE Phase 2 task created per ticket (1:1 relationship verified)",
        "All discoveries saved to memory for hive mind",
        "Task marked as done with summary of tickets and tasks created",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A FEATURE PLANNER - ANALYZE, PLAN, AND CREATE WORK ITEMS
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Analyze the feature, break it down, create tickets with blocking relationships

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES - READ BEFORE STARTING
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - that's just a placeholder in examples!
   Your actual agent ID is in your task context or environment.

1. **CHECK EXISTING MEMORIES FIRST**
   Before scanning the codebase, check if index_repo was run.
   If memories exist, USE THEM instead of re-scanning!

2. **ONE TICKET PER WORK ITEM**
   Break the feature into logical work items.
   Each work item gets its own ticket.
   DO NOT create one ticket for the entire feature!

3. **ONE TASK PER TICKET (1:1 RELATIONSHIP)**
   Every ticket MUST have a corresponding Phase 2 task.
   Every task MUST include "TICKET: ticket-xxxxx" in description.

4. **USE BLOCKING RELATIONSHIPS**
   If work item B depends on work item A, then ticket B must have:
   `blocked_by_ticket_ids: [ticket_A_id]`

5. **ONLY PHASE 3 RESOLVES TICKETS**
   Phase 1: Create tickets in 'backlog', NEVER resolve them

═══════════════════════════════════════════════════════════════════════

STEP 1: UNDERSTAND THE FEATURE REQUEST

Read the feature description in your task carefully:
- What functionality is being requested?
- What should the user experience be?
- Are there specific requirements or constraints?
- What is the expected behavior?

Save your understanding:

```python
save_memory(
    content="Feature request: [one-line summary of what's being built]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 2: DISCOVER THE CODEBASE

**FIRST: Check for existing memories from index_repo workflow!**

If memories exist about tech stack, components, and structure - USE THEM!

**IF no memories exist:** Do a quick codebase scan:

1. **Read overview files:** README.md, package.json / pyproject.toml
2. **Identify tech stack:** Languages, frameworks, database
3. **Map directory structure:** src/, lib/, tests/, frontend/, backend/
4. **Understand existing patterns:** How are similar features implemented?

Save discoveries:

```python
save_memory(
    content="Tech stack: Language=[X], Framework=[Y], Database=[Z]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="Feature [X] will integrate with: [list existing components]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 3: BREAK DOWN THE FEATURE INTO WORK ITEMS

**🚨 CRITICAL: DO NOT CREATE ONE TICKET FOR THE ENTIRE FEATURE! 🚨**

Break the feature into logical, independent work items:

**Common breakdown patterns:**

**For Backend Features:**
- Database models/migrations (if new tables needed)
- Backend service/business logic
- API endpoints
- Backend tests

**For Frontend Features:**
- UI components
- State management (if needed)
- API integration
- Frontend tests

**For Full-Stack Features:**
- Backend: Models + API (can be one or split)
- Frontend: Components + Integration
- Integration tests (end-to-end)

**Example breakdown for "Add user profiles":**
1. **Backend: Profile Model & API** - Create Profile model, migrations, CRUD endpoints
2. **Frontend: Profile Components** - Profile page, edit form, avatar upload (BLOCKED BY #1)
3. **Integration Tests** - E2E tests for profile workflows (BLOCKED BY #1 and #2)

**Example breakdown for "Add search functionality":**
1. **Backend: Search Service** - Search logic, indexing, query parsing
2. **Backend: Search API** - Search endpoints with filters/pagination (BLOCKED BY #1)
3. **Frontend: Search UI** - Search bar, results display, filters (BLOCKED BY #2)
4. **Tests: Search Integration** - E2E search tests (BLOCKED BY #3)

Document your breakdown:

```python
save_memory(
    content="Feature [X] work items: 1) [item1], 2) [item2], 3) [item3] with blocking: [describe]",
    agent_id="[YOUR AGENT ID]",
    memory_type="decision"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 4: DETERMINE IMPLEMENTATION ORDER AND BLOCKING

**🚨 MANDATORY: Plan blocking relationships BEFORE creating tickets! 🚨**

For each work item, determine:
- What does it depend on? (blocked_by)
- What depends on it? (blocks)

**Typical ordering:**
1. **Backend/Infrastructure first** (no blockers or minimal)
2. **Frontend depends on backend** (blocked by API work)
3. **Integration/Tests last** (blocked by implementation)

**Write out your blocking map:**

```markdown
## Blocking Relationships for [FEATURE]

1. **[Work Item 1: Backend Model/API]**
   - blocked_by_ticket_ids: [] (no blockers - start first)
   - BLOCKS: Frontend, Integration tests

2. **[Work Item 2: Frontend Components]**
   - blocked_by_ticket_ids: [work_item_1_id]
   - BLOCKS: Integration tests

3. **[Work Item 3: Integration Tests]**
   - blocked_by_ticket_ids: [work_item_1_id, work_item_2_id]
   - BLOCKS: Nothing (can complete after this)
```

═══════════════════════════════════════════════════════════════════════

STEP 5: CREATE TICKETS (ONE PER WORK ITEM)

**Create tickets IN ORDER (so you have IDs for blocking):**

1. First create tickets with NO blockers
2. Then create tickets that depend on those (using their IDs)
3. Save each ticket ID as you create it!

**Ticket template (use triple-quoted strings for proper markdown):**

```python
# Work Item 1: Backend (no blockers - create first)
backend_ticket = create_ticket(
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    title="Feature: [Feature Name] - Backend API",
    description=\"\"\"## Work Item: [Feature Name] Backend

### Purpose
[What this work item accomplishes - 1-2 sentences]

### Scope
- [Specific task 1]
- [Specific task 2]
- [Specific task 3]

### Files to Modify/Create
- `[path/to/file1]` - [what changes]
- `[path/to/file2]` - [what changes]

### Integration Points
- [How this connects to existing code]
- [What existing components it uses]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### Technical Notes
[Patterns to follow, constraints, existing code to reference, etc.]\"\"\",
    ticket_type="feature",
    priority="high",
    tags=["phase-2-pending", "backend"],
    blocked_by_ticket_ids=[]  # No blockers
)
backend_ticket_id = backend_ticket["ticket_id"]  # SAVE THIS!

# Work Item 2: Frontend (blocked by backend)
frontend_ticket = create_ticket(
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    title="Feature: [Feature Name] - Frontend",
    description=\"\"\"## Work Item: [Feature Name] Frontend

### Purpose
[What this work item accomplishes - 1-2 sentences]

### Scope
- [Specific task 1]
- [Specific task 2]

### Dependencies
- Requires backend API to be complete (blocked by ticket above)

### Files to Modify/Create
- `[path/to/file1]` - [what changes]
- `[path/to/file2]` - [what changes]

### Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

### Technical Notes
[UI patterns to follow, existing components to reference, etc.]\"\"\",
    ticket_type="feature",
    priority="medium",
    tags=["phase-2-pending", "frontend"],
    blocked_by_ticket_ids=[backend_ticket_id]  # BLOCKED BY BACKEND!
)
frontend_ticket_id = frontend_ticket["ticket_id"]  # SAVE THIS!

# Work Item 3: Tests (blocked by both)
tests_ticket = create_ticket(
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    title="Feature: [Feature Name] - Integration Tests",
    description=\"\"\"## Work Item: [Feature Name] Integration Tests

### Purpose
End-to-end tests for the complete feature

### Scope
- [Test scenario 1]
- [Test scenario 2]

### Dependencies
- Requires backend AND frontend complete

### Test Cases
- [ ] [Test case 1 - description]
- [ ] [Test case 2 - description]
- [ ] [Test case 3 - description]

### Test Setup
[Any setup needed, test data, environment requirements]\"\"\",
    ticket_type="feature",
    priority="medium",
    tags=["phase-2-pending", "tests"],
    blocked_by_ticket_ids=[backend_ticket_id, frontend_ticket_id]  # BLOCKED BY BOTH!
)
tests_ticket_id = tests_ticket["ticket_id"]
```

═══════════════════════════════════════════════════════════════════════

STEP 6: CREATE PHASE 2 TASKS (ONE PER TICKET - 1:1)

**🚨 CRITICAL: Every ticket MUST have exactly ONE Phase 2 task! 🚨**

Create tasks IN THE SAME ORDER as tickets:

```python
# Task for Backend Ticket
create_task(
    description=f"Phase 2: Implement [Feature] Backend - TICKET: {backend_ticket_id}. Implement backend logic and API endpoints. Follow existing patterns. See ticket for full requirements.",
    done_definition=f"Backend implemented with tests. Ticket {backend_ticket_id} moved to 'implemented'. Phase 3 validation task created.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=2,
    priority="high",
    ticket_id=backend_ticket_id  # Link to ticket!
)

# Task for Frontend Ticket
create_task(
    description=f"Phase 2: Implement [Feature] Frontend - TICKET: {frontend_ticket_id}. Implement UI components. Blocked by backend. See ticket for full requirements.",
    done_definition=f"Frontend implemented with tests. Ticket {frontend_ticket_id} moved to 'implemented'. Phase 3 validation task created.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=2,
    priority="medium",
    ticket_id=frontend_ticket_id
)

# Task for Tests Ticket
create_task(
    description=f"Phase 2: Implement [Feature] Integration Tests - TICKET: {tests_ticket_id}. Write E2E tests. Blocked by backend and frontend. See ticket for test cases.",
    done_definition=f"Integration tests implemented and passing. Ticket {tests_ticket_id} moved to 'implemented'. Phase 3 validation task created.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=2,
    priority="medium",
    ticket_id=tests_ticket_id
)
```

═══════════════════════════════════════════════════════════════════════

STEP 7: VERIFY 1:1 RELATIONSHIP (MANDATORY!)

**Before marking your task done, VERIFY:**

```python
# Count tickets created
tickets_created = [
    backend_ticket_id,
    frontend_ticket_id,
    tests_ticket_id,
    # ... list ALL ticket IDs
]
total_tickets = len(tickets_created)

# Count tasks created
tasks_created = [
    # List task IDs or just count
]
total_tasks = len(tasks_created)

# VERIFY
if total_tickets != total_tasks:
    print(f"❌ ERROR: {total_tickets} tickets but {total_tasks} tasks!")
    print("GO BACK AND CREATE MISSING TASKS!")
    # DO NOT PROCEED
else:
    print(f"✅ VERIFIED: {total_tickets} tickets = {total_tasks} tasks")
    # Proceed to mark done
```

═══════════════════════════════════════════════════════════════════════

STEP 8: MARK YOUR TASK AS DONE

**Only after verification passes:**

```python
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary=f"Feature analysis complete. Broke down [feature] into {total_tickets} work items. Created {total_tickets} tickets with blocking relationships and {total_tasks} Phase 2 tasks. VERIFIED 1:1 relationship. Work items: [list items]."
)
```

═══════════════════════════════════════════════════════════════════════
EXAMPLES OF GOOD VS BAD BREAKDOWNS
═══════════════════════════════════════════════════════════════════════

**❌ BAD (One ticket for everything):**
- Ticket: "Add user profiles feature" (everything in one)
- Result: Too big, no blocking, hard to parallelize

**✅ GOOD (Multiple tickets with blocking):**
- Ticket 1: "Feature: User Profiles - Backend API" (no blockers)
- Ticket 2: "Feature: User Profiles - Frontend" (blocked by #1)
- Ticket 3: "Feature: User Profiles - Integration Tests" (blocked by #1, #2)

**❌ BAD (Too granular):**
- Ticket 1: "Create User model"
- Ticket 2: "Create get_user endpoint"
- Ticket 3: "Create update_user endpoint"
- Result: Too many tiny tickets, hard to manage

**✅ GOOD (Logical grouping):**
- Ticket 1: "Feature: User Profiles - Backend" (model + all endpoints)
- Result: Logical unit of work, manageable scope

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Check for existing memories FIRST
- Break feature into 2-5 logical work items
- Create ONE ticket per work item
- Use blocked_by_ticket_ids for dependencies
- Create ONE task per ticket (1:1)
- Verify 1:1 relationship before marking done
- Save discoveries to memory

❌ DO NOT:
- Create one ticket for the entire feature
- Create tasks without "TICKET: xxx" in descriptions
- Skip blocking relationships
- Create more tasks than tickets (or vice versa)
- Mark done without verifying 1:1 relationship
- Resolve tickets (ONLY Phase 3 can!)

═══════════════════════════════════════════════════════════════════════
ADDITIONAL CONTEXT FROM USER
═══════════════════════════════════════════════════════════════════════

{feature_description}

**Target Area (if specified):** {target_area}

**Additional Context:** {additional_context}

Use this context to guide your analysis and breakdown.
""",
    outputs=[
        "Feature request analysis saved to memory",
        "Codebase structure understanding (from memories or quick scan)",
        "Feature broken down into logical work items",
        "ONE ticket per work item with blocking relationships",
        "ONE Phase 2 task per ticket (1:1 verified)",
        "Implementation order enforced via blocking",
    ],
    next_steps=[
        "Phase 2 agents will implement each work item",
        "Blocked tickets wait for their blockers to complete",
        "Each Phase 2 task creates a Phase 3 validation task",
        "Phase 3 validates and resolves individual tickets",
    ],
)
