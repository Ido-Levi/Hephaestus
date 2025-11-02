# coached-data-explore Development Notes

This file tracks progress, learnings, and agent insights for the coached-data-explore project.

## Project Overview

**Goal**: Build a multi-audience data discovery platform that serves:
- Executives (high-level insights)
- Data scientists (technical deep-dives)
- Business analysts (actionable recommendations)

**Approach**: Using Hephaestus PRD-to-software workflow with autonomous agents

## Current Status

**Last Updated**: 2025-11-02

**Phase**: Phase 7 - Multi-audience discovery PRD
**PRD Location**: `/Users/mike/www/ai/coached-data-explore/docs/prds/phase7-multi-audience-discovery-prd.md`

**Active Work**:
- [ ] Phase 1: PRD Analysis (initial task creation)
- [ ] Phase 2: Implementation planning
- [ ] Phase 3: Development & testing

## Key Learnings

### Hephaestus System

**Configuration Discoveries**:
- System designed for OpenRouter + Cerebras + gpt-oss-120b (not gpt-4o-mini)
- Guardian monitoring requires correct multi-provider setup
- Single database approach: `./hephaestus.db` (simpler than per-project DBs)
- Agents need 120-second grace period to register before monitor checks

**Bootstrap Process**:
1. Clean Qdrant collections (optional, for fresh start)
2. Initialize database and collections
3. Start backend server (port 8000)
4. Start monitor (Guardian + agent lifecycle management)
5. Create Phase 1 PRD analysis task
6. Agent spawns in tmux session

**Workflow Phases**:
- Phase 1: PRD Analysis → Extract requirements, create tickets
- Phase 2: Plan & Implementation → Per-component planning
- Phase 3: Development → Implementation with tests
- Phase 4: Validation → Guardian reviews quality

### Agent Observations

**What Works Well**:
- Agents can analyze PRDs and create structured requirements
- Memory system (Qdrant) helps agents share context
- Guardian provides trajectory analysis and alignment scores

**Common Issues**:
- Agents can get stuck on overly complex tasks (need task breakdown)
- Monitor can prematurely kill agents during long-running operations
- Database split issues (fixed with single DB approach)

## Agent Insights

### Session: [DATE]

**Task**: [Description]
**Agent ID**: [UUID]
**Outcome**: [Success/Blocked/In Progress]

**Key Discoveries**:
- [What the agent learned]
- [Decisions made]
- [Blockers encountered]

**Memory Artifacts**:
- [Important context saved to vector DB]
- [Reusable patterns identified]

---

## TODO / Next Steps

- [ ] Monitor Phase 1 agent progress
- [ ] Review generated tickets for completeness
- [ ] Verify infrastructure dependencies identified correctly
- [ ] Check Guardian analyses for quality insights

## Questions / Blockers

- None currently

## Useful Commands

**Check system status**:
```bash
# Backend health
curl http://localhost:8000/health

# View tasks
curl http://localhost:8000/api/tasks | jq

# View agents
curl http://localhost:8000/api/agents | jq

# View tickets
open http://localhost:8000/tickets
```

**Monitor logs**:
```bash
tail -f logs/monitor.out
tail -f logs/server.out
tail -f logs/agent_*.log
```

**Tmux sessions**:
```bash
# List agent sessions
tmux ls

# Attach to agent session
tmux attach -t prd-builder-XXXXXXXX

# Kill stuck agent
tmux kill-session -t prd-builder-XXXXXXXX
```

**Database queries**:
```bash
sqlite3 hephaestus.db "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 5;"
sqlite3 hephaestus.db "SELECT * FROM agents WHERE status='active';"
sqlite3 hephaestus.db "SELECT COUNT(*) FROM guardian_analyses;"
```

## Resources

- **Hephaestus Docs**: https://github.com/Ido-Levi/Hephaestus
- **coached-data-explore Repo**: /Users/mike/www/ai/coached-data-explore
- **PRD**: ../../../coached-data-explore/docs/prds/phase7-multi-audience-discovery-prd.md
