# Feature Development Workflow

A workflow for adding features to existing codebases. Breaks features into work items, creates tickets with blocking relationships, and implements them in parallel.

## Overview

This workflow is designed for **adding features to existing projects** - not for greenfield development. It:

1. **Breaks features into work items** - Backend, frontend, tests, etc.
2. **Creates blocking relationships** - Frontend blocked by backend, tests blocked by implementation
3. **Runs work items in parallel** - Independent work items proceed simultaneously
4. **Validates each work item** - Tests and regression checks before completing

Key principles:
- **Respect existing patterns** - Follow the codebase's conventions
- **Proper planning** - Break down into logical work items with dependencies
- **Regression testing** - Never break existing functionality
- **1:1 ticket-to-task** - Every ticket has exactly one Phase 2 task

## Phases

### Phase 1: Feature Analysis & Planning

The entry point. Analyzes the feature request, breaks it into work items, and creates tickets with blocking relationships.

**What it does:**
1. Understands the feature request
2. Checks for existing codebase memories (from index_repo)
3. Breaks feature into 2-5 logical work items
4. Determines implementation order and blocking
5. Creates ONE ticket per work item with `blocked_by_ticket_ids`
6. Creates ONE Phase 2 task per ticket (1:1)
7. Verifies 1:1 relationship before marking done

**Work Item Breakdown Examples:**

| Feature | Work Items |
|---------|-----------|
| User Profiles | Backend API (no blockers) → Frontend (blocked by backend) → Tests (blocked by both) |
| Search | Search Service → Search API (blocked by service) → Search UI (blocked by API) → Tests |
| Auth | Auth Backend → Auth Frontend (blocked) → E2E Tests (blocked by both) |

**Outputs:**
- Multiple tickets (one per work item) with blocking relationships
- Multiple Phase 2 tasks (one per ticket)
- Implementation order enforced via blocking

### Phase 2: Design & Implementation

Implements ONE work item from a single ticket. Multiple Phase 2 tasks run in parallel for independent work items.

**What it does:**
1. Reads ticket to understand specific work item scope
2. Studies existing code patterns
3. Implements the work item following existing patterns
4. Adds tests for the work item
5. Creates ONE Phase 3 validation task

**Key rule:** Each Phase 2 agent handles ONE ticket, not the entire feature.

**Outputs:**
- Work item implementation
- Tests for the work item
- Ticket moved to "implemented"
- Phase 3 task created

### Phase 3: Validate & Complete

Validates ONE work item and resolves its ticket. Multiple Phase 3 tasks run in parallel.

**What it does:**
1. Runs tests for the work item
2. Checks for regressions in related areas
3. Fixes bugs via Task tool
4. Resolves ticket when validation passes

**Key rule:** Each Phase 3 agent validates ONE ticket, then resolves it.

**Outputs:**
- Tests run and passing
- Regressions checked
- Ticket resolved and moved to "done"

## Kanban Board

5-column board tracking work item progress:

| Column | Status | Purpose |
|--------|--------|---------|
| 📋 Backlog | backlog | Work item created, not started |
| 🔨 Implementing | implementing | Phase 2 building the work item |
| ✅ Implemented | implemented | Phase 2 complete, ready for validation |
| 🧪 Testing | testing | Phase 3 validating the work item |
| 🎉 Done | done | Work item complete, ticket resolved |

## Example Flow

```
User requests: "Add user profile feature"
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 1: Feature Analysis          │
│  - Breaks into 3 work items         │
│  - Creates 3 tickets with blocking  │
│  - Creates 3 Phase 2 tasks          │
└─────────────────────────────────────┘
         │
         ▼ Creates tickets:
┌─────────────────────────────────────┐
│ Ticket 1: Backend API (no blockers) │
│ Ticket 2: Frontend (blocked by #1)  │
│ Ticket 3: Tests (blocked by #1, #2) │
└─────────────────────────────────────┘
         │
         ▼ Phase 2 tasks (parallel where possible):
┌─────────────────┐
│ P2: Backend API │ ← Starts immediately (no blockers)
│ (Ticket 1)      │
└────────┬────────┘
         │ completes, unblocks Ticket 2
         ▼
┌─────────────────┐
│ P2: Frontend    │ ← Starts when backend done
│ (Ticket 2)      │
└────────┬────────┘
         │ completes, unblocks Ticket 3
         ▼
┌─────────────────┐
│ P2: Tests       │ ← Starts when both done
│ (Ticket 3)      │
└─────────────────┘
         │
         ▼ Phase 3 tasks (validate each):
┌─────────┬─────────┬─────────┐
│ P3: API │ P3: FE  │ P3:Tests│
│ Resolve │ Resolve │ Resolve │
│ Ticket1 │ Ticket2 │ Ticket3 │
└─────────┴─────────┴─────────┘
         │
         ▼
    Feature Complete!
    All tickets resolved
```

## Ticket Lifecycle

```
backlog → implementing → implemented → testing → done
   │           │              │           │        │
   │           │              │           │        └── Ticket resolved
   │           │              │           │
   │           │              │           └── Phase 3 validating
   │           │              │
   │           │              └── Phase 2 complete
   │           │
   │           └── Phase 2 working
   │
   └── Initial status (may be blocked)

If bugs found in testing:
testing → implementing (back to Phase 2 for fixes)
```

## Blocking Relationships

```
┌─────────────────┐
│ Backend Work    │ ← No blockers (starts first)
│ blocked_by: []  │
└────────┬────────┘
         │ blocks
         ▼
┌─────────────────┐
│ Frontend Work   │ ← Blocked by backend
│ blocked_by:     │
│ [backend_id]    │
└────────┬────────┘
         │ blocks
         ▼
┌─────────────────┐
│ Integration     │ ← Blocked by both
│ Tests           │
│ blocked_by:     │
│ [backend_id,    │
│  frontend_id]   │
└─────────────────┘
```

## Best Practices

### 1. Run index_repo First (Recommended)

For best results, run the "Index Repository" workflow before Feature Development:

```
Index Repository → Feature Development
```

This gives Phase 1 rich context about the codebase via memories.

### 2. Good Work Item Breakdown

**✅ Good (logical groupings):**
- "Feature: Profiles - Backend API" (models + endpoints together)
- "Feature: Profiles - Frontend" (components + pages together)
- "Feature: Profiles - Tests" (integration tests)

**❌ Bad (too granular):**
- "Create User model"
- "Create get_user endpoint"
- "Create ProfilePage component"

**❌ Bad (too broad):**
- "Add user profiles" (one ticket for everything)

### 3. Respect Blocking

- Backend typically has no blockers
- Frontend is blocked by backend (needs API)
- Tests are blocked by implementation

## Differences from Other Workflows

| Aspect | PRD Workflow | Feature Development |
|--------|-------------|---------------------|
| Starting point | PRD document | Feature request |
| Codebase | Empty/new | Existing |
| Ticket count | Many (6+ columns) | 2-5 per feature |
| Board columns | 6 | 5 |
| Focus | Build from scratch | Integrate with existing |
| Regression testing | N/A | CRITICAL |

## Workflow Integration

Feature Development works well with other workflows:

1. **After Index Repo**: Use indexed memories for faster analysis
2. **Before Bug Fix**: Feature may introduce bugs that need fixing
3. **With PRD**: Use PRD for new projects, Feature Dev for additions
