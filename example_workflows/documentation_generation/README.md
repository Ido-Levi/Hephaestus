# Documentation Generation Workflow

A workflow for generating comprehensive documentation for existing codebases. Discovers what to document, checks existing docs, and creates/updates markdown documentation.

## Overview

This workflow creates documentation for any existing project. It:

1. **Discovers what to document** - Based on user request (everything or specific areas)
2. **Checks existing documentation** - Updates rather than overwrites
3. **Generates documentation in parallel** - One agent per documentation area
4. **Creates a docs/ folder** - All documentation in one place

Key principles:
- **Component-based** - Group related docs logically
- **Update-friendly** - Preserve existing good content
- **Leverage memories** - Uses index_repo data if available
- **1:1 ticket-to-task** - Every ticket has exactly one Phase 2 task

## Phases

### Phase 1: Documentation Discovery

The entry point. Analyzes the codebase and documentation request, then creates tickets for each documentation area.

**What it does:**
1. Understands the documentation request ("everything" vs specific)
2. Checks for existing codebase memories (from index_repo)
3. Scans docs/ folder for existing documentation
4. Identifies documentation areas to create/update
5. Creates ONE ticket per documentation area
6. Creates ONE Phase 2 task per ticket (1:1)
7. Verifies 1:1 relationship before marking done

**Documentation Areas (for "everything" requests):**

| Area | Target File | Content |
|------|-------------|---------|
| Overview | `docs/README.md` | Project summary, features, quick start |
| Getting Started | `docs/getting-started.md` | Installation, setup, first steps |
| Architecture | `docs/architecture.md` | System design, components, data flow |
| API Reference | `docs/api-reference.md` | Endpoints, parameters, responses |
| Configuration | `docs/configuration.md` | Config options, environment variables |
| Contributing | `docs/contributing.md` | Development setup, PR process |

**Outputs:**
- Multiple tickets (one per documentation area)
- Multiple Phase 2 tasks (one per ticket)
- Documentation plan saved to memory

### Phase 2: Documentation Generation

Generates documentation for ONE area from a single ticket. Multiple Phase 2 tasks run in parallel.

**What it does:**
1. Reads ticket to understand documentation scope
2. Checks if docs file already exists (UPDATE if so!)
3. Analyzes relevant code (uses memories if available)
4. Generates comprehensive markdown documentation
5. Updates docs/README.md index if needed
6. Resolves ticket when documentation is complete

**Key rule:** Each Phase 2 agent handles ONE ticket, creates ONE docs file.

**Outputs:**
- Documentation file created/updated in docs/
- docs/README.md index updated (if applicable)
- Ticket resolved

## Kanban Board

Simple 3-column board tracking documentation progress:

| Column | Status | Purpose |
|--------|--------|---------|
| 📋 To Document | to_document | Documentation area identified |
| ✍️ Documenting | documenting | Phase 2 writing documentation |
| ✅ Done | done | Documentation complete, ticket resolved |

## Example Flow

```
User requests: "Document everything"
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 1: Documentation Discovery   │
│  - Checks existing memories         │
│  - Scans docs/ folder              │
│  - Identifies 5 documentation areas │
│  - Creates 5 tickets               │
│  - Creates 5 Phase 2 tasks         │
└─────────────────────────────────────┘
         │
         ▼ Creates tickets:
┌─────────────────────────────────────┐
│ Ticket 1: Overview (docs/README.md) │
│ Ticket 2: Getting Started           │
│ Ticket 3: Architecture              │
│ Ticket 4: API Reference             │
│ Ticket 5: Configuration             │
└─────────────────────────────────────┘
         │
         ▼ Phase 2 tasks run in PARALLEL:
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ P2:     │ P2:     │ P2:     │ P2:     │ P2:     │
│ Overview│ Getting │ Arch    │ API     │ Config  │
│         │ Started │         │         │         │
└────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘
     │         │         │         │         │
     ▼         ▼         ▼         ▼         ▼
   docs/     docs/     docs/     docs/     docs/
   README    getting-  arch.md   api.md    config.md
   .md       started
             .md
         │
         ▼
    Documentation Complete!
    All tickets resolved
```

## Ticket Lifecycle

```
to_document → documenting → done
     │             │          │
     │             │          └── Ticket resolved, docs created
     │             │
     │             └── Phase 2 writing documentation
     │
     └── Initial status (Phase 1 created)
```

## Documentation Structure

All documentation goes in the `docs/` folder:

```
docs/
├── README.md           # Index/overview (links to all docs)
├── getting-started.md  # Installation and setup
├── architecture.md     # System design
├── api-reference.md    # API documentation
├── configuration.md    # Config options
├── contributing.md     # Development guide
└── [component].md      # Component-specific docs
```

## Best Practices

### 1. Run index_repo First (Recommended)

For best results, run the "Index Repository" workflow before Documentation Generation:

```
Index Repository → Documentation Generation
```

This gives Phase 1 and Phase 2 rich context about the codebase via memories.

### 2. Specific vs Everything

**"Everything" request:**
- Creates comprehensive documentation suite
- 5-7 documentation tickets
- Good for projects with no/minimal docs

**Specific request (e.g., "API endpoints"):**
- Focuses on just that area
- 1-3 tickets
- Good for filling gaps or updating specific areas

### 3. Update Existing Docs

The workflow checks for existing documentation:
- **If exists:** Updates and preserves good content
- **If missing:** Creates from scratch

This prevents losing existing documentation.

### 4. Target Audience

Specify who will read the docs:
- **developers** - Technical depth, code examples
- **end-users** - Usage focused, less technical
- **administrators** - Deployment, configuration
- **contributors** - Development setup, PR process
- **all** - Balance of all audiences

## Differences from Other Workflows

| Aspect | Index Repo | Documentation Generation |
|--------|-----------|-------------------------|
| Output | Memories (internal) | Markdown files (external) |
| Purpose | AI context | Human reading |
| Phases | 2 | 2 |
| Location | Qdrant DB | docs/ folder |
| Reusability | Other workflows use it | Standalone documentation |

## Workflow Integration

Documentation Generation works well with other workflows:

1. **After Index Repo**: Leverage indexed memories for better docs
2. **After Feature Dev**: Document new features
3. **Standalone**: Generate docs for any existing project

## Example Requests

**Full documentation:**
```
Documentation Scope: "Generate complete documentation for this project.
Include overview, getting started, architecture, and API reference."

Target Audience: developers
```

**Specific area:**
```
Documentation Scope: "Document the authentication system - how it works,
how to configure it, and how to extend it."

Target Audience: developers
```

**User-focused:**
```
Documentation Scope: "Create end-user documentation for the CLI tool.
Cover installation, basic usage, and common commands."

Target Audience: end-users
```
