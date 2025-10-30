# PRD to Software Builder Workflow

A fully generic, self-building Hephaestus workflow that takes a PRD (Product Requirements Document) and builds working software. Works for **any** type of software project: web apps, CLIs, libraries, microservices, mobile backends, and more.

## Overview

This workflow implements the best practices from [Workflow Design Best Practices](../../docs/workflows/workflow-design-best-practices.md). It uses 5 specialized phases that work together to:

1. **Analyze** the PRD and identify components
2. **Design** each component in parallel
3. **Implement** code for each component
4. **Validate** through comprehensive testing
5. **Document** the final system

The workflow is **self-building** - it creates a dynamic tree of tasks based on what it discovers in the PRD, enabling massive parallelism and adaptive execution.

## Quick Start

### Prerequisites

1. **Qdrant running:**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Environment configured:**
   ```bash
   # .env file
   LLM_PROVIDER=openai           # or "anthropic"
   OPENAI_API_KEY=sk-...
   LLM_MODEL=gpt-4-turbo
   DATABASE_PATH=./hephaestus.db
   QDRANT_URL=http://localhost:6333
   MCP_PORT=8000
   ```

3. **PRD document exists:**
   - Create `PRD.md`, `REQUIREMENTS.md`, or `README.md` in your project directory
   - Or specify path with `--prd` flag

### Run the Workflow

```bash
# Basic usage (auto-detects PRD file)
python run_prd_workflow.py

# Specify PRD location
python run_prd_workflow.py --prd /path/to/requirements.md

# Fresh start (drop database)
python run_prd_workflow.py --drop-db

# Monitor progress at http://localhost:3000
```

## How It Works

### Phase 1: Requirements Analysis

**Entry point.** Parses the PRD document and extracts:
- Functional requirements (what it must do)
- Non-functional requirements (how it must perform)
- System components (architecture breakdown)
- Success criteria (completion definition)

**Spawns:** Multiple Phase 2 tasks (one per component)

**Example:**
```
PRD identifies:
- Authentication system
- Database layer
- API endpoints
- Frontend UI
- Deployment infrastructure

Phase 1 creates 5 Phase 2 tasks, one for each component.
```

### Phase 2: Solution Design

**Runs in parallel** (one instance per component). Creates detailed specifications:
- Component architecture
- Interfaces and APIs
- Data models and schemas
- Integration points
- Error handling strategy

**Spawns:** One Phase 3 implementation task

**Example:**
```
P2-auth task creates:
- auth_design.md with JWT token structure, password hashing, session management
- Phase 3 task: "Implement authentication per auth_design.md"
```

### Phase 3: Implementation

**Writes actual code** following Phase 2 specifications exactly:
- Implements all interfaces
- Creates test stubs
- Runs linters and formatters
- Documents integration points

**Spawns:** One Phase 4 validation task

**Can be spawned by:**
- Phase 2 (initial implementation)
- Phase 4 (bug fixes)
- Phase 5 (missing features)

### Phase 4: Validation

**The workflow router.** Runs tests and makes routing decisions:

**If tests pass:**
- Component testing → Create Phase 5 documentation task
- System testing → Submit workflow result ✅

**If tests fail:**
- Create Phase 3 fix tasks (one per bug)
- After fixes, retest (Phase 4 self-loop)

**If design flaw found:**
- Create Phase 2 redesign task
- Rebuild and retest

**Example:**
```
P4-test-auth finds 3 bugs:
- Creates P3-fix-bug-1 task
- Creates P3-fix-bug-2 task
- Creates P3-fix-bug-3 task

Each fix task spawns its own P4-retest task.
When all pass, P4 creates P5-doc-auth task.
```

### Phase 5: Documentation

**Creates user-facing docs:**
- README with quick start
- API reference
- Usage examples
- Integration guides
- Deployment instructions

**May spawn:** Phase 3 tasks if missing features discovered

**Marks:** Component as complete

## Workflow Flow

```
P1: Analyze PRD
├─ P2: Design Auth (parallel)
│  └─ P3: Build Auth
│     └─ P4: Test Auth
│        ├─ P3: Fix bug 1
│        │  └─ P4: Retest
│        │     └─ P5: Document Auth ✅
│        └─ P3: Fix bug 2
│           └─ P4: Retest
│
├─ P2: Design Database (parallel)
│  └─ P3: Build Database
│     └─ P4: Test Database
│        └─ P5: Document Database ✅
│
├─ P2: Design API (parallel)
│  └─ P3: Build API
│     └─ P4: Test API
│        ├─ P2: Redesign (design flaw)
│        │  └─ P3: Rebuild API
│        │     └─ P4: Retest API
│        │        └─ P5: Document API ✅
│
└─ [All components done]
   └─ P4: System Integration Test
      └─ P4: Final Validation
         └─ Submit Result ✅
```

## Features

### ✨ Fully Generic
Works for **any** software type:
- ✅ Web applications (Flask, Django, Express, etc.)
- ✅ CLI tools (Python, Go, Rust)
- ✅ Libraries and frameworks
- ✅ Microservices
- ✅ Mobile backends
- ✅ Data pipelines
- ✅ Desktop applications

### 🚀 Massively Parallel
- Multiple components designed simultaneously (Phase 2)
- Multiple components implemented in parallel (Phase 3)
- Multiple tests run concurrently (Phase 4)

