"""Workflow termination handler for stopping all agents when result is validated."""

import logging
from typing import List, Dict, Any
from datetime import datetime

from src.core.database import DatabaseManager, Workflow, Task, Agent
from src.agents.manager import AgentManager

logger = logging.getLogger(__name__)


class WorkflowTerminationHandler:
    """Handles termination of workflows when results are validated."""

    def __init__(self, db_manager: DatabaseManager, agent_manager: AgentManager):
        """Initialize the termination handler.

        Args:
            db_manager: Database manager instance
            agent_manager: Agent manager for terminating agents
        """
        self.db_manager = db_manager
        self.agent_manager = agent_manager

    async def terminate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Terminate all aspects of a workflow when a result is validated.

        Args:
            workflow_id: ID of the workflow to terminate

        Returns:
            Dictionary with termination results and statistics

        Raises:
            ValueError: If workflow not found
        """
        logger.info(f"Starting termination of workflow {workflow_id}")

        session = self.db_manager.get_session()
        termination_results = {
            "workflow_id": workflow_id,
            "terminated_agents": [],
            "cancelled_tasks": [],
            "cleanup_actions": [],
            "errors": [],
            "terminated_at": datetime.utcnow().isoformat(),
        }

        try:
            # Get the workflow
            workflow = session.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")

            # 1. Terminate all active agents in the workflow
            agents_terminated = await self._terminate_workflow_agents(workflow_id, termination_results)
            logger.info(f"Terminated {agents_terminated} agents for workflow {workflow_id}")

            # 2. Cancel all pending and in-progress tasks
            tasks_cancelled = await self._cancel_workflow_tasks(workflow_id, session, termination_results)
            logger.info(f"Cancelled {tasks_cancelled} tasks for workflow {workflow_id}")

            # 3. Clean up workflow resources
            cleanup_actions = await self._cleanup_workflow_resources(workflow_id, session, termination_results)
            logger.info(f"Performed {len(cleanup_actions)} cleanup actions for workflow {workflow_id}")

            # 4. Mark workflow as completed by result
            workflow.status = "completed"
            workflow.completed_by_result = True
            session.commit()

            termination_results["cleanup_actions"].append({
                "action": "mark_workflow_complete",
                "details": f"Workflow {workflow_id} marked as completed by result",
                "success": True,
            })

            logger.info(f"Successfully terminated workflow {workflow_id}")

            return termination_results

        except Exception as e:
            logger.error(f"Error during workflow termination: {e}")
            termination_results["errors"].append({
                "error": str(e),
                "context": "workflow_termination",
            })
            session.rollback()
            raise
        finally:
            session.close()

    async def _terminate_workflow_agents(self, workflow_id: str, results: Dict[str, Any]) -> int:
        """Terminate all agents working on the workflow.

        Args:
            workflow_id: Workflow ID
            results: Results dictionary to update

        Returns:
            Number of agents terminated
        """
        session = self.db_manager.get_session()
        agents_terminated = 0

        try:
            # Find all active agents with tasks in this workflow
            # Specify the join explicitly using assigned_agent_id
            agents = session.query(Agent).join(Task, Agent.id == Task.assigned_agent_id).filter(
                Task.workflow_id == workflow_id,
                Agent.status.in_(["working", "idle"]),
                Agent.agent_type != "result_validator"  # Don't terminate result validators
            ).distinct().all()

            for agent in agents:
                try:
                    logger.info(f"Terminating agent {agent.id} for workflow {workflow_id}")
                    await self.agent_manager.terminate_agent(agent.id)
                    agents_terminated += 1

                    results["terminated_agents"].append({
                        "agent_id": agent.id,
                        "agent_type": agent.agent_type,
                        "success": True,
                        "current_task_id": agent.current_task_id,
                    })

                except Exception as e:
                    logger.error(f"Failed to terminate agent {agent.id}: {e}")
                    results["errors"].append({
                        "error": str(e),
                        "context": f"terminate_agent_{agent.id}",
                    })
                    results["terminated_agents"].append({
                        "agent_id": agent.id,
                        "agent_type": agent.agent_type,
                        "success": False,
                        "error": str(e),
                    })

            return agents_terminated

        finally:
            session.close()

    async def _cancel_workflow_tasks(self, workflow_id: str, session, results: Dict[str, Any]) -> int:
        """Cancel all pending and in-progress tasks for the workflow.

        Args:
            workflow_id: Workflow ID
            session: Database session
            results: Results dictionary to update

        Returns:
            Number of tasks cancelled
        """
        tasks_cancelled = 0

        try:
            # Find all non-completed tasks in the workflow
            tasks = session.query(Task).filter(
                Task.workflow_id == workflow_id,
                Task.status.in_(["pending", "assigned", "in_progress", "under_review"])
            ).all()

            for task in tasks:
                try:
                    original_status = task.status
                    task.status = "failed"
                    task.failure_reason = "Workflow terminated due to validated result"
                    task.completed_at = datetime.utcnow()
                    tasks_cancelled += 1

                    results["cancelled_tasks"].append({
                        "task_id": task.id,
                        "original_status": original_status,
                        "success": True,
                        "phase_id": task.phase_id,
                    })

                    logger.debug(f"Cancelled task {task.id} (was {original_status})")

                except Exception as e:
                    logger.error(f"Failed to cancel task {task.id}: {e}")
                    results["errors"].append({
                        "error": str(e),
                        "context": f"cancel_task_{task.id}",
                    })

            session.commit()
            return tasks_cancelled

        except Exception as e:
            logger.error(f"Error cancelling workflow tasks: {e}")
            session.rollback()
            raise

    async def _cleanup_workflow_resources(self, workflow_id: str, session, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Clean up workflow-specific resources.

        Args:
            workflow_id: Workflow ID
            session: Database session
            results: Results dictionary to update

        Returns:
            List of cleanup actions performed
        """
        cleanup_actions = []

        try:
            # 1. Clean up agent worktrees for this workflow
            from src.core.database import AgentWorktree
            # Specify the join explicitly using assigned_agent_id
            worktrees = session.query(AgentWorktree).join(
                Agent, AgentWorktree.agent_id == Agent.id
            ).join(
                Task, Agent.id == Task.assigned_agent_id
            ).filter(
                Task.workflow_id == workflow_id,
                AgentWorktree.merge_status == "active"
            ).all()

            for worktree in worktrees:
                try:
                    # Mark worktree as abandoned (don't actually delete files)
                    worktree.merge_status = "abandoned"
                    cleanup_actions.append({
                        "action": "abandon_worktree",
                        "details": f"Abandoned worktree for agent {worktree.agent_id}",
                        "success": True,
                        "worktree_path": worktree.worktree_path,
                    })
                    logger.debug(f"Abandoned worktree for agent {worktree.agent_id}")

                except Exception as e:
                    logger.error(f"Failed to cleanup worktree {worktree.agent_id}: {e}")
                    cleanup_actions.append({
                        "action": "abandon_worktree",
                        "details": f"Failed to abandon worktree for agent {worktree.agent_id}",
                        "success": False,
                        "error": str(e),
                    })

            # 2. Update phase executions to completed
            from src.core.database import PhaseExecution, Phase
            phase_executions = session.query(PhaseExecution).join(Phase).filter(
                Phase.workflow_id == workflow_id,
                PhaseExecution.status.in_(["pending", "in_progress"])
            ).all()

            for execution in phase_executions:
                try:
                    execution.status = "completed"
                    execution.completed_at = datetime.utcnow()
                    execution.completion_summary = "Completed due to workflow termination by validated result"
                    cleanup_actions.append({
                        "action": "complete_phase_execution",
                        "details": f"Completed phase execution {execution.id}",
                        "success": True,
                        "phase_id": execution.phase_id,
                    })

                except Exception as e:
                    logger.error(f"Failed to complete phase execution {execution.id}: {e}")
                    cleanup_actions.append({
                        "action": "complete_phase_execution",
                        "details": f"Failed to complete phase execution {execution.id}",
                        "success": False,
                        "error": str(e),
                    })

            session.commit()
            results["cleanup_actions"].extend(cleanup_actions)

            return cleanup_actions

        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")
            session.rollback()
            raise

    def get_workflow_termination_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the termination status of a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Dictionary with termination status information
        """
        session = self.db_manager.get_session()

        try:
            workflow = session.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                return {"error": "Workflow not found"}

            # Count remaining active elements
            # Specify the join explicitly using assigned_agent_id
            active_agents = session.query(Agent).join(
                Task, Agent.id == Task.assigned_agent_id
            ).filter(
                Task.workflow_id == workflow_id,
                Agent.status.in_(["working", "idle"])
            ).count()

            active_tasks = session.query(Task).filter(
                Task.workflow_id == workflow_id,
                Task.status.in_(["pending", "assigned", "in_progress"])
            ).count()

            return {
                "workflow_id": workflow_id,
                "workflow_status": workflow.status,
                "completed_by_result": workflow.completed_by_result,
                "result_found": workflow.result_found,
                "active_agents": active_agents,
                "active_tasks": active_tasks,
                "is_terminated": workflow.completed_by_result and workflow.status == "completed",
            }

        finally:
            session.close()