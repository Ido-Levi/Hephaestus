# Diagnostic Agent System

## Overview

The **Diagnostic Agent System** is a self-healing mechanism that prevents workflows from getting permanently stuck. When all tasks are complete but the workflow goal hasn't been achieved, a specialized diagnostic agent analyzes the situation and creates new tasks to push the workflow forward.

## Purpose

In complex workflows, agents sometimes:
- Complete their individual tasks successfully but miss the bigger picture
- Fail to submit final results even though the work is done
- Get stuck in a particular phase when they should move to another
- Need to revisit earlier phases based on failures in later phases

The diagnostic agent serves as a "workflow doctor" that:
1. Detects when the workflow is stuck
2. Analyzes what's been accomplished
3. Diagnoses what's missing
4. Creates targeted tasks to achieve the workflow goal

## When It Activates

The diagnostic agent triggers automatically when **ALL** of the following conditions are met:

1. **Active workflow exists**: A workflow with phases is currently running
2. **Tasks exist**: At least one task has been created in the workflow
3. **All tasks finished**: No tasks have status `pending`, `assigned`, `in_progress`, `under_review`, or `validation_in_progress`
4. **No validated result**: No `WorkflowResult` with status `validated` has been submitted
5. **Cooldown passed**: At least `diagnostic_cooldown_seconds` (default: 60s) have passed since the last diagnostic agent was created
6. **Stuck long enough**: At least `diagnostic_min_stuck_time_seconds` (default: 60s) have passed since the last task was created or completed

## How It Works

### 1. Detection (MonitoringLoop)

Every monitoring cycle (default: 60 seconds), the `MonitoringLoop._check_workflow_stuck_state()` method:

```python
# Pseudo-code
if workflow_exists and has_tasks:
    if all_tasks_finished and no_validated_result:
        if cooldown_passed and stuck_long_enough:
            create_diagnostic_agent()
```

### 2. Context Gathering

When triggered, the system gathers comprehensive context:

**Workflow Information:**
- Workflow goal (from `result_criteria`)
- All phase definitions with their objectives
- Current phase statuses

**Recent History:**
- Last 15 completed/failed agents (configurable)
- Their task descriptions, statuses, and outcomes
- Completion notes and failure reasons

**System Observations:**
- Last 5 Conductor system analyses
- Duplicate work detections
- System coherence scores

**Submitted Results:**
- Any result submissions (even if rejected)
- Validation feedback explaining rejections

### 3. Agent Creation

A diagnostic task and agent are created:

```python
Task(
    description="DIAGNOSTIC: Analyze why workflow has stalled and create tasks to progress toward goal",
    done_definition="Created 1-5 new tasks with clear phase assignments",
    agent_type="diagnostic",
    phase_id=None,  # Diagnostic tasks span all phases
)
```

The diagnostic agent:
- Works in the main repository (no worktree isolation)
- Gets a specialized prompt with all gathered context
- Has access to all Hephaestus MCP tools
- Can create tasks in any phase

### 4. Diagnostic Process

The diagnostic agent follows a structured 4-step process:

**Step 1: Understand the Goal**
- Reads the workflow's `result_criteria`
- Identifies what "success" looks like

**Step 2: Analyze Current State**
- Reviews what agents have accomplished
- Examines which phases have progressed
- Checks what outputs have been created
- Analyzes any result submission failures

**Step 3: Identify the Gap**
- Diagnoses why the goal hasn't been achieved
- Identifies common stuck scenarios:
  - Missing evidence/documentation
  - Incomplete implementation
  - Wrong direction
  - Premature task completion
  - Phase misalignment
  - Validation failures

**Step 4: Create Tasks**
- Uses `create_task` MCP tool to create 1-5 tasks
- Assigns tasks to appropriate phases
- Defines concrete completion criteria
- Marks diagnostic task as `done`

### 5. Workflow Progression

Once the diagnostic agent creates new tasks:
- Tasks are picked up by regular agents
- Workflow progresses toward the goal
- System continues monitoring
- Another diagnostic may trigger if needed (after cooldown)

## Configuration

### YAML Configuration (`hephaestus_config.yaml`)

```yaml
diagnostic_agent:
  enabled: true  # Enable/disable diagnostic agents
  cooldown_seconds: 60  # Min time between diagnostics
  min_stuck_time_seconds: 60  # How long "stuck" before triggering
  max_agents_to_analyze: 15  # Number of recent agents in context
  max_conductor_analyses: 5  # Number of Conductor analyses in context
  max_tasks_per_run: 5  # Max tasks diagnostic can create
```

### Environment Variables

