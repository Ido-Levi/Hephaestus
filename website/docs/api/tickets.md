# Ticket Tracking API Documentation

This document describes the complete API for Hephaestus's ticket tracking system. The system provides a Jira-like experience for AI agents to manage work items, track progress, and maintain dependencies.

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [API Endpoints](#api-endpoints)
4. [MCP Tools](#mcp-tools)
5. [Common Workflows](#common-workflows)
6. [WebSocket Events](#websocket-events)

---

## Overview

The ticket tracking system provides:
- **Agent-driven ticket management**: AI agents create and manage tickets via MCP tools
- **Smart search**: Hybrid semantic + keyword search prevents duplicate work
- **Auto-linking**: Task completion automatically resolves tickets and links commits
- **Blocking/Dependencies**: Tickets can block others; resolution cascades to unblock dependents
- **Kanban UI**: Real-time visualization for humans
- **Automatic workflow_id detection**: Agents don't need to track workflow context (for supported operations)

### Key Features

- **Workflow Auto-Detection**: `create_ticket` automatically detects workflow_id from agent's current task
- **Semantic Search**: Uses OpenAI embeddings + Qdrant for intelligent duplicate detection
- **FTS5 Keyword Search**: SQLite full-text search for precise matching
- **Hybrid Search**: Combines semantic (70%) + keyword (30%) using Reciprocal Rank Fusion (RRF)
- **Auto-resolution**: Tasks automatically resolve and link to tickets on completion
- **Circular Blocking Prevention**: System prevents dependency cycles
- **Board Configuration**: Fully customizable Kanban columns per workflow

---

## Core Concepts

### Tickets

A ticket represents a unit of work with:
- **Core Fields**: title, description, type, priority, status
- **Metadata**: created_at, updated_at, started_at, completed_at
- **Relationships**: parent_ticket_id, related_task_ids, related_ticket_ids
- **Search**: Embedding (cached), embedding_id (Qdrant reference)
- **Dependencies**: blocked_by_ticket_ids, is_resolved, resolved_at

### Board Configuration

Each workflow can have a board config defining:
- **Columns**: Kanban columns (id, name, order, color)
- **Ticket Types**: Allowed types (bug, feature, improvement, task, spike)
- **Initial Status**: Default status for new tickets
- **Settings**: auto_assign, require_comments_on_status_change, allow_reopen

### Ticket Comments

Comments support:
- **Types**: general, status_change, assignment, blocker, resolution
- **Rich Content**: mentions (agent/ticket IDs), attachments (file paths)
- **Audit Trail**: All comments tracked in ticket_history

### Ticket Commits

Links git commits to tickets:
- **Commit Info**: SHA, message, timestamp
- **Change Stats**: files_changed, insertions, deletions, files_list
- **Link Methods**: manual, auto_detected, worktree, auto_task_completion, resolution

---

## Workflow Auto-Detection

### How It Works

The `create_ticket` endpoint supports **automatic workflow_id detection**. When an agent creates a ticket without providing `workflow_id`, the system:

1. Extracts the agent_id from the `X-Agent-ID` header
2. Queries the database for the agent's current task
3. Retrieves the workflow_id from that task
4. Uses the detected workflow_id for the ticket

### When to Use Auto-Detection

**Use auto-detection when:**
- Agent is working within a task (most common case)
- Creating tickets related to the current workflow
- Simplifying agent prompts and reducing context pollution

**Explicitly provide workflow_id when:**
- Agent needs to create tickets for a different workflow
- Agent is not assigned to a task (rare)
- Cross-workflow ticket management is needed

### Error Handling

If workflow_id cannot be auto-detected:
- **Agent has no current task**: Returns HTTP 400 with message "Could not determine workflow_id: agent has no current task. Please provide workflow_id explicitly."
- **Task has no workflow**: Returns HTTP 400 with message "Could not determine workflow_id: agent's task has no workflow"

---

## API Endpoints

### 1. Create Ticket

**Endpoint**: `POST /api/tickets/create`

Creates a new ticket with semantic indexing and duplicate detection.

**✨ NEW**: `workflow_id` is now **OPTIONAL** - automatically detected from agent's current task!

**Request**:
```json
{
  "workflow_id": "workflow-123",  // OPTIONAL - auto-detected if not provided
  "title": "Fix authentication bug",
  "description": "Users are unable to log in with OAuth2",
  "ticket_type": "bug",
  "priority": "high",
  "initial_status": "backlog",  // Optional, uses board_config default if not provided
  "assigned_agent_id": "agent-456",  // Optional
  "parent_ticket_id": "ticket-789",  // Optional
  "blocked_by_ticket_ids": ["ticket-abc"],  // Optional
  "tags": ["auth", "oauth2"],  // Optional
  "related_task_ids": ["task-xyz"]  // Optional
}
```

**Minimal Request (with auto-detection)**:
```json
{
  "title": "Fix authentication bug",
  "description": "Users are unable to log in with OAuth2",
  "ticket_type": "bug",
  "priority": "high"
}
```

**Response**:
```json
{
  "success": true,
  "ticket_id": "ticket-def456",
  "status": "backlog",
  "message": "Ticket created successfully",
  "embedding_created": true,
  "similar_tickets": [
    {
      "ticket_id": "ticket-abc123",
      "title": "OAuth login failure",
      "similarity_score": 0.89,
      "relation_type": "related",
      "status": "in_progress",
      "priority": "high"
    }
  ]
}
```

**Validation**:
- Workflow must exist and be active/paused (auto-detected or provided)
- Board config must exist for workflow
- Ticket type must be allowed by board config
- All blocking tickets must exist in same workflow
- **Circular blocking prevention**: System checks for dependency cycles
- **Board config validation**: Ensures columns and initial_status are valid
- **Auto-detection validation**: If workflow_id not provided, agent must have a current task with a valid workflow

**Auto-Detection Behavior**:
- If `workflow_id` is provided → uses provided value (no detection)
- If `workflow_id` is null/missing → automatically detects from agent's current task
- Logs detection: `"Auto-detected workflow_id {id} from agent's task {task_id}"`

**Notes**:
- Automatically generates embedding and stores in Qdrant
- Finds semantically similar tickets for duplicate detection
- **Warns if potential duplicate** (similarity >= 0.9)
- Creates initial history entry with "created" change type

---

### 2. Update Ticket

**Endpoint**: `POST /api/tickets/update`

Updates ticket fields (excluding status changes - use change-status for that).

**Request**:
```json
{
  "ticket_id": "ticket-def456",
  "updates": {
    "title": "Fix OAuth2 authentication bug",
    "priority": "critical",
    "assigned_agent_id": "agent-999",
    "tags": ["auth", "oauth2", "security"],
    "blocked_by_ticket_ids": ["ticket-ghi"]
  },
  "update_comment": "Escalating priority due to user impact"  // Optional
}
```

**Response**:
```json
{
  "success": true,
  "ticket_id": "ticket-def456",
  "fields_updated": ["title", "priority", "assigned_agent_id", "tags", "blocked_by_ticket_ids"],
  "message": "Updated 5 field(s)",
  "embedding_updated": true
}
```

**Allowed Fields**:
- title, description, priority, assigned_agent_id, ticket_type, tags, blocked_by_ticket_ids

**Validation**:
- **Circular blocking check**: When updating blocked_by_ticket_ids, prevents cycles
- Ticket and agent must exist
- Each field change creates a history entry

**Notes**:
- If title or description changes, embedding is regenerated
- If update_comment provided, creates a comment entry
- **Circular blocking prevention** for blocked_by_ticket_ids updates

---

### 3. Change Ticket Status

**Endpoint**: `POST /api/tickets/change-status`

Moves ticket to a different status column on the Kanban board.

**Request**:
```json
{
  "ticket_id": "ticket-def456",
  "new_status": "in_progress",
  "comment": "Starting work on this bug",
  "commit_sha": "abc123def456"  // Optional
}
```

**Response (Success)**:
```json
{
  "success": true,
  "ticket_id": "ticket-def456",
  "old_status": "backlog",
  "new_status": "in_progress",
  "message": "Status changed from backlog to in_progress",
  "blocked": false,
  "blocking_ticket_ids": []
}
```

**Response (Blocked)**:
```json
{
  "success": false,
  "ticket_id": "ticket-def456",
  "old_status": "backlog",
  "new_status": "backlog",
  "message": "Cannot change status: Ticket is blocked by 2 ticket(s): ticket-abc: Fix database schema, ticket-xyz: Update API endpoint and 0 more",
  "blocked": true,
  "blocking_ticket_ids": ["ticket-abc", "ticket-xyz"],
  "blocking_tickets": ["ticket-abc: Fix database schema", "ticket-xyz: Update API endpoint"]
}
```

**Validation**:
- New status must be valid per board_config
- **CRITICAL**: Blocked tickets cannot change status
- **Enhanced error messages** include blocking ticket titles

**Notes**:
- Automatically creates status_change comment
- Updates timing fields (started_at, completed_at)
- If commit_sha provided, links commit to ticket
- **Blocked tickets** cannot move until blockers are resolved

---

### 4. Add Comment

**Endpoint**: `POST /api/tickets/comment`

Adds a comment to a ticket.

**Request**:
```json
{
  "ticket_id": "ticket-def456",
  "comment_text": "Found the root cause - OAuth token expiry logic is broken",
  "comment_type": "general",  // general, status_change, blocker, resolution
  "mentions": ["agent-123", "ticket-abc"],  // Optional
  "attachments": ["/path/to/screenshot.png"]  // Optional
}
```

**Response**:
```json
{
  "success": true,
  "comment_id": "comment-xyz789",
  "ticket_id": "ticket-def456",
  "message": "Comment added successfully"
}
```

**Notes**:
- Creates history entry with "commented" change type
- Every 5 comments triggers ticket reindexing (updates embedding with comments)

---

### 5. Get Ticket

**Endpoint**: `GET /api/tickets/{ticket_id}`

Retrieves full ticket details including comments, history, and linked commits.

**Response**:
```json
{
  "ticket_id": "ticket-def456",
  "workflow_id": "workflow-123",
  "title": "Fix OAuth2 authentication bug",
  "description": "Users are unable to log in with OAuth2...",
  "ticket_type": "bug",
  "priority": "critical",
  "status": "in_progress",
  "created_by_agent_id": "agent-456",
  "assigned_agent_id": "agent-999",
  "created_at": "2025-10-21T10:00:00Z",
  "updated_at": "2025-10-21T10:30:00Z",
  "started_at": "2025-10-21T10:15:00Z",
  "completed_at": null,
  "parent_ticket_id": null,
  "related_task_ids": ["task-xyz"],
  "related_ticket_ids": [],
  "tags": ["auth", "oauth2", "security"],
  "blocked_by_ticket_ids": [],
  "is_resolved": false,
  "resolved_at": null,
  "comments": [
    {
      "comment_id": "comment-xyz789",
      "agent_id": "agent-999",
      "comment_text": "Found the root cause...",
      "comment_type": "general",
      "created_at": "2025-10-21T10:20:00Z",
      "mentions": ["agent-123"],
      "attachments": []
    }
  ],
  "history": [...],
  "commits": [...]
}
```

---

### 6. Search Tickets

**Endpoint**: `POST /api/tickets/search`

**⚠️ NOTE**: This endpoint currently REQUIRES workflow_id. Auto-detection is not yet implemented for search operations.

Performs hybrid semantic + keyword search across tickets.

**Request**:
```json
{
  "workflow_id": "workflow-123",
  "query": "authentication oauth login failure",
  "limit": 10,
  "filters": {
    "status": ["backlog", "in_progress"],
    "priority": ["high", "critical"],
    "ticket_type": "bug",
    "assigned_agent_id": "agent-456",
    "is_blocked": false
  },
  "include_comments": true
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "ticket_id": "ticket-def456",
      "title": "Fix OAuth2 authentication bug",
      "description": "Users are unable to log in...",
      "status": "in_progress",
      "priority": "critical",
      "ticket_type": "bug",
      "relevance_score": 0.95,
      "matched_in": ["semantic", "keyword"],
      "preview": "Users are unable to log in with OAuth2. The token expiry logic...",
      "created_at": "2025-10-21T10:00:00Z",
      "assigned_agent_id": "agent-999"
    }
  ],
  "search_time_ms": 145
}
```

**Search Modes**:
- **Hybrid (Default)**: Semantic (70%) + Keyword (30%) with RRF merging
- **Graceful Degradation**: Falls back to keyword-only if Qdrant unavailable
- **Performance Logging**: Tracks search time and result counts

---

### 7. Get Ticket Stats

**Endpoint**: `GET /api/tickets/stats/{workflow_id}`

Returns aggregated statistics for a workflow's tickets.

**Response**:
```json
{
  "success": true,
  "workflow_id": "workflow-123",
  "stats": {
    "total_tickets": 47,
    "by_status": {
      "backlog": 12,
      "in_progress": 8,
      "review": 5,
      "done": 22
    },
    "by_priority": {
      "low": 10,
      "medium": 25,
      "high": 9,
      "critical": 3
    },
    "by_type": {
      "bug": 15,
      "feature": 20,
      "improvement": 8,
      "task": 4
    },
    "blocked_count": 3,
    "resolved_count": 22,
    "unresolved_count": 25
  }
}
```

---

### 8. Get Tickets (List)

**Endpoint**: `GET /api/tickets`

**⚠️ NOTE**: This endpoint currently REQUIRES workflow_id as a query parameter. Auto-detection is not yet implemented.

Returns all tickets for a workflow with optional filtering.

**Query Parameters**:
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority
- `assigned_agent_id` (optional): Filter by assignee
- `ticket_type` (optional): Filter by type
- `is_resolved` (optional): Filter by resolution status

**Response**: List of ticket summaries (description truncated to 200 chars)

---

### 9. Resolve Ticket

**Endpoint**: `POST /api/tickets/resolve`

Marks ticket as resolved and automatically unblocks all dependent tickets.

**Request**:
```json
{
  "ticket_id": "ticket-def456",
  "resolution_comment": "Fixed OAuth2 token expiry logic. All tests passing.",
  "commit_sha": "abc123def456"  // Optional
}
```

**Response**:
```json
{
  "success": true,
  "ticket_id": "ticket-def456",
  "message": "Ticket resolved. Unblocked 3 ticket(s)",
  "unblocked_tickets": ["ticket-ghi", "ticket-jkl", "ticket-mno"]
}
```

**Behavior**:
- Sets `is_resolved = true` and `resolved_at = now()`
- Adds resolution comment with type "resolution"
- Links commit if commit_sha provided
- **Cascading unblock**: Removes this ticket from all dependent tickets' blocked_by_ticket_ids
- Adds "unblocked" comments to dependent tickets
- Creates history entries for resolution and unblocking

**Logging**:
```
INFO: Resolving ticket ticket-def456 by agent agent-999
INFO: Resolved ticket ticket-def456, unblocking 3 dependent tickets: ['ticket-ghi', 'ticket-jkl', 'ticket-mno']
```

---

### 10. Link Commit

**Endpoint**: `POST /api/tickets/link-commit`

Manually links a git commit to a ticket.

**Request**:
```json
{
  "ticket_id": "ticket-def456",
  "commit_sha": "abc123def456",
  "commit_message": "Fix: OAuth2 token expiry logic"
}
```

**Response**:
```json
{
  "success": true,
  "ticket_id": "ticket-def456",
  "commit_sha": "abc123def456",
  "message": "Commit linked successfully"
}
```

**Link Methods**:
- `manual`: Via this endpoint
- `auto_task_completion`: Auto-linked when task completes (see Common Workflows)
- `auto_detected`: Future: Parse commit messages for ticket IDs
- `worktree`: Linked during worktree merge
- `status_change`: Linked during status change
- `resolution`: Linked during ticket resolution

---

### 11. Get Board Config

**Endpoint**: `GET /api/tickets/board-config/{workflow_id}`

Retrieves the Kanban board configuration for a workflow.

**Response**:
```json
{
  "success": true,
  "board_config": {
    "id": "board-123",
    "workflow_id": "workflow-123",
    "name": "Bug Bounty Board",
    "columns": [
      {"id": "backlog", "name": "Backlog", "order": 0, "color": "#gray"},
      {"id": "in_progress", "name": "In Progress", "order": 1, "color": "#blue"},
      {"id": "review", "name": "Review", "order": 2, "color": "#yellow"},
      {"id": "done", "name": "Done", "order": 3, "color": "#green"}
    ],
    "ticket_types": [
      {"id": "bug", "name": "Bug", "icon": "🐛"},
      {"id": "feature", "name": "Feature", "icon": "✨"},
      {"id": "improvement", "name": "Improvement", "icon": "⚡"}
    ],
    "default_ticket_type": "task",
    "initial_status": "backlog",
    "auto_assign": false,
    "require_comments_on_status_change": false,
    "allow_reopen": true,
    "track_time": false
  }
}
```

---

## MCP Tools

Agents interact with the ticket system through MCP tools. These are exposed as:

```
mcp__hephaestus__create_ticket
mcp__hephaestus__update_ticket
mcp__hephaestus__change_ticket_status
mcp__hephaestus__add_ticket_comment
mcp__hephaestus__get_ticket
mcp__hephaestus__search_tickets
mcp__hephaestus__get_ticket_stats
mcp__hephaestus__get_tickets
mcp__hephaestus__resolve_ticket
mcp__hephaestus__link_commit
mcp__hephaestus__get_board_config
```

All tools use the X-Agent-ID header to identify the calling agent.

---

## Common Workflows

### Workflow 1: Create Ticket → Create Task → Complete → Auto-Resolve

This is the primary workflow for agent-driven development.

**Step 1: Agent creates a ticket (with auto-detection)**
```python
# Agent uses MCP tool - workflow_id automatically detected!
result = mcp__hephaestus__create_ticket(
    agent_id="agent-456",
    title="Implement user profile API",
    description="Create REST API endpoint for user profile CRUD operations",
    ticket_type="feature",
    priority="medium",
    tags=["api", "backend"]
    # workflow_id is auto-detected from agent's current task
)
# result.ticket_id = "ticket-abc123"
# result.similar_tickets = [] (no duplicates found)
```

**Alternative: Explicit workflow_id** (when creating tickets for other workflows):
```python
result = mcp__hephaestus__create_ticket(
    agent_id="agent-456",
    workflow_id="workflow-123",  # Explicitly specified
    title="Implement user profile API",
    description="Create REST API endpoint for user profile CRUD operations",
    ticket_type="feature",
    priority="medium"
)
```

**Step 2: Agent creates a task linked to the ticket**
```python
# Agent uses MCP tool
task_result = mcp__hephaestus__create_task(
    task_description="Implement GET /api/users/:id endpoint",
    done_definition="Endpoint returns user profile with 200 status",
    ticket_id="ticket-abc123",  # REQUIRED when ticket tracking enabled
    phase_id=2
)
# task_result.task_id = "task-xyz789"
```

**Note**: If ticket tracking is enabled for the workflow and `ticket_id` is not provided:
```json
{
  "error": "Ticket tracking is enabled for this workflow",
  "message": "You must provide a ticket_id when creating tasks",
  "hint": "Create a ticket first using create_ticket, then use that ticket_id here",
  "workflow_id": "workflow-123",
  "board_config_name": "Development Board"
}
```

**Step 3: Task completion auto-resolves ticket**

When the agent completes the task:
```python
# Agent uses update_task_status
mcp__hephaestus__update_task_status(
    task_id="task-xyz789",
    status="done",
    summary="Implemented GET /api/users/:id endpoint with tests"
)
```

**Behind the scenes** (in `update_task_status` endpoint, lines 1301-1341):
```python
if request.status == "done" and task.ticket_id and merge_commit_sha:
    # 1. Link the merge commit to the ticket
    await TicketService.link_commit(
        ticket_id=task.ticket_id,
        agent_id=agent_id,
        commit_sha=merge_commit_sha,
        commit_message=f"Task {task.id} completed and merged",
        link_method="auto_task_completion"
    )

    # 2. Resolve the ticket
    await TicketService.resolve_ticket(
        ticket_id=task.ticket_id,
        agent_id=agent_id,
        resolution_comment=f"Task {task.id} completed and merged. {summary}",
        commit_sha=merge_commit_sha
    )

    # 3. Broadcast WebSocket event
    await server_state.broadcast_update({
        "type": "ticket_auto_resolved",
        "ticket_id": task.ticket_id,
        "task_id": task.id,
        "commit_sha": merge_commit_sha,
        "unblocked_tickets": [...]
    })
```

**Result**:
- Ticket is marked resolved
- Commit is linked to ticket
- Any tickets blocked by this ticket are unblocked
- WebSocket event notifies frontend

---

### Workflow 2: Search Before Creating (Duplicate Prevention)

Agents should search before creating tickets to avoid duplicates.

**Step 1: Agent searches for similar work**
```python
# Agent uses MCP tool
# ⚠️ NOTE: search_tickets currently REQUIRES workflow_id (auto-detection not yet implemented)
search_result = mcp__hephaestus__search_tickets(
    agent_id="agent-456",
    workflow_id="workflow-123",  # Currently required
    query="user profile API endpoint",
    limit=5
)
```

**Step 2: Analyze results**
```python
if search_result.results:
    for ticket in search_result.results:
        if ticket.relevance_score >= 0.9:
            # Very similar - likely duplicate
            print(f"Duplicate found: {ticket.ticket_id} - {ticket.title}")
            print("Consider using existing ticket instead")
        elif ticket.relevance_score >= 0.7:
            # Related work
            print(f"Related work: {ticket.ticket_id}")
            print("Consider linking or referencing this ticket")
```

**Step 3: Create ticket with awareness**
```python
# If creating anyway, reference related tickets
# Note: workflow_id auto-detected from agent's current task
result = mcp__hephaestus__create_ticket(
    agent_id="agent-456",
    title="Implement user profile UPDATE API",
    description="Extends existing GET endpoint with PUT/PATCH support",
    related_ticket_ids=[ticket.ticket_id for ticket in search_result.results]
)
```

---

### Workflow 3: Blocking Dependencies

Use blocking when work depends on other work.

**Scenario**: "Implement user profile cache" depends on "Implement user profile API"

**Step 1: Create foundation ticket**
```python
# workflow_id auto-detected from agent's task
foundation = mcp__hephaestus__create_ticket(
    agent_id="agent-456",
    title="Implement user profile API",
    ticket_type="feature",
    priority="high"
)
# foundation.ticket_id = "ticket-api-123"
```

**Step 2: Create dependent ticket**
```python
# workflow_id auto-detected from same agent's task
dependent = mcp__hephaestus__create_ticket(
    agent_id="agent-456",
    title="Implement user profile caching",
    description="Add Redis caching layer for user profiles",
    blocked_by_ticket_ids=["ticket-api-123"],
    priority="medium"
)
# dependent.ticket_id = "ticket-cache-456"
```

**Step 3: Try to move dependent ticket (will fail)**
```python
result = mcp__hephaestus__change_ticket_status(
    ticket_id="ticket-cache-456",
    new_status="in_progress",
    comment="Starting cache implementation"
)
# result.success = False
# result.message = "Cannot change status: Ticket is blocked by 1 ticket(s): ticket-api-123: Implement user profile API"
```

**Step 4: Complete foundation work**
```python
# Complete the API implementation
task_result = mcp__hephaestus__update_task_status(
    task_id="task-api-999",
    status="done"
)
# Auto-resolves ticket-api-123

# Now dependent ticket is automatically unblocked!
```

**Step 5: Move dependent ticket (now succeeds)**
```python
result = mcp__hephaestus__change_ticket_status(
    ticket_id="ticket-cache-456",
    new_status="in_progress",
    comment="Foundation complete, starting cache work"
)
# result.success = True
```

---

## WebSocket Events

The system broadcasts real-time events for frontend updates:

### ticket_created
```json
{
  "type": "ticket_created",
  "ticket_id": "ticket-abc123",
  "workflow_id": "workflow-123",
  "agent_id": "agent-456",
  "title": "Fix authentication bug"
}
```

### ticket_updated
```json
{
  "type": "ticket_updated",
  "ticket_id": "ticket-abc123",
  "agent_id": "agent-456",
  "fields_updated": ["priority", "tags"]
}
```

### ticket_status_changed
```json
{
  "type": "ticket_status_changed",
  "ticket_id": "ticket-abc123",
  "agent_id": "agent-456",
  "old_status": "backlog",
  "new_status": "in_progress",
  "blocked": false
}
```

### ticket_comment_added
```json
{
  "type": "ticket_comment_added",
  "ticket_id": "ticket-abc123",
  "agent_id": "agent-456",
  "comment_id": "comment-xyz789"
}
```

### commit_linked
```json
{
  "type": "commit_linked",
  "ticket_id": "ticket-abc123",
  "agent_id": "agent-456",
  "commit_sha": "abc123def456"
}
```

### ticket_resolved
```json
{
  "type": "ticket_resolved",
  "ticket_id": "ticket-abc123",
  "agent_id": "agent-456",
  "unblocked_tickets": ["ticket-def", "ticket-ghi"]
}
```

### ticket_auto_resolved (Task Completion)
```json
{
  "type": "ticket_auto_resolved",
  "ticket_id": "ticket-abc123",
  "task_id": "task-xyz789",
  "agent_id": "agent-456",
  "commit_sha": "abc123def456",
  "unblocked_tickets": ["ticket-jkl"]
}
```

---

## Performance & Reliability

### Database Indexes

The following indexes are created for optimal query performance:

- `idx_tickets_workflow_status` - Composite index on (workflow_id, status)
- `idx_tickets_workflow_priority` - Composite index on (workflow_id, priority)
- `idx_tickets_assigned_agent` - Index on assigned_agent_id
- `idx_tickets_created_at` - Index on created_at
- `idx_ticket_comments_ticket_id` - Index on ticket_id
- `idx_ticket_history_ticket_id` - Index on ticket_id
- `idx_ticket_commits_ticket_id` - Index on ticket_id
- `idx_ticket_commits_sha` - Index on commit_sha
- `idx_tasks_ticket_id` - Index on ticket_id

### Retry Logic

Embedding generation uses exponential backoff retry (tenacity):
- **Max attempts**: 3
- **Wait strategy**: Exponential (1-10 seconds)
- **Retry on**: OpenAI API errors (APIError, APIConnectionError, RateLimitError)

### Graceful Degradation

If Qdrant is unavailable:
- Semantic search falls back to keyword-only search
- System logs warning but continues functioning
- Hybrid search automatically degrades gracefully

### Error Handling

- **Validation errors**: Return 400 with detailed error messages
- **Circular blocking**: Prevented at create/update time
- **Board config validation**: Ensures columns and types are valid
- **Blocked status changes**: Return clear error with blocking ticket titles

---

## Logging

Key operations log comprehensively:

```python
# Ticket creation
logger.info(f"Creating ticket for workflow {workflow_id}: '{title}' by agent {agent_id}")

# Duplicate detection
logger.warning(f"Potential duplicate ticket detected: {similar_ticket_id} (similarity: 0.95)")

# Ticket resolution
logger.info(f"Resolving ticket {ticket_id} by agent {agent_id}")
logger.info(f"Resolved ticket {ticket_id}, unblocking 3 dependent tickets: [...]")

# Hybrid search
logger.info(f"Hybrid search for 'query...' in workflow {workflow_id}: 10 results in 145ms (from 15 semantic + 12 keyword)")
```

---

## Error Messages

The system provides helpful, actionable error messages:

### Blocked Ticket Status Change
```
Cannot change status: Ticket is blocked by 2 ticket(s):
ticket-abc123: Fix database schema, ticket-xyz789: Update API endpoint
```

### Circular Blocking Prevention
```
Circular blocking detected: ticket-xyz789 is already blocked by this ticket (ticket-abc123)
```

### Missing ticket_id for Task Creation
```json
{
  "error": "Ticket tracking is enabled for this workflow",
  "message": "You must provide a ticket_id when creating tasks",
  "hint": "Create a ticket first using create_ticket, then use that ticket_id here",
  "workflow_id": "workflow-123",
  "board_config_name": "Development Board"
}
```

### Invalid Board Configuration
```
Invalid board configuration: columns must be a non-empty list
Invalid board config: initial_status 'backlog' not in columns
```

---

## Best Practices

### For Agents

1. **Always search before creating** to avoid duplicates
2. **Use descriptive titles** for better semantic search
3. **Add tags** to improve searchability and categorization
4. **Link related tickets** to build context
5. **Use blocking** for dependencies, not just comments
6. **Provide meaningful commit messages** when linking commits
7. **Add resolution comments** explaining what was done

### For System Design

1. **Enable ticket tracking per workflow** via BoardConfig
2. **Configure meaningful columns** matching your process
3. **Define clear ticket types** (bug, feature, improvement, etc.)
4. **Set appropriate initial_status** for new tickets
5. **Use WebSocket events** for real-time UI updates
6. **Monitor search performance** via logs
7. **Review duplicate warnings** to improve agent prompts

---

## Troubleshooting

### Workflow Auto-Detection Issues

#### "Could not determine workflow_id: agent has no current task"

**Symptom**: create_ticket fails with this error
**Cause**: Agent is not assigned to a task, or current_task_id is null
**Solution**:
- Provide `workflow_id` explicitly in the request
- Ensure agent is properly assigned to a task before creating tickets

**Example**:
```python
# Explicitly provide workflow_id when agent has no task
result = mcp__hephaestus__create_ticket(
    agent_id="agent-456",
    workflow_id="workflow-123",  # Explicit workflow
    title="My ticket",
    description="Ticket description"
)
```

#### "Could not determine workflow_id: agent's task has no workflow"

**Symptom**: create_ticket fails even though agent has a task
**Cause**: The task exists but has workflow_id=null in database
**Solution**:
- Fix the task to have a valid workflow_id
- Provide workflow_id explicitly when creating the ticket

### Qdrant Connection Issues

**Symptom**: Semantic search failing
**Solution**: System automatically falls back to keyword search
**Check**: Qdrant container running on localhost:6333

### Duplicate Detection Not Working

**Symptom**: similar_tickets always empty
**Solution**: Check embedding generation and Qdrant indexing
**Verify**: embedding_created=true in create response

### Blocked Tickets Won't Move

**Symptom**: Status change fails with "blocked" message
**Solution**: Resolve blocking tickets first
**Check**: blocking_ticket_ids in error response

### Circular Blocking Error

**Symptom**: Cannot update blocked_by_ticket_ids
**Solution**: Remove circular dependency before updating
**Check**: Ensure A doesn't block B while B blocks A

### search_tickets or get_tickets Failing

**Symptom**: HTTP 422 or validation errors when calling search or list operations
**Cause**: workflow_id is currently required for these operations (auto-detection not yet implemented)
**Solution**: Always provide workflow_id when searching or listing tickets
**Status**: Auto-detection for search/list operations is planned for a future update

---

## Future Enhancements

Planned features:
- **Auto-detect commit links**: Parse commit messages for ticket IDs
- **Time tracking**: Optional start/stop timers per ticket
- **Ticket templates**: Pre-defined ticket structures
- **Custom fields**: Per-workflow custom metadata
- **SLA tracking**: Due dates and breach notifications
- **Email notifications**: Optional email on status changes
- **Ticket archiving**: Move old tickets to archive
- **Bulk operations**: Update multiple tickets at once
- **Advanced search**: Date ranges, text operators, saved queries

---

## Implementation Status

### ✅ Auto-Detection Implemented
- **create_ticket**: Full workflow_id auto-detection from agent's current task

### ⚠️ Auto-Detection Pending
- **search_tickets**: Currently requires explicit workflow_id
- **get_tickets**: Currently requires explicit workflow_id

These limitations are documented in their respective sections above and will be addressed in a future update.

---

## Related Documentation

- **[Audit Report](TICKET_AUDIT_REPORT.md)** - Detailed technical audit of recent changes
- **[CLAUDE.md](../../CLAUDE.md)** - Project overview and development guide
- **[Memory System](../core/memory-system.md)** - RAG system integration

---

**Last Updated**: 2025-10-21
**Version**: Wave 5 (Auto-Detection Update)
**Status**: Partially implemented - create_ticket only
