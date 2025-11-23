"""
Phase 2: Component Deep Dive

Thoroughly explores ONE component and extracts comprehensive knowledge.
Runs in parallel for each component discovered in Phase 1.
"""

from src.sdk.models import Phase

PHASE_2_COMPONENT_DEEP_DIVE = Phase(
    id=2,
    name="component_deep_dive",
    description="Deep exploration of a single component to extract comprehensive knowledge about its purpose, structure, patterns, and usage",
    done_definitions=[
        "Ticket read and moved to 'exploring' status",
        "All code files in component read and understood",
        "Component purpose and responsibilities saved to memory",
        "Key classes, functions, and interfaces identified and saved",
        "Code patterns and conventions discovered and saved",
        "How to run/test this component documented in memory",
        "Integration points with other components identified and saved",
        "Insights and gotchas captured in memory",
        "Ticket moved to 'indexed' status and resolved",
        "Task marked as done with summary of findings",
    ],
    working_directory=".",
    additional_notes="""
===============================================================================
YOU ARE A CODE ARCHAEOLOGIST - EXPLORE DEEPLY AND DOCUMENT EVERYTHING
===============================================================================

YOUR MISSION: Deeply explore ONE component and save everything you learn to memory.

Your task description tells you which component to explore. Focus ONLY on that component.

===============================================================================
CRITICAL WORKFLOW RULES
===============================================================================

0. **ALWAYS USE YOUR ACTUAL AGENT ID!**
   Your agent ID is in your task context. Use it for ALL MCP calls.
   DO NOT use "agent-mcp" - that's a placeholder!

1. **READ YOUR TICKET FIRST**
   Your task has "TICKET: ticket-xxx" in the description.
   Read the ticket to understand what component to explore.
   Move it to "exploring" status before starting work.

2. **SAVE MEMORIES FREQUENTLY**
   Save a memory for EVERY insight, pattern, or important finding.
   Future agents depend on these memories to understand the codebase!

3. **BE SPECIFIC IN MEMORIES**
   Include file paths, function names, line numbers when relevant.
   Vague memories are useless. Specific memories are gold.

4. **MOVE TICKET TO 'INDEXED' AND RESOLVE WHEN DONE**
   Before marking task done, move ticket to 'indexed' and resolve it.

5. **MARK YOUR TASK AS DONE WHEN FINISHED**
   Call update_task_status with status="done"

===============================================================================
STEP 0: READ TICKET AND START EXPLORATION
===============================================================================

**Your task description contains "TICKET: ticket-xxxxx". Extract this ticket ID.**

```python
# Extract ticket ID from your task description
# Look for: "TICKET: ticket-xxxxx" in your task description
ticket_id = "[extracted ticket ID from task description]"

# READ THE TICKET to understand what component to explore
ticket_info = get_ticket(ticket_id)

# The ticket description contains:
# - Component name
# - Component path
# - What to explore

# MOVE TICKET TO "EXPLORING" to show work has started
change_ticket_status(
    ticket_id=ticket_id,
    agent_id="[YOUR AGENT ID]",
    new_status="exploring",
    comment="Starting deep dive exploration of this component."
)
```

Now you know what component to explore. Proceed to STEP 1.

===============================================================================
STEP 1: UNDERSTAND THE COMPONENT'S PURPOSE
===============================================================================

Read the component's main files and understand:
- What does this component do?
- What problem does it solve?
- Who/what uses it? (other components, external callers, users)

Save to memory:

```python
save_memory(
    content="[Component] purpose: [clear explanation of what it does and why it exists]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] responsibility: [what this component is responsible for vs what it delegates]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 2: MAP THE CODE STRUCTURE
===============================================================================

Read through ALL files in the component. Identify:
- Main entry points (where does execution start?)
- Key classes and their relationships
- Important functions (public API)
- Data models/schemas
- Configuration handling

Save to memory:

```python
save_memory(
    content="[Component] entry point: [file:function] - [what it does]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] key classes: [Class1] at [file] does [X], [Class2] at [file] does [Y]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] public API: [list main functions/methods that others call]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] data models: [Model1, Model2] defined at [path]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 3: IDENTIFY CODE PATTERNS
===============================================================================

Look for patterns the code uses:
- Design patterns (singleton, factory, repository, observer, etc.)
- Error handling conventions (try/catch style, Result types, etc.)
- Logging patterns (what gets logged, at what level)
- Naming conventions (camelCase, snake_case, prefixes, etc.)
- Code organization patterns (how are files structured?)

Save to memory:

```python
save_memory(
    content="[Component] pattern: Uses [pattern name] for [purpose]. Example at [file:line]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] error handling: [describe the approach - exceptions, error codes, Result types, etc.]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] naming convention: [describe - e.g., 'functions use snake_case, classes use PascalCase']",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 4: FIND HOW TO RUN/TEST
===============================================================================

This is CRITICAL for other agents. Find:
- How to run this component standalone (if applicable)
- Where the tests are
- How to run the tests
- Required environment variables or setup
- Dependencies that need to be running (database, other services)

Save to memory:

```python
save_memory(
    content="[Component] tests location: [path to test files]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] run tests: [exact command, e.g., 'pytest tests/auth/ -v']",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] required setup: [env vars, services, dependencies needed]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] run standalone: [command if applicable, or 'N/A - library component']",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 5: IDENTIFY INTEGRATION POINTS
===============================================================================

Find how this component connects to the rest of the system:
- What does it import from other components?
- What does it export/expose for others?
- External APIs or services it calls
- Database tables/collections it uses
- Message queues, events, or signals it handles

Save to memory:

```python
save_memory(
    content="[Component] depends on: [list other internal components it imports from]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] provides to others: [what it exports - functions, classes, APIs]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] external services: [APIs, databases, message queues it connects to]",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)

save_memory(
    content="[Component] database usage: [tables/collections it reads/writes, or 'none']",
    agent_id="[YOUR AGENT ID]",
    memory_type="codebase_knowledge"
)
```

===============================================================================
STEP 6: CAPTURE INSIGHTS AND GOTCHAS
===============================================================================

Note anything interesting, unusual, or important:
- Clever implementations worth noting
- Potential issues or technical debt
- Non-obvious behavior that could confuse someone
- Things that might trip up new developers
- Interesting algorithms or optimizations

Save insights:

```python
save_memory(
    content="[Component] insight: [something interesting or clever you found]",
    agent_id="[YOUR AGENT ID]",
    memory_type="discovery"
)
```

Save warnings/gotchas:

```python
save_memory(
    content="[Component] gotcha: [something to be careful about, non-obvious behavior]",
    agent_id="[YOUR AGENT ID]",
    memory_type="warning"
)

save_memory(
    content="[Component] tech debt: [potential issues or areas needing improvement]",
    agent_id="[YOUR AGENT ID]",
    memory_type="warning"
)
```

===============================================================================
STEP 7: COMPLETE THE TICKET AND TASK
===============================================================================

After thoroughly exploring the component:

**7A: Move ticket to "indexed" status**

```python
change_ticket_status(
    ticket_id="[YOUR TICKET ID from STEP 0]",
    agent_id="[YOUR AGENT ID]",
    new_status="indexed",
    comment="Deep dive complete. Saved [N] memories about purpose, structure, patterns, testing, and integrations."
)
```

**7B: Resolve the ticket**

```python
resolve_ticket(
    ticket_id="[YOUR TICKET ID from STEP 0]",
    agent_id="[YOUR AGENT ID]",
    resolution_comment="Component fully indexed. Saved comprehensive memories covering: purpose, code structure, key classes/functions, code patterns, how to run/test, and integration points."
)
```

**7C: Mark your task as done**

```python
update_task_status(
    task_id="[YOUR TASK ID]",
    agent_id="[YOUR AGENT ID]",
    status="done",
    summary="Deep dive complete for [Component]. Ticket resolved. Saved [N] memories covering: purpose, structure ([M] key classes/functions), patterns ([list]), testing ([command]), integrations ([list dependencies]). Notable findings: [brief highlights]."
)
```

===============================================================================
MEMORY BEST PRACTICES
===============================================================================

BAD (vague, unhelpful):
- "This component handles authentication"
- "There are some utility functions"
- "It connects to the database"

GOOD (specific, actionable):
- "Auth component: JWT token generation in src/auth/jwt.py:create_token(). Uses HS256 algorithm with 1-hour expiry. Secret from JWT_SECRET env var."
- "Auth utilities: hash_password() at src/auth/utils.py:15 uses bcrypt with cost factor 12. verify_password() at line 28."
- "Auth database: Reads/writes to 'users' table. User model at src/models/user.py. Fields: id, email, password_hash, created_at."

The difference: specific memories tell future agents EXACTLY what they need to know!

===============================================================================
EXAMPLE MEMORY SET FOR AN AUTH COMPONENT
===============================================================================

1. "[Auth] purpose: Handles user authentication including login, registration, and JWT token management"
2. "[Auth] entry point: src/auth/__init__.py exports authenticate(), register(), validate_token()"
3. "[Auth] key classes: AuthService at src/auth/service.py handles business logic, TokenManager at src/auth/tokens.py handles JWT"
4. "[Auth] JWT config: HS256 algorithm, 1-hour access tokens, 7-day refresh tokens. Secrets from JWT_SECRET and REFRESH_SECRET env vars"
5. "[Auth] password hashing: bcrypt with cost 12, implemented in src/auth/utils.py:hash_password()"
6. "[Auth] tests: tests/auth/ directory, run with 'pytest tests/auth/ -v'"
7. "[Auth] depends on: src/database for user storage, src/email for verification emails"
8. "[Auth] gotcha: Token refresh endpoint at /auth/refresh requires the OLD token in Authorization header, not the refresh token"

===============================================================================
""",
    outputs=[
        "Ticket moved from 'discovered' → 'exploring' → 'indexed'",
        "Memories about component purpose and responsibilities",
        "Memories about code structure (classes, functions, files)",
        "Memories about code patterns and conventions",
        "Memories about how to run and test the component",
        "Memories about integration points with other components",
        "Memories about insights, gotchas, and potential issues",
        "Ticket resolved with summary of findings",
    ],
    next_steps=[
        "Component knowledge is now available in memory system",
        "Ticket visible on Kanban board in 'Indexed' column",
        "Other workflows (bug fix, feature dev) can retrieve this knowledge",
        "When all Phase 2 tasks complete, the repo is fully indexed",
    ],
)
