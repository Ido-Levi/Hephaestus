# Worktree Isolation System Documentation

## Overview

The Worktree Isolation System provides automatic workspace isolation for Hephaestus agents using Git worktrees, enabling parallel agent execution without conflicts while maintaining complete transparency - agents are never aware they're working in isolated environments.

### Key Features

- **Complete Transparency**: Agents have NO awareness of worktrees, branches, or git operations
- **Zero Conflicts**: Multiple agents work in parallel without interfering with each other
- **Knowledge Inheritance**: Child agents start with their parent's exact state
- **Automatic Conflict Resolution**: Uses "newest file wins" strategy for automatic merging
- **Clean History**: Complete git history of all agent attempts and decisions

### Problem Solved

Multiple agents working simultaneously create file conflicts, overwrite each other's changes, and create chaos in the main workspace. Failed experiments pollute the codebase, and there's no clean way to manage parallel work. This system solves all these issues transparently.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        AgentManager                         │
│  - Creates agents for tasks                                 │
│  - Manages tmux sessions                                    │
│  - Integrates with WorktreeManager                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     WorktreeManager                         │
│  - Creates isolated git worktrees                           │
│  - Manages parent-child relationships                       │
│  - Handles automatic conflict resolution                    │
│  - Performs cleanup and maintenance                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Git Repository                          │
│  - Main branch (clean state)                                │
│  - Agent branches (isolated work)                           │
│  - Worktrees in /tmp/hephaestus_worktrees/                  │
└──────────────────────────────────────────────────────────────┘
```

### Database Schema

The system uses three main tables to track worktree state:

1. **agent_worktrees**: Tracks worktree paths, branches, and parent relationships
2. **worktree_commits**: Records all checkpoint commits for traceability
3. **merge_conflict_resolutions**: Logs automatic conflict resolutions

## API Reference

### WorktreeManager Class

#### `create_agent_worktree(agent_id, parent_id=None)`

Creates an isolated worktree for an agent.

**Parameters:**
- `agent_id` (str): Unique agent identifier
- `parent_id` (str, optional): Parent agent ID for inheritance

**Returns:**
```python
{
    "working_directory": "/tmp/hephaestus_worktrees/wt_agent123",
    "branch_name": "agent-123",  # Hidden from agent
    "parent_commit": "abc123def456"  # Hidden from agent
}
```

**Usage Example:**
```python
from src.core.worktree_manager import WorktreeManager
from src.core.database import DatabaseManager

db_manager = DatabaseManager()
worktree_manager = WorktreeManager(db_manager)

# Create worktree for new agent
result = worktree_manager.create_agent_worktree(
    agent_id="agent-123",
    parent_id="agent-100"  # Optional parent
)

# Agent only sees the working directory
working_dir = result["working_directory"]
```

#### `commit_for_validation(agent_id, iteration)`

Creates a checkpoint commit for validation examination.

**Parameters:**
- `agent_id` (str): Agent identifier
- `iteration` (int): Validation attempt number

**Returns:**
```python
{
    "commit_sha": "def456ghi789",
    "files_changed": 5,
    "message": "[Agent 123] Iteration 1 - Ready for validation"
}
```

**Usage Example:**
```python
# Create validation checkpoint
commit_info = worktree_manager.commit_for_validation(
    agent_id="agent-123",
    iteration=1
)

# Pass to validator for examination
validator.examine_changes(commit_info["commit_sha"])
```

#### `merge_to_parent(agent_id)`

Merges agent's work with automatic conflict resolution.

**Parameters:**
- `agent_id` (str): Agent identifier

**Returns:**
```python
{
    "status": "success" | "conflict_resolved",
    "merged_to": "main",  # or parent branch
    "commit_sha": "xyz789abc123",
    "conflicts_resolved": [...],
    "resolution_strategy": "newest_file_wins",
    "total_conflicts": 0
}
```

**Usage Example:**
```python
# Merge agent's work when task is complete
merge_result = worktree_manager.merge_to_parent("agent-123")

if merge_result["status"] == "conflict_resolved":
    print(f"Resolved {merge_result['total_conflicts']} conflicts")
