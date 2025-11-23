# Index Repository Workflow

A knowledge extraction workflow that scans a codebase and builds comprehensive memories for other workflows to use.

## Overview

This workflow is designed to run **before** other workflows (bug fix, feature development) to give agents rich context about a codebase. It creates memories about:

- Project purpose and goals
- Tech stack (languages, frameworks, tools)
- Directory structure and organization
- Components and their responsibilities
- Code patterns and conventions
- How to run and test different parts
- Integration points between components
- Gotchas and potential issues

## Phases

### Phase 1: Initial Scan

The entry point. Scans the repository at a high level to understand what it is and discover logical components.

**What it does:**
1. Reads README, docs, and config files
2. Identifies the project purpose and tech stack
3. Maps the directory structure
4. Discovers logical components (services, domains, architectural layers)
5. Saves high-level memories
6. Creates a ticket for each component (in "discovered" status)
7. Creates Phase 2 tasks for each ticket

**What is a "component"?**

A component is a LOGICAL SERVICE or DOMAIN - not individual files!

| Good Components | Bad Components |
|----------------|----------------|
| Authentication Service | `LoginButton.tsx` |
| API Layer | `userRoutes.ts` |
| Database Layer | `User.ts` model |
| Frontend Application | Individual React components |
| Order Processing | `validateOrder.ts` |

The number depends on the repo - small repos might have 2-3, large repos might have dozens.

**Outputs:**
- Memories about project overview
- Memories about tech stack
- Memories about structure
- Tickets for each logical component
- Phase 2 tasks (one per ticket)

### Phase 2: Component Deep Dive

Runs **in parallel** for each component discovered in Phase 1. Thoroughly explores one component.

**What it does:**
1. Reads all code files in the component
2. Understands the component's purpose and responsibilities
3. Identifies key classes, functions, and interfaces
4. Discovers code patterns and conventions
5. Finds how to run and test the component
6. Maps integration points with other components
7. Captures insights and gotchas
8. Saves detailed memories

**Outputs:**
- 10-20+ granular memories per component

## Usage

### From UI

1. Go to the Workflow Executions page
2. Click "Launch Workflow"
3. Select "Index Repository"
4. Optionally add context about the repo
5. Launch!

### Programmatic

```python
from example_workflows.index_repo.phases import (
    INDEX_REPO_PHASES,
    INDEX_REPO_CONFIG,
    INDEX_REPO_LAUNCH_TEMPLATE,
)
from src.sdk import HephaestusSDK
from src.sdk.models import WorkflowDefinition

index_repo_definition = WorkflowDefinition(
    id="index-repo",
    name="Index Repository",
    phases=INDEX_REPO_PHASES,
    config=INDEX_REPO_CONFIG,
    description="Scan and index a repository to build codebase knowledge",
    launch_template=INDEX_REPO_LAUNCH_TEMPLATE,
)

sdk = HephaestusSDK(
    workflow_definitions=[index_repo_definition],
    working_directory="/path/to/repo",
    # ... other config
)
```

## Configuration

### Launch Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repo_context` | textarea | No | Optional context about the repo to help guide exploration |

### Workflow Config

```python
INDEX_REPO_CONFIG = WorkflowConfig(
    has_result=False,     # No final deliverable - memories ARE the output
    enable_tickets=True,  # Track components on Kanban board
    board_config={
        "columns": [
            {"id": "discovered", "name": "🔍 Discovered", "order": 1},
            {"id": "exploring", "name": "🔬 Exploring", "order": 2},
            {"id": "indexed", "name": "✅ Indexed", "order": 3},
        ],
        "ticket_types": ["component", "area"],
        "default_ticket_type": "component",
        "initial_status": "discovered",
    },
)
```

### Kanban Board

The workflow uses a simple 3-column board to track component exploration:

| Column | Purpose |
|--------|---------|
| 🔍 Discovered | Components found in Phase 1, waiting to be explored |
| 🔬 Exploring | Phase 2 agent is currently deep-diving this component |
| ✅ Indexed | Exploration complete, memories saved |

## Example Flow

```
User launches "Index Repository" workflow
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 1: Initial Scan              │
│  - Reads README, docs               │
│  - Identifies tech stack            │
│  - Discovers 5 components           │
│  - Creates 5 tickets (Discovered)   │
│  - Creates 5 Phase 2 tasks          │
│  - Saves 8 high-level memories      │
└─────────────────────────────────────┘
         │
         ▼ (spawns 5 parallel tasks)
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ P2:Auth │ P2:API  │ P2:DB   │ P2:Core │ P2:Utils│
│ 15 mem  │ 12 mem  │ 10 mem  │ 18 mem  │ 8 mem   │
│ ticket→ │ ticket→ │ ticket→ │ ticket→ │ ticket→ │
│ indexed │ indexed │ indexed │ indexed │ indexed │
└─────────┴─────────┴─────────┴─────────┴─────────┘
         │
         ▼
    Workflow Complete
    63 memories saved
    5 tickets resolved
```

### Kanban Board Mid-Workflow

```
┌─────────────────┬─────────────────┬─────────────────┐
│  🔍 Discovered  │  🔬 Exploring   │  ✅ Indexed     │
├─────────────────┼─────────────────┼─────────────────┤
│  frontend       │  auth           │  database       │
│  utils          │  api            │  core           │
│                 │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
```

## Memory Types Used

| Type | Purpose | Example |
|------|---------|---------|
| `codebase_knowledge` | Structure, components, how things work | "Auth entry point: src/auth/__init__.py" |
| `discovery` | Interesting insights, patterns | "Auth uses a clever token refresh mechanism" |
| `decision` | Architecture decisions found | "Chose SQLite for simplicity per README" |
| `warning` | Gotchas, issues, things to avoid | "Auth: Token refresh requires OLD token in header" |

## Benefits for Other Workflows

After running Index Repository:

### Bug Fix Workflow
- Agents can retrieve memories about where components are
- Know how to run tests for affected components
- Understand integration points that might be affected

### Feature Development Workflow
- Agents understand existing patterns to follow
- Know the tech stack and conventions
- Can find related code quickly

### PRD to Software Workflow
- Understands existing infrastructure
- Can build on top of existing components
- Follows established patterns

## Best Practices

1. **Run on new codebases first** - Index before trying to fix bugs or add features
2. **Re-run after major changes** - Keep memories up to date
3. **Provide context** - If you know something about the repo, add it to help focus exploration
4. **Check memory count** - A well-indexed repo should have 50+ memories

## Differences from Other Workflows

| Aspect | PRD Workflow | Bug Fix | Index Repo |
|--------|-------------|---------|------------|
| Goal | Build software | Fix bugs | Extract knowledge |
| Result | Final deliverable | Patch/fix | No result (memories) |
| Tickets | Yes (6 columns) | Optional | Yes (3 columns) |
| Phases | 3 | 3 | 2 |
| Output | Code, tests, docs | Fixed code | Memories only |
| Board flow | backlog→building→validating→done | varies | discovered→exploring→indexed |
