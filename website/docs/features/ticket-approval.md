# Ticket Human Approval Workflow

Hephaestus supports human-in-the-loop approval for ticket creation, allowing you to review and approve or reject tickets before agents can work on them.

## Overview

When enabled, agents must wait for human approval before proceeding with ticket creation. This provides:

- **Quality Control**: Review ticket descriptions and requirements before work begins
- **Resource Management**: Prevent agents from working on low-priority or incorrect tickets
- **Workflow Oversight**: Maintain control over what gets added to the backlog

## Configuration

Human approval is **disabled by default**. You can enable it per workflow in your `phases.json`:

```json
{
  "workflow_id": "your-workflow-id",
  "board_config": {
    "ticket_human_review": true,
    "approval_timeout_seconds": 1800
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ticket_human_review` | boolean | `false` | Enable human approval for ticket creation |
| `approval_timeout_seconds` | integer | `1800` | Timeout in seconds (default: 30 minutes) |

## How It Works

### 1. Agent Requests Ticket Creation

When an agent attempts to create a ticket in a workflow with human approval enabled:

1. The ticket is created with `approval_status: "pending_review"`
2. The agent's MCP request **blocks and waits** for human decision
3. The ticket appears in the UI with orange visual indicators

### 2. Human Reviews and Decides

The ticket appears in the UI with prominent indicators:

- **Orange left border and background**
- **Pulsing clock icon**
- **"⏳ Needs Human Review" banner**
- **Pending review count badge** in the header

You can:

- **Click the "Pending Review" badge** to see all tickets awaiting approval
- **Click any orange ticket card** to open the approval modal
- **Review the full ticket description** and details

### 3. Approve or Reject

#### Approve
- Click "Approve Ticket" in the modal
- Agent receives success response and continues working
- Ticket `approval_status` changes to `"approved"`
- Orange indicators disappear
- UI updates in real-time via WebSocket

#### Reject
- Click "Reject Ticket" in the modal
- Enter a rejection reason explaining why
- Agent receives error with your rejection message
- Ticket is **deleted from the database**
- UI updates in real-time

#### Timeout
- If no decision is made within the timeout period:
  - Ticket is automatically deleted
  - Agent receives timeout error: "Ticket approval timeout after N seconds. Please try again."

## Visual Indicators

### Pending Review State

Tickets awaiting approval show:

```
┌─────────────────────────────────────┐
│ 🟧 Orange left border               │
│ 🟧 Orange background                │
│ ⏰ Pulsing clock icon (animated)    │
│ ⏳ Needs Human Review (banner)      │
└─────────────────────────────────────┘
```

### Approved State

After approval, tickets return to normal styling with no special indicators.

## API Endpoints

### Approve Ticket

```http
POST /api/tickets/approve
Content-Type: application/json
X-Agent-ID: ui-user

{
  "ticket_id": "ticket-abc-123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ticket approved",
  "ticket_id": "ticket-abc-123"
}
```

### Reject Ticket

```http
POST /api/tickets/reject
Content-Type: application/json
X-Agent-ID: ui-user

{
  "ticket_id": "ticket-abc-123",
  "rejection_reason": "Duplicate of existing ticket"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ticket rejected and deleted",
  "ticket_id": "ticket-abc-123",
  "rejection_reason": "Duplicate of existing ticket"
}
```

### Get Pending Review Count

```http
GET /api/tickets/pending-review-count
```

**Response:**
```json
{
  "pending_count": 3
}
```

## Real-Time Updates

The UI automatically updates via WebSocket when:

- Tickets are approved
- Tickets are rejected
- Tickets are deleted due to timeout

**WebSocket Events:**
- `ticket_approved` - Ticket was approved
- `ticket_rejected` - Ticket was rejected by human
- `ticket_deleted` - Ticket was deleted (timeout or rejection)

The Kanban board listens for these events and automatically refetches tickets without requiring a page refresh.

## Best Practices

### When to Enable

Enable human approval when:

- Starting a new project and want to review initial tickets
- Working with experimental or unproven agents
- Tickets have high impact (production deployments, database changes)
- You want tight control over backlog composition

### When to Disable

Disable human approval when:

- Agents are well-established and produce consistent quality tickets
- Working on low-risk development tasks
- You want maximum agent autonomy and speed
- The workflow is fully automated (CI/CD, monitoring)

### Timeout Recommendations

| Workflow Type | Recommended Timeout |
|--------------|---------------------|
| Real-time development | 300s (5 minutes) |
| Normal development | 1800s (30 minutes) |
| Async/overnight | 7200s (2 hours) |

## Troubleshooting

### Agent Times Out Immediately

**Problem:** Agent fails after ~10 seconds instead of waiting

**Solution:** Ensure `MCP_TOOL_TIMEOUT` environment variable is set correctly. The agent manager automatically sets this based on `approval_timeout_seconds` in the workflow config.

### UI Doesn't Show Orange Indicators

**Problem:** Tickets are pending review but don't show visual indicators

**Solution:**
1. Hard refresh the browser (Cmd+Shift+R / Ctrl+Shift+R)
2. Check browser console for `approval_status: pending_review`
3. Verify WebSocket connection is active (green "Connected" indicator)

### Tickets Don't Update After Approval

**Problem:** Must manually refresh to see updates

**Solution:**
1. Check WebSocket connection status (should be "Connected")
2. Verify WebSocket events in browser console
3. Backend should broadcast `ticket_approved` events

## Example Workflow

Here's a complete example with human approval enabled:

```json
{
  "workflow_definition": {
    "id": "secure-deployment",
    "name": "Secure Deployment Pipeline",
    "description": "Production deployment with human oversight"
  },
  "board_config": {
    "ticket_human_review": true,
    "approval_timeout_seconds": 600,
    "columns": [
      {"name": "Backlog", "status": "backlog"},
      {"name": "In Progress", "status": "in_progress"},
      {"name": "Review", "status": "in_review"},
      {"name": "Done", "status": "done"}
    ]
  },
  "phases": [
    {
      "phase_number": 1,
      "name": "Plan Deployment",
      "description": "Create deployment tickets (requires approval)",
      "completion_criteria": "All deployment tasks identified and approved"
    }
  ]
}
```

In this workflow:
1. Agent creates deployment tickets
2. Human reviews and approves each ticket
3. Only approved tickets proceed to "In Progress"
4. Rejected tickets are removed with feedback to the agent
