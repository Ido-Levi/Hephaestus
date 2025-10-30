# Ticket Tracking: Kanban for AI Agents

Here's the thing about multi-agent workflows: when you have multiple agents building different components in parallel, they need a way to coordinate. Which work is blocked? What's currently being built? Who's working on what?

That's where the ticket tracking system comes in.

## What Tickets Actually Are

Think of tickets as **work items with memory**. Unlike tasks (which agents execute and complete), tickets are persistent records that agents create, move through status columns, comment on, and eventually resolve.

A ticket for "Build Authentication System" might live for days as it moves through your workflow:
- Phase 1 agent creates the ticket
- Phase 2 agent moves it to "Building" status and starts implementing
- Phase 2 agent leaves comments about progress
- Phase 2 agent moves it to "Built" when done
- Phase 3 agent moves it to "Testing" and runs tests
- Phase 3 agent resolves it when everything passes

All that history — the comments, status changes, which agents touched it, what commits happened — stays attached to the ticket.

## The Kanban Board

Here's what the Kanban board looks like in action:

![Kanban Board](/img/kanban_board.png)

Your workflow defines columns that match your process. Common patterns:

**Simple**: Backlog → Building → Testing → Done

**Detailed**: Backlog → Building → Building Done → Validating → Validating Done → Done

Agents move tickets through columns as work progresses. The board gives you real-time visibility into:
- Which components are being worked on
- Which components are blocked
- Which agents are assigned to what
- Which phase each component is in

## Blocking Relationships

The most powerful feature: tickets can block other tickets.

Say you're building a web app. The authentication system depends on the database schema. The API endpoints depend on authentication. You set up blocking relationships:

```
Database Schema (no blockers) → starts immediately
   ↓ blocks
Auth System (blocked by database) → waits
   ↓ blocks
API Endpoints (blocked by auth) → waits
```

When Database Schema is resolved, Auth System automatically unblocks. When Auth System is resolved, API Endpoints unblocks.

Here's what that looks like in the UI:

![Ticket Blocking Graph](/img/tickets_interaction.png)

The graph shows the entire dependency tree. Infrastructure tickets at the top (no blockers) can start immediately. Component tickets in the middle wait for infrastructure. Service tickets at the bottom wait for components.

When you resolve a ticket, the system automatically unblocks everything that was waiting on it.

## How Agents Use Tickets with Phases

The pattern that works best: **Phase 1 creates tickets, later phases consume them**.

### Phase 1: Creating the Structure

Your Phase 1 agent reads the requirements and identifies components. For each component, it creates a ticket:

```yaml
# Phase 1 Instructions
additional_notes: |
  After analyzing the requirements, create tickets for each component.

  For each component you identify:
  1. Search for existing tickets first (avoid duplicates!)
     search_tickets(query="component name", search_type="hybrid")

  2. Create ticket with dependencies:
     create_ticket({
         "title": "Build Authentication System",
         "description": "Implement JWT auth with login/register/refresh",
         "ticket_type": "component",
         "blocked_by_ticket_ids": [infrastructure_ticket_id]
     })

  3. Create Phase 2 task linking to the ticket:
     create_task({
         "description": "Phase 2: Build Auth System - TICKET: ticket-xxx",
         "phase_id": 2,
         "ticket_id": "ticket-xxx"
     })
```

The Phase 1 agent spawns multiple Phase 2 tasks, each linked to a ticket. Some tickets have blockers (must wait), some don't (can start immediately).

### Phase 2: Building Components

Phase 2 agents work on their assigned tickets. Your phase instructions tell them to move tickets through the board:

```yaml
# Phase 2 Instructions
additional_notes: |
  You're building a component. Extract your ticket ID from the task description.

  STEP 1: Move ticket to 'building' status
  change_ticket_status(
      ticket_id="your-ticket-id",
      new_status="building",
      comment="Starting implementation"
  )

  STEP 2: Build the component
  [do the implementation work]

  STEP 3: Leave progress comments as you work
  add_ticket_comment(
      ticket_id="your-ticket-id",
      comment_text="Completed token generation, working on validation middleware next"
  )

  STEP 4: Move to 'building-done' when implementation complete
  change_ticket_status(
      new_status="building-done",
      comment="Implementation complete. JWT generation, validation, and refresh all working. 8 test cases added."
  )

  STEP 5: Create Phase 3 testing task
  create_task({
      "description": "Phase 3: Test Auth System - TICKET: your-ticket-id",
      "phase_id": 3,
      "ticket_id": "your-ticket-id"
  })
```

The agent moves the ticket from Backlog → Building → Building Done, leaving a trail of comments showing progress.

### Phase 3: Testing and Resolution

Phase 3 agents test components and either resolve tickets or send them back for fixes:

```yaml
# Phase 3 Instructions
additional_notes: |
  You're testing a component. Extract your ticket ID from the task description.

  STEP 1: Move ticket to 'testing'
  change_ticket_status(new_status="testing")

  STEP 2: Run comprehensive tests
  [run tests]

  STEP 3a: If ALL tests pass:
  - Resolve the ticket:
    resolve_ticket(
        ticket_id="your-ticket-id",
        resolution_comment="All tests pass. Verified: login flow, token refresh, error handling. 12/12 tests passing."
    )
  - This automatically unblocks any tickets blocked by this one!

  STEP 3b: If tests fail:
  - Add comment with failure details
  - Create Phase 2 bug-fix task:
    create_task({
        "description": "Phase 2: Fix bugs in Auth - TICKET: your-ticket-id. Token refresh failing with expired tokens.",
        "phase_id": 2,
        "ticket_id": "your-ticket-id"
    })
```

