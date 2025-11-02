#!/usr/bin/env python3
"""
Claude MCP Client for Hephaestus
This client connects to the Hephaestus server running on port 8000
"""

from mcp.server.fastmcp import FastMCP
import httpx
import asyncio

# Initialize MCP client
mcp = FastMCP("hephaestus-client")

# Hephaestus server URL
HEPHAESTUS_URL = "http://localhost:8000"
DEFAULT_AGENT_ID = "main-session-agent"

@mcp.tool()
def health_check() -> str:
    """Check if Hephaestus server is running"""
    try:
        import requests
        response = requests.get(f"{HEPHAESTUS_URL}/health", timeout=5)
        if response.status_code == 200:
            return "✅ Hephaestus server is healthy and running on port 8000"
        else:
            return f"⚠️ Server responded with status {response.status_code}"
    except Exception as e:
        return f"❌ Cannot connect to Hephaestus server: {str(e)}"

@mcp.tool()
async def create_task(description: str, done_definition: str, agent_id: str, phase_id: int, priority: str = "medium", cwd: str = None, ticket_id: str = None) -> str:
    """Create a new task in Hephaestus.

    Args:
        description: What needs to be done
        done_definition: Clear criteria for completion
        agent_id: Your agent ID (REQUIRED - found in your initial prompt under "Your Agent ID:")
        phase_id: Phase ID for the task (REQUIRED - MUST specify which workflow phase this task belongs to, e.g., 1, 2, 3)
        priority: Task priority (low/medium/high)
        cwd: Current working directory for the task (optional)
        ticket_id: Associated ticket ID (OPTIONAL for SDK/root tasks, REQUIRED when ticket tracking is enabled for MCP agents)

    CRITICAL: You MUST provide both agent_id AND phase_id for every task.
    - agent_id: ALWAYS use YOUR agent ID from the prompt header (looks like "6a062184-e189-4d8d-8376-89da987b9996"). 
      NEVER use placeholder values like 'agent-mcp' - they will cause authorization failures.
    - phase_id: REQUIRED - Specify the workflow phase number (e.g., 1 for Phase 1, 2 for Phase 2, etc.)

    IMPORTANT FOR TICKET TRACKING:
    - When ticket tracking is active, MCP agents MUST provide ticket_id
    - SDK tasks (root/beginning tasks created by main-session-agent) may omit ticket_id as they ARE the ticket creators
    - Use create_ticket() first to get a ticket_id, then pass it here when creating tasks

    Omitting phase_id will cause workflow coordination issues.
    """
    try:
        async with httpx.AsyncClient() as client:
            request_data = {
                "task_description": description,
                "done_definition": done_definition,
                "ai_agent_id": agent_id,
                "priority": priority,
                "phase_id": str(phase_id)
            }

            # Add optional fields if provided
            if cwd:
                request_data["cwd"] = cwd
            if ticket_id:
                request_data["ticket_id"] = ticket_id

            response = await client.post(
                f"{HEPHAESTUS_URL}/create_task",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                cwd_info = f"\nWorking Directory: {cwd}" if cwd else ""
                return f"""✅ Task created successfully!
Task ID: {result.get('task_id', 'unknown')}
Assigned to: {result.get('assigned_agent_id', 'unknown')}
Status: {result.get('status', 'unknown')}{cwd_info}
Description: {result.get('enriched_description', description)[:100]}..."""
            else:
                return f"❌ Failed to create task: {response.text}"
    except Exception as e:
        return f"❌ Error creating task: {str(e)}"

@mcp.tool()
async def get_tasks(status: str = "all") -> str:
    """List tasks in Hephaestus.

    Args:
        status: Filter by status (all/pending/assigned/in_progress/done/failed)
    """
    try:
        async with httpx.AsyncClient() as client:
            params = {} if status == "all" else {"status": status}
            response = await client.get(
                f"{HEPHAESTUS_URL}/task_progress",
                params=params,
                headers={"X-Agent-ID": DEFAULT_AGENT_ID},
                timeout=10.0
            )

            if response.status_code == 200:
                tasks = response.json()
                if not tasks:
                    return "📋 No tasks found"

                if isinstance(tasks, list):
                    task_list = []
                    for task in tasks:
                        task_list.append(
                            f"• [{task['status']}] {task['id'][:8]}: {task['description'][:60]}..."
                        )
                    return f"📋 Tasks:\n" + "\n".join(task_list)
                else:
                    # Single task
                    return f"📋 Task {tasks['id'][:8]}: {tasks['status']} - {tasks['description']}"
            else:
                return f"❌ Failed to get tasks: {response.text}"
    except Exception as e:
        return f"❌ Error getting tasks: {str(e)}"

@mcp.tool()
async def save_memory(content: str, agent_id: str, memory_type: str = "discovery") -> str:
    """Save a memory to Hephaestus knowledge base.

    Args:
        content: The memory content to save
        agent_id: Your agent ID (CRITICAL: must match YOUR agent ID from your initial prompt)
        memory_type: Type of memory (error_fix/discovery/decision/learning/warning/codebase_knowledge)

    CRITICAL: Use your actual agent UUID from your initial prompt.
    Example: agent_id="84f15f6c-35b1-4d57-97ac-92a3c0c94d29"
    DO NOT use 'agent-mcp' or any placeholder - it will cause errors!
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/save_memory",
                json={
                    "ai_agent_id": agent_id,
                    "memory_content": content,
                    "memory_type": memory_type,
                    "tags": [],
                    "related_files": []
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                return f"✅ Memory saved! ID: {result.get('memory_id', 'unknown')}"
            else:
                return f"❌ Failed to save memory: {response.text}"
    except Exception as e:
        return f"❌ Error saving memory: {str(e)}"

@mcp.tool()
async def update_task_status(
    task_id: str,
    agent_id: str,
    status: str,
    summary: str = "",
    failure_reason: str = "",
    key_learnings: list = None
) -> str:
    """Update the status of a task in Hephaestus.

    Args:
        task_id: The ID of the task to update
        agent_id: Your agent ID (CRITICAL: must match YOUR agent ID from your initial prompt)
        status: New status (done/failed/in_progress)
        summary: Summary of what was accomplished (for done status)
        failure_reason: Reason for failure (for failed status)
        key_learnings: List of key learnings from the task

    CRITICAL: agent_id must match YOUR agent ID from your initial prompt.
    Example (use your actual ID from prompt):
        update_task_status(
            agent_id="6a062184-e189-4d8d-8376-89da987b9996",  # Your actual UUID
            task_id="dc2c0279-ba16-4a8d-9fd5-846259967e68",
            status="done",
            summary="Task completed successfully"
        )
    
    DO NOT use 'agent-mcp' or any placeholder - it will cause "Agent not authorized" errors!
    """
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "task_id": task_id,
                "status": status,
                "agent_id": agent_id,
                "key_learnings": key_learnings or []
            }

            if summary:
                payload["summary"] = summary
            if failure_reason:
                payload["failure_reason"] = failure_reason

            response = await client.post(
                f"{HEPHAESTUS_URL}/update_task_status",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                message = result.get("message", f"Task {status} successfully")

                # Use appropriate emoji based on message content
                if "validation" in message.lower():
                    status_emoji = "🔍"  # Magnifying glass for validation
                elif status == "done":
                    status_emoji = "✅"
                elif status == "failed":
                    status_emoji = "❌"
                else:
                    status_emoji = "🔄"

                return f"{status_emoji} {message}"
            else:
                return f"❌ Failed to update task status: {response.text}"
    except Exception as e:
        return f"❌ Error updating task status: {str(e)}"

@mcp.tool()
async def give_validation_review(
    task_id: str,
    validator_agent_id: str,
    validation_passed: bool,
    feedback: str,
    evidence: list = None,
    recommendations: list = None
) -> str:
    """Submit validation review for a task.

    Args:
        task_id: The ID of the task being validated
        validator_agent_id: Your validator agent ID
        validation_passed: Whether validation passed (true/false)
        feedback: Detailed feedback about what passed/failed
        evidence: List of evidence items supporting your decision (optional)
        recommendations: List of recommended follow-up tasks if validation passes (optional)

    This tool should only be called by validator agents after reviewing a task.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/give_validation_review",
                json={
                    "task_id": task_id,
                    "validator_agent_id": validator_agent_id,
                    "validation_passed": validation_passed,
                    "feedback": feedback,
                    "evidence": evidence or [],
                    "recommendations": recommendations or []
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": validator_agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                status_emoji = "✅" if result.get("status") == "completed" else "🔄"
                return f"""{status_emoji} Validation Review Submitted!
Status: {result.get('status', 'unknown')}
Message: {result.get('message', '')}
Iteration: {result.get('iteration', 'N/A')}"""
            else:
                return f"❌ Failed to submit validation review: {response.text}"
    except Exception as e:
        return f"❌ Error submitting validation review: {str(e)}"


@mcp.tool()
async def validate_my_agent_id(agent_id: str) -> str:
    """Validate that your agent ID has the correct format before using it.
    
    Args:
        agent_id: The agent ID you plan to use
        
    Returns:
        Validation result with helpful error messages if invalid
    
    Use this tool if you're unsure about your agent ID format!
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HEPHAESTUS_URL}/validate_agent_id/{agent_id}",
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["valid"]:
                    return f"✅ {result['message']}"
                else:
                    mistakes = "\n".join(f"  • {m}" for m in result["common_mistakes"])
                    return f"""❌ {result['message']}

Common mistakes:
{mistakes}

Check your initial prompt for "Your Agent ID:" - it should be a UUID like:
  6a062184-e189-4d8d-8376-89da987b9996"""
            else:
                return f"❌ Validation failed: {response.text}"
    except Exception as e:
        return f"❌ Error validating agent ID: {str(e)}"


@mcp.tool()
async def get_agent_status() -> str:
    """Get status of all active agents in Hephaestus"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HEPHAESTUS_URL}/agent_status",
                headers={"X-Agent-ID": DEFAULT_AGENT_ID},
                timeout=10.0
            )

            if response.status_code == 200:
                agents = response.json()
                if not agents:
                    return "🤖 No active agents"

                agent_list = []
                for agent in agents:
                    status_emoji = "🟢" if agent['status'] == "working" else "🔴"
                    agent_list.append(
                        f"{status_emoji} {agent['id'][:8]}: {agent['status']} - Task: {agent.get('current_task_id', 'none')[:8] if agent.get('current_task_id') else 'none'}"
                    )
                return f"🤖 Active Agents:\n" + "\n".join(agent_list)
            else:
                return f"❌ Failed to get agent status: {response.text}"
    except Exception as e:
        return f"❌ Error getting agent status: {str(e)}"


@mcp.tool()
async def submit_result(markdown_file_path: str, agent_id: str, explanation: str, evidence: list = None) -> str:
    """Submit a workflow result with evidence for validation.

    Args:
        markdown_file_path: Path to markdown file with solution and evidence
        agent_id: Your agent ID
        explanation: Brief explanation of what was accomplished
        evidence: List of evidence supporting completion (optional)

    Use when you have found the definitive solution to a workflow problem.
    The markdown file should contain comprehensive evidence including:
    - Clear solution statement
    - Execution outputs and proof
    - Step-by-step methodology
    - Reproduction steps for verification
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/submit_result",
                json={
                    "markdown_file_path": markdown_file_path,
                    "explanation": explanation,
                    "evidence": evidence or [],
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                validation_info = f"\n🔍 Validation: {'Triggered' if result.get('validation_triggered') else 'Not required'}"
                return f"""✅ Result submitted successfully!
Result ID: {result.get('result_id', 'unknown')}
Workflow ID: {result.get('workflow_id', 'unknown')}
Status: {result.get('status', 'unknown')}{validation_info}
Message: {result.get('message', '')}"""
            else:
                return f"❌ Failed to submit result: {response.text}"
    except Exception as e:
        return f"❌ Error submitting result: {str(e)}"


@mcp.tool()
async def submit_result_validation(
    result_id: str,
    validation_passed: bool,
    feedback: str,
    evidence: list = None
) -> str:
    """Submit validation review for a workflow result.

    Args:
        result_id: ID of the result being validated (REQUIRED - this is the full result ID you were given)
        validation_passed: Whether the result meets criteria (true/false)
        feedback: Detailed validation feedback explaining decision
        evidence: Evidence supporting the decision (list of dicts, optional)

    This tool should only be called by result validator agents after reviewing
    a submitted workflow result against the configured criteria.

    IMPORTANT: You must use the complete result_id that was provided to you (e.g., result-a3145b59-e954-434e-a254-962ef2d1f669).
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/submit_result_validation",
                json={
                    "result_id": result_id,
                    "validation_passed": validation_passed,
                    "feedback": feedback,
                    "evidence": evidence or [],
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                workflow_action = result.get('workflow_action_taken', 'none')
                action_emoji = "🛑" if workflow_action == "workflow_terminated" else "▶️"
                action_text = f"\n{action_emoji} Workflow Action: {workflow_action}" if workflow_action != 'none' else ""

                return f"""✅ Result Validation Submitted!
Status: {result.get('status', 'unknown')}
Message: {result.get('message', '')}{action_text}
Result ID: {result.get('result_id', 'unknown')}"""
            else:
                return f"❌ Failed to submit result validation: {response.text}"
    except Exception as e:
        return f"❌ Error submitting result validation: {str(e)}"


@mcp.tool()
async def get_workflow_results(workflow_id: str) -> str:
    """Get all submitted results for a workflow.

    Args:
        workflow_id: ID of the workflow

    Returns list of results with their validation status and details.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HEPHAESTUS_URL}/workflows/{workflow_id}/results",
                headers={"X-Agent-ID": DEFAULT_AGENT_ID},
                timeout=10.0
            )

            if response.status_code == 200:
                results = response.json()
                if not results:
                    return f"📋 No results found for workflow {workflow_id}"

                result_list = []
                for result in results:
                    status_emoji = "✅" if result['status'] == "validated" else ("❌" if result['status'] == "rejected" else "⏳")
                    # Show full result_id - critical for validators to use correct ID
                    result_list.append(
                        f"{status_emoji} {result['result_id']}: {result['status']} by {result['agent_id'][:8]}"
                    )
                return f"📋 Workflow Results:\n" + "\n".join(result_list)
            else:
                return f"❌ Failed to get workflow results: {response.text}"
    except Exception as e:
        return f"❌ Error getting workflow results: {str(e)}"


@mcp.tool()
async def broadcast_message(message: str, sender_agent_id: str) -> str:
    """Broadcast a message to all active agents in the system.

    Use this when you have information that ALL other agents should know about,
    or when you need help but don't know which specific agent to ask.

    Args:
        message: The message content to broadcast to all agents
        sender_agent_id: Your agent ID (REQUIRED - use your assigned agent ID)

    Examples of when to use broadcast:
    - "I found a critical bug in module X that affects everyone"
    - "Does anyone have information about how authentication works?"
    - "I've completed the database schema - all agents can now use it"
    - "Warning: The API endpoint /users is currently down"

    The message will be delivered to all active agents with the prefix:
    [AGENT {your_id} BROADCAST]: {your_message}
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/broadcast_message",
                json={"message": message},
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": sender_agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                recipient_count = result.get('recipient_count', 0)
                if recipient_count == 0:
                    return "📢 Broadcast sent, but no other agents are currently active"
                return f"📢 Message broadcast successfully to {recipient_count} agent(s)"
            else:
                return f"❌ Failed to broadcast message: {response.text}"
    except Exception as e:
        return f"❌ Error broadcasting message: {str(e)}"


@mcp.tool()
async def send_message(message: str, sender_agent_id: str, recipient_agent_id: str) -> str:
    """Send a direct message to a specific agent.

    Use this when you know which specific agent you want to communicate with,
    such as asking for help from an agent working on a related task or
    providing targeted information to a specific agent.

    Args:
        message: The message content to send
        sender_agent_id: Your agent ID (REQUIRED - use your assigned agent ID)
        recipient_agent_id: The ID of the agent you want to message

    Examples of when to use direct messaging:
    - "Agent X: I need the API specs you were working on"
    - "Agent Y: Your task conflicts with mine - can we coordinate?"
    - "Agent Z: I found the answer to your earlier question about caching"
    - "Agent W: Can you review my implementation before I submit?"

    The message will be delivered with the prefix:
    [AGENT {your_id} TO AGENT {recipient_id}]: {your_message}

    Tip: Use get_agent_status() to see which agents are currently active
    and what tasks they're working on before sending a message.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/send_message",
                json={
                    "recipient_agent_id": recipient_agent_id,
                    "message": message
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": sender_agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return f"✉️ Message sent successfully to agent {recipient_agent_id[:8]}"
                else:
                    return f"❌ {result.get('message', 'Failed to send message')}"
            else:
                return f"❌ Failed to send message: {response.text}"
    except Exception as e:
        return f"❌ Error sending message: {str(e)}"


# ==================== TICKET TRACKING SYSTEM TOOLS ====================

@mcp.tool()
async def create_ticket(
    agent_id: str,
    title: str,
    description: str,
    ticket_type: str = "task",
    priority: str = "medium",
    tags: list = None,
    blocked_by_ticket_ids: list = None,
    assigned_agent_id: str = None,
    parent_ticket_id: str = None
) -> str:
    """Create a new ticket in the workflow tracking system.

    Use this when you discover work that needs to be tracked separately from tasks.
    Returns similar tickets for duplicate detection.

    Args:
        agent_id: Your agent ID (CRITICAL: use YOUR UUID from initial prompt, e.g., "84f15f6c-35b1-4d57-97ac-92a3c0c94d29")
        title: Short, descriptive title for the ticket (3-500 chars)
        description: Detailed description of what needs to be done (min 10 chars)
        ticket_type: Type of ticket (bug/feature/improvement/task/spike) - default: task
        priority: Priority level (low/medium/high/critical) - default: medium
        tags: Optional list of tags for categorization
        blocked_by_ticket_ids: List of ticket IDs that block this ticket
        assigned_agent_id: Optional agent to assign ticket to
        parent_ticket_id: Optional parent ticket for sub-tickets

    CRITICAL: agent_id must be your full UUID from your initial prompt!
    DO NOT use 'agent' or 'agent-mcp' - it will fail with "Agent not found"!
    
    IMPORTANT: Search for existing tickets before creating to avoid duplicates!
    Use search_tickets() with semantic search to find related work.
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[MCP_CLIENT_TICKET] ========== START ==========")
    logger.info(f"[MCP_CLIENT_TICKET] Agent: {agent_id}")
    logger.info(f"[MCP_CLIENT_TICKET] Title: {title[:60]}...")
    logger.info(f"[MCP_CLIENT_TICKET] Type: {ticket_type}, Priority: {priority}")

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "title": title,
                "description": description,
                "ticket_type": ticket_type,
                "priority": priority,
                "tags": tags or [],
                "blocked_by_ticket_ids": blocked_by_ticket_ids or [],
                "assigned_agent_id": assigned_agent_id,
                "parent_ticket_id": parent_ticket_id,
            }

            logger.info(f"[MCP_CLIENT_TICKET] Payload: {payload}")
            logger.info(f"[MCP_CLIENT_TICKET] Sending POST to {HEPHAESTUS_URL}/api/tickets/create")

            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/create",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            logger.info(f"[MCP_CLIENT_TICKET] Response status: {response.status_code}")
            logger.info(f"[MCP_CLIENT_TICKET] Response body: {response.text}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"[MCP_CLIENT_TICKET] ✅ Success! Ticket ID: {result.get('ticket_id')}")

                similar_msg = ""
                if result.get("similar_tickets"):
                    similar_msg = f"\n\n⚠️ Found {len(result['similar_tickets'])} similar tickets - check for duplicates!"

                success_message = f"""✅ Ticket created successfully!
Ticket ID: {result.get('ticket_id', 'unknown')}
Status: {result.get('status', 'unknown')}
Message: {result.get('message', '')}{similar_msg}"""
                logger.info(f"[MCP_CLIENT_TICKET] Returning success message to agent")
                logger.info(f"[MCP_CLIENT_TICKET] ========== SUCCESS ==========")
                return success_message
            else:
                error_message = f"❌ Failed to create ticket: {response.text}"
                logger.error(f"[MCP_CLIENT_TICKET] ❌ HTTP {response.status_code}: {response.text}")
                logger.error(f"[MCP_CLIENT_TICKET] Returning error message to agent")
                logger.error(f"[MCP_CLIENT_TICKET] ========== FAILED ==========")
                return error_message
    except Exception as e:
        error_message = f"❌ Error creating ticket: {str(e)}"
        logger.error(f"[MCP_CLIENT_TICKET] ❌ Exception: {type(e).__name__}: {e}")
        logger.error(f"[MCP_CLIENT_TICKET] ========== EXCEPTION ==========")
        return error_message


@mcp.tool()
async def update_ticket(
    ticket_id: str,
    agent_id: str,
    updates: dict,
    update_comment: str = None
) -> str:
    """Update ticket fields (title, description, priority, tags, assigned_agent_id, blocked_by_ticket_ids).

    Cannot change status - use change_ticket_status for that.

    Args:
        ticket_id: ID of the ticket to update
        agent_id: Your agent ID
        updates: Fields to update (dict with keys: title, description, priority, assigned_agent_id, ticket_type, tags, blocked_by_ticket_ids)
        update_comment: Optional comment explaining the update
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/update",
                json={
                    "ticket_id": ticket_id,
                    "updates": updates,
                    "update_comment": update_comment,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                return f"""✅ Ticket updated successfully!
Ticket ID: {ticket_id}
Fields updated: {', '.join(result.get('fields_updated', []))}
Message: {result.get('message', '')}"""
            else:
                return f"❌ Failed to update ticket: {response.text}"
    except Exception as e:
        return f"❌ Error updating ticket: {str(e)}"


@mcp.tool()
async def change_ticket_status(
    ticket_id: str,
    agent_id: str,
    new_status: str,
    comment: str,
    commit_sha: str = None
) -> str:
    """Move ticket to a different status column.

    IMPORTANT: Blocked tickets (with blocked_by_ticket_ids) cannot change status until blockers are resolved.

    Args:
        ticket_id: ID of the ticket
        agent_id: Your agent ID
        new_status: New status (must match board_config columns)
        comment: Required comment explaining status change (min 10 chars)
        commit_sha: Optional commit SHA to link to this status change
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/change-status",
                json={
                    "ticket_id": ticket_id,
                    "new_status": new_status,
                    "comment": comment,
                    "commit_sha": commit_sha,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("blocked"):
                    blocking_ids = ', '.join(result.get("blocking_ticket_ids", []))
                    return f"""🔒 Ticket is BLOCKED!
Ticket ID: {ticket_id}
Blocked by: {blocking_ids}
Cannot change status until blocking tickets are resolved."""
                else:
                    return f"""✅ Ticket status changed!
Ticket ID: {ticket_id}
From: {result.get('old_status', 'unknown')}
To: {result.get('new_status', 'unknown')}"""
            else:
                return f"❌ Failed to change ticket status: {response.text}"
    except Exception as e:
        return f"❌ Error changing ticket status: {str(e)}"


@mcp.tool()
async def add_ticket_comment(
    ticket_id: str,
    agent_id: str,
    comment_text: str,
    comment_type: str = "general",
    mentions: list = None
) -> str:
    """Add a comment to a ticket.

    Use for progress updates, blockers, or communication with other agents.

    Args:
        ticket_id: ID of the ticket
        agent_id: Your agent ID
        comment_text: Comment text (min 1 char)
        comment_type: Type of comment (general/status_change/blocker/resolution) - default: general
        mentions: Agent/ticket IDs mentioned in comment
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/comment",
                json={
                    "ticket_id": ticket_id,
                    "comment_text": comment_text,
                    "comment_type": comment_type,
                    "mentions": mentions or [],
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                return f"✅ Comment added to ticket {ticket_id}"
            else:
                return f"❌ Failed to add comment: {response.text}"
    except Exception as e:
        return f"❌ Error adding comment: {str(e)}"


@mcp.tool()
async def search_tickets(
    agent_id: str,
    query: str,
    search_type: str = "hybrid",
    filters: dict = None,
    limit: int = 10,
    include_comments: bool = True
) -> str:
    """Search for tickets using HYBRID search (70% semantic + 30% keyword) by default.

    Use natural language queries. Shows blocked (🔒) and resolved (✅) indicators.

    Args:
        agent_id: Your agent ID
        query: Search query (natural language, min 3 chars)
        search_type: Search mode (semantic/keyword/hybrid) - DEFAULT: hybrid = 70% semantic + 30% keyword
        filters: Optional filters (dict with keys: status, priority, ticket_type, assigned_agent_id, tags, is_blocked)
        limit: Max number of results (1-50) - default: 10
        include_comments: Whether to search in comments too - default: true

    BEST PRACTICE: Use hybrid search (default) for best results!
    - Hybrid combines semantic understanding with keyword precision
    - Semantic search is good for conceptual queries
    - Keyword search is good for exact term matching
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/search",
                json={
                    "query": query,
                    "search_type": search_type,
                    "filters": filters or {},
                    "limit": limit,
                    "include_comments": include_comments,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                if not result.get("results"):
                    return f"🔍 No tickets found for query: '{query}'"

                ticket_list = []
                for ticket in result.get("results", []):
                    blocked_icon = "🔒" if ticket.get("is_blocked") else ""
                    resolved_icon = "✅" if ticket.get("is_resolved") else ""
                    ticket_list.append(
                        f"{blocked_icon}{resolved_icon} {ticket['ticket_id'][:12]}: [{ticket['status']}] {ticket['title'][:60]} (score: {ticket.get('relevance_score', 0):.2f})"
                    )

                search_mode_msg = f"({search_type} search: " + (
                    "70% semantic + 30% keyword" if search_type == "hybrid" else search_type
                ) + ")"

                return f"""🔍 Found {result.get('total_found', 0)} tickets {search_mode_msg}
Search time: {result.get('search_time_ms', 0):.0f}ms

{chr(10).join(ticket_list)}

💡 Tip: Use hybrid search (default) for best results!"""
            else:
                return f"❌ Failed to search tickets: {response.text}"
    except Exception as e:
        return f"❌ Error searching tickets: {str(e)}"


@mcp.tool()
async def get_ticket(ticket_id: str) -> str:
    """Get detailed information about a specific ticket by its exact ID.

    IMPORTANT: You MUST provide the EXACT, COMPLETE ticket ID.

    Args:
        ticket_id: The complete ticket ID (e.g., "ticket-c368a0d1-cbd7-4231-a374-0a3a7374064e")
                   Do NOT use shortened IDs like "ticket-c368a"!

    Returns:
        Complete ticket details including:
        - Full description
        - All comments with timestamps
        - Complete history of status changes
        - All linked commits with file changes
        - Blocking/blocked relationships
        - Tags and metadata

    If you DON'T know the exact ticket ID:
        1. Use search_tickets() to find tickets by title/description
        2. Use get_tickets() to list all tickets
        3. Then use this function with the exact ticket_id from those results

    Example workflow:
        # First, search for the ticket
        search_result = search_tickets(
            agent_id="your-id",
            query="Frontend Infrastructure",
            search_type="hybrid"
        )
        # Note the exact ticket_id from results: ticket-c368a0d1-cbd7-4231-a374-0a3a7374064e

        # Then get full details
        details = get_ticket("ticket-c368a0d1-cbd7-4231-a374-0a3a7374064e")
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HEPHAESTUS_URL}/api/tickets/{ticket_id}",
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                ticket = data.get("ticket", {})
                comments = data.get("comments", [])
                history = data.get("history", [])
                commits = data.get("commits", [])

                # Format the output
                result = []

                # Header
                blocked_icon = "🔒 " if ticket.get("is_blocked") else ""
                resolved_icon = "✅ " if ticket.get("is_resolved") else ""
                result.append(f"{'='*80}")
                result.append(f"{blocked_icon}{resolved_icon}TICKET: {ticket['id']}")
                result.append(f"{'='*80}")

                # Basic info
                result.append(f"\n📋 BASIC INFORMATION")
                result.append(f"Title: {ticket['title']}")
                result.append(f"Status: {ticket['status']}")
                result.append(f"Type: {ticket['ticket_type']}")
                result.append(f"Priority: {ticket['priority']}")
                result.append(f"Created: {ticket['created_at']}")
                result.append(f"Updated: {ticket['updated_at']}")

                if ticket.get('assigned_agent_id'):
                    result.append(f"Assigned to: {ticket['assigned_agent_id']}")

                if ticket.get('tags'):
                    result.append(f"Tags: {', '.join(ticket['tags'])}")

                # Blocking info
                if ticket.get('blocked_by_ticket_ids'):
                    result.append(f"\n🔒 BLOCKED BY:")
                    for blocking_id in ticket['blocked_by_ticket_ids']:
                        result.append(f"  - {blocking_id}")

                # Description
                result.append(f"\n📝 DESCRIPTION")
                result.append(ticket['description'])

                # Comments
                if comments:
                    result.append(f"\n💬 COMMENTS ({len(comments)})")
                    for comment in comments:
                        result.append(f"\n  [{comment['created_at']}] {comment['agent_id'][:8]}...")
                        result.append(f"  Type: {comment['comment_type']}")
                        result.append(f"  {comment['comment_text']}")

                # History
                if history:
                    result.append(f"\n📜 HISTORY ({len(history)})")
                    for event in history[-10:]:  # Last 10 events
                        result.append(f"\n  [{event['changed_at']}] {event['change_type']}")
                        if event.get('old_value') and event.get('new_value'):
                            result.append(f"  {event['old_value']} → {event['new_value']}")
                        if event.get('change_description'):
                            result.append(f"  {event['change_description']}")

                # Commits
                if commits:
                    result.append(f"\n🔨 LINKED COMMITS ({len(commits)})")
                    for commit in commits:
                        result.append(f"\n  {commit['commit_sha'][:8]}: {commit['commit_message'][:60]}")
                        result.append(f"  Files: {commit['files_changed']}, +{commit['insertions']} -{commit['deletions']}")
                        if commit.get('files_list'):
                            result.append(f"  Modified: {', '.join(commit['files_list'][:5])}")

                result.append(f"\n{'='*80}")

                return "\n".join(result)

            elif response.status_code == 404:
                return f"❌ Ticket not found: {ticket_id}\n\nMake sure you're using the COMPLETE ticket ID (e.g., ticket-c368a0d1-cbd7-4231-a374-0a3a7374064e)\nUse search_tickets() or get_tickets() to find the correct ticket ID."
            else:
                return f"❌ Failed to get ticket: {response.text}"
    except Exception as e:
        return f"❌ Error getting ticket: {str(e)}"


@mcp.tool()
async def get_tickets(
    agent_id: str,
    status: str = None,
    ticket_type: str = None,
    priority: str = None,
    assigned_agent_id: str = None,
    include_completed: bool = True,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> str:
    """List tickets with filtering and pagination.

    Shows blocked (🔒) and resolved (✅) indicators.

    Args:
        agent_id: Your agent ID
        status: Filter by status
        ticket_type: Filter by type
        priority: Filter by priority
        assigned_agent_id: Filter by assigned agent
        include_completed: Include completed tickets - default: true
        limit: Max number of results (1-200) - default: 50
        offset: Offset for pagination - default: 0
        sort_by: Sort field (created_at/updated_at/priority/status) - default: created_at
        sort_order: Sort order (asc/desc) - default: desc
    """
    try:
        async with httpx.AsyncClient() as client:
            params = {
                "include_completed": include_completed,
                "limit": limit,
                "offset": offset,
                "sort_by": sort_by,
                "sort_order": sort_order,
            }
            if status:
                params["status"] = status
            if ticket_type:
                params["ticket_type"] = ticket_type
            if priority:
                params["priority"] = priority
            if assigned_agent_id:
                params["assigned_agent_id"] = assigned_agent_id

            response = await client.get(
                f"{HEPHAESTUS_URL}/api/tickets",
                params=params,
                headers={"X-Agent-ID": agent_id},
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                if not result.get("tickets"):
                    return "📋 No tickets found"

                ticket_list = []
                for ticket in result.get("tickets", []):
                    blocked_icon = "🔒" if ticket.get("is_blocked") else ""
                    resolved_icon = "✅" if ticket.get("is_resolved") else ""
                    ticket_list.append(
                        f"{blocked_icon}{resolved_icon} {ticket['ticket_id'][:12]}: [{ticket['status']}] {ticket['title'][:60]}"
                    )

                return f"""📋 Found {result.get('total_count', 0)} tickets (showing {len(result.get('tickets', []))})
Has more: {result.get('has_more', False)}

{chr(10).join(ticket_list)}"""
            else:
                return f"❌ Failed to get tickets: {response.text}"
    except Exception as e:
        return f"❌ Error getting tickets: {str(e)}"


@mcp.tool()
async def link_commit_to_ticket(
    ticket_id: str,
    agent_id: str,
    commit_sha: str,
    commit_message: str = None
) -> str:
    """Manually link a git commit to a ticket for traceability.

    Auto-linking happens on task completion.

    Args:
        ticket_id: ID of the ticket
        agent_id: Your agent ID
        commit_sha: Git commit SHA
        commit_message: Optional commit message (auto-fetched if not provided)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/link-commit",
                json={
                    "ticket_id": ticket_id,
                    "commit_sha": commit_sha,
                    "commit_message": commit_message,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                return f"✅ Commit {commit_sha[:8]} linked to ticket {ticket_id}"
            else:
                return f"❌ Failed to link commit: {response.text}"
    except Exception as e:
        return f"❌ Error linking commit: {str(e)}"


@mcp.tool()
async def get_commit_diff(
    commit_sha: str,
    agent_id: str
) -> str:
    """Get detailed git diff for a commit (used by Git Diff Window in UI).

    Returns structured diff data with file changes, insertions, deletions.

    Args:
        commit_sha: Git commit SHA to get diff for
        agent_id: Your agent ID
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HEPHAESTUS_URL}/api/tickets/commit-diff/{commit_sha}",
                headers={"X-Agent-ID": agent_id},
                timeout=30.0  # Longer timeout for git operations
            )

            if response.status_code == 200:
                result = response.json()
                file_summary = []
                for file_info in result.get("files", []):
                    file_summary.append(
                        f"  {file_info['status'][:1].upper()}: {file_info['path']} (+{file_info['insertions']} -{file_info['deletions']})"
                    )

                return f"""📊 Commit {commit_sha[:8]}
Message: {result.get('message', 'No message')}
Author: {result.get('author_agent_id', 'unknown')}
Files changed: {result.get('files_changed', 0)}
+{result.get('insertions', 0)} -{result.get('deletions', 0)}

{chr(10).join(file_summary) if file_summary else 'No files changed'}"""
            else:
                return f"❌ Failed to get commit diff: {response.text}"
    except Exception as e:
        return f"❌ Error getting commit diff: {str(e)}"


@mcp.tool()
async def resolve_ticket(
    ticket_id: str,
    agent_id: str,
    resolution_comment: str,
    commit_sha: str = None
) -> str:
    """Mark ticket as resolved.

    IMPORTANT: Automatically unblocks all tickets that were blocked by this ticket.
    Returns list of unblocked ticket IDs.

    Args:
        ticket_id: ID of the ticket to resolve
        agent_id: Your agent ID
        resolution_comment: Comment explaining resolution (min 10 chars)
        commit_sha: Optional commit SHA that resolved the ticket
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/resolve",
                json={
                    "ticket_id": ticket_id,
                    "resolution_comment": resolution_comment,
                    "commit_sha": commit_sha,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                unblocked = result.get("unblocked_tickets", [])
                unblocked_msg = ""
                if unblocked:
                    unblocked_msg = f"\n🔓 Unblocked {len(unblocked)} tickets: {', '.join([t[:12] for t in unblocked])}"

                return f"""✅ Ticket resolved!
Ticket ID: {ticket_id}
Message: {result.get('message', '')}{unblocked_msg}"""
            else:
                return f"❌ Failed to resolve ticket: {response.text}"
    except Exception as e:
        return f"❌ Error resolving ticket: {str(e)}"


@mcp.tool()
async def request_ticket_clarification(
    ticket_id: str,
    agent_id: str,
    conflict_description: str,
    context: str = "",
    potential_solutions: list = None
) -> str:
    """Request LLM-powered clarification for a ticket with conflicting/unclear requirements.

    🎯 USE THIS WHEN:
    - You encounter conflicting requirements in a ticket
    - Instructions are ambiguous and could be interpreted multiple ways
    - You're uncertain about which approach to take
    - You need arbitration between different implementation options
    - You would otherwise create a new task to ask for clarification

    ⚠️ IMPORTANT: Use this INSTEAD of creating new tasks when unclear!
    This prevents infinite loops of task creation.

    The LLM arbitrator will:
    1. Analyze your conflict against the project goal
    2. Review all recent tickets and tasks for context
    3. Evaluate your potential solutions systematically
    4. Provide clear, actionable resolution with specific next steps
    5. Store the clarification as a comment on the ticket

    Args:
        ticket_id: ID of the ticket needing clarification
        agent_id: Your agent ID
        conflict_description: Clear description of the conflict or ambiguity (min 20 chars)
        context: Additional context that might help resolve the conflict
        potential_solutions: List of potential solutions you're considering (highly recommended!)

    Returns:
        Detailed markdown guidance including:
        - Analysis of the conflict
        - Evaluation of your proposed solutions
        - Recommended resolution with rationale
        - Specific ticket updates to make
        - Specific file changes needed
        - What to avoid

    Example:
        request_ticket_clarification(
            ticket_id="ticket-123",
            agent_id="agent-456",
            conflict_description="The ticket says to 'optimize performance' but also 'maintain compatibility'. These seem to conflict because the optimization would break the old API.",
            context="We have a legacy API used by external clients.",
            potential_solutions=[
                "Create new optimized API endpoint and keep old one",
                "Add versioning to API and optimize new version",
                "Optimize only internal parts, keep API unchanged"
            ]
        )
    """
    import logging

    potential_solutions = potential_solutions or []

    logger = logging.getLogger(__name__)
    logger.info(f"[MCP_CLARIFICATION] Agent {agent_id[:8]} requesting clarification for {ticket_id}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HEPHAESTUS_URL}/api/tickets/request-clarification",
                json={
                    "ticket_id": ticket_id,
                    "conflict_description": conflict_description,
                    "context": context,
                    "potential_solutions": potential_solutions,
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Agent-ID": agent_id
                },
                timeout=60.0  # Longer timeout for LLM reasoning
            )

            if response.status_code == 200:
                result = response.json()
                clarification = result.get('clarification', '')
                comment_id = result.get('comment_id', 'unknown')

                return f"""✅ **Clarification Received from Arbitration System**

{clarification}

---

💬 **Audit Trail**: This clarification has been stored as comment `{comment_id[:12]}` on ticket `{ticket_id}`

📝 **Next Steps**:
1. Review the "RESOLUTION & ACTION PLAN" section above
2. Update the ticket as specified
3. Make the file changes as outlined
4. Follow the testing requirements
5. Avoid the approaches listed in "What NOT to Do"

⚡ You now have clear direction - proceed with confidence!"""
            else:
                logger.error(f"[MCP_CLARIFICATION] Failed: {response.status_code} - {response.text}")
                return f"❌ Failed to get clarification: {response.text}"
    except Exception as e:
        logger.error(f"[MCP_CLARIFICATION] Exception: {e}", exc_info=True)
        return f"❌ Error requesting clarification: {str(e)}"


# Run the MCP server
if __name__ == "__main__":
    print("🚀 Starting Claude MCP Client for Hephaestus...")
    print("📡 Connecting to Hephaestus server at http://localhost:8000")
    print("✨ Available tools:")
    print("\n📋 Task Management:")
    print("  - health_check: Check server status")
    print("  - create_task: Create a new task")
    print("  - get_tasks: List all tasks")
    print("  - update_task_status: Update task status (done/failed/in_progress)")
    print("  - save_memory: Save knowledge to memory")
    print("\n🔍 Validation & Results:")
    print("  - give_validation_review: Submit validation review (validator agents only)")
    print("  - submit_result: Submit workflow result with evidence")
    print("  - submit_result_validation: Submit result validation (result validator agents only)")
    print("  - get_workflow_results: Get all results for a workflow")
    print("\n👥 Agent Communication:")
    print("  - get_agent_status: Get agent statuses")
    print("  - broadcast_message: Broadcast a message to all active agents")
    print("  - send_message: Send a direct message to a specific agent")
    print("\n🎫 Ticket Tracking (when enabled for workflow):")
    print("  - create_ticket: Create a new ticket (returns similar tickets for duplicate detection)")
    print("  - update_ticket: Update ticket fields (title, description, priority, tags, etc.)")
    print("  - change_ticket_status: Move ticket to different status (checks blockers)")
    print("  - add_ticket_comment: Add comment to ticket (for progress updates, blockers)")
    print("  - search_tickets: Search tickets using HYBRID search (70% semantic + 30% keyword) - DEFAULT")
    print("  - get_ticket: Get full details for a specific ticket by exact ID (description, comments, history, commits)")
    print("  - get_tickets: List/filter tickets with pagination")
    print("  - link_commit_to_ticket: Manually link git commit to ticket (auto-linking on task completion)")
    print("  - get_commit_diff: Get detailed git diff for commit (for Git Diff Window)")
    print("  - resolve_ticket: Mark ticket as resolved (auto-unblocks dependent tickets)")
    print("  - request_ticket_clarification: Request LLM arbitration for conflicting requirements (PREVENTS TASK LOOPS!)")
    print("\n💡 Ticket Tracking Tips:")
    print("  - Search BEFORE creating to avoid duplicates (use search_tickets with hybrid mode)")
    print("  - Use get_ticket() with the EXACT ticket ID to see full details (description, comments, history)")
    print("  - If you don't know the exact ticket ID, search first with search_tickets() or get_tickets()")
    print("  - Use blocked_by_ticket_ids to create dependencies between tickets")
    print("  - Blocked tickets cannot change status until blocking tickets are resolved")
    print("  - Resolving a ticket automatically unblocks all dependent tickets")
    print("  - Hybrid search (default) combines semantic understanding + keyword precision")
    mcp.run()