```

#### `get_workspace_changes(agent_id, since_commit=None)`

Gets diff information for validation or review.

**Parameters:**
- `agent_id` (str): Agent identifier
- `since_commit` (str, optional): Base commit for comparison

**Returns:**
```python
{
    "files_created": ["new_file.py"],
    "files_modified": ["existing.py"],
    "files_deleted": ["old_file.py"],
    "total_changes": 3,
    "stats": {
        "insertions": 150,
        "deletions": 30
    },
    "detailed_diff": "..."
}
```

#### `cleanup_worktree(agent_id)`

Removes worktree after agent completion.

**Parameters:**
- `agent_id` (str): Agent identifier

**Returns:**
```python
{
    "status": "cleaned",
    "branch_preserved": True,
    "disk_space_freed_mb": 125
}
```

## Integration with AgentManager

The WorktreeManager is automatically integrated with AgentManager. When creating an agent:

```python
# In AgentManager.create_agent_for_task()
# This happens automatically - transparent to users

# 1. Create isolated worktree
worktree_info = self.worktree_manager.create_agent_worktree(
    agent_id=agent_id,
    parent_agent_id=parent_agent_id  # For inheritance
)

# 2. Use worktree directory for agent
agent_working_dir = worktree_info["working_directory"]

# 3. Create tmux session in worktree
tmux_session = self._create_tmux_session(
    session_name,
    working_directory=agent_working_dir
)
```

## Configuration

Configuration is managed through environment variables or `src/core/simple_config.py`.

### Environment Variables

```bash
# Worktree paths
WORKTREE_BASE_PATH=/tmp/hephaestus_worktrees
MAIN_REPO_PATH=/path/to/main/repo

# Limits
WORKTREE_MAX_COUNT=50
WORKTREE_MAX_DEPTH=10
WORKTREE_DISK_THRESHOLD_GB=10

# Conflict resolution
WORKTREE_AUTO_MERGE=true
WORKTREE_CONFLICT_STRATEGY=newest_file_wins
WORKTREE_PREFER_CHILD_ON_TIE=true

# Cleanup
WORKTREE_AUTO_CLEANUP=true
WORKTREE_CLEANUP_INTERVAL_HOURS=6
WORKTREE_RETENTION_MERGED=1
WORKTREE_RETENTION_FAILED=24
WORKTREE_RETENTION_ABANDONED=6

# Checkpoints
WORKTREE_AUTO_CHECKPOINT=true
WORKTREE_CHECKPOINT_INTERVAL=30
WORKTREE_CHECKPOINT_ON_ERROR=true
WORKTREE_CHECKPOINT_BEFORE_CHILD=true

# Branches
WORKTREE_BRANCH_PREFIX=agent-
WORKTREE_ARCHIVE_PREFIX=refs/archive/
```

## Usage Examples

### Creating a Child Agent with Inheritance

```python
# Parent agent completes initial analysis
parent_agent = agent_manager.create_agent_for_task(
    task=analysis_task,
    enriched_data={...},
    memories=[...]
)

# Child agent inherits parent's work
child_agent = agent_manager.create_agent_for_task(
    task=implementation_task,
    enriched_data={...},
    memories=[...],
    parent_agent_id=parent_agent.id  # Inherits parent's state
)

# Child sees all parent's files immediately
# No re-discovery needed!
```

### Handling Parallel Agents

```python
# Create multiple agents working in parallel
agent1 = agent_manager.create_agent_for_task(task1)
agent2 = agent_manager.create_agent_for_task(task2)
agent3 = agent_manager.create_agent_for_task(task3)

# Each works in complete isolation
# No conflicts, no interference
# All can modify the same files differently
```

### Automatic Merge with Conflict Resolution

```python
# When agent completes task
async def on_task_complete(agent_id):
    # Merge with automatic conflict resolution
    merge_result = worktree_manager.merge_to_parent(agent_id)

    if merge_result["total_conflicts"] > 0:
        print(f"Auto-resolved {merge_result['total_conflicts']} conflicts")
        for conflict in merge_result["conflicts_resolved"]:
            print(f"  {conflict['file']}: chose {conflict['resolution']}")

    # Cleanup worktree
    worktree_manager.cleanup_worktree(agent_id)
