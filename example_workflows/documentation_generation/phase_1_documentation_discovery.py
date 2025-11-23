"""
Phase 1: Documentation Discovery

Entry point for the Documentation Generation workflow. Analyzes the codebase,
discovers what needs to be documented, and creates documentation tasks.
"""

from src.sdk.models import Phase

PHASE_1_DOCUMENTATION_DISCOVERY = Phase(
    id=1,
    name="documentation_discovery",
    description="""Discover what needs to be documented and create documentation tasks.

This phase analyzes the codebase (leveraging index_repo memories if available),
understands the user's documentation request, and creates tickets for each
documentation area. Each ticket gets a corresponding Phase 2 task.

Supports both "document everything" and specific documentation requests.""",
    done_definitions=[
        "User's documentation request understood",
        "Existing codebase memories retrieved (if available from index_repo)",
        "If no memories: Quick codebase scan completed",
        "Existing docs/ folder checked for current documentation",
        "Documentation areas identified based on request",
        "ONE ticket created per documentation area",
        "ONE Phase 2 task created per ticket (1:1 relationship)",
        "Documentation plan saved to memory",
        "Task marked as done with summary",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A DOCUMENTATION ARCHITECT - DISCOVER WHAT NEEDS DOCUMENTING
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Discover what to document and create documentation tasks

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - use your real agent ID from task context.

1. **CHECK EXISTING MEMORIES FIRST**
   If index_repo was run, use those memories instead of re-scanning!

2. **CHECK EXISTING DOCS**
   Look at the docs/ folder to see what documentation already exists.
   Phase 2 will UPDATE existing docs, not overwrite blindly.

3. **ONE TICKET PER DOCUMENTATION AREA**
   Each component/area gets its own ticket and task.

4. **COMPONENT-BASED DISCOVERY**
   Think in terms of logical components, not individual files.

═══════════════════════════════════════════════════════════════════════

STEP 1: UNDERSTAND THE DOCUMENTATION REQUEST

Read the user's request carefully:

**If "everything" or "full documentation":**
- Document ALL major components
- Create comprehensive documentation suite
- Include: Overview, Getting Started, Architecture, Components, API, Config

**If specific request (e.g., "API endpoints", "authentication"):**
- Focus ONLY on the requested area
- Create targeted documentation
- May be 1-3 tickets instead of many

Save your understanding:

```python
save_memory(
    content="Documentation request: [summary of what user wants documented]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 2: DISCOVER THE CODEBASE

**FIRST: Check for existing memories from index_repo workflow!**

```python
# If index_repo was run, memories exist about:
# - Project purpose and tech stack
# - Components and their responsibilities
# - Code patterns and structure
# USE THESE instead of re-scanning!
```

**IF no memories exist:** Do a quick codebase scan:

1. Read README.md, package.json/pyproject.toml
2. Identify tech stack and project type
3. Map directory structure
4. Identify major components

```python
save_memory(
    content="Project overview: [type] using [tech stack]. Components: [list]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 3: CHECK EXISTING DOCUMENTATION

**Look at the docs/ folder:**

```bash
ls -la docs/
```

Note what documentation already exists:
- Does docs/README.md exist? (index file)
- What component docs exist?
- What's missing?
- What needs updating?

```python
save_memory(
    content="Existing docs: [list files in docs/]. Missing: [list gaps].",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

═══════════════════════════════════════════════════════════════════════

STEP 4: IDENTIFY DOCUMENTATION AREAS

**For "everything" requests, consider these areas:**

1. **Overview/README** - Project overview, what it does, quick start
2. **Getting Started** - Installation, setup, first steps
3. **Architecture** - System design, components, data flow
4. **API Reference** - Endpoints, parameters, responses (if applicable)
5. **Components Guide** - Each major component explained
6. **Configuration** - Config options, environment variables
7. **Contributing** - How to contribute, development setup

**For specific requests:**
- Identify just the relevant area(s)
- May be 1-3 documentation tickets

**Group logically - don't create too many small tickets:**

✅ GOOD: "Backend API Documentation" (covers all endpoints)
❌ BAD: "GET /users endpoint", "POST /users endpoint" (too granular)

═══════════════════════════════════════════════════════════════════════

STEP 5: CREATE DOCUMENTATION TICKETS

**Create tickets IN ORDER. Use markdown for descriptions!**

```python
# Example: Overview/README documentation
overview_ticket = create_ticket(
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    title="Documentation: Project Overview",
    description=\"\"\"## Documentation: Project Overview

### What to Document
Create/update the main project overview documentation.

### Target File
`docs/README.md` or `docs/overview.md`

### Content to Include
- Project name and one-line description
- What problem it solves
- Key features (bullet list)
- Tech stack summary
- Quick start (3-5 steps to get running)
- Links to other documentation sections

### Existing Documentation
- [ ] Check if docs/README.md exists - UPDATE if so
- [ ] Check if docs/overview.md exists - UPDATE if so

### Target Audience
{target_audience}

### Style Guidelines
- Clear, concise language
- Use code blocks for commands
- Include examples where helpful
- Link to other docs sections\"\"\",
    ticket_type="task",
    priority="high",
    tags=["documentation", "overview"],
    blocked_by_ticket_ids=[]
)
overview_ticket_id = overview_ticket["ticket_id"]

# Example: API Reference documentation
api_ticket = create_ticket(
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    title="Documentation: API Reference",
    description=\"\"\"## Documentation: API Reference

### What to Document
Document all API endpoints with parameters, responses, and examples.

### Target File
`docs/api-reference.md`

### Content to Include
For each endpoint:
- HTTP method and path
- Description of what it does
- Request parameters (query, path, body)
- Request body schema (if applicable)
- Response schema with examples
- Error responses
- Authentication requirements
- Example curl/code snippets

### Existing Documentation
- [ ] Check if docs/api-reference.md exists - UPDATE if so
- [ ] Check if docs/api/ folder exists with individual endpoint docs

### Style Guidelines
- Use tables for parameters
- Include realistic examples
- Group endpoints by resource/domain
- Note required vs optional parameters\"\"\",
    ticket_type="task",
    priority="medium",
    tags=["documentation", "api"],
    blocked_by_ticket_ids=[]
)
api_ticket_id = api_ticket["ticket_id"]

# Example: Architecture documentation
arch_ticket = create_ticket(
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    title="Documentation: Architecture",
    description=\"\"\"## Documentation: Architecture

### What to Document
Document the system architecture, components, and how they interact.

### Target File
`docs/architecture.md`

### Content to Include
- High-level system overview
- Component diagram (can be ASCII or mermaid)
- Each component's responsibility
- Data flow between components
- External dependencies/integrations
- Directory structure explanation
- Key design decisions and rationale

### Existing Documentation
- [ ] Check if docs/architecture.md exists - UPDATE if so

### Style Guidelines
- Use diagrams where possible (mermaid/ASCII)
- Explain the "why" not just the "what"
- Link to component-specific docs\"\"\",
    ticket_type="task",
    priority="medium",
    tags=["documentation", "architecture"],
    blocked_by_ticket_ids=[]
)
arch_ticket_id = arch_ticket["ticket_id"]
```

═══════════════════════════════════════════════════════════════════════

STEP 6: CREATE PHASE 2 TASKS (ONE PER TICKET)

**🚨 CRITICAL: Every ticket MUST have exactly ONE Phase 2 task! 🚨**

```python
# Task for Overview documentation
create_task(
    description=f"Phase 2: Generate Project Overview Documentation - TICKET: {overview_ticket_id}. Create/update docs/README.md or docs/overview.md with project overview, features, quick start. Check existing docs first - UPDATE don't overwrite.",
    done_definition=f"Overview documentation created/updated in docs/. Ticket {overview_ticket_id} resolved.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=2,
    priority="high",
    ticket_id=overview_ticket_id
)

# Task for API documentation
create_task(
    description=f"Phase 2: Generate API Reference Documentation - TICKET: {api_ticket_id}. Create/update docs/api-reference.md with all endpoints, parameters, examples. Check existing docs first - UPDATE don't overwrite.",
    done_definition=f"API documentation created/updated in docs/. Ticket {api_ticket_id} resolved.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=2,
    priority="medium",
    ticket_id=api_ticket_id
)

# Continue for all tickets...
```

═══════════════════════════════════════════════════════════════════════

STEP 7: VERIFY 1:1 RELATIONSHIP

```python
# Count tickets and tasks
total_tickets = len([overview_ticket_id, api_ticket_id, ...])
total_tasks = [count tasks created]

if total_tickets != total_tasks:
    print(f"❌ ERROR: {total_tickets} tickets but {total_tasks} tasks!")
    # GO BACK AND CREATE MISSING TASKS
else:
    print(f"✅ VERIFIED: {total_tickets} tickets = {total_tasks} tasks")
```

═══════════════════════════════════════════════════════════════════════

STEP 8: MARK YOUR TASK AS DONE

```python
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary=f"Documentation discovery complete. Identified {total_tickets} documentation areas. Created {total_tickets} tickets and {total_tasks} Phase 2 tasks. Areas: [list areas]. Checked existing docs/ folder."
)
```

═══════════════════════════════════════════════════════════════════════
DOCUMENTATION AREA TEMPLATES
═══════════════════════════════════════════════════════════════════════

**Use these as starting points for ticket descriptions:**

**Getting Started:**
- Installation steps
- Prerequisites
- Environment setup
- First run instructions
- Troubleshooting common issues

**Configuration:**
- All config options
- Environment variables
- Config file format
- Default values
- Examples for common setups

**Components Guide:**
- Each component's purpose
- How to use it
- Public API/interface
- Examples
- Related components

**Contributing:**
- Development setup
- Code style guidelines
- Testing requirements
- PR process
- Issue reporting

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Check existing memories from index_repo FIRST
- Check docs/ folder for existing documentation
- Create ONE ticket per logical documentation area
- Use markdown in ticket descriptions
- Create ONE task per ticket (1:1)
- Note what exists vs what needs creating
- Consider target audience

❌ DO NOT:
- Create one ticket for ALL documentation
- Create too granular tickets (per-file)
- Ignore existing documentation
- Skip checking for index_repo memories
- Forget 1:1 ticket-to-task relationship

═══════════════════════════════════════════════════════════════════════
ADDITIONAL CONTEXT FROM USER
═══════════════════════════════════════════════════════════════════════

**Documentation Scope:**
{documentation_scope}

**Target Audience:**
{target_audience}

Use this to guide what documentation to create and how to write it.
""",
    outputs=[
        "Documentation request understood",
        "Codebase analyzed (from memories or quick scan)",
        "Existing docs/ folder checked",
        "ONE ticket per documentation area with markdown descriptions",
        "ONE Phase 2 task per ticket (1:1 verified)",
        "Documentation plan saved to memory",
    ],
    next_steps=[
        "Phase 2 agents will generate documentation in parallel",
        "Each Phase 2 task creates/updates one documentation file",
        "Phase 2 updates docs/README.md index",
        "When all tickets resolved, documentation is complete",
    ],
)