```bash
DIAGNOSTIC_AGENT_ENABLED=true
DIAGNOSTIC_COOLDOWN_SECONDS=60
DIAGNOSTIC_MIN_STUCK_TIME=60
```

### SDK Configuration

```python
from hephaestus_sdk import HephaestusConfig

config = HephaestusConfig(
    diagnostic_agent_enabled=True,
    diagnostic_cooldown_seconds=60,
    diagnostic_min_stuck_time_seconds=60,
)
```

## Database Schema

### DiagnosticRun Table

Tracks each diagnostic agent execution:

```sql
CREATE TABLE diagnostic_runs (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    diagnostic_agent_id TEXT,
    diagnostic_task_id TEXT,

    -- Trigger conditions
    triggered_at DATETIME NOT NULL,
    total_tasks_at_trigger INTEGER NOT NULL,
    done_tasks_at_trigger INTEGER NOT NULL,
    failed_tasks_at_trigger INTEGER NOT NULL,
    time_since_last_task_seconds INTEGER NOT NULL,

    -- Results
    tasks_created_count INTEGER DEFAULT 0,
    tasks_created_ids JSON,
    completed_at DATETIME,
    status TEXT CHECK(status IN ('created', 'running', 'completed', 'failed')),

    -- Analysis context
    workflow_goal TEXT,
    phases_analyzed JSON,
    agents_reviewed JSON,
    diagnosis TEXT,

    FOREIGN KEY (workflow_id) REFERENCES workflows(id),
    FOREIGN KEY (diagnostic_agent_id) REFERENCES agents(id),
    FOREIGN KEY (diagnostic_task_id) REFERENCES tasks(id)
);
```

### Agent Type Update

The `agents.agent_type` constraint now includes `'diagnostic'`:

```sql
agent_type TEXT CHECK(agent_type IN ('phase', 'validator', 'result_validator', 'monitor', 'diagnostic'))
```

## Monitoring & Observability

### Logs

Diagnostic agents produce distinctive log messages:

```
🚨 WORKFLOW STUCK DETECTED - 120s with no progress
🔍 Creating diagnostic agent for workflow abc12345
✅ Diagnostic agent def67890 created for workflow abc12345
```

### Database Queries

**View all diagnostic runs:**
```sql
SELECT * FROM diagnostic_runs ORDER BY triggered_at DESC;
```

**Check diagnostic effectiveness:**
```sql
SELECT
    dr.id,
    dr.triggered_at,
    dr.tasks_created_count,
    dr.status,
    COUNT(t.id) as tasks_completed
FROM diagnostic_runs dr
LEFT JOIN tasks t ON t.created_by_agent_id = dr.diagnostic_agent_id
    AND t.status = 'done'
GROUP BY dr.id;
```

**See which phases diagnostics create tasks in:**
```sql
SELECT
    p.name as phase_name,
    COUNT(t.id) as tasks_created
FROM tasks t
JOIN agents a ON t.created_by_agent_id = a.id
JOIN phases p ON t.phase_id = p.id
WHERE a.agent_type = 'diagnostic'
GROUP BY p.name;
```

## Troubleshooting

### Diagnostic Not Triggering

**Symptoms:** Workflow seems stuck but no diagnostic agent is created

**Check:**
1. Is `diagnostic_agent_enabled` set to `true`?
2. Are there any active tasks? (Check `tasks` table)
3. Has cooldown period passed? (Check `diagnostic_runs` for last run)
4. Has workflow been stuck long enough? (Check `diagnostic_min_stuck_time_seconds`)

**Debug:**
```python
# Check workflow status
SELECT workflow_id, status FROM tasks WHERE workflow_id = '<workflow_id>';

# Check last diagnostic
SELECT * FROM diagnostic_runs
WHERE workflow_id = '<workflow_id>'
ORDER BY triggered_at DESC LIMIT 1;
```

### Diagnostic Creating Wrong Tasks

**Symptoms:** Diagnostic creates tasks but they don't help

**Possible causes:**
1. Insufficient context (increase `max_agents_to_analyze`)
2. Poor workflow goal definition (review `result_criteria`)
3. Diagnostic agent misunderstood situation

**Solutions:**
- Review diagnostic agent's output in tmux session
- Check `diagnosis` field in `diagnostic_runs` table
- Improve workflow phase done_definitions for clarity

### Too Many Diagnostics

**Symptoms:** Diagnostics keep triggering in a loop

**Causes:**
1. Cooldown too short
2. Diagnostic creates tasks that immediately complete

**Solutions:**
```yaml
diagnostic_agent:
  cooldown_seconds: 120  # Increase cooldown
  min_stuck_time_seconds: 120  # Require longer stuck time
```

