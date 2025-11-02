# Troubleshooting Agent Issues

This guide covers common issues when running Hephaestus agents and their solutions.

## Agent Authorization Failures

**Symptoms:**
- "Agent not authorized for this task" errors
- Task status updates fail
- Ticket creation fails

**Root Cause:**
Agent using incorrect ID (placeholder like 'agent-mcp' instead of actual UUID).

**Solution:**
Agents receive their UUID in the initial prompt under "Your Agent ID: [UUID]". This exact UUID must be used in all MCP tool calls.

**Verification:**
```bash
# Check your agent ID format
curl http://127.0.0.1:8000/validate_agent_id/YOUR-AGENT-ID
```

## Monitor Killing New Agents

**Symptoms:**
- Agents terminated within 20-60 seconds of spawning
- Workflow stops at Phase 1
- Logs show "orphaned session" messages

**Root Cause:**
Race condition where monitor checks for agents in database before registration completes.

**Solution:**
The system now includes a 120-second grace period for newly spawned agents. No action needed.

## Database Split Issues

**Symptoms:**
- "Agent not found" errors
- Backend and agents can't see each other's data
- Multiple `hephaestus*.db` files

**Root Cause:**
Backend and agents using different database files.

**Solution:**
Use the simplified bootstrap approach with single default database:
```bash
python scripts/bootstrap_project.py \
  --working-dir "./your_project" \
  --worktrees "/tmp/hephaestus_worktrees" \
  --prd "./your_project/PRD.md"
```

## Checking System Health

**Verify backend:**
```bash
curl http://127.0.0.1:8000/health
```

**Check database in use:**
```bash
lsof | grep "hephaestus.*db"
```

**View active agents:**
```bash
sqlite3 hephaestus.db "SELECT id, status FROM agents;"
```

**Check tmux sessions:**
```bash
tmux list-sessions
```
