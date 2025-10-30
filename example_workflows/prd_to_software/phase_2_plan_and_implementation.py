"""
Phase 2: Plan & Implementation

Designs AND implements ONE specific component based on tickets created by Phase 1.
This phase merges design and implementation into a single agent workflow.
"""

from src.sdk.models import Phase

# Phase 2: Plan & Implementation
# Designs one component in detail, then implements it
PHASE_2_PLAN_AND_IMPLEMENTATION = Phase(
    id=2,
    name="plan_and_implementation",
    description="""Design AND implement ONE specific component based on a ticket from Phase 1.

This phase combines design and implementation into a single workflow:
1. DESIGN: Create detailed specifications (architecture, interfaces, data models, algorithms)
2. IMPLEMENT: Write production-quality code following the design specification exactly

The output is both a design document AND working code that Phase 3 can validate and document.

Generic for any component type.""",
    done_definitions=[
        "Component architecture designed and documented in [component]_design.md (or skipped for reopened bug fix tasks)",
        "All interfaces and APIs fully specified in design doc",
        "Data models and schemas defined in design doc",
        "ALL code implemented per design specification",
        "Code follows project conventions and style guide",
        "Test stubs created in tests/ directory",
        "Code compiles/runs without syntax errors",
        "Self-validation completed (basic functionality check)",
        "ALL TESTS PASSING (comprehensive testing completed - unit + manual verification)",
        "Test execution instructions documented in run_instructions/[component]_test_instructions.md",
        "Design decisions saved to memory",
        "Ticket moved from 'backlog' to 'building-done' status",
        "ONE Phase 3 validation task created with ticket ID and test instructions reference",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A PLANNER & BUILDER - DESIGN THEN IMPLEMENT
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Design component in detail, then implement it completely

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES - READ BEFORE STARTING
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - that's just a placeholder in examples!
   Your actual agent ID is in your task context or environment.

   ❌ WRONG: `"agent_id": "agent-mcp"`
   ✅ RIGHT: `"agent_id": "[your actual agent ID from task context]"`

1. **CHECK BEFORE CREATING TASKS** (Prevent Duplicates)
   Before creating Phase 3 validation task, check if one exists for YOUR ticket:
   ```python
   # Use your ticket_id (you got it in STEP 0A)
   existing_tasks = mcp__hephaestus__get_tasks({
       "agent_id": "[YOUR ACTUAL AGENT ID]",
       "status": "all"
   })
   # Look for tasks with YOUR ticket_id and "Phase 3:" in description
   # If Phase 3 task exists for your ticket, DO NOT create duplicate!
   ```

2. **ALWAYS INCLUDE TICKET ID IN TASKS**
   Every task description MUST include: "TICKET: ticket-xxxxx"
   Example: "Phase 3: Validate & Document Auth - TICKET: ticket-abc123. ..."

3. **🚨 DO NOT CREATE NEW TICKETS - USE YOUR EXISTING TICKET ID! 🚨**
   Phase 2 works on a ticket created by Phase 1.
   When creating Phase 3 task, pass the SAME ticket ID forward.
   DO NOT create a new ticket!

4. **ONLY PHASE 3 RESOLVES TICKETS**
   - Phase 2: Move tickets 'backlog' → 'building' → 'building-done'
   - NEVER resolve tickets (only Phase 3 can resolve)

5. **🚨 IF YOU HAVE REQUIREMENT CONFLICTS OR AMBIGUITY - USE request_ticket_clarification! 🚨**
   **DO NOT CREATE NEW TICKETS FOR CLARIFICATIONS!**

   See detailed examples in STEP sections below for when and how to use this.

═══════════════════════════════════════════════════════════════════════

**🚨🚨🚨 BEFORE YOU DO ANYTHING - READ YOUR TICKET! 🚨🚨🚨**

STEP 0A: READ YOUR TICKET (MANDATORY FIRST STEP)

**Before you change ticket status, before you design or implement anything, READ THE TICKET!**

Your task description contains "TICKET: ticket-xxxxx". Extract this ticket ID.

**Then IMMEDIATELY use the get_ticket MCP endpoint to read the full ticket:**

```python
# Extract ticket ID from your task description
# Look for: "TICKET: ticket-xxxxx" in your task description
ticket_id = "[extracted ticket ID from task description]"

# READ THE TICKET FIRST - This is MANDATORY!
# Use the EXACT ticket ID to get the full ticket details
ticket_info = mcp__hephaestus__get_ticket(ticket_id)

# READ THE TICKET DESCRIPTION CAREFULLY
# The ticket description contains YOUR ENTIRE SCOPE!
# It tells you EXACTLY what to design and implement
```

**🎯 CRITICAL: THE TICKET DESCRIPTION IS YOUR SCOPE!**

**The ticket description tells you:**
- ✅ What to design (Purpose section)
- ✅ What to implement (Scope section)
- ✅ What features to include (detailed bullet points with PRD references)
- ✅ What dependencies exist (Dependencies section)

**⛔ WORK ONLY WITHIN THE TICKET SCOPE!**

- ✅ **DO**: Design AND implement ONLY what the ticket describes
- ✅ **DO**: Follow the ticket scope exactly
- ✅ **DO**: Include ALL features mentioned in the ticket
- ✅ **DO**: Reference the PRD sections mentioned in the ticket

- ❌ **DON'T**: Add features not mentioned in the ticket
- ❌ **DON'T**: Skip features mentioned in the ticket
- ❌ **DON'T**: Design/implement components outside your ticket scope
- ❌ **DON'T**: Assume requirements - read what the ticket says!

**DO NOT add features because you think they're good ideas!**
**DO NOT skip features because you think they're not needed!**
**FOLLOW THE TICKET EXACTLY!**

---

**🚨🚨🚨 SPECIAL RULE FOR INFRASTRUCTURE TICKETS! 🚨🚨🚨**

**IF YOUR TICKET IS AN INFRASTRUCTURE TICKET, READ THIS CAREFULLY:**

Infrastructure tickets are SETUP ONLY - absolutely NO features or business logic!

**🚨🚨🚨 CRITICAL PROJECT STRUCTURE RULES - MUST FOLLOW! 🚨🚨🚨**

**1. PORT 8000 IS RESERVED - NEVER USE IT!**
- Port 8000 is used by Hephaestus MCP server and MUST remain open
- If your project needs a backend server, use a DIFFERENT port (8002, 3000, 5000, etc.)
- ❌ WRONG: Backend runs on port 8000
- ✅ CORRECT: Backend runs on port 8002 (or any port except 8000)

**2. FRONTEND AND BACKEND MUST BE IN SEPARATE DIRECTORIES!**
- Create a `frontend/` directory for ALL frontend code
- Create a `backend/` directory for ALL backend code
- NEVER mix frontend and backend code in a single `src/` directory
- ❌ WRONG: Single `src/` with mixed frontend/backend code
- ✅ CORRECT: `frontend/src/` and `backend/src/` as separate directories

**Example Correct Project Structure:**
```
project-root/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── src/
│   │   ├── api/
│   │   ├── models/
│   │   └── services/
│   ├── main.py
│   └── requirements.txt
└── README.md
```

**✅ INFRASTRUCTURE DESIGN SHOULD SPECIFY:**
- Setup commands to run (create-react-app, poetry init, npm init, etc.)
- **Create frontend/ and backend/ directories** (for web apps)
- **Configure backend to run on PORT 8002** (NOT 8000!)
- Folder structure to create (empty folders only)
- Tools to install and configure (linters, formatters, build tools)
- Configuration files to create (.env templates with PORT=8002, config files)
- How to verify setup works (run dev server, hello world endpoint on port 8002)

**✅ INFRASTRUCTURE IMPLEMENTATION SHOULD ONLY:**
- **Create frontend/ and backend/ directories** (for web apps)
- Run setup commands (create-react-app, poetry init, npm init, etc.)
- **Configure backend server to use PORT 8002** (not 8000!)
- Create empty folder structure (frontend/src/, backend/src/)
- Install and configure tools (linters, formatters, build tools)
- Create configuration files (.env.example with PORT=8002, basic configs)
- Verify setup works (run dev server, hello world endpoint on port 8002)

**❌ INFRASTRUCTURE SHOULD NOT INCLUDE:**
- Using PORT 8000 for backend (it's RESERVED!)
- Mixing frontend and backend in single src/ directory
- Components, pages, or modules (these are features!)
- Authentication, APIs, database models (these are features!)
- Business logic or application code (these are features!)
- Anything beyond basic project skeleton!

**⚠️ IF IT IMPLEMENTS A FEATURE OR BUSINESS LOGIC, IT'S NOT INFRASTRUCTURE!**

Before proceeding, ask yourself:
- Is this ticket for "Infrastructure: [Something] Setup"?
- If YES: Keep design+implementation minimal - SETUP STEPS ONLY, no features!
- If NO: Proceed with normal component design+implementation

---

STEP 0B: UPDATE TICKET STATUS

**After reading your ticket, move it from "backlog" to "building" to show work has started.**

```python
# Move ticket from "backlog" to "building" status
mcp__hephaestus__change_ticket_status({
    "ticket_id": ticket_id,
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "building",
    "comment": "Starting plan & implementation. Creating design specification then implementing code per ticket scope. Ticket moved from 'backlog' to 'building'."
})
```

STEP 0C: DETECT IF THIS IS A REOPENED TASK (BUG FIX)

**🚨 IMPORTANT: Check if you're working on bug fixes vs new implementation! 🚨**

If your task description contains phrases like:
- "Fix critical bugs"
- "Fix ALL critical bugs found in validation"
- "Critical design flaws"
- "Reopened from P3"

Then you are working on **BUG FIXES**, not new implementation!

**🚨 IF REOPENED FOR BUG FIXES:**
- ✅ READ the original design doc (design/[component]_design.md) - it still exists!
- ✅ READ your task description THOROUGHLY - it lists specific bugs to fix
- ✅ READ the test report (test_reports/) mentioned in task description
- ✅ **SKIP STEP 1-3 (design phase)** - design already exists!
- ✅ **GO DIRECTLY TO STEP 4-5 (implementation)** - fix ONLY the listed bugs
- ✅ Still do STEP 10-16 (testing) - verify fixes work
- ✅ Still do STEP 17-20 (handoff) - create P3 task at end

**IF THIS IS NEW IMPLEMENTATION (not reopened):**
- ✅ Proceed normally with STEP 1-3 (design phase)

═══════════════════════════════════════════════════════════════════════
🎨 PART 1: DESIGN PHASE
═══════════════════════════════════════════════════════════════════════

STEP 1: UNDERSTAND YOUR SCOPE (FROM THE TICKET YOU JUST READ)

**🎯 HOW TO THINK ABOUT DESIGN:**

You just read your ticket. Now you need to understand the FULL context:

1. **Re-read the PRD** (the original requirements document)
   - Find the sections referenced in your ticket
   - Understand the USER need this component addresses
   - Understand what problem you're solving

2. **Retrieve relevant memories** about:
   - Overall system architecture (from Phase 1)
   - Technology stack decisions
   - Other components and their interfaces
   - Integration requirements

3. **Read requirements_analysis.md** to understand:
   - How your component fits into the system
   - What depends on you (what you're blocking)
   - What you depend on (what blocks you)

**🎯 CRITICAL THINKING FRAMEWORK:**

Before you design, ask yourself:
- **What** am I building? (from ticket description)
- **Why** am I building it? (from PRD - what user problem does it solve?)
- **Who** uses it? (internal component? external API? end user?)
- **How** does it fit into the system? (integrations, dependencies)
- **What** is the MINIMUM scope? (implement ONLY what the ticket says, nothing more!)

**⚠️ SCOPE DISCIPLINE:**
- ✅ Implement what the ticket describes
- ✅ Reference the PRD sections mentioned in the ticket
- ❌ DO NOT add "nice to have" features
- ❌ DO NOT implement features from other tickets
- ❌ DO NOT over-engineer beyond requirements

**Now design ONLY what the ticket requires, informed by the PRD context.**

STEP 2: DESIGN THE COMPONENT

Create design/[component_name]_design.md with these sections:

```markdown
# [Component Name] Design Specification

## Overview
- Purpose: What this component does
- Scope: What's in scope and out of scope
- Dependencies: Other components this relies on

## Architecture

### High-Level Structure
[Diagram or description of major parts]

### Components/Modules
1. **[Module A]**
   - Responsibility: [what it does]
   - Interfaces: [public API]

2. **[Module B]**
   ...

## Interfaces & APIs

### Public Interface
```[language]
class ComponentName:
    def method_name(param1: Type, param2: Type) -> ReturnType:
        \"\"\"
        Description of what this method does.

        Args:
            param1: Description
            param2: Description

        Returns:
            Description

        Raises:
            ErrorType: When this error occurs
        \"\"\"
        pass
```

For REST APIs:
```
GET /api/resource
Request: { ... }
Response: { ... }
Status Codes: 200, 400, 404, 500
```

### Internal Interfaces
[How modules within this component interact]

## Data Models

### Database Schema (if applicable)
```sql
CREATE TABLE table_name (
    id SERIAL PRIMARY KEY,
    field1 VARCHAR(255) NOT NULL,
    field2 INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_field1 ON table_name(field1);
```

### Data Structures
```[language]
class DataModel:
    field1: str
    field2: int
    field3: List[SomeType]
```

## Algorithms & Logic

For complex operations, provide pseudocode:
```
algorithm process_data(input):
    1. Validate input
    2. Transform data
    3. Store result
    4. Return response
```

## Error Handling

### Error Types
- ValidationError: Invalid input
- NotFoundError: Resource doesn't exist
- DatabaseError: Database operation failed
...

### Error Responses
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "User-friendly message",
        "details": { "field": "reason" }
    }
}
```

## Integration Points

### Integration with [Other Component]
- How: REST API calls / Function calls / Message queue
- Data format: JSON / Protocol buffers / etc.
- Authentication: How authentication happens
- Error handling: What happens if integration fails

## Configuration

### Required Config
```yaml
component:
  setting1: value
  setting2: value
```

### Environment Variables
- ENV_VAR_1: Description
- ENV_VAR_2: Description

## Testing Strategy

### Unit Tests Needed
- Test case 1: Description
- Test case 2: Description

### Integration Tests Needed
- Test integration with [Component A]
- Test integration with [Component B]

## Implementation Notes

### File Structure
```
src/
  component/
    __init__.py
    core.py
    models.py
    api.py
    utils.py
tests/
  component/
    test_core.py
    test_api.py
```

### Dependencies
- library1 >= 1.2.0
- library2 ~= 2.0

### Security Considerations
- Input validation requirements
- Authentication/authorization checks
- Data encryption needs

## Open Questions
[Any ambiguities that need clarification]
```

STEP 3: SAVE DESIGN TO MEMORY

memory_type: codebase_knowledge
- "[Component] design: design/[component]_design.md"
- "[Component] architecture: [brief description]"
- "[Component] integrates with [Other Component] via [method]"

memory_type: decision
- "[Component] uses [approach] for [concern] because [reason]"
- "[Component] error handling strategy: [strategy]"

═══════════════════════════════════════════════════════════════════════
⚙️ PART 2: IMPLEMENTATION PHASE
═══════════════════════════════════════════════════════════════════════

STEP 4: SET UP PROJECT STRUCTURE

Create necessary directories and files per design:
```
src/
  component/
    __init__.py
    core.py
    models.py
    api.py
    utils.py
tests/
  component/
    test_core.py
    test_api.py
```

═══════════════════════════════════════════════════════════════════════
⚡ OPTIMIZATION: USE TASK TOOL FOR PARALLEL WORK (STRONGLY ENCOURAGED)
═══════════════════════════════════════════════════════════════════════

**🎯 WHY USE TASK TOOL?**
- Reduces context rot (long implementations cause memory issues)
- Unblocks dependent tasks faster (they're waiting on you!)
- Parallelizes independent work (multiple things at once)
- Uses specialized agents (@agent-senior-fastapi-engineer, @agent-senior-frontend-engineer, @agent-test-automation-engineer, etc.)

**WHEN TO CONSIDER TASK TOOL:**

✅ **Large Implementations (>500 lines)**
   - Single large component that takes >30 minutes to implement
   - Solution: Break into logical sub-tasks, use Task tool

✅ **Independent Frontend + Backend Work**
   - Component has both frontend and backend parts
   - Solution: Spawn parallel agents for frontend and backend

✅ **Specialized Work**
   - Need React component → Use @agent-senior-frontend-engineer agent
   - Need backend API → Use @agent-senior-fastapi-engineer agent
   - Need testing → Use @agent-test-automation-engineer agent
   - See available specialized agents list below

**AVAILABLE SPECIALIZED SUB-AGENTS:**

Use Claude Code's Task tool with these subagent_type values when appropriate:

1. **@agent-senior-fastapi-engineer** - FastAPI/backend expert
   - Use for: Backend APIs, FastAPI endpoints, server-side logic
   - Example: Implementing auth endpoints, data processing APIs

2. **@agent-senior-frontend-engineer** - React/frontend expert
   - Use for: React components, UI implementation, frontend features
   - Example: Building dashboard pages, form components

3. **@agent-test-automation-engineer** - Testing specialist
   - Use for: Writing comprehensive test suites, test infrastructure
   - Example: Unit tests, integration tests, test coverage

4. **@agent-debug-troubleshoot-expert** - Debugging specialist
   - Use for: Root cause analysis, bug investigation
   - Example: Tracking down elusive bugs, analyzing failures

5. **@agent-devops-engineer** - Docker/DevOps expert
   - Use for: Docker Compose, CI/CD, deployment configs
   - Example: Container setup, deployment pipelines

6. **@agent-api-integration-engineer** - API integration expert
   - Use for: Third-party API integrations, external services
   - Example: Payment APIs, authentication providers

7. **@agent-database-architect** - Database design expert
   - Use for: Schema design, migrations, query optimization
   - Example: Database models, migration scripts

8. **@agent-technical-documentation-writer** - Documentation expert
   - Use for: Creating setup guides, run instructions
   - Example: Test execution documentation, deployment guides

9. **@agent-senior-code-reviewer** - Code quality expert
   - Use for: Code review, quality checks (optional pre-validation)
   - Example: Pre-P3 quality gate, architecture review

**HOW TO USE TASK TOOL:**

Example: Auth system with 3 independent modules
Instead of implementing sequentially, spawn parallel agents:

```python
# Agent 1: Login module
Task(
    subagent_type="@agent-senior-fastapi-engineer",  # Use specialized agent for backend work
    description="Implement login authentication module",
    prompt=\"\"\"Implement login functionality for auth system.

Must handle email/password validation, JWT token generation, rate limiting.
See design/auth_design.md section 2.1.
Create at src/auth/login.py with tests.\"\"\"
)

# Agent 2: Registration module (parallel!)
Task(
    subagent_type="@agent-senior-fastapi-engineer",
    description="Implement user registration module",
    prompt=\"\"\"Implement registration functionality.

Must handle email uniqueness check, password hashing, email verification.
See design/auth_design.md section 2.2.
Create at src/auth/registration.py with tests.\"\"\"
)

# Agent 3: Password reset (parallel!)
Task(
    subagent_type="@agent-senior-fastapi-engineer",
    description="Implement password reset module",
    prompt=\"\"\"Implement password reset flow.

Must handle reset token generation, email sending, token validation.
See design/auth_design.md section 2.3.
Create at src/auth/password_reset.py with tests.\"\"\"
)

# Wait for all to complete, then integrate and test together
```

**WHEN NOT TO USE TASK TOOL:**
- ❌ Simple single-file implementations (<200 lines)
- ❌ Components with heavy interdependencies (can't parallelize)
- ❌ When you're already fixing a specific bug (stay focused)

**This is ENCOURAGED but OPTIONAL - use your judgment!**

═══════════════════════════════════════════════════════════════════════

STEP 5: IMPLEMENT CORE FUNCTIONALITY

Follow the design document EXACTLY:
- Implement all specified classes/functions
- Use exact interface signatures from design
- Implement error handling as specified
- Add logging/debugging as appropriate

Example:
```python
# From design_doc.md:
# def authenticate_user(email: str, password: str) -> Optional[User]:
#     Validates credentials and returns User object or None

def authenticate_user(email: str, password: str) -> Optional[User]:
    \"\"\"
    Authenticate user with email and password.

    Args:
        email: User email address
        password: Plain text password (will be hashed)

    Returns:
        User object if authentication succeeds, None otherwise
    \"\"\"
    # Validate email format
    if not validate_email(email):
        logger.warning(f"Invalid email format: {email}")
        return None

    # Hash password
    password_hash = hash_password(password)

    # Query database
    try:
        user = db.query(User).filter(
            User.email == email,
            User.password_hash == password_hash
        ).first()

        if user:
            logger.info(f"User authenticated: {email}")
            return user
        else:
            logger.info(f"Authentication failed: {email}")
            return None

    except DatabaseError as e:
        logger.error(f"Database error during authentication: {e}")
        raise AuthenticationError("Database unavailable") from e
```

STEP 6: IMPLEMENT DATA MODELS

If the design specifies database models, implement them:
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

STEP 7: IMPLEMENT INTEGRATIONS

Integrate with other components as designed:
```python
# Design says: "Integrate with auth component for user validation"

from src.auth import authenticate_user

def process_request(email: str, password: str, data: dict):
    # Use auth component
    user = authenticate_user(email, password)
    if not user:
        raise UnauthorizedError("Invalid credentials")

    # Continue processing...
```

STEP 8: CREATE TEST STUBS

Create test files with stubs for each function:
```python
# tests/component/test_core.py
import pytest
from src.component.core import authenticate_user

def test_authenticate_user_valid_credentials():
    # TODO: Test successful authentication
    # - Create test user in database
    # - Call authenticate_user with valid credentials
    # - Assert User object returned
    # - Assert user has correct email
    pass

def test_authenticate_user_invalid_credentials():
    # TODO: Test authentication failure
    # - Call authenticate_user with invalid credentials
    # - Assert None returned
    pass

def test_authenticate_user_invalid_email_format():
    # TODO: Test email validation
    # - Call with malformed email
    # - Assert None returned
    pass

def test_authenticate_user_database_error():
    # TODO: Test database error handling
    # - Mock database to raise error
    # - Assert AuthenticationError raised
    pass
```

STEP 9: RUN LINTERS AND FORMATTERS

```bash
# Python example
black src/
pylint src/component/
mypy src/component/

# JavaScript example
npm run lint
npm run format
```

Fix any issues before marking task complete.

STEP 10: SELF-VALIDATION - TEST YOUR IMPLEMENTATION

**MANDATORY: You MUST validate your implementation works before creating Phase 3 task!**

**🎯 YOUR GOAL: Catch all obvious issues NOW, before Phase 3 sees your code.**

**WHAT TO VALIDATE:**

**1. Code Compilation/Syntax Check** (MANDATORY)
```bash
# Python
python -m py_compile src/component/*.py
# Or import check
python -c "from src.component import *"

# JavaScript/TypeScript
npm run build  # or tsc --noEmit
# Or import check
node -e "require('./src/component')"

# Go
go build ./component/...

# Rust
cargo check --package component
```

**Expected: NO syntax errors, NO import errors, code compiles successfully**

If this fails, FIX IT NOW before proceeding!

**2. Basic Functionality Test** (MANDATORY)
Run your code with simple inputs to verify it actually works:

```python
# Python example - Authentication component
python -c "
from src.auth.core import authenticate_user
# Test it actually runs (even if returns None)
result = authenticate_user('test@example.com', 'password')
print(f'Function executed: {result}')
# If it crashes here, you have a problem - FIX IT!
"
```

**Expected: Function runs without crashing (even if logic isn't perfect)**

If this crashes with basic errors, FIX IT NOW before proceeding!

**3. Dependency Check** (MANDATORY)
Verify all imports/dependencies exist:

```bash
# Python
python -c "import package1, package2, package3"

# JavaScript
node -e "require('package1'); require('package2');"

# Check requirements file matches reality
pip freeze | grep package-name
```

**Expected: All dependencies installed and importable**

If imports fail, FIX IT NOW before proceeding!

**VALIDATION CHECKLIST - ALL MUST PASS:**

Before moving to STEP 11, verify:
- [ ] ✅ Code compiles/parses without syntax errors
- [ ] ✅ All imports work (no ModuleNotFoundError, ImportError, etc.)
- [ ] ✅ Basic function calls execute without crashing
- [ ] ✅ Dependencies are installed and correct versions
- [ ] ✅ Linters pass (from STEP 9)

**IF ANY CHECKBOX IS ❌, YOU MUST FIX IT BEFORE PROCEEDING!**

STEP 11: SAVE IMPLEMENTATION TO MEMORY

memory_type: codebase_knowledge
- "[Component] implemented at: src/component/"
- "[Component] exports: function1(), function2(), Class1, Class2"
- "[Component] dependencies: [list imported modules]"

memory_type: decision
- "Implemented [feature] using [approach] because [reason]"
- "Deviated from design in [aspect] because [justified reason]"

═══════════════════════════════════════════════════════════════════════
🧪 PART 2B: TESTING PHASE
═══════════════════════════════════════════════════════════════════════

**🚨🚨🚨 CRITICAL: YOU MUST THOROUGHLY TEST YOUR IMPLEMENTATION! 🚨🚨🚨**

**WHY THIS PHASE EXISTS:**
Phase 3 should receive WORKING code, not broken code. You must test comprehensively
and fix ALL issues before handing off. If Phase 3 receives broken code, YOU FAILED.

**🎯 YOUR GOAL: Ensure 100% working implementation before Phase 3.**

STEP 12: RUN COMPREHENSIVE TESTS

**Execute ALL relevant tests for your component:**

```bash
# Python - Run unit tests for your component
pytest tests/component/ -v --tb=short

# Python - Run with coverage
pytest tests/component/ --cov=src/component -v

# JavaScript/TypeScript - Run tests
npm test -- component.test.js

# JavaScript - Run all tests
npm test

# Go - Run tests
go test ./component/... -v

# Rust - Run tests
cargo test --package component --lib
```

**Capture the full output - you'll need it if tests fail.**

STEP 13: VERIFY YOUR CODE ACTUALLY WORKS

**Beyond unit tests, verify the component works in context:**

**For Backend Components:**
```bash
# Start the backend server
python src/main.py  # or uvicorn, flask run, etc.

# In another terminal, test the endpoints
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# Verify response is correct
# Verify logs show expected behavior
# Verify database changes are correct (if applicable)
```

**For Frontend Components:**
```bash
# Start the frontend dev server
npm run dev

# Open browser to http://localhost:5173
# Manually test the component:
# - Does it render?
# - Does it handle user interaction?
# - Does it call APIs correctly?
# - Are there console errors?
```

**For CLI Tools:**
```bash
# Run the CLI with test inputs
python src/cli.py --command test --input "sample data"

# Verify output is correct
# Verify exit code is correct
# Verify files created/modified as expected
```

**For Libraries:**
```python
# Import and test the library
python -c "
from src.component import ComponentClass
component = ComponentClass({'setting': 'value'})
result = component.do_something('test')
print(f'Result: {result}')
assert result['status'] == 'success', 'Expected success!'
print('✅ Library works!')
"
```

STEP 14: FIX ALL ISSUES UNTIL TESTS PASS

**If ANY test fails or component doesn't work:**

1. **Analyze the failure:**
   - What's the error message?
   - What's the root cause?
   - Is it a logic error, integration issue, or missing dependency?

2. **Fix the issue:**
   - Update the code
   - Add missing error handling
   - Fix the logic
   - Install missing dependencies

3. **Re-run the test:**
   ```bash
   # Re-run the specific failing test
   pytest tests/component/test_specific.py::test_that_failed -v

   # Or re-run all tests
   pytest tests/component/ -v
   ```

4. **Repeat until ALL tests pass:**
   - Do NOT skip failing tests
   - Do NOT comment out failing tests
   - Do NOT ignore test failures
   - FIX the issues until tests PASS

**🚨 YOU CANNOT PROCEED TO STEP 15 UNTIL ALL TESTS PASS! 🚨**

STEP 15: VERIFY INTEGRATION POINTS

**If your component integrates with other components, test the integration:**

```python
# Example: If you built Auth, test it works with the API layer
# Start both services and verify integration

# Test authentication flow end-to-end:
# 1. Register user
# 2. Login user
# 3. Get token
# 4. Use token to access protected endpoint
# 5. Verify all steps work
```

**Common integration checks:**
- Database connections work
- API calls between components succeed
- Message queue communication works
- File I/O operations work
- External service integrations work

STEP 16: DOCUMENT TEST RESULTS

Create a quick test summary (you don't need a formal report yet - Phase 3 will do that):

```markdown
# Phase 2 Testing Summary - [Component]

**All tests passing:** ✅ YES / ❌ NO

**Test execution:**
- Unit tests: [X/Y passed]
- Integration tests: [X/Y passed]
- Manual verification: ✅ Component works end-to-end

**Issues found and fixed:**
1. Issue: [description] → Fix: [what you did]
2. Issue: [description] → Fix: [what you did]

**Ready for Phase 3:** ✅ YES - All tests pass, component fully functional
```

**CHECKLIST - ALL MUST BE ✅ BEFORE PROCEEDING:**

Before moving to STEP 17, verify:
- [ ] ✅ All unit tests pass (100% pass rate)
- [ ] ✅ Component works when run/tested manually
- [ ] ✅ Integration points tested and working
- [ ] ✅ No errors in logs during testing
- [ ] ✅ All issues found during testing were FIXED
- [ ] ✅ Re-ran tests after fixes - everything passes

**IF ANY CHECKBOX IS ❌, GO BACK TO STEP 14 AND FIX!**

**DO NOT PROCEED TO HANDOFF IF ANYTHING IS BROKEN!**

═══════════════════════════════════════════════════════════════════════
🚀 PART 3: HANDOFF TO PHASE 3
═══════════════════════════════════════════════════════════════════════

STEP 16B: CREATE TEST EXECUTION INSTRUCTIONS FOR PHASE 3

**🚨 MANDATORY: P3 needs to know HOW to run your tests! 🚨**

Create `run_instructions/[component]_test_instructions.md` documenting EXACTLY how you ran tests.

**Why this is critical:**
- P3 doesn't know your setup (Docker, env vars, services)
- Without instructions, P3 will fail to run tests correctly
- This prevents wasted time figuring out test environment

**Template (flexible guidelines, adapt as needed):**

```markdown
# Test Execution Instructions: [Component Name]

## Prerequisites

**Services/Dependencies Required:**
- Docker containers: `docker-compose up -d postgres redis`
- Environment variables: `export DATABASE_URL=postgresql://...`
- External services: Start mock API server on port 9000

**Installation:**
```bash
# Backend dependencies
cd backend && poetry install

# Frontend dependencies
cd frontend && npm install
```

## Setup Steps

1. **Initialize database:**
   ```bash
   python scripts/init_db.py
   python scripts/seed_test_data.py
   ```

2. **Start required services:**
   ```bash
   docker-compose up -d
   # Wait 5 seconds for services to be ready
   sleep 5
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env - set DATABASE_URL, JWT_SECRET, etc.
   ```

## Running Tests

### Unit Tests
```bash
# Run all unit tests for this component
pytest tests/auth/ -v --tb=short

# Expected output:
# ============== test session starts ==============
# collected 42 items
# tests/auth/test_core.py::test_authenticate_user PASSED
# [... 40 more tests ...]
# ============== 42 passed in 3.2s ==============
```

### Integration Tests
```bash
# Start backend first (in background)
uvicorn main:app --reload --port 8002 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# Run integration tests
pytest tests/integration/test_auth_api.py -v

# Expected output:
# ============== 15 passed in 8.1s ==============

# Stop backend
kill $BACKEND_PID
```

### Manual Verification (Optional)
```bash
# Start backend
uvicorn main:app --reload --port 8002

# In another terminal, test login endpoint
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# Expected response:
# {"token": "eyJ...", "user": {"id": 1, "email": "test@example.com"}}
```

## Test Results (Phase 2 Execution)

**Date**: [Current date]
**All tests passing**: ✅ YES

**Unit tests**: 42/42 passed (100%)
**Integration tests**: 15/15 passed (100%)
**Manual verification**: ✅ All endpoints responding correctly

## Troubleshooting

**Issue**: Database connection error
**Solution**: Ensure PostgreSQL is running on port 5432: `docker ps | grep postgres`

**Issue**: Port 8002 already in use
**Solution**: Kill existing process: `lsof -ti:8002 | xargs kill -9`

**Issue**: Import errors in tests
**Solution**: Install dependencies: `poetry install` or `pip install -r requirements.txt`
```

**Adapt this template to your component's needs!**

**After creating this file:**
- ✅ Test that P3 can follow these instructions successfully
- ✅ Include reference to this file in your P3 task description
- ✅ Save the file path - you'll need it for STEP 19

STEP 17: CHECK FOR EXISTING PHASE 3 TASKS FOR YOUR TICKET

**CRITICAL: Before creating Phase 3 validation task, check if one already exists for YOUR ticket!**

**YOU ALREADY HAVE THE TICKET ID** - it was provided to you when your task was created, and you used it in STEP 0A with `get_ticket(ticket_id)`.

```python
# Use the SAME ticket_id you got in STEP 0A
my_ticket_id = "[your ticket ID from STEP 0A]"

# Get all tasks to check if a Phase 3 task already exists for YOUR ticket
existing_tasks = mcp__hephaestus__get_tasks({
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "all"
})

# Review the results - look for tasks where:
# 1. The description contains: f"TICKET: {my_ticket_id}"
# 2. The description starts with "Phase 3:"
#
# If you find a Phase 3 task for your ticket_id:
#   - DO NOT create a duplicate
#   - Skip to STEP 20 (mark your task done)
# If NO Phase 3 task exists for your ticket_id:
#   - Proceed to STEP 19 (create the Phase 3 task)
```

STEP 18: MOVE TICKET TO BUILDING-DONE STATUS

**Design + implementation + testing complete! Move ticket to "building-done" to show this phase is finished.**
**Phase 3 will move it from "building-done" to "validating" when they start.**

```python
mcp__hephaestus__change_ticket_status({
    "ticket_id": "[your ticket ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "new_status": "building-done",
    "comment": "Design + implementation + testing complete! Design at design/[component]_design.md, code at src/component/. ALL TESTS PASSING (see Phase 2 Testing Summary). Moving to 'building-done'. Ready for Phase 3 validation."
})
```

STEP 19: CREATE PHASE 3 VALIDATION TASK (DO NOT CREATE NEW TICKET!)

**🚨🚨🚨 CRITICAL: DO NOT CREATE A NEW TICKET! 🚨🚨🚨**

You are working on a ticket that was created by Phase 1.
When creating the Phase 3 task, you must:
1. Include "TICKET: {ticket_id}" in the task description
2. **Pass the ticket_id parameter** to create_task
3. **DO NOT** call create_ticket - the ticket already exists!

**The SAME ticket flows through all phases:**
- Phase 1 created the ticket → You received it
- You (Phase 2) worked on it → Pass it to Phase 3
- Phase 3 will work on it and resolve it

**🚨 MANDATORY: Include "TICKET: {ticket_id}" in description AND pass ticket_id parameter! 🚨**

```python
# Extract the ticket ID you've been working on
my_ticket_id = "[your ticket ID from STEP 0]"

# Create Phase 3 task - pass the SAME ticket ID forward
mcp__hephaestus__create_task({
    "description": f"Phase 3: Validate & Document [COMPONENT_NAME] - TICKET: {my_ticket_id}. 🚨 CRITICAL: Read run_instructions/[component]_test_instructions.md for test setup! Run comprehensive test suite (Phase 2 already tested - verify again), fix bugs via Task tool if any, write documentation. Implementation at src/component/. Design spec: design/[component]_design.md. Phase 2 reports all tests passing. Test setup documented in run_instructions/. Must validate: [critical features from ticket].",
    "done_definition": f"All tests executed and validated, bugs fixed via Task tool (if any found), documentation written. Ticket {my_ticket_id} resolved and moved to 'done' status.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "phase_id": 3,
    "priority": "high",
    "cwd": ".",
    "ticket_id": my_ticket_id  # 🚨 CRITICAL: Pass the ticket ID here!
})
```

**What NOT to do:**
❌ DO NOT call `create_ticket()` - the ticket already exists!
❌ DO NOT create a new ticket ID - use the one you extracted in STEP 0A!
❌ DO NOT forget the `ticket_id` parameter in create_task!

═══════════════════════════════════════════════════════════════════════
🚨🚨🚨 MANDATORY PRE-FLIGHT CHECKLIST - READ BEFORE MARKING DONE! 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════

**⛔ YOU CANNOT MARK YOUR TASK AS DONE UNTIL ALL BOXES ARE CHECKED! ⛔**

**CHECKLIST (ALL MUST BE ✅):**

□ ✅ Design document created (design/[component]_design.md) OR skipped for reopened task
□ ✅ All code implemented per design specification
□ ✅ All tests passing (100% pass rate verified in STEP 12-16)
□ ✅ Test instructions file created (run_instructions/[component]_test_instructions.md)
□ ✅ Ticket moved to "building-done" status
□ ✅ **Phase 3 validation task CREATED** ← 🔥 THIS IS CRITICAL! 🔥

**IF ANY BOX IS UNCHECKED, YOU MUST COMPLETE IT BEFORE PROCEEDING!**

**🚨🚨🚨 THE #1 MOST COMMON FAILURE: FORGETTING TO CREATE P3 TASK! 🚨🚨🚨**

**⛔ STOP AND VERIFY RIGHT NOW:**
- Did I create the Phase 3 validation task in STEP 19? (YES/NO)
- If NO: GO BACK TO STEP 19 IMMEDIATELY!
- If YES: Verify it includes "TICKET: {ticket_id}" and run_instructions reference

**THE WORKFLOW BREAKS IF YOU DON'T CREATE P3 TASK!**

Your Phase 2 work is WORTHLESS if Phase 3 never validates it!
If you haven't created the P3 task yet:
- ⛔ STOP what you're doing
- 🔙 Go back to STEP 19
- ✅ Create the P3 task with ticket ID and test instructions reference
- 🔄 Then return here

**ONLY AFTER ALL BOXES ARE CHECKED can you proceed to STEP 20!**

═══════════════════════════════════════════════════════════════════════

STEP 20: MARK YOUR TASK AS DONE

**🚨 MANDATORY: After moving ticket to 'building-done' and creating Phase 3 task, mark your Phase 2 task as DONE! 🚨**

```python
mcp__hephaestus__update_task_status({
    "task_id": "[your Phase 2 task ID]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",
    "status": "done",
    "summary": "[Component] designed + implemented + tested. Design at design/[component]_design.md, code at src/component/. ALL TESTS PASSING (unit tests + manual verification complete). Ticket moved to 'building-done'. Phase 3 validation task created with ticket ID."
})
```

**This is CRITICAL - without marking your task as Done, the system doesn't know you're finished!**

Your task is complete when:
✅ Design document created (design/[component]_design.md)
✅ All interfaces and APIs specified in design
✅ All code implemented per design specification
✅ Test stubs created
✅ Code formatted and linted
✅ **ALL TESTS PASSING** (STEP 12-16: comprehensive testing complete)
✅ **Component verified working** (unit tests + manual testing)
✅ Design and implementation decisions saved to memory
✅ Ticket moved to "building-done" status
✅ Phase 3 task created with "TICKET: xxx" in description
✅ Your Phase 2 task marked as "done"

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Read ticket FIRST to understand scope
- **For web apps: Create frontend/ and backend/ directories** (NEVER single src/)
- **For backend: Configure server to run on PORT 8002** (PORT 8000 is RESERVED!)
- Design ONE component exhaustively
- Create [component]_design.md with full specification
- Implement ALL code per design specification exactly
- Write clean, readable, maintainable code
- Add inline comments for complex logic
- Create comprehensive test stubs
- Run linters and fix issues
- **VALIDATE your code works before handoff (STEP 10 - MANDATORY!)**
- Save design and implementation decisions to memory
- Move ticket: backlog → building → building-done
- Create ONE Phase 3 validation task with ticket ID

❌ DO NOT:
- **Use PORT 8000 for backend** (it's RESERVED - use 8002!)
- **Mix frontend and backend in single src/** (must be separate directories!)
- Add features not in ticket description
- Skip features mentioned in ticket
- Run comprehensive tests (that's Phase 3)
- Write documentation (that's Phase 3)
- Implement features not in the design
- Skip error handling
- **Skip self-validation (STEP 10) - this is MANDATORY!**
- Move ticket to "validating" (move to "building-done" instead)
- Resolve tickets (ONLY Phase 3 can resolve tickets!)
- Create tasks without "TICKET: xxx" in descriptions
- Forget to mark your Phase 2 task as "done" when finished
- Create duplicate tasks (search first!)
- Create new tickets (ticket already exists!)""",
    outputs=[
        "design/[component]_design.md with complete specification (or skipped for reopened tasks)",
        "Production code implementing the specification at src/component/ (or frontend/, backend/)",
        "Test stubs in tests/ directory",
        "ALL TESTS PASSING - comprehensive testing completed (unit + manual verification)",
        "Phase 2 Testing Summary documenting test results and fixes",
        "run_instructions/[component]_test_instructions.md with test setup and execution details",
        "Memory entries about design decisions and implementation",
        "ONE Phase 3 validation task with ticket ID and test instructions reference",
    ],
    next_steps=[
        "Ticket moved to 'building-done' status, waiting for Phase 3",
        "Phase 3 will move ticket: 'building-done' → 'validating' → routing based on results",
        "Phase 3 will test this implementation",
        "Phase 3 routing: tests pass → write docs & resolve | critical bugs → create Phase 2 fix tasks",
        "If Phase 3 finds critical bugs, new Phase 2 agent will fix and handoff back to Phase 3",
    ],
)