```

## Git Operations

### Commit Message Formats

| Type | Format | Example |
|------|--------|---------|
| Parent Checkpoint | `[Agent {id}] Checkpoint before spawning: {task}` | `[Agent 123] Checkpoint before spawning: Create API` |
| Validation Ready | `[Agent {id}] Iteration {n} - Ready for validation` | `[Agent 123] Iteration 1 - Ready for validation` |
| Final | `[Agent {id}] Final - Task completed` | `[Agent 123] Final - Task completed` |
| Conflict Resolution | `[Auto-Merge] Resolved conflicts using {strategy}` | `[Auto-Merge] Resolved conflicts using newest_file_wins` |

### Branch Naming Convention

- Agent branches: `agent-{agent_id}`
- Example: `agent-abc123def456`

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Not a git repository" | Main repo path not a git repo | Initialize git in main repo |
| "Disk space exhausted" | Too many worktrees | Cleanup old worktrees |
| "Branch already exists" | Stale branch from failed cleanup | Force recreate branch |
| "Worktree already exists" | Previous worktree not cleaned | Force remove and recreate |

### Recovery Procedures

```python
# Manual cleanup if automatic fails
def manual_cleanup(agent_id):
    try:
        # Try normal cleanup
        worktree_manager.cleanup_worktree(agent_id)
    except Exception as e:
        # Force cleanup
        worktree_path = f"/tmp/hephaestus_worktrees/wt_{agent_id}"
        if os.path.exists(worktree_path):
            shutil.rmtree(worktree_path, ignore_errors=True)

        # Remove git worktree reference
        repo.git.worktree("prune")
```

## Testing

Run the test suite:

```bash
# Run all worktree tests
pytest tests/test_worktree_manager.py -v

# Run specific test
pytest tests/test_worktree_manager.py::test_parent_child_inheritance -v
```

### Test Coverage

The test suite covers:
- Worktree creation and isolation
- Parent-child inheritance
- Parallel agent isolation
- Validation commits
- Automatic conflict resolution
- Cleanup operations

## Troubleshooting

### Debug Commands

```bash
# List all worktrees
git worktree list

# Check worktree status
git worktree list --porcelain

# Remove stale worktrees
git worktree prune

# Check disk usage
du -sh /tmp/hephaestus_worktrees/*
```

### Log Locations

Worktree operations are logged to the standard Hephaestus logs:
- Look for `WorktreeManager` entries
- Debug level shows detailed git operations

### Common Issues

1. **Worktrees not cleaning up**
   - Check if cleanup service is running
   - Verify retention policies in config
   - Manually run cleanup if needed

2. **Conflicts not resolving**
   - Ensure newest_file_wins strategy is enabled
   - Check file timestamps are being read correctly
   - Verify git is configured properly

3. **Parent state not inherited**
   - Ensure parent has committed changes
   - Verify parent_agent_id is passed correctly
   - Check parent worktree still exists

## Performance Considerations

- **Worktree Creation**: < 2 seconds for most repos
- **Merge Operations**: < 5 seconds including conflict resolution
- **Cleanup**: < 1 second per worktree
- **Disk Usage**: ~100MB per worktree (varies by repo size)

### Optimization Tips

1. Enable shallow clones for large repos
2. Set aggressive cleanup policies
3. Monitor disk usage and set thresholds
4. Archive old branches periodically

## Future Enhancements

Planned improvements include:
- Distributed worktrees across multiple machines
- AI-powered conflict resolution
- Worktree templates for common patterns
- Performance profiling per worktree

## Summary

The Worktree Isolation System enables:
- **Parallel execution** without conflicts
- **Knowledge transfer** through inheritance
- **Clean experiments** that don't pollute main
- **Automatic merging** with smart conflict resolution
- **Complete transparency** to agents

All while maintaining a complete git history of every agent's work, making debugging and auditing straightforward.