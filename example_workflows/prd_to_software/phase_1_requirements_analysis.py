"""
Phase 1: Requirements Analysis

Entry point for the PRD to Software workflow. Parses the PRD document and creates
structured tickets with blocking relationships.
"""

from src.sdk.models import Phase

# Phase 1: Requirements Analysis
# Entry point - parses PRD and spawns multiple component design tasks
PHASE_1_REQUIREMENTS_ANALYSIS = Phase(
    id=1,
    name="requirements_analysis",
    description="""Analyze the PRD document and extract structured requirements.

This phase is the entry point for the workflow. It reads the PRD (could be PRD.md,
REQUIREMENTS.md, README.md, or any markdown file), extracts functional and non-functional
requirements, identifies the components that need to be built, and spawns multiple Phase 2
tasks - one for each major component.

Works for ANY type of software project.""",
    done_definitions=[
        "PRD document located and thoroughly analyzed",
        "Functional requirements extracted and documented",
        "Non-functional requirements (performance, security, etc.) identified",
        "Infrastructure needs identified (project setup, build tools, frameworks)",
        "Implementation order and dependencies determined",
        "System components identified and categorized",
        "Dependencies between components mapped with blocking relationships",
        "Success criteria defined (how to know when done)",
        "CRITICAL: Infrastructure tickets created FIRST with no blockers",
        "CRITICAL: Component tickets created with proper blocked_by_ticket_ids",
        "CRITICAL: ONE Phase 2 Plan & Implementation task created for EVERY ticket (1:1 relationship)",
        "All requirements and decisions saved to memory for the hive mind",
    ],
    working_directory=".",
    additional_notes="""═══════════════════════════════════════════════════════════════════════
YOU ARE A REQUIREMENTS ANALYST - UNDERSTAND WHAT TO BUILD
═══════════════════════════════════════════════════════════════════════

🎯 YOUR MISSION: Parse the PRD and spawn component design tasks

═══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL WORKFLOW RULES - READ BEFORE STARTING
═══════════════════════════════════════════════════════════════════════

0. **🚨 ALWAYS USE YOUR ACTUAL AGENT ID! 🚨**
   DO NOT use "agent-mcp" - that's just a placeholder in examples!
   Your actual agent ID is in your task context or environment.

   ❌ WRONG: `"agent_id": "agent-mcp"`
   ✅ RIGHT: `"agent_id": "[your actual agent ID from task context]"`

   Use your real agent ID in ALL MCP tool calls:
   - change_ticket_status
   - create_ticket
   - create_task
   - update_task_status
   - save_memory
   - search_tickets
   - ALL other MCP calls

1. **SEARCH BEFORE CREATING TASKS** (Prevent Duplicates)
   Before creating ANY task, search existing tasks:
   ```python
   existing = mcp__hephaestus__search_tickets({
       "agent_id": "[YOUR ACTUAL AGENT ID]",  # NOT "agent-mcp"!
       "query": "[component name] design",
       "search_type": "hybrid",
       "limit": 5
   })
   # Review results - if similar task exists, DO NOT create duplicate!
   ```

2. **ALWAYS INCLUDE TICKET ID IN TASKS**
   Every task description MUST include: "TICKET: ticket-xxxxx"
   Example: "Phase 2: Design Auth - TICKET: ticket-abc123. ..."

3. **ALWAYS MARK YOUR TASK AS DONE**
   When you finish ALL your work, update your task:
   ```python
   mcp__hephaestus__update_task_status({
       "task_id": "[your task ID]",
       "agent_id": "[YOUR ACTUAL AGENT ID]",  # NOT "agent-mcp"!
       "status": "done",
       "summary": "Requirements analyzed. Created [N] component tickets and Phase 2 tasks."
   })
   ```

4. **ONLY PHASE 5 RESOLVES TICKETS**
   - Phase 1: Create tickets in 'backlog', but NEVER resolve them
   - Only Phase 5 can call resolve_ticket()

═══════════════════════════════════════════════════════════════════════

STEP 1: FIND THE PRD DOCUMENT
Look for files like:
- PRD.md, prd.md
- REQUIREMENTS.md, requirements.md
- README.md (may contain requirements)
- SPEC.md, specification.md
- Any .md file mentioned in the task description

Read it thoroughly. This is your source of truth.

STEP 2: EXTRACT REQUIREMENTS

Functional Requirements (what it must DO):
- Core features and capabilities
- User interactions and workflows
- Data processing and transformations
- Integrations with external systems
- Business logic and rules

Non-Functional Requirements (how it must PERFORM):
- Performance targets (response time, throughput)
- Security requirements (auth, encryption, compliance)
- Scalability needs (users, data volume)
- Availability/reliability targets
- Technology constraints or preferences

**🚨 CRITICAL: RESPECT PRD TECH STACK CHOICES!**
The PRD document specifies EXACT technology choices. You MUST follow them exactly:
- If PRD says "SQLite" → Use SQLite, NOT SQLAlchemy or PostgreSQL
- If PRD says "React" → Use React, NOT Vue or Angular
- If PRD says "FastAPI" → Use FastAPI, NOT Flask or Django
- If PRD says "Basic CSS" → Use Basic CSS, NOT Tailwind or Styled Components

**NEVER substitute technologies unless the PRD explicitly allows alternatives!**
**The tech stack in the PRD is NOT optional - it's a requirement!**

Success Criteria (how to know it's DONE):
- Acceptance criteria for each feature
- Test scenarios that must pass
- Performance benchmarks to meet
- Documentation requirements

STEP 3: IDENTIFY COMPONENTS

Break the system into logical modules. Common patterns:

For Web Applications:
- Authentication/Authorization
- Database layer
- API/Backend services
- Frontend/UI
- External integrations
- Deployment infrastructure

For CLI Tools:
- Argument parsing
- Core logic/engine
- Output formatting
- Configuration management
- Error handling

For Libraries:
- Core API
- Utility functions
- Integration helpers
- Documentation/examples
- Testing framework

For Microservices:
- Individual services
- Inter-service communication
- Data storage
- API gateway
- Monitoring/logging

**Integration Tasks (CRITICAL):**
Think about what integration work is needed to connect components together. Integration tasks should run at the end after individual components are complete. Consider:
- Frontend-backend API integration
- Database integration with services
- Authentication flows across components
- End-to-end workflows
- Component wiring and orchestration

Document each component with:
- Purpose: What does it do?
- Inputs: What data does it receive?
- Outputs: What does it produce?
- Dependencies: What other components does it need?

STEP 4: SAVE TO MEMORY (CRITICAL FOR HIVE MIND)

memory_type: decision
- "Technology stack: [stack] because [reasons]"
- "Architecture pattern: [pattern] because [reasons]"
- "Component [X] must integrate with [Y] via [method]"

memory_type: codebase_knowledge
- "Project type: [web/cli/library/service/etc.]"
- "Primary language: [language]"
- "Key frameworks: [list]"
- "Component list: [all components identified]"

memory_type: warning
- "Security requirement: [specific requirement]"
- "Performance target: [specific target]"
- "MUST NOT [constraint from PRD]"

WHY: All Phase 2+ agents will retrieve these memories to understand
the overall system architecture and constraints.

STEP 5: CREATE REQUIREMENTS DOCUMENT

Create requirements_analysis.md with:

```markdown
# Requirements Analysis

## PRD Summary
[2-3 sentences summarizing what needs to be built]

## Functional Requirements
1. [Requirement 1]
   - Acceptance criteria: [how to verify]
2. [Requirement 2]
   ...

## Non-Functional Requirements
- Performance: [targets]
- Security: [requirements]
- Scalability: [needs]
...

## System Architecture

### Components
1. **[Component Name]**
   - Purpose: [what it does]
   - Inputs: [data it receives]
   - Outputs: [data it produces]
   - Dependencies: [other components]

2. **[Component Name]**
   ...

### Integration Points
- [Component A] → [Component B]: [how they connect]

## Technology Stack
- Language: [choice] because [reasons]
- Framework: [choice] because [reasons]
- Database: [choice] because [reasons]
- Deployment: [choice] because [reasons]

## Success Criteria
✅ [Criterion 1]
✅ [Criterion 2]
...
```

STEP 5A: IDENTIFY INFRASTRUCTURE NEEDS

**CRITICAL: Before identifying components, identify infrastructure setup needs!**

Infrastructure must be built FIRST before any features can be implemented.

**🚨🚨🚨 CRITICAL: INFRASTRUCTURE = SKELETON ONLY, NEVER FEATURES! 🚨🚨🚨**

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

**INFRASTRUCTURE SCOPE RULES - READ CAREFULLY:**

**✅ INFRASTRUCTURE IS:**
- Running setup commands (create-react-app, poetry init, npm init, etc.)
- Creating basic project skeleton with empty folders
- Installing and configuring tools (linters, formatters, build tools)
- Setting up configuration files (.env templates, config files)
- Basic "hello world" or minimal boilerplate to verify setup works

**❌ INFRASTRUCTURE IS NOT:**
- Implementing ANY features or business logic
- Creating components, pages, or modules
- Writing authentication, APIs, database models, etc.
- Anything beyond basic project skeleton and tooling

**EXAMPLES OF CORRECT INFRASTRUCTURE SCOPE:**

✅ **Frontend Infrastructure (React):**
- Create `frontend/` directory
- Run `npx create-react-app frontend --template typescript` (or `npm create vite@latest frontend -- --template react-ts`)
- Install ESLint, Prettier in frontend/
- Create basic folder structure (frontend/src/components/, frontend/src/pages/, frontend/src/utils/)
- Configure Tailwind CSS
- **THAT'S IT! No components, no pages, no features!**

✅ **Backend Infrastructure (FastAPI):**
- Create `backend/` directory
- Run `poetry init` inside backend/ and `poetry add fastapi uvicorn`
- Create backend/main.py with minimal FastAPI app and ONE hello world endpoint
- **CRITICAL: Configure backend to run on PORT 8002 (or any port except 8000!)**
- Set up CORS middleware
- Create folder structure (backend/api/, backend/models/, backend/services/, backend/utils/)
- Create backend/.env.example template
- **THAT'S IT! No auth, no database models, no business logic!**

✅ **Database Infrastructure:**
- Install PostgreSQL
- Create database
- Install SQLAlchemy / ORM
- Create database.py with connection setup
- Initialize Alembic for migrations
- **THAT'S IT! No models, no schemas, no tables!**

❌ **WRONG - TOO MUCH SCOPE:**
- ❌ "Frontend Infrastructure: Create React app AND implement Login component and Dashboard component"
- ❌ "Backend Infrastructure: Set up FastAPI AND implement user authentication and JWT tokens"
- ❌ "Database Infrastructure: Set up PostgreSQL AND create User table and Auth schema"

**All of the above are WRONG! Auth, Login, User models are FEATURES, not infrastructure!**

❌ **WRONG - VIOLATES PROJECT STRUCTURE RULES:**
- ❌ "Backend Infrastructure: Set up FastAPI on port 8000" ← Port 8000 is RESERVED!
- ❌ "Create single src/ directory with both frontend and backend code" ← Must be separate!
- ❌ "Set up unified codebase in src/" ← Frontend and backend MUST be in separate directories!

Ask yourself:
- What needs to be set up before ANY code can be written?
- What project structure/scaffolding is needed?
- What build tools, package managers, or frameworks need initialization?

**⚠️ IF IT IMPLEMENTS A FEATURE OR BUSINESS LOGIC, IT'S NOT INFRASTRUCTURE!**

Common infrastructure needs by project type (SETUP ONLY):

**Web Applications (Frontend):**
- Create `frontend/` directory
- Create React app inside frontend/ (create-react-app, Vite, Next.js)
- TypeScript configuration
- Tailwind CSS / styling setup
- Build tooling (Webpack, Vite)
- **NOT: Router setup, State management, Components, Pages** ← These are features!

**Web Applications (Backend):**
- Create `backend/` directory
- FastAPI/Flask/Django project initialization inside backend/
- **CRITICAL: Configure to run on PORT 8002 or any port EXCEPT 8000!**
- Environment configuration (.env, config files)
- **NOT: Database models, ORM setup, Authentication, API endpoints** ← These are features!

**CLI Tools:**
- Package structure (setuptools, Poetry)
- **NOT: Argument parser, Configuration management, Business logic** ← These are features!

**Libraries:**
- Package structure and setup.py
- Testing framework setup
- **NOT: Core library code, API implementation** ← These are features!

**Microservices:**
- Docker/containerization setup
- **NOT: Service implementation, API gateway, Message queues** ← These are features!

Document infrastructure needs in requirements_analysis.md under new section:

```markdown
## Infrastructure Setup

### Required Infrastructure Components
1. **[Infrastructure Component 1]**
   - Purpose: [what it sets up]
   - Tools: [specific tools/commands]
   - Must be completed before: [which components depend on this]

2. **[Infrastructure Component 2]**
   ...
```

Example for a React + FastAPI app:
```markdown
## Infrastructure Setup

### Required Infrastructure Components
1. **Frontend Project Initialization**
   - Purpose: Set up React TypeScript project with Vite
   - Tools: `npm create vite@latest frontend -- --template react-ts`
   - Must be completed before: All frontend components

2. **Backend Project Initialization**
   - Purpose: Set up FastAPI project structure with Poetry
   - Tools: `poetry init`, create main.py, setup CORS
   - Must be completed before: All API endpoints

3. **Database Setup**
   - Purpose: Initialize PostgreSQL database and SQLAlchemy
   - Tools: PostgreSQL, SQLAlchemy, Alembic migrations
   - Must be completed before: Auth, API endpoints, all database-dependent components

4. **Build and Development Tooling**
   - Purpose: Set up development environment, linters, formatters
   - Tools: ESLint, Prettier (frontend), Black, mypy (backend)
   - Must be completed before: Any code development
```

STEP 5B: DETERMINE IMPLEMENTATION ORDER AND BLOCKING RELATIONSHIPS

**🚨🚨🚨 CRITICAL: YOU MUST PLAN IMPLEMENTATION ORDER BEFORE CREATING TICKETS! 🚨🚨🚨**

**This is NOT optional! You MUST think through dependencies and blocking relationships!**

**DO NOT skip this step. DO NOT create tickets without determining blocking relationships first!**

---

**Sub-step 1: Identify the Implementation Phases**

Infrastructure → Foundational Components → Feature Components → Integration

Write out the implementation phases for YOUR specific project:

```markdown
## Implementation Order for [PROJECT_NAME]

### Phase 1: Infrastructure (FIRST - NO BLOCKERS)
**These have NO dependencies. They MUST be built first.**

List your infrastructure needs:
- [ ] Frontend project setup (e.g., create-react-app, Vite, Next.js)
- [ ] Backend project setup (e.g., FastAPI, Django, Express)
- [ ] Database setup (e.g., PostgreSQL, MySQL, MongoDB)
- [ ] Build tooling (e.g., ESLint, Prettier, Black, mypy)
- [ ] Docker setup (if needed)
- [ ] CI/CD pipeline (if needed)

### Phase 2: Foundation (BLOCKED BY: Infrastructure)
**These depend on infrastructure. They BLOCK feature development.**

List your foundation components:
- [ ] Database schema and models (BLOCKED BY: database setup)
- [ ] Authentication system (BLOCKED BY: database setup, backend setup)
- [ ] Core utilities/helpers (BLOCKED BY: project setup)
- [ ] Logging and monitoring setup (BLOCKED BY: project setup)

### Phase 3: Core Features (BLOCKED BY: Foundation)
**These depend on foundation. They provide main functionality.**

List your feature components:
- [ ] API Layer (BLOCKED BY: auth, database)
- [ ] Business logic components (BLOCKED BY: database, auth)
- [ ] Data processing (BLOCKED BY: database)

### Phase 4: User Interface (BLOCKED BY: Core Features)
**These depend on backend features being ready.**

List your UI components:
- [ ] Frontend components (BLOCKED BY: frontend setup, API)
- [ ] Pages and routing (BLOCKED BY: frontend setup, API)
- [ ] State management (BLOCKED BY: frontend setup)

### Phase 5: Integration (BLOCKED BY: Everything else)
**These depend on all components being complete.**

- [ ] End-to-end workflows
- [ ] Frontend-backend API integration
- [ ] Database integration with services
- [ ] Authentication flows across components
- [ ] Component wiring and orchestration
- [ ] External service integrations
- [ ] Final polish
```

---

**Sub-step 2: Create Explicit Blocking Relationship Map**

**🚨 MANDATORY: For EVERY component, explicitly write down what blocks it! 🚨**

Go through EVERY component from STEP 3 and determine its blockers:

```markdown
## Blocking Relationships for [PROJECT_NAME]

### Infrastructure (No Blockers)
1. **Frontend Setup** → blocked_by_ticket_ids: []
2. **Backend Setup** → blocked_by_ticket_ids: []
3. **Database Setup** → blocked_by_ticket_ids: [Backend Setup ID] (needs backend project structure)

### Foundation Components
4. **Authentication System**
   - BLOCKED BY: Database Setup, Backend Setup
   - blocked_by_ticket_ids: [database_setup_id, backend_setup_id]
   - BLOCKS: API Layer, all protected endpoints

5. **Database Models**
   - BLOCKED BY: Database Setup
   - blocked_by_ticket_ids: [database_setup_id]
   - BLOCKS: Auth, API, all data operations

### Feature Components
6. **API Layer**
   - BLOCKED BY: Authentication, Database Setup, Backend Setup
   - blocked_by_ticket_ids: [auth_id, database_setup_id, backend_setup_id]
   - BLOCKS: Frontend components, business logic

7. **User Registration Component**
   - BLOCKED BY: API Layer, Authentication, Frontend Setup
   - blocked_by_ticket_ids: [api_id, auth_id, frontend_setup_id]
   - BLOCKS: Nothing (can be worked on in parallel with other UI)

8. **Dashboard Component**
   - BLOCKED BY: API Layer, Authentication, Frontend Setup
   - blocked_by_ticket_ids: [api_id, auth_id, frontend_setup_id]
   - BLOCKS: Nothing
```

**VERIFICATION CHECKLIST - DO NOT PROCEED UNTIL YOU CAN CHECK ALL:**
- ✅ Every infrastructure component has `blocked_by_ticket_ids: []` OR only blocked by other infrastructure
- ✅ Every foundation component is blocked by at least one infrastructure component
- ✅ Every feature component is blocked by the foundation components it depends on
- ✅ No component is blocked by a component that comes later in the implementation order
- ✅ You've written out the explicit blocking relationships for EVERY component

**If you cannot check all boxes above, GO BACK and fix your blocking relationships!**

---

**Sub-step 3: Prioritize Based on Dependencies**

For EACH component, assign priority based on how many things it blocks:

- **Critical priority:** Infrastructure + Foundation components that BLOCK many other things
  - Examples: Database setup, Auth system, Backend setup
- **High priority:** Feature components that other features depend on
  - Examples: API layer, Core business logic
- **Medium priority:** UI components, integrations, polish
  - Examples: Individual pages, styling, nice-to-have features

STEP 5C: SEARCH FOR EXISTING TASKS (PREVENT DUPLICATES)

**CRITICAL: Before creating tickets and tasks, check if similar work already exists!**

For EACH component you identified, search to see if a ticket/task already exists:

```python
# Search for existing design tasks for this component
existing_tasks = mcp__hephaestus__search_tickets({
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "query": "[Component Name] design",  # e.g., "Authentication design"
    "search_type": "hybrid",
    "limit": 5
})

# Review the results
# If you find a similar ticket/task for this component:
#   - DO NOT create a duplicate
#   - Use the existing ticket ID
# If no similar ticket exists:
#   - Proceed to create a new ticket (STEP 6A)
```

Example searches:
- "Authentication System design" - before creating auth ticket
- "Database Layer design" - before creating database ticket
- "API Layer design" - before creating API ticket

**If you find an existing ticket for a component, skip creating a new one for that component.**
**Only create tickets for components that don't already have tickets.**

STEP 6A: CREATE TICKETS WITH BLOCKING RELATIONSHIPS (USE YOUR STEP 5B MAP!)

**🚨🚨🚨 CRITICAL: USE THE BLOCKING RELATIONSHIPS YOU JUST MAPPED OUT IN STEP 5B! 🚨🚨🚨**

**You MUST create tickets with the EXACT `blocked_by_ticket_ids` you determined in Step 5B Sub-step 2!**

**DO NOT create tickets in random order. DO NOT skip the `blocked_by_ticket_ids` parameter!**

---

**Ticket Creation Order (STRICTLY FOLLOW THIS ORDER):**

1. **Infrastructure tickets FIRST** (blocked_by_ticket_ids: [] or only other infrastructure)
2. **Foundation tickets SECOND** (blocked_by_ticket_ids: [infrastructure IDs])
3. **Feature tickets THIRD** (blocked_by_ticket_ids: [foundation IDs + infrastructure IDs])
4. **Integration tickets LAST** (blocked_by_ticket_ids: [feature IDs])

**Why this order matters:**
- You need the ticket IDs from infrastructure to block foundation tickets
- You need the ticket IDs from foundation to block feature tickets
- Creating in order ensures you have the IDs you need for blocking

---

**For EACH ticket you create, you MUST:**
1. Look at your STEP 5B Sub-step 2 blocking map
2. Find what this component is BLOCKED BY
3. Use those ticket IDs in `blocked_by_ticket_ids: [...]`
4. Save the new ticket ID - other tickets will need it for blocking!

**Example workflow:**
```python
# Step 1: Create backend infra (no blockers)
backend_infra_id = create_ticket(...)["ticket_id"]  # Save this ID!

# Step 2: Create database setup (blocked by backend infra - you have the ID from step 1)
database_id = create_ticket(..., blocked_by_ticket_ids=[backend_infra_id])["ticket_id"]  # Save this ID!

# Step 3: Create auth (blocked by database AND backend - you have both IDs from above)
auth_id = create_ticket(..., blocked_by_ticket_ids=[database_id, backend_infra_id])["ticket_id"]  # Save this ID!

# Step 4: Create API (blocked by auth, database, backend - you have all IDs from above)
api_id = create_ticket(..., blocked_by_ticket_ids=[auth_id, database_id, backend_infra_id])["ticket_id"]
```

**See how each ticket uses the IDs from previous tickets? That's the blocking chain!**

---

**🚨🚨🚨 CRITICAL: WRITE DETAILED TICKET DESCRIPTIONS! 🚨🚨🚨**

**Before creating ANY ticket, read this carefully:**

**Your ticket descriptions are THE ONLY INFORMATION downstream agents will have!**

Agents in Phase 2, 3, 4, and 5 will ONLY read the ticket description to understand what to do. They will NOT read the PRD. They will NOT read other documentation. They will ONLY read YOUR ticket description!

**Therefore, your ticket descriptions MUST be:**

1. **LONG** - At least 10-15 lines minimum. More is better!
2. **DETAILED** - Include every specific requirement from the PRD
3. **EXPLICIT** - Don't assume anything - spell everything out
4. **COMPLETE** - Cover all acceptance criteria, edge cases, requirements
5. **STRUCTURED** - Use the format shown below (Purpose, Scope, Dependencies, etc.)
6. **SPECIFIC** - Include exact file paths, function names, field names from PRD
7. **CLEAR** - Write as if the reader has never seen the PRD before

**❌ BAD ticket description (TOO SHORT):**
```
"Set up authentication system with login and registration"
```
This is USELESS! The agent won't know:
- Which authentication method? JWT? Sessions?
- What fields are required?
- What validation rules?
- What security requirements?
- What endpoints to create?

**✅ GOOD ticket description (DETAILED):**
```
## Component: Authentication System

### Purpose
Implement comprehensive user authentication including registration, login, session management, and password operations using JWT tokens as specified in PRD section 1.1.

### Scope
- User registration with email validation (PRD REQ-AUTH-001)
  - Fields: email (unique), password (min 8 chars, complexity requirements)
  - Email verification with 24hr token expiry (REQ-AUTH-002)
  - Password hashing with bcrypt cost 12 (REQ-SEC-001)

- Login with JWT tokens (REQ-AUTH-006 to REQ-AUTH-010)
  - Access tokens: 1 hour expiry
  - Refresh tokens: 30 day expiry (90 days with "remember me")
  - Rate limiting: 5 attempts per 15 minutes per IP (REQ-SEC-007)

- Password reset functionality (REQ-AUTH-011 to REQ-AUTH-014)
  - Email-based reset with secure token
  - Token expiry: 1 hour
  - Password complexity validation

- User profile management (REQ-AUTH-015 to REQ-AUTH-018)
  - Update email, password
  - Account deletion with 30-day grace period

### Dependencies
- Database Infrastructure (needs User model)
- Backend Infrastructure (needs FastAPI structure)

### Blocks
All protected API endpoints depend on this authentication system.

### Reference
See PRD section 1.1 for complete authentication requirements (REQ-AUTH-001 to REQ-AUTH-018).
```

**This is good because it:**
- ✅ Specifies exact requirements from PRD
- ✅ Includes token expiry times
- ✅ Lists security constraints (bcrypt cost 12, rate limiting)
- ✅ Details all functionality (registration, login, reset, profile)
- ✅ References specific PRD sections

**EVERY ticket you create MUST be this detailed!**

**Template for ticket descriptions:**
```
## Component: [Component Name]

### Purpose
[1-2 sentences explaining what this component does and why it exists]

### Scope
[Detailed bullet list of EVERY feature, requirement, and acceptance criterion]
- Feature 1 (PRD REQ-XXX-YYY)
  - Sub-requirement 1 with specific details
  - Sub-requirement 2 with specific details

- Feature 2 (PRD REQ-XXX-YYY)
  - Implementation details
  - Validation rules
  - Edge cases to handle

[Continue for ALL features...]

### Dependencies
[What this component depends on]

### Blocks
[What depends on this component]

### Reference
See PRD section X.Y for complete requirements.
```

**Remember: Downstream agents ONLY see the ticket description!**
**If you don't write it in the ticket, they won't know to do it!**
**Write LONG, DETAILED descriptions or agents will miss requirements!**

---

**Infrastructure Tickets** (CREATE THESE FIRST):

```python
# Example 1: Frontend Infrastructure (MINIMAL SETUP ONLY!)
frontend_infra_ticket = mcp__hephaestus__create_ticket({
    "workflow_id": "[workflow_id]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "title": "Infrastructure: Frontend Project Setup",
    "description": (
        "## Infrastructure: Frontend Project Setup\\n\\n"
        "### Purpose\\n"
        "Initialize React TypeScript project skeleton with basic tooling in frontend/ directory. SETUP ONLY - NO FEATURES OR COMPONENTS!\\n\\n"
        "### Scope\\n"
        "🚨 CRITICAL: INFRASTRUCTURE = SKELETON ONLY! DO NOT IMPLEMENT FEATURES!\\n\\n"
        "🚨 CRITICAL: ALL frontend code MUST be in frontend/ directory (not src/ or root)!\\n\\n"
        "ONLY do the following setup steps:\\n"
        "- Create frontend/ directory in project root\\n"
        "- Run `npm create vite@latest frontend -- --template react-ts`\\n"
        "- Install ESLint, Prettier in frontend/\\n"
        "- Configure Tailwind CSS (install only, no custom styles)\\n"
        "- Create empty folder structure (frontend/src/components/, frontend/src/pages/, frontend/src/utils/)\\n"
        "- Configure TypeScript strict mode\\n"
        "- Verify dev server runs with default Vite template\\n\\n"
        "❌ DO NOT IMPLEMENT:\\n"
        "- ❌ NO components (Login, Dashboard, etc.)\\n"
        "- ❌ NO pages or routing\\n"
        "- ❌ NO state management setup\\n"
        "- ❌ NO API integration\\n"
        "- ❌ NOTHING beyond basic project skeleton!\\n\\n"
        "### Dependencies\\n"
        "None - this is infrastructure setup\\n\\n"
        "### Blocks\\n"
        "All frontend components depend on this infrastructure being set up first.\\n\\n"
        "### Reference\\n"
        "See requirements_analysis.md 'Infrastructure Setup' section 1."
    ),
    "ticket_type": "component",
    "priority": "critical",  # Infrastructure is always critical!
    "tags": ["phase-2-pending", "infrastructure", "frontend"],
    "blocked_by_ticket_ids": [],  # Infrastructure has no blockers
})
frontend_infra_id = frontend_infra_ticket["ticket_id"]

# Example 2: Backend Infrastructure (MINIMAL SETUP ONLY!)
backend_infra_ticket = mcp__hephaestus__create_ticket({
    "workflow_id": "[workflow_id]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "title": "Infrastructure: Backend Project Setup",
    "description": (
        "## Infrastructure: Backend Project Setup\\n\\n"
        "### Purpose\\n"
        "Initialize FastAPI project skeleton with basic tooling in backend/ directory. SETUP ONLY - NO FEATURES OR ENDPOINTS!\\n\\n"
        "### Scope\\n"
        "🚨 CRITICAL: INFRASTRUCTURE = SKELETON ONLY! DO NOT IMPLEMENT FEATURES!\\n\\n"
        "🚨 CRITICAL: ALL backend code MUST be in backend/ directory (not src/ or root)!\\n\\n"
        "🚨 CRITICAL: Backend MUST run on PORT 8002 (or any port EXCEPT 8000)! Port 8000 is RESERVED!\\n\\n"
        "ONLY do the following setup steps:\\n"
        "- Create backend/ directory in project root\\n"
        "- Run `poetry init` inside backend/ and `poetry add fastapi uvicorn`\\n"
        "- Create backend/main.py with minimal FastAPI app and ONE hello world endpoint\\n"
        "- **CRITICAL: Configure uvicorn to run on PORT 8002** (not 8000!)\\n"
        "- Set up CORS middleware (basic config only)\\n"
        "- Create backend/.env.example file template with PORT=8002\\n"
        "- Create empty folder structure (backend/api/, backend/models/, backend/services/, backend/utils/)\\n"
        "- Install Black, mypy (configuration only, no custom rules)\\n"
        "- Verify server runs with `uvicorn main:app --reload --port 8002`\\n\\n"
        "❌ DO NOT IMPLEMENT:\\n"
        "- ❌ NO authentication or user management\\n"
        "- ❌ NO database models or connections\\n"
        "- ❌ NO API endpoints beyond hello world\\n"
        "- ❌ NO business logic or services\\n"
        "- ❌ NOTHING beyond basic project skeleton!\\n\\n"
        "### Dependencies\\n"
        "None - this is infrastructure setup\\n\\n"
        "### Blocks\\n"
        "All backend components depend on this infrastructure being set up first.\\n\\n"
        "### Reference\\n"
        "See requirements_analysis.md 'Infrastructure Setup' section 2."
    ),
    "ticket_type": "component",
    "priority": "critical",
    "tags": ["phase-2-pending", "infrastructure", "backend"],
    "blocked_by_ticket_ids": [],
})
backend_infra_id = backend_infra_ticket["ticket_id"]

# Example 3: Database Infrastructure (MINIMAL SETUP ONLY!)
database_infra_ticket = mcp__hephaestus__create_ticket({
    "workflow_id": "[workflow_id]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "title": "Infrastructure: Database Setup",
    "description": (
        "## Infrastructure: Database Setup\\n\\n"
        "### Purpose\\n"
        "Set up database connection skeleton. SETUP ONLY - NO MODELS OR SCHEMAS!\\n\\n"
        "### Scope\\n"
        "🚨 CRITICAL: INFRASTRUCTURE = CONNECTION SETUP ONLY! DO NOT CREATE MODELS!\\n\\n"
        "ONLY do the following setup steps:\\n"
        "- Install PostgreSQL (or SQLite for development)\\n"
        "- Create database\\n"
        "- Install SQLAlchemy\\n"
        "- Create database.py with basic connection setup and declarative base\\n"
        "- Initialize Alembic for migrations (initialization only)\\n"
        "- Create database connection pool configuration\\n"
        "- Verify connection works with simple test query\\n\\n"
        "❌ DO NOT IMPLEMENT:\\n"
        "- ❌ NO database models (User, Product, etc.)\\n"
        "- ❌ NO database schemas or tables\\n"
        "- ❌ NO migrations beyond initial Alembic setup\\n"
        "- ❌ NO CRUD operations or database logic\\n"
        "- ❌ NOTHING beyond connection setup!\\n\\n"
        "### Dependencies\\n"
        "- Backend Infrastructure (needs project structure)\\n\\n"
        "### Blocks\\n"
        "Auth, API, and all data-dependent components depend on this.\\n\\n"
        "### Reference\\n"
        "See requirements_analysis.md 'Infrastructure Setup' section 3."
    ),
    "ticket_type": "component",
    "priority": "critical",
    "tags": ["phase-2-pending", "infrastructure", "database"],
    "blocked_by_ticket_ids": [backend_infra_id],  # Blocked by backend infra
})
database_infra_id = database_infra_ticket["ticket_id"]
```

**Component Tickets** (CREATE AFTER INFRASTRUCTURE):

Now create tickets for feature components WITH PROPER BLOCKING:

```python
# Foundation Component Example: Authentication
# Auth depends on Database infrastructure being complete
auth_ticket = mcp__hephaestus__create_ticket({
    "workflow_id": "[workflow_id]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "title": "Authentication System",
    "description": (
        "## Component: Authentication System\\n\\n"
        "### Purpose\\n"
        "Handle user login, registration, session management, and password reset using JWT-based tokens.\\n\\n"
        "### Scope\\n"
        "- User registration and login\\n"
        "- JWT token generation and validation\\n"
        "- Password hashing and verification\\n"
        "- Session management\\n"
        "- Password reset flow\\n\\n"
        "### Dependencies\\n"
        "- Database Infrastructure (for user storage)\\n"
        "- Backend Infrastructure (for API structure)\\n\\n"
        "### Blocks\\n"
        "All protected API endpoints depend on this authentication system.\\n\\n"
        "### Integration Points\\n"
        "- Provides authentication middleware for API\\n"
        "- Stores user data in database\\n"
        "- Returns JWT tokens to clients\\n\\n"
        "### Reference\\n"
        "See requirements_analysis.md section 3.1 for full authentication requirements."
    ),
    "ticket_type": "component",
    "priority": "critical",  # Auth is critical - many things depend on it
    "tags": ["phase-2-pending", "component", "auth", "foundation"],
    "blocked_by_ticket_ids": [database_infra_id, backend_infra_id],  # Can't build auth until DB and backend infra exist!
})
auth_ticket_id = auth_ticket["ticket_id"]

# Feature Component Example: API Layer
# API depends on Auth being complete
api_ticket = mcp__hephaestus__create_ticket({
    "workflow_id": "[workflow_id]",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "title": "API Layer",
    "description": (
        "## Component: API Layer\\n\\n"
        "### Purpose\\n"
        "RESTful API endpoints with authentication middleware, error handling, and rate limiting.\\n\\n"
        "### Scope\\n"
        "- REST API endpoint definitions\\n"
        "- Request/response validation\\n"
        "- Authentication middleware integration\\n"
        "- Error handling and responses\\n"
        "- Rate limiting\\n\\n"
        "### Dependencies\\n"
        "- Authentication System (for auth middleware)\\n"
        "- Database Infrastructure (for data access)\\n"
        "- Backend Infrastructure (for FastAPI structure)\\n\\n"
        "### Integration Points\\n"
        "- Exposes HTTP API to clients\\n"
        "- Uses Auth component for authentication\\n"
        "- Uses Database for data persistence\\n\\n"
        "### Reference\\n"
        "See requirements_analysis.md section 3.3 for API requirements."
    ),
    "ticket_type": "component",
    "priority": "high",
    "tags": ["phase-2-pending", "component", "api", "feature"],
    "blocked_by_ticket_ids": [auth_ticket_id, database_infra_id, backend_infra_id],  # API needs auth and database!
})
api_ticket_id = api_ticket["ticket_id"]

# Save all ticket IDs - you'll need them for Phase 2 tasks!
```

**Key principles:**
- Infrastructure tickets: `priority="critical"`, `blocked_by_ticket_ids=[]`
- Foundation tickets (Auth, DB models): `priority="critical"`, blocked by infrastructure
- Feature tickets: `priority="high"`, blocked by foundation components they depend on
- Use `blocked_by_ticket_ids=[...]` to enforce implementation order

---

**🚨🚨🚨 MANDATORY BLOCKING VERIFICATION - DO THIS BEFORE MOVING TO STEP 6B! 🚨🚨🚨**

**After creating all tickets, you MUST verify that you actually set up blocking relationships correctly!**

Go back through ALL tickets you just created and verify:

```markdown
## Blocking Relationship Verification

### Infrastructure Tickets Created
- [ ] Frontend Setup: blocked_by_ticket_ids = [] ✅
- [ ] Backend Setup: blocked_by_ticket_ids = [] ✅
- [ ] Database Setup: blocked_by_ticket_ids = [backend_setup_id] ✅

### Foundation Tickets Created
- [ ] Authentication: blocked_by_ticket_ids = [database_id, backend_id] ✅
- [ ] Database Models: blocked_by_ticket_ids = [database_id] ✅

### Feature Tickets Created
- [ ] API Layer: blocked_by_ticket_ids = [auth_id, database_id, backend_id] ✅
- [ ] User Registration: blocked_by_ticket_ids = [api_id, auth_id, frontend_id] ✅
- [ ] Dashboard: blocked_by_ticket_ids = [api_id, auth_id, frontend_id] ✅

### Integration Tickets Created (if needed)
- [ ] Frontend-Backend Integration: blocked_by_ticket_ids = [api_id, frontend_id] ✅
- [ ] End-to-End Workflows: blocked_by_ticket_ids = [all component IDs] ✅

### Verification Checks
- ✅ EVERY foundation ticket has at least one infrastructure ticket blocking it
- ✅ EVERY feature ticket has at least one foundation ticket blocking it
- ✅ EVERY integration ticket is blocked by ALL components it integrates
- ✅ NO ticket can start before its blockers are resolved
- ✅ Infrastructure tickets form the base (most have no blockers or only other infrastructure)
- ✅ The dependency chain makes logical sense (can't build auth without database)
```

**CRITICAL CHECKS - ALL MUST BE TRUE:**
1. ✅ Did you create tickets in order (infrastructure → foundation → features)?
2. ✅ Did you save each ticket ID after creation so you could use it for blocking?
3. ✅ Did you use `blocked_by_ticket_ids=[...]` for tickets that have dependencies?
4. ✅ Did you use empty `blocked_by_ticket_ids=[]` for infrastructure with no dependencies?
5. ✅ Do the blocking relationships match what you planned in STEP 5B Sub-step 2?

**If ANY check is ❌, you did NOT set up blocking correctly! You must fix this!**

**Common mistakes to avoid:**
- ❌ Creating all tickets with `blocked_by_ticket_ids=[]` (nothing is blocked - wrong!)
- ❌ Not saving ticket IDs and therefore can't use them for blocking later tickets
- ❌ Creating tickets in random order instead of infrastructure → foundation → features
- ❌ Forgetting to include the `blocked_by_ticket_ids` parameter entirely

**Only proceed to STEP 6B after verifying ALL blocking relationships are correct!**

---

STEP 6B: CREATE PHASE 2 TASKS (ONE TASK PER TICKET - 1:1 RELATIONSHIP)

**🚨🚨🚨 CRITICAL RULE: EVERY TICKET MUST HAVE A CORRESPONDING TASK! 🚨🚨🚨**

**Phase 2 is now "Plan & Implementation" - agents will design AND implement in one phase!**

**⚠️ WARNING: If you created 13 tickets, you MUST create 13 tasks. Not 12. Not 10. Not 5. THIRTEEN!**

**⛔ BEFORE YOU START: READ THIS CAREFULLY!**

**You are about to create Phase 2 tasks. This is a MANDATORY step.**

**IF YOU ENCOUNTER ANY ERRORS WHILE CREATING TASKS:**
1. ✅ **DO**: Read the error message, fix the parameter, retry immediately
2. ✅ **DO**: Use exponential backoff if you get "Internal Server Error"
3. ✅ **DO**: Keep retrying until the task is successfully created
4. ✅ **DO**: Check if your priority is "low", "medium", or "high" (not "critical")
5. ❌ **DON'T**: Give up after 1-2 errors
6. ❌ **DON'T**: Skip the task and move to the next one
7. ❌ **DON'T**: Mark Phase 1 as done if tasks are missing
8. ❌ **DON'T**: Blame "system errors" - FIX and RETRY!

**TASK CREATION IS NOT OPTIONAL. IT IS MANDATORY.**

**This is a 1:1 relationship - NO EXCEPTIONS:**
- Created infrastructure ticket → Create infrastructure task
- Created component ticket → Create component task
- NO tickets without tasks!
- NO tasks without tickets!
- If you created N tickets, you MUST create N tasks!
- If task creation fails, FIX THE ERROR and retry until it succeeds!
- You CANNOT mark Phase 1 as "done" until ALL tasks are created!

**If you finish this step with missing tasks, you have FAILED Phase 1.**

Now create Phase 2 tasks referencing the ticket IDs you just created.

**🚨 MANDATORY: EVERY task description MUST include "TICKET: {ticket_id}"! 🚨**

Create tasks IN THE SAME ORDER as tickets (infrastructure first, then components):

**Infrastructure Tasks** (CREATE THESE FIRST - one for each infrastructure ticket):

```python
# Task for Frontend Infrastructure Ticket
mcp__hephaestus__create_task({
    "description": f"Phase 2: Plan & Implement Frontend Infrastructure Setup - TICKET: {frontend_infra_id}. Design setup steps, then execute: Initialize React TypeScript project with Vite, set up build tooling, linters (ESLint, Prettier), Tailwind CSS. Configure folder structure and TypeScript strict mode. See requirements_analysis.md 'Infrastructure Setup' section 1.",
    "done_definition": f"Frontend infrastructure designed + implemented. Design at frontend_infrastructure_design.md, setup complete and verified. Ticket {frontend_infra_id} moved to 'building-done'. Phase 3 validation task created with ticket ID.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "phase_id": 2,
    "priority": "critical",  # Infrastructure is critical priority
    "cwd": ".",
    "ticket_id": frontend_infra_id  # Pass the ticket ID!
})

# Task for Backend Infrastructure Ticket
mcp__hephaestus__create_task({
    "description": f"Phase 2: Plan & Implement Backend Infrastructure Setup - TICKET: {backend_infra_id}. Design setup steps, then execute: Initialize FastAPI project with Poetry, set up project structure (api/, models/, services/), CORS, environment configuration. See requirements_analysis.md 'Infrastructure Setup' section 2.",
    "done_definition": f"Backend infrastructure designed + implemented. Design at backend_infrastructure_design.md, setup complete and verified. Ticket {backend_infra_id} moved to 'building-done'. Phase 3 validation task created with ticket ID.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "phase_id": 2,
    "priority": "critical",
    "cwd": ".",
    "ticket_id": backend_infra_id  # Pass the ticket ID!
})

# Task for Database Infrastructure Ticket
mcp__hephaestus__create_task({
    "description": f"Phase 2: Plan & Implement Database Infrastructure Setup - TICKET: {database_infra_id}. Design database setup, then execute: Set up PostgreSQL, SQLAlchemy ORM, Alembic migrations. Configure connection pooling and test database. Depends on backend infrastructure. See requirements_analysis.md 'Infrastructure Setup' section 3.",
    "done_definition": f"Database infrastructure designed + implemented. Design at database_infrastructure_design.md, setup complete and verified. Ticket {database_infra_id} moved to 'building-done'. Phase 3 validation task created with ticket ID.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "phase_id": 2,
    "priority": "critical",
    "cwd": ".",
    "ticket_id": database_infra_id  # Pass the ticket ID!
})
```

**Component Tasks** (CREATE AFTER INFRASTRUCTURE TASKS - one for each component ticket):

```python
# Task for Auth Component Ticket
mcp__hephaestus__create_task({
    "description": f"Phase 2: Plan & Implement Authentication System - TICKET: {auth_ticket_id}. Design auth architecture, then implement: user login, registration, session management, password reset with JWT-based tokens. Must integrate with database infrastructure. Blocked by database and backend infrastructure being complete. See requirements_analysis.md section 3.1.",
    "done_definition": f"auth_design.md created with spec, code implemented at src/auth/, tests created, ticket {auth_ticket_id} moved to 'building-done' status, Phase 3 validation task created with ticket ID.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "phase_id": 2,
    "priority": "critical",  # Auth is critical - many things depend on it
    "cwd": ".",
    "ticket_id": auth_ticket_id  # Pass the ticket ID!
})

# Task for API Layer Component Ticket
mcp__hephaestus__create_task({
    "description": f"Phase 2: Plan & Implement API Layer - TICKET: {api_ticket_id}. Design API architecture, then implement: RESTful API endpoints, request/response formats, authentication middleware, error handling, rate limiting. Must integrate with auth and database. Blocked by auth component being complete. See requirements_analysis.md section 3.3.",
    "done_definition": f"api_design.md created with endpoint definitions, code implemented at src/api/, tests created, ticket {api_ticket_id} moved to 'building-done', Phase 3 validation task created with ticket ID.",
    "agent_id": "[YOUR ACTUAL AGENT ID]",  # Use your real agent ID!
    "phase_id": 2,
    "priority": "high",
    "cwd": ".",
    "ticket_id": api_ticket_id  # Pass the ticket ID!
})

# Continue for ALL tickets...
# Remember: ONE task per ticket - if you created 8 tickets, create 8 tasks!
```

**🚨🚨🚨 MANDATORY 1:1 VERIFICATION - DO THIS BEFORE STEP 7! 🚨🚨🚨**

**YOU CANNOT PROCEED TO STEP 7 UNTIL YOU VERIFY THE 1:1 RELATIONSHIP!**

**STEP 6C: COUNT AND VERIFY (MANDATORY - DO NOT SKIP THIS!)**

**1. Count your tickets:**
```python
# Manually count the tickets you created and list them:
infrastructure_tickets = [
    "ticket-xxx",  # Backend setup
    "ticket-yyy",  # Frontend setup
    "ticket-zzz",  # Database setup
    # ... list ALL infrastructure ticket IDs
]

component_tickets = [
    "ticket-aaa",  # Auth system
    "ticket-bbb",  # API layer
    # ... list ALL component ticket IDs
]

total_tickets = len(infrastructure_tickets) + len(component_tickets)
print(f"Total tickets created: {total_tickets}")
```

**2. Count your tasks:**
```python
# Manually count the tasks you created and list them:
infrastructure_tasks = [
    "task-111",  # Backend setup task
    "task-222",  # Frontend setup task
    "task-333",  # Database setup task
    # ... list ALL infrastructure task IDs
]

component_tasks = [
    "task-444",  # Auth system task
    "task-555",  # API layer task
    # ... list ALL component task IDs
]

total_tasks = len(infrastructure_tasks) + len(component_tasks)
print(f"Total tasks created: {total_tasks}")
```

**3. VERIFY THE 1:1 RELATIONSHIP:**
```python
if total_tickets != total_tasks:
    print(f"❌ ERROR: Ticket count ({total_tickets}) != Task count ({total_tasks})")
    print("YOU MUST CREATE MORE TASKS! DO NOT MARK PHASE 1 AS DONE!")
    print(f"Missing tasks: {total_tickets - total_tasks}")
    # GO BACK and create the missing tasks!
else:
    print(f"✅ VERIFIED: {total_tickets} tickets = {total_tasks} tasks (1:1 relationship)")
```

**IF THE COUNTS DON'T MATCH:**

**🚨🚨🚨 STOP! YOU CANNOT PROCEED! YOU MUST FIX THIS! 🚨🚨🚨**

If ticket count != task count, you are **FORBIDDEN** from marking your task as done.

**MANDATORY ACTIONS:**
1. **STOP** - Do NOT move to STEP 7
2. **IDENTIFY** - Which tickets don't have tasks?
3. **FIX ERRORS** - Read error messages, fix parameters
4. **RETRY** - Create tasks again with correct parameters
5. **REPEAT** - Keep retrying until ALL tasks are created
6. **VERIFY** - Count again, ensure ticket count == task count
7. **ONLY THEN** proceed to STEP 7

**YOU ARE NOT ALLOWED TO GIVE UP. YOU MUST CREATE ALL TASKS.**

---

**COMMON ERRORS AND HOW TO FIX THEM:**

**Error: "Internal Server Error"**
- **FIX**: Wait 2 seconds, then retry the EXACT same request
- If it fails again, wait 4 seconds and retry
- If it fails a third time, wait 8 seconds and retry
- **DO NOT GIVE UP** - Keep retrying with exponential backoff
- The server may be temporarily overloaded - persistence will succeed

**Error: Priority validation failed**
- **FIX**: Change `priority: "critical"` to `priority: "high"`
- Valid values are ONLY: "low", "medium", "high"
- Retry immediately after fixing

**Error: Missing required parameter**
- **FIX**: Read the error message to see which parameter is missing
- Add the required parameter
- Retry immediately after fixing

**Error: Validation error on any field**
- **FIX**: Read the error message carefully
- Fix the exact parameter mentioned in the error
- Retry immediately after fixing

---

**RETRY STRATEGY (MANDATORY):**

```python
# For EACH ticket that needs a task:
max_retries = 10
retry_count = 0
task_created = False

while not task_created and retry_count < max_retries:
    try:
        # Try to create the task
        result = mcp__hephaestus__create_task({...})
        task_created = True
        print(f"✅ Task created successfully for ticket {ticket_id}")
    except Exception as error:
        retry_count += 1
        wait_seconds = 2 ** retry_count  # Exponential backoff: 2, 4, 8, 16, 32...
        print(f"❌ Error creating task (attempt {retry_count}/{max_retries}): {error}")
        print(f"Waiting {wait_seconds} seconds before retry...")
        time.sleep(wait_seconds)

        # If it's a validation error, FIX THE PARAMETERS before retry
        if "validation" in str(error).lower():
            # Fix the parameter based on error message
            # Then retry with fixed parameters
            pass

if not task_created:
    print(f"⚠️ Failed to create task after {max_retries} attempts")
    print("DO NOT MARK PHASE 1 AS DONE - MUST CREATE THIS TASK!")
    # GO BACK and try again with different approach
```

**YOU MUST CREATE TASKS FOR ALL TICKETS. NO EXCEPTIONS. NO EXCUSES.**

**"System errors" is NOT a valid reason to skip task creation!**
**"MCP issues" is NOT a valid reason to skip task creation!**
**Retry until it works. Period.**

---

STEP 7: MARK YOUR TASK AS DONE (ONLY AFTER STEP 6C VERIFICATION!)

**🚨🚨🚨 READ THIS CAREFULLY BEFORE PROCEEDING! 🚨🚨🚨**

**YOU CANNOT MARK YOUR TASK AS DONE UNLESS ALL CONDITIONS ARE MET!**

---

**MANDATORY PRE-FLIGHT CHECKLIST (ALL MUST BE TRUE):**

**Before you can mark your task as done, you MUST verify ALL of these:**

1. **Did you count your tickets?**
   - ❌ If NO → Go back and count them now
   - ✅ If YES → Proceed to #2

2. **Did you count your tasks?**
   - ❌ If NO → Go back and count them now
   - ✅ If YES → Proceed to #3

3. **Does ticket count EXACTLY EQUAL task count?**
   - ❌ If NO → **STOP! DO NOT MARK DONE! GO BACK TO STEP 6B AND CREATE MISSING TASKS!**
   - ✅ If YES → Proceed to #4

4. **Did you verify the 1:1 relationship?**
   - ❌ If NO → Go back and verify now
   - ✅ If YES → Proceed to #5

5. **Are ALL tasks successfully created (no errors)?**
   - ❌ If NO → **STOP! DO NOT MARK DONE! FIX ERRORS AND RETRY!**
   - ✅ If YES → Proceed to #6

6. **Do ALL tasks include "TICKET: xxx" in descriptions?**
   - ❌ If NO → Go back and fix task descriptions
   - ✅ If YES → You may proceed to mark done

---

**IF YOU ANSWERED "NO" TO QUESTION #3 OR #5, YOU ARE FORBIDDEN FROM CONTINUING!**

**Examples of FORBIDDEN behavior:**
- ❌ "I created 24 tickets but only 2 tasks due to errors, marking done anyway"
- ❌ "System errors prevented task creation, but I'm done with my part"
- ❌ "MCP issues stopped me from creating all tasks, updating status anyway"
- ❌ "I'll let the next phase handle the missing tasks, marking done"

**ALL OF THESE ARE ABSOLUTELY FORBIDDEN!**

**If you encounter errors:**
1. Read the error message
2. Fix the parameters
3. Retry with exponential backoff (up to 10 times)
4. If it still fails, try a different approach
5. Ask yourself: "Did I use the correct priority value?" (must be low/medium/high)
6. Keep trying until ALL tasks are created
7. Only mark done when ticket count == task count

---

**FINAL VERIFICATION BEFORE MARKING DONE:**

```python
# Count tickets
total_tickets = [count your tickets here]

# Count tasks
total_tasks = [count your tasks here]

# VERIFY
if total_tickets != total_tasks:
    print(f"❌ VERIFICATION FAILED!")
    print(f"Tickets: {total_tickets}, Tasks: {total_tasks}")
    print(f"Missing tasks: {total_tickets - total_tasks}")
    print(f"🚨 DO NOT MARK PHASE 1 AS DONE!")
    print(f"🚨 GO BACK AND CREATE THE MISSING TASKS!")
    # DO NOT PROCEED TO update_task_status
    # YOU ARE FORBIDDEN FROM MARKING DONE
else:
    print(f"✅ VERIFICATION PASSED!")
    print(f"Tickets: {total_tickets}, Tasks: {total_tasks}")
    print(f"1:1 relationship confirmed - proceeding to mark done")

    # ONLY NOW can you mark your task as done:
    mcp__hephaestus__update_task_status({
        "task_id": "[your Phase 1 task ID]",
        "agent_id": "[YOUR ACTUAL AGENT ID]",
        "status": "done",
        "summary": f"Requirements analyzed. Created {total_tickets} component tickets in 'backlog' status with blocking relationships and {total_tasks} Phase 2 design tasks with ticket IDs. VERIFIED 1:1 ticket-to-task relationship ({total_tickets} tickets = {total_tasks} tasks). Verified all blocking relationships are correct. See requirements_analysis.md for details."
    })
```

---

**⛔ ABSOLUTE RULES - NEVER VIOLATE THESE:**

1. **NEVER** mark your task as done if ticket count != task count
2. **NEVER** include phrases like "due to errors" or "MCP issues" in your done summary
3. **NEVER** give up on task creation - retry until success
4. **NEVER** blame the system - fix the parameters and retry
5. **NEVER** proceed to STEP 7 without completing STEP 6C verification

**If you violate these rules, you will break the entire workflow and cause massive problems for downstream agents!**

Your task is complete ONLY when:
✅ requirements_analysis.md created
✅ All components identified and documented
✅ All memories saved
✅ All component tickets created in 'backlog' status
✅ ALL Phase 2 tasks created (one for each ticket) with "TICKET: xxx" in descriptions
✅ STEP 6C verification passed (ticket count == task count)
✅ Your Phase 1 task marked as "done"

═══════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════

✅ DO:
- Read the entire PRD document carefully
- Identify infrastructure needs FIRST (project setup, build tools, etc.)
- **Specify frontend/ and backend/ directories for web apps** (NEVER single src/)
- **Specify PORT 8002 for backend servers** (PORT 8000 is RESERVED!)
- Determine implementation order and dependencies
- Identify ALL major components
- Save comprehensive memories for the hive mind
- Create infrastructure tickets FIRST with no blockers
- Create component tickets with proper blocking relationships
- Create ONE task for EVERY ticket (1:1 relationship)
- Use ticket blocking to enforce correct implementation order
- Document everything in requirements_analysis.md with infrastructure section

❌ DO NOT:
- Design implementations (that's Phase 2)
- Write code (that's Phase 3)
- Test anything (that's Phase 4)
- Skip infrastructure identification (CRITICAL!)
- **Allow backend to use PORT 8000** (it's RESERVED - use 8002!)
- **Allow mixed frontend/backend in single src/** (must be separate directories!)
- Create component tickets without considering dependencies
- Create tickets without corresponding tasks (must be 1:1!)
- Create tasks without "TICKET: xxx" in descriptions
- Resolve tickets (ONLY Phase 5 can resolve tickets!)
- Create duplicate tasks (search first!)
- Forget to set blocked_by_ticket_ids for dependent components

**🚨 ABSOLUTELY FORBIDDEN (WILL BREAK WORKFLOW):**
- **Mark your Phase 1 task as "done" if ticket count != task count** ← THIS IS THE #1 RULE!
- **Mark your Phase 1 task as "done" without completing STEP 6C verification**
- **Give up on task creation due to errors** ← Errors are not an excuse! Retry!
- **Blame "system errors" or "MCP issues" for incomplete work** ← Fix and retry!
- **Skip creating tasks because it's "too hard"** ← Every ticket MUST have a task!
- **Mark done with a summary saying "only X out of Y tasks created"** ← Unacceptable!
- **Proceed to STEP 7 when you know tasks are missing** ← Complete STEP 6B first!

**IF YOU VIOLATE THESE FORBIDDEN RULES, YOU FAIL PHASE 1 COMPLETELY!**

**Remember: Your job is NOT done until ticket count == task count. Period.**""",
    outputs=[
        "requirements_analysis.md with infrastructure setup section and component breakdown",
        "Multiple memory entries documenting decisions and constraints",
        "Infrastructure tickets in 'backlog' status (frontend, backend, database, build tools)",
        "Component tickets in 'backlog' status with proper blocking relationships",
        "ONE Phase 2 Plan & Implementation task for EVERY ticket created (infrastructure + components)",
        "Ticket-to-task mapping documented (1:1 relationship maintained)",
    ],
    next_steps=[
        "Infrastructure tickets (no blockers) can start immediately in Phase 2",
        "Component tickets blocked by infrastructure will wait until blockers are resolved",
        "Phase 2 agents will design + implement, moving tickets: 'backlog' → 'building' → 'building-done'",
        "Ticket blocking ensures correct implementation order (infra → foundation → features)",
        "Phase 2 plan & implementation tasks will run in parallel (respecting blocking constraints)",
        "Each Phase 2 task will spawn Phase 3 validation task with ticket ID",
        "The workflow tree branches out from here with proper dependency management",
    ],
)