### 🔄 Self-Healing
- Tests find bugs → Spawns fix tasks automatically
- Design flaws discovered → Spawns redesign tasks
- Missing features found → Spawns implementation tasks

### 🧠 Hive Mind Coordination
Uses Qdrant memory system:
- Phase 1 saves architecture decisions
- Phase 2 saves component interfaces
- Phase 3 saves integration points
- All phases retrieve memories for context

### 📊 Quality Gates
- Phase 4 validates before proceeding
- Test coverage must be >80%
- All tests must pass (100% pass rate)
- Code quality checks enforced

## Configuration

### Working Directory

Set via environment variable:
```bash
WORKING_DIRECTORY=/path/to/your/project
```

Or uses current directory by default.

### PRD File Detection

Auto-detects in this order:
1. `PRD.md`
2. `prd.md`
3. `REQUIREMENTS.md`
4. `requirements.md`
5. `SPEC.md`
6. `spec.md`
7. `README.md`

Override with `--prd` flag.

### Git Integration

Workflow uses git worktrees for isolation:
- Each agent gets its own worktree
- Branches named: `prd-builder-[agent-id]`
- Auto-commits enabled by default
- Conflict resolution: newest file wins

## Result Submission

The workflow submits a result when final validation passes. The result must include:

1. **Requirements Coverage**
   - Every PRD requirement implemented
   - Evidence for each requirement

2. **Test Results**
   - 100% test pass rate
   - >80% code coverage
   - Full test output

3. **Deployment Evidence**
   - Working deployment instructions
   - Proof application runs

4. **Documentation**
   - README, API docs, deployment guide
   - All tested and accurate

5. **Code Quality**
   - No linting errors
   - No type checking errors
   - Clean, maintainable code

## Monitoring

### Headless Mode (Default)
```bash
python run_prd_workflow.py
```

Monitor via logs:
```bash
tail -f ~/.hephaestus/logs/session-*/backend.log
tail -f ~/.hephaestus/logs/session-*/monitor.log
```

Or use the web UI at http://localhost:3000 for real-time monitoring of:
- Task status
- Agent activity
- System health
- Workflow progress

## Example PRD

```markdown
# Product Requirements: Todo API

## Overview
Build a REST API for managing todo items with user authentication.

## Functional Requirements

### Authentication
- User registration with email/password
- JWT-based authentication
- Password reset via email

### Todo Management
- Create todo items
- List user's todos (with filtering)
- Update todo status
- Delete todos
- Assign priority levels

### API Requirements
- RESTful endpoints
- JSON request/response
- Proper error handling
- Rate limiting

## Non-Functional Requirements
- Response time <100ms for simple queries
- Handle 1000 concurrent users
- PostgreSQL database
- Deploy via Docker

## Success Criteria
- All endpoints working and tested
- >90% test coverage
- Complete API documentation
- Deployment guide tested
```

The workflow will:
1. Identify components (auth, database, API, deployment)
2. Design each in parallel
3. Implement with tests
4. Validate thoroughly
5. Document completely
6. Submit working system

## Troubleshooting

### "No PRD file found"
**Cause:** PRD file not detected in working directory
**Solution:**
- Create `PRD.md` in your project directory
- Or use `--prd /path/to/file.md`

### "Qdrant connection error"
**Cause:** Qdrant not running
**Solution:**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### "Port 8000 already in use"
**Cause:** Previous Hephaestus instance still running
**Solution:**
```bash
# Script auto-kills, but if issues persist:
lsof -ti :8000 | xargs kill -9
```

### Workflow seems stuck
**Check:** Agent logs for errors
```bash
tail -f ~/.hephaestus/logs/session-*/monitor.log
```

Guardian agent monitors and intervenes if agents get stuck.

## Architecture

### Phase Interactions

| From | Creates | To | When |
|------|---------|-----|------|
| P1 | → | P2 (multiple) | For each component |
| P2 | → | P3 | Design complete |
| P3 | → | P4 | Code complete |
| P4 | → | P3 (multiple) | For each bug |
| P4 | → | P2 | Design flaw |
| P4 | → | P5 | Tests pass |
| P4 | → | Result | Final validation |
| P5 | → | P3 | Missing feature |

### Memory System

**Phase 1 saves:**
- `decision`: Technology choices, architecture
- `codebase_knowledge`: Component list, tech stack
- `warning`: Constraints, requirements

**Phase 2 saves:**
- `codebase_knowledge`: Component interfaces, APIs
- `decision`: Design choices, patterns

**Phase 3 saves:**
- `codebase_knowledge`: Implementation details, exports
- `decision`: Implementation approaches

**Phase 4 saves:**
- `discovery`: Test results, validation status
- `error_fix`: Bug descriptions, fixes

**All phases retrieve memories for context.**

## Contributing

To improve this workflow:

1. Follow [Workflow Design Best Practices](../../docs/workflows/workflow-design-best-practices.md)
2. Test with multiple PRD types (web, CLI, library)
3. Ensure phases remain generic (no tech-stack hardcoding)
4. Update documentation

## Related Documentation

- [Workflow Design Best Practices](../../docs/workflows/workflow-design-best-practices.md)
- [Python Phases Guide](../../docs/sdk/python-phases.md)
- [SDK Configuration](../../docs/sdk/configuration.md)
- [Memory System](../../docs/core/memory-system.md)

---

**Version:** 1.0
**Last Updated:** 2025-10-20
**Maintainer:** Hephaestus Core Team