When a ticket is resolved, any tickets blocked by it automatically become available for agents to work on. The dependency chain flows naturally.

## Board Configuration

You define your board structure in the workflow config:

```python
from src.sdk.models import WorkflowConfig

config = WorkflowConfig(
    enable_tickets=True,
    board_config={
        "columns": [
            {"id": "backlog", "name": "📋 Backlog"},
            {"id": "building", "name": "🔨 Building"},
            {"id": "building-done", "name": "✅ Built"},
            {"id": "testing", "name": "🧪 Testing"},
            {"id": "testing-done", "name": "✅ Tested"},
            {"id": "done", "name": "✅ Done"}
        ],
        "ticket_types": ["component", "bug", "feature"],
        "initial_status": "backlog"
    }
)
```

Map columns to your phases:
- **Phase 1** creates tickets in Backlog
- **Phase 2** moves tickets: Backlog → Building → Building Done
- **Phase 3** moves tickets: Building Done → Testing → Testing Done → Done

## Task-Ticket Linking Format

Critical: every task description must reference its ticket with a specific format:

**"Phase X: Description - TICKET: ticket-xxx"**

Example:
```
Phase 2: Build Authentication System - TICKET: ticket-auth-456. Implement JWT token generation, validation, and refresh endpoints with comprehensive tests.
```

Why this matters:
- **Traceability** - Know which agent is working on which ticket
- **Guardian validation** - Guardian can verify agents follow the format
- **Commit linking** - System auto-links git commits to tickets
- **Progress tracking** - See active work on each ticket

## Comments: The Communication Layer

Tickets accumulate comments as agents work. This creates a living history of the work:

```
Agent A (2 hours ago): Starting implementation. Setting up JWT library and token generation logic.

Agent A (1 hour ago): Token generation working. Moving on to validation middleware.

Agent A (30 min ago): Blocked: Need database schema for user table before implementing login. Creating task for database team.

Agent B (15 min ago): Database schema complete. User table available. Unblocking auth work.

Agent A (5 min ago): Login endpoint implemented and tested. All functionality complete.
```

Agents leave comments when:
- Starting work on a component
- Hitting blockers
- Making significant progress
- Completing work
- Discovering issues

Use `add_ticket_comment()` to document progress and communicate with other agents working on related tickets.

## Searching Before Creating

Always search before creating tickets to avoid duplicates:

```yaml
# In Phase 1 instructions:
additional_notes: |
  Before creating a ticket:

  STEP 1: Search for existing tickets
  results = search_tickets(
      query="authentication JWT login",
      search_type="hybrid"  # 70% semantic + 30% keyword
  )

  STEP 2: Review results
  If similar ticket exists → Reference it instead of creating duplicate
  If no similar ticket → Create new one

  STEP 3: Create ticket only if needed
```

The search uses hybrid semantic + keyword search, so it finds conceptually similar tickets even if they use different wording.

## The Dependency Patterns

### Pattern 1: Fan-Out from Foundation

```
Infrastructure (no blockers)
   ↓ blocks
Database, Auth, Workers (all parallel after infra)
```

One foundational ticket blocks multiple component tickets. When foundation completes, all components unblock simultaneously and agents work in parallel.

### Pattern 2: Sequential Chain

```
Infrastructure → Database → Auth → API
```

Each ticket blocks the next. Work happens sequentially.

### Pattern 3: Hierarchical Tree

```
Infrastructure (no blockers)
   ↓
Database (blocked by infra)
   ↓
Auth, API (both blocked by database)
   ↓
Frontend (blocked by both auth AND api)
```

Complex dependencies with multiple levels. The graph visualization makes this clear.

## Why Tickets + Phases Work

Phases define **how to do the work** (instructions for agents).

Tickets track **what work to do** (components with dependencies).

Together, they create structured parallelism:
- Phase 1 identifies work and creates tickets with dependencies
- Phase 2 agents work on unblocked tickets in parallel
- Phase 3 agents test and resolve tickets
- Resolving tickets automatically unblocks dependent work

The Kanban board shows real-time progress. Guardian validates agents move tickets correctly. Comments capture the story of how work progressed.

## Viewing the Board

**Web UI**: `http://localhost:3000`
- Kanban Board tab shows ticket columns
- Graph tab shows dependency visualization
- Search tab finds specific tickets
- Statistics tab shows workflow metrics

**API Access**:
- `GET /api/tickets?workflow_id=xxx` - List tickets
- `GET /api/tickets/{ticket_id}` - Ticket details
- `GET /api/tickets/{ticket_id}/graph` - Dependency graph

## The Result

With ticket tracking, your workflows coordinate automatically:
- Agents know what to work on (unblocked tickets)
- Agents know what to wait for (blocked tickets)
- Agents communicate through comments
- Dependencies flow naturally through blocking relationships
- Visual progress tracking shows workflow state
- History persists (who did what, when, why)

Design clear phases. Configure your board. Tell agents to create tickets, move them through columns, and leave comments. The coordination happens naturally.

---

## Related Documentation

- [Phases System](phases-system.md) - How phases work and branch dynamically
- [Best Practices](best-practices.md) - Designing interconnected workflows
- [Guardian Monitoring](guardian-monitoring.md) - How Guardian keeps workflows on track
