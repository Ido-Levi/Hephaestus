"""
Phase 1: Initial Scan

Scans the repository to understand its purpose, tech stack, and structure.
Discovers components and creates Phase 2 tasks for deep exploration of each.
"""

from src.sdk.models import Phase

PHASE_1_INITIAL_SCAN = Phase(
    id=1,
    name="initial_scan",
    description="Scan the repository to understand its purpose, tech stack, and discover components for deep exploration",
    done_definitions=[
        "README and documentation files read and understood",
        "Project purpose and goals identified and saved to memory",
        "Tech stack (languages, frameworks, tools) discovered and saved to memory",
        "Directory structure mapped and saved to memory",
        "Major components/modules identified and listed",
        "Ticket created for EACH discovered component in 'discovered' status",
        "Phase 2 deep-dive task created for EACH ticket (1:1 relationship)",
        "Task marked as done with summary of components found",
    ],
    working_directory=".",
    additional_notes="""
===============================================================================
YOU ARE A CODEBASE EXPLORER - SCAN AND DISCOVER
===============================================================================

YOUR MISSION: Scan this repository, understand what it is, and discover components to explore deeply.

You are building a knowledge map that other agents will use. Everything you learn should be saved to memory.

===============================================================================
CRITICAL WORKFLOW RULES
===============================================================================

0. **ALWAYS USE YOUR ACTUAL AGENT ID!**
   Your agent ID is in your task context. Use it for ALL MCP calls.
   DO NOT use "agent-mcp" - that's a placeholder!

1. **SAVE MEMORIES FREQUENTLY**
   Use save_memory for EVERY insight you discover.
   Other agents depend on these memories!

2. **CREATE A TICKET FOR EACH COMPONENT**
   Every component you discover needs a ticket on the Kanban board.
   Tickets start in "discovered" status.

3. **CREATE PHASE 2 TASKS FOR EACH TICKET (1:1)**
   Every ticket needs a corresponding Phase 2 task.
   Include the ticket_id in the task!

4. **MARK YOUR TASK AS DONE WHEN FINISHED**
   Call update_task_status with status="done"

===============================================================================
STEP 1: READ OVERVIEW DOCUMENTS
===============================================================================

Look for and read these files (if they exist):
- README.md, README.rst, README.txt
- docs/ folder contents (especially architecture, getting-started, overview docs)
- CONTRIBUTING.md, ARCHITECTURE.md, DESIGN.md
- setup.py, pyproject.toml, package.json, Cargo.toml, go.mod
- .env.example, config files
- Makefile, docker-compose.yml

Read these to understand what the project IS and what it DOES.

===============================================================================
STEP 2: IDENTIFY PROJECT PURPOSE
===============================================================================

After reading the docs, save these memories:

```python
save_memory(
    content="Project: [name] - [one-line description of what it does]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="Project purpose: [what problem does this solve? who uses it?]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="Project type: [web app / CLI / library / API / microservice / etc]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 3: DISCOVER TECH STACK
===============================================================================

Identify and save:
- Primary programming language(s)
- Frameworks (FastAPI, React, Django, Express, etc.)
- Database (if any)
- Build tools (npm, poetry, cargo, make, etc.)
- Testing framework (pytest, jest, etc.)
- Other key dependencies

```python
save_memory(
    content="Tech stack: Language=[X], Framework=[Y], Database=[Z], Build=[W]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="Dependencies: [key libraries and their purposes]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 4: MAP DIRECTORY STRUCTURE
===============================================================================

Explore the directory structure:
- Run `ls -la` at root
- Identify major directories (src/, lib/, tests/, docs/, etc.)
- Note the entry points (main.py, index.js, etc.)

```python
save_memory(
    content="Directory structure: src/ contains [X], tests/ contains [Y], docs/ contains [Z]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="Entry point: [main file or startup command]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 5: IDENTIFY LOGICAL COMPONENTS AND CREATE TICKETS
===============================================================================

**🚨 CRITICAL: WHAT IS A "COMPONENT"? 🚨**

A component is a LOGICAL SERVICE, DOMAIN, or ARCHITECTURAL LAYER.
It is NOT individual files, classes, or UI components!

**RULE: If it's a single file, it's NOT a component. Group related files together.**

✅ GOOD components (logical domains/services):
- "Backend API" - ALL routes, controllers, middleware (not each route file!)
- "Database Layer" - ALL models, migrations, queries (not each model!)
- "Frontend Application" - the ENTIRE React/Vue/Angular app (not each component!)
- "Authentication System" - login, registration, JWT, sessions (all together!)
- "Test Infrastructure" - ALL test setup, fixtures, utilities (not each test file!)
- "DevOps & Config" - Docker, CI/CD, environment configs (all together!)

❌ BAD components (TOO GRANULAR - DO NOT DO THIS):
- Individual React/Vue/Angular components - group as "Frontend Application"
- Individual API route files - group as "Backend API"
- Individual model files - group as "Database Layer"
- Individual hooks or utilities - group with their parent domain
- Individual test files - group as "Test Suite" or with what they test
- Any single file - if it's one file, it belongs to a larger component

**🎯 THINK IN TERMS OF SERVICES, NOT FILES:**

Ask yourself: "Would a team own this as a service/domain?"
- A team owns "Authentication" - not individual auth files
- A team owns "Frontend" - not each UI component
- A team owns "API" - not each endpoint file

**HOW TO GROUP INTO COMPONENTS:**

1. **Frontend apps** = ONE component (unless truly separate apps)
   - All React/Vue/Angular code = "Frontend Application"
   - Includes: components, hooks, services, utils, state management

2. **Backend services** = Group by domain/responsibility
   - All API routes + middleware = "Backend API"
   - All database code = "Database Layer"
   - All auth code = "Authentication System" (if substantial)

3. **Monorepos** = Each package/app is a component
   - packages/api = "API Package"
   - packages/web = "Web Application"
   - packages/shared = "Shared Utilities"

4. **Test suites** = ONE component (or group with what they test)
   - All E2E tests = "E2E Test Suite"
   - Or include tests with their respective components

**The number of components depends on the repo:**
- Small frontend app: 2-3 components (Frontend, Backend/API, Config)
- Medium app: 4-6 components
- Large monorepo: One per package/service

```python
save_memory(
    content="Components discovered: [list all logical components with brief descriptions]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

**For EACH logical component, create a DETAILED ticket:**

The ticket should give Phase 2 a clear roadmap of what to explore.

```python
# Create ticket for component (starts in "discovered" status automatically)
ticket_result = create_ticket(
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    title="[Component Name]",
    description=(
        "## Component: [Component Name]\\n\\n"
        "### Root Path\\n"
        "`[path/to/component]`\\n\\n"
        "### What This Component Does\\n"
        "[2-3 sentences explaining the purpose and responsibility]\\n\\n"
        "### Key Files & Directories to Explore\\n"
        "- `[path/to/main/entry.py]` - Entry point / main file\\n"
        "- `[path/to/models/]` - Data models and schemas\\n"
        "- `[path/to/services/]` - Business logic\\n"
        "- `[path/to/tests/]` - Test files\\n"
        "[List 5-10 most important files/folders]\\n\\n"
        "### Questions to Answer\\n"
        "1. What is the main entry point and how does execution flow?\\n"
        "2. What are the key classes/functions and what do they do?\\n"
        "3. How do you run this component? (commands, env vars, dependencies)\\n"
        "4. How do you test this component? (test commands, setup needed)\\n"
        "5. What other components does this depend on?\\n"
        "6. What does this component expose/export for others?\\n\\n"
        "### Technology & Patterns to Document\\n"
        "- Framework/library used: [e.g., FastAPI, React, SQLAlchemy]\\n"
        "- Key patterns to look for: [e.g., Repository pattern, React hooks]\\n"
        "- Configuration: [e.g., env vars, config files]\\n\\n"
        "### Integration Points\\n"
        "- Connects to: [list other components/services it talks to]\\n"
        "- Exposes: [APIs, functions, events it provides]"
    ),
    ticket_type="component",
    priority="medium",
    tags=["phase-2-pending"]
)
component_ticket_id = ticket_result["ticket_id"]  # Save this for the task!
```

===============================================================================
STEP 6: CREATE PHASE 2 TASKS (ONE PER TICKET)
===============================================================================

For EACH ticket you created, create a Phase 2 deep-dive task:

```python
create_task(
    description=f"Phase 2: Deep dive into [COMPONENT_NAME] - TICKET: {component_ticket_id}. Path: [component_path]. Explore this component thoroughly - understand its purpose, read the code, identify key classes/functions, find how to run/test it, discover code patterns. Save ALL findings to memory.",
    done_definition=f"Component thoroughly explored. Memories saved for: purpose, code structure, key classes/functions, code patterns, how to run/test, integration points. Ticket {component_ticket_id} moved to 'indexed' status.",
    agent_id="[YOUR AGENT ID]",
    workflow_id="[YOUR WORKFLOW ID]",
    phase_id=2,
    priority="medium",
    ticket_id=component_ticket_id  # Link task to ticket!
)
```

**CRITICAL: 1:1 RELATIONSHIP**
- Every ticket MUST have a corresponding task
- Every task MUST include "TICKET: {ticket_id}" in description
- Every task MUST pass ticket_id parameter

REMEMBER: Components are LOGICAL domains/services, not individual files.
Create one ticket + task per logical component you discover.

===============================================================================
STEP 7: MARK YOUR TASK AS DONE
===============================================================================

After creating all Phase 2 tasks:

```python
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary="Initial scan complete. Identified [N] components: [list]. Created [N] Phase 2 deep-dive tasks. Saved [M] memories about project overview, tech stack, and structure."
)
```

===============================================================================
MEMORY TYPES TO USE
===============================================================================

- codebase_knowledge: Structure, components, tech stack, file locations, how things work
- discovery: Interesting insights, patterns, non-obvious findings
- decision: Architecture decisions documented in the codebase
- warning: Gotchas, known issues, things to be careful about

===============================================================================
TIPS FOR GOOD MEMORIES
===============================================================================

BAD (too vague):
- "The project has authentication"
- "There are some tests"

GOOD (specific and useful):
- "Authentication uses JWT tokens, implemented in src/auth/jwt.py. Tokens expire after 1 hour."
- "Tests are in tests/ directory. Run with: pytest tests/ -v. Coverage report: pytest --cov=src"

Include file paths, specific details, and actionable information!

===============================================================================
ADDITIONAL CONTEXT FROM USER
===============================================================================

{repo_context}

Use any context provided above to focus your exploration.
""",
    outputs=[
        "Multiple memories about project overview and purpose",
        "Multiple memories about tech stack and dependencies",
        "Multiple memories about directory structure",
        "List of discovered components",
        "Phase 2 deep-dive task for each component",
    ],
    next_steps=[
        "Phase 2 agents will run in parallel, each exploring one component deeply",
        "Each Phase 2 agent saves detailed memories about their component",
        "When complete, memory system contains comprehensive codebase knowledge",
    ],
)