### Diagnostic Agent Fails

**Symptoms:** Diagnostic task shows status `failed`

**Check:**
1. Diagnostic agent logs in tmux
2. `failure_reason` in tasks table
3. MCP tool availability

**Recovery:**
- System will retry after cooldown period
- Investigate and fix underlying issue
- Manually create tasks if needed

## Best Practices

### 1. Clear Workflow Goals

Define concrete, measurable `result_criteria`:

```yaml
# ❌ Vague
result_criteria: "Complete the project"

# ✅ Specific
result_criteria: |
  Submit a result.md file containing:
  - The cracked password
  - Full methodology used
  - Execution outputs as proof
  - Use submit_result() tool to submit
```

### 2. Detailed Done Definitions

Help diagnostic agents understand what "done" means:

```yaml
# ❌ Vague
Done_Definitions:
  - "Tests pass"

# ✅ Specific
Done_Definitions:
  - "All unit tests in tests/ directory pass with 0 failures"
  - "Integration tests in tests/integration/ execute successfully"
  - "Test results saved to test_results.txt with timestamps"
```

### 3. Completion Notes

Agents should provide detailed completion notes:

```python
# Help diagnostic understand what was actually done
update_task_status(
    task_id="...",
    status="done",
    summary="Created test_password.go with 15 test cases. All tests pass. Output saved to test_output.txt"
)
```

### 4. Monitor Diagnostic Effectiveness

Regularly check:
```sql
-- Diagnostic success rate
SELECT
    COUNT(CASE WHEN tasks_created_count > 0 THEN 1 END) as successful,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(CASE WHEN tasks_created_count > 0 THEN 1 END) / COUNT(*), 2) as success_rate
FROM diagnostic_runs;
```

## Integration with Existing Systems

### Guardian & Conductor

Diagnostic agents work alongside:
- **Guardian**: Monitors individual agent health
- **Conductor**: Detects system-wide issues (duplicates, coherence)
- **Diagnostic**: Handles workflow-level stuckness

They complement each other:
- Guardian/Conductor run every monitoring cycle
- Diagnostic only triggers when workflow is stuck
- All three share the same monitoring infrastructure

### Validation System

Diagnostic agents respect the validation system:
- Won't trigger if workflow has validated result
- Considers validation feedback when analyzing
- May create validation tasks if results were rejected

### Phase System

Diagnostic agents are phase-aware:
- Can create tasks in any phase (not just current)
- May recommend going back to earlier phases
- Understands phase dependencies and progression

## Examples

### Example 1: Missing Result Submission

**Situation:**
- All tests passed
- No result submitted

**Diagnostic finds:**
- Tasks show "tests pass" but no evidence file
- No `submit_result` calls in logs

**Tasks created:**
```
Phase 3: "Create evidence.md documenting all test outputs and execution steps"
Phase 3: "Submit result using submit_result() tool with evidence.md as proof"
```

### Example 2: Implementation Incomplete

**Situation:**
- "Implementation" phase tasks all done
- "Testing" phase tasks failing

**Diagnostic finds:**
- Tests can't run - missing dependencies
- Implementation didn't include setup steps

**Tasks created:**
```
Phase 2: "Add dependency installation to setup.sh script"
Phase 2: "Document build prerequisites in BUILD.md"
Phase 3: "Re-run tests after dependencies are installed"
```

### Example 3: Wrong Architectural Approach

**Situation:**
- Multiple implementation attempts failed
- All with similar errors

**Diagnostic finds:**
- Approach doesn't match codebase architecture
- Need to revisit planning phase

**Tasks created:**
```
Phase 1: "Analyze existing codebase architecture in detail"
Phase 1: "Design integration approach matching current patterns"
Phase 2: "Implement using new architectural approach from Phase 1"
```

## Future Enhancements

Potential improvements to the diagnostic system:

1. **Learning from Past Diagnostics**
   - Store successful diagnostic patterns
   - Use RAG to suggest similar solutions

2. **Multi-Agent Diagnostics**
   - Create diagnostic teams for complex analysis
   - Parallel investigation of different hypotheses

3. **Proactive Diagnostics**
   - Trigger before complete stuck state
   - Based on trajectory analysis

4. **User Notifications**
   - Alert users when diagnostic triggers
   - Request human input for ambiguous situations

## Support

For issues with the diagnostic agent system:

1. Check logs in `logs/monitor.log`
2. Query `diagnostic_runs` table for history
3. Review diagnostic agent tmux sessions
4. Open issue on GitHub with diagnostic run ID
