"""Intelligent monitoring and self-healing system for Hephaestus."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import json

from src.core.simple_config import get_config
from src.core.database import DatabaseManager, Agent, Task, AgentLog, GuardianAnalysis, ConductorAnalysis, DetectedDuplicate, SteeringIntervention
from src.agents.manager import AgentManager
from src.interfaces import LLMProviderInterface, get_cli_agent
from src.memory.rag import RAGSystem
from src.phases import PhaseManager
from src.monitoring.guardian import Guardian
from src.monitoring.conductor import Conductor, SystemDecision
from src.monitoring.trajectory_context import TrajectoryContext

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent state enumeration."""
    HEALTHY = "healthy"
    STUCK_WAITING = "stuck_waiting"
    STUCK_ERROR = "stuck_error"
    STUCK_CONFUSED = "stuck_confused"
    UNRECOVERABLE = "unrecoverable"


class MonitoringDecision(Enum):
    """Monitoring decision enumeration."""
    CONTINUE = "continue"
    NUDGE = "nudge"
    ANSWER = "answer"
    RESTART = "restart"
    RECREATE = "recreate"


class IntelligentMonitor:
    """LLM-powered monitoring system for agent health and intervention."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        agent_manager: AgentManager,
        llm_provider: LLMProviderInterface,
        rag_system: RAGSystem,
    ):
        """Initialize intelligent monitor.

        Args:
            db_manager: Database manager
            agent_manager: Agent manager
            llm_provider: LLM provider for analysis
            rag_system: RAG system for context
        """
        self.db_manager = db_manager
        self.agent_manager = agent_manager
        self.llm_provider = llm_provider
        self.rag_system = rag_system
        self.config = get_config()

    async def analyze_agent_state(self, agent: Agent) -> Dict[str, Any]:
        """Analyze agent state and decide on intervention.

        Args:
            agent: Agent to analyze

        Returns:
            Analysis result with state and decision
        """
        logger.debug(f"Analyzing agent {agent.id} state")

        try:
            # Collect comprehensive context
            context = await self._collect_agent_context(agent)

            # Analyze with LLM
            analysis = await self.llm_provider.analyze_agent_state(
                agent_output=context["tmux_output"],
                task_info={
                    "description": context["task_description"],
                    "done_definition": context["done_definition"],
                    "time_elapsed": context["time_elapsed"],
                },
                project_context=context["project_context"],
            )

            logger.info(
                f"Agent {agent.id} analysis: state={analysis['state']}, "
                f"decision={analysis['decision']}, confidence={analysis.get('confidence', 0)}"
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze agent {agent.id}: {e}")
            return {
                "state": AgentState.HEALTHY.value,
                "decision": MonitoringDecision.CONTINUE.value,
                "message": "",
                "reasoning": "Analysis failed, assuming healthy",
                "confidence": 0.1,
            }

    async def _collect_agent_context(self, agent: Agent) -> Dict[str, Any]:
        """Collect comprehensive context for agent analysis.

        Args:
            agent: Agent to collect context for

        Returns:
            Context dictionary
        """
        # Get tmux output
        tmux_output = self.agent_manager.get_agent_output(
            agent.id,
            lines=self.config.tmux_output_lines,
        )

        # Get task details
        session = self.db_manager.get_session()
        task = session.query(Task).filter_by(id=agent.current_task_id).first()
        session.close()

        if not task:
            logger.error(f"Task {agent.current_task_id} not found for agent {agent.id}")
            task_description = "Unknown task"
            done_definition = "Unknown"
            time_elapsed = 0
        else:
            task_description = task.enriched_description or task.raw_description
            done_definition = task.done_definition
            time_elapsed = int((datetime.utcnow() - task.started_at).total_seconds() / 60) if task.started_at else 0

        # Get project context
        project_context = await self.agent_manager.get_project_context()

        # Search for similar past issues if agent appears stuck
        similar_issues = []
        if self._appears_stuck(tmux_output):
            similar_issues = await self.rag_system.search_error_solutions(
                tmux_output[-500:],  # Last 500 chars
                limit=3,
            )

        return {
            "tmux_output": tmux_output,
            "task_description": task_description,
            "done_definition": done_definition,
            "time_elapsed": time_elapsed,
            "project_context": project_context,
            "similar_issues": similar_issues,
        }

    def _appears_stuck(self, output: str) -> bool:
        """Quick check if agent appears stuck.

        Args:
            output: Agent output

        Returns:
            True if appears stuck
        """
        stuck_indicators = [
            "error",
            "failed",
            "stuck",
            "waiting",
            "timeout",
            "rate limit",
        ]

        output_lower = output.lower()
        return any(indicator in output_lower for indicator in stuck_indicators)

    async def execute_intervention(
        self,
        agent: Agent,
        decision: Dict[str, Any],
    ):
        """Execute the monitoring decision.

        Args:
            agent: Agent to intervene on
            decision: Decision from analysis
        """
        action = decision.get("decision", MonitoringDecision.CONTINUE.value)
        message = decision.get("message", "")
        reasoning = decision.get("reasoning", "")

        logger.info(f"Executing intervention for agent {agent.id}: {action}")

        if action == MonitoringDecision.CONTINUE.value:
            # No action needed
            return

        elif action == MonitoringDecision.NUDGE.value:
            # Send helpful nudge message
            await self._nudge_agent(agent, message)
            await self._log_intervention(agent, "nudged", message)

        elif action == MonitoringDecision.ANSWER.value:
            # Answer agent's question with context
            enriched_answer = await self._enrich_answer(message, agent.current_task_id)
            await self._send_agent_message(agent, enriched_answer)
            await self._log_intervention(agent, "answered", enriched_answer)

        elif action == MonitoringDecision.RESTART.value:
            # Restart the agent
            await self.agent_manager.restart_agent(agent.id, reasoning)
            await self._log_intervention(agent, "restarted", reasoning)

        elif action == MonitoringDecision.RECREATE.value:
            # Create new agent with enhanced approach
            await self._recreate_agent_with_new_approach(agent, reasoning)
            await self._log_intervention(agent, "recreated", reasoning)

    async def _nudge_agent(self, agent: Agent, message: str):
        """Send a nudge message to the agent.

        Args:
            agent: Agent to nudge
            message: Nudge message
        """
        if not message:
            message = f"""
[HEPHAESTUS ASSISTANT]: Just checking in! You're working on task {agent.current_task_id}.
If you're stuck or need help, remember you can:
- Create sub-tasks using create_task
- Save discoveries using save_memory
- Update task status when done using update_task_status

Current time: {datetime.utcnow().isoformat()}
"""

        await self._send_agent_message(agent, message)

    async def _send_agent_message(self, agent: Agent, message: str):
        """Send a message to the agent.

        Args:
            agent: Agent to message
            message: Message to send
        """
        formatted_message = f"\n[HEPHAESTUS]: {message}\n"
        await self.agent_manager.send_message_to_agent(agent.id, formatted_message)

    async def _enrich_answer(self, answer: str, task_id: str) -> str:
        """Enrich an answer with additional context.

        Args:
            answer: Base answer
            task_id: Related task ID

        Returns:
            Enriched answer
        """
        # Search for relevant knowledge
        relevant_knowledge = await self.rag_system.retrieve_for_task(
            task_description=answer,
            requesting_agent_id="monitor",
            limit=5,
        )

        if relevant_knowledge:
            enriched = f"{answer}\n\nAdditional context from knowledge base:\n"
            for memory in relevant_knowledge[:3]:
                enriched += f"- {memory['content'][:200]}...\n"
            return enriched

        return answer

    async def _recreate_agent_with_new_approach(self, agent: Agent, reason: str):
        """Recreate agent with a new approach.

        Args:
            agent: Agent to recreate
            reason: Reason for recreation
        """
        logger.info(f"Recreating agent {agent.id} with new approach: {reason}")

        session = self.db_manager.get_session()
        try:
            # Get task
            task = session.query(Task).filter_by(id=agent.current_task_id).first()
            if not task:
                logger.error(f"Task {agent.current_task_id} not found")
                return

            # Terminate old agent
            await self.agent_manager.terminate_agent(agent.id)

            # Get failure context
            failure_context = f"""
Previous agent failed with: {reason}
Previous approach issues:
- {reason}

Please try a different approach, considering:
- Break down the task into smaller steps
- Use create_task for complex sub-tasks
- Save any discoveries or errors encountered
"""

            # Get enhanced memories including failure patterns
            memories = await self.rag_system.retrieve_for_task(
                task_description=f"{task.enriched_description} {failure_context}",
                requesting_agent_id="monitor",
                limit=15,
            )

            # Create new agent with enhanced context
            enriched_data = {
                "enriched_description": task.enriched_description,
                "completion_criteria": [task.done_definition],
                "agent_prompt": failure_context,
                "required_capabilities": ["recovery", "problem_solving"],
                "estimated_complexity": 8,  # Increase complexity
            }

            project_context = await self.agent_manager.get_project_context()
            new_agent = await self.agent_manager.create_agent_for_task(
                task=task,
                enriched_data=enriched_data,
                memories=memories,
                project_context=f"{project_context}\n\n{failure_context}",
            )

            logger.info(f"Created new agent {new_agent.id} to replace {agent.id}")

        except Exception as e:
            logger.error(f"Failed to recreate agent: {e}")
            session.rollback()
        finally:
            session.close()

    async def _log_intervention(self, agent: Agent, intervention_type: str, details: str):
        """Log an intervention.

        Args:
            agent: Agent involved
            intervention_type: Type of intervention
            details: Intervention details
        """
        session = self.db_manager.get_session()
        try:
            log_entry = AgentLog(
                agent_id=agent.id,
                log_type="intervention",
                message=f"Intervention: {intervention_type}",
                details={"type": intervention_type, "details": details[:500]},
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to log intervention: {e}")
            session.rollback()
        finally:
            session.close()


class MonitoringLoop:
    """Main monitoring loop for the system with trajectory monitoring."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        agent_manager: AgentManager,
        llm_provider: LLMProviderInterface,
        rag_system: RAGSystem,
        phase_manager: Optional[PhaseManager] = None,
    ):
        """Initialize monitoring loop with trajectory monitoring.

        Args:
            db_manager: Database manager
            agent_manager: Agent manager
            llm_provider: LLM provider
            rag_system: RAG system
            phase_manager: Optional phase manager for workflow monitoring
        """
        self.db_manager = db_manager
        self.agent_manager = agent_manager
        self.phase_manager = phase_manager
        self.llm_provider = llm_provider
        self.rag_system = rag_system

        # Initialize trajectory monitoring components
        self.guardian = Guardian(
            db_manager=db_manager,
            agent_manager=agent_manager,
            llm_provider=llm_provider,
        )
        self.conductor = Conductor(
            db_manager=db_manager,
            agent_manager=agent_manager,
        )
        self.trajectory_context = TrajectoryContext(db_manager=db_manager)

        # Keep old monitor for fallback
        self.intelligent_monitor = IntelligentMonitor(
            db_manager=db_manager,
            agent_manager=agent_manager,
            llm_provider=llm_provider,
            rag_system=rag_system,
        )

        self.config = get_config()
        self.running = False

        # Cache for Guardian summaries
        self.guardian_summaries_cache: Dict[str, Dict[str, Any]] = {}

    async def start(self):
        """Start the monitoring loop."""
        self.running = True
        logger.info("Starting monitoring loop")

        while self.running:
            try:
                await self._monitoring_cycle()
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")

            # Wait for next cycle
            await asyncio.sleep(self.config.monitoring_interval_seconds)

    async def stop(self):
        """Stop the monitoring loop."""
        logger.info("Stopping monitoring loop")
        self.running = False

    async def _monitoring_cycle(self):
        """Execute one monitoring cycle with trajectory monitoring."""
        logger.debug("Starting trajectory monitoring cycle")

        # DEBUG: Log phase_manager status
        logger.info(f"[DIAGNOSTIC CYCLE] phase_manager exists: {self.phase_manager is not None}")
        if self.phase_manager:
            logger.info(f"[DIAGNOSTIC CYCLE] phase_manager.workflow_id: {self.phase_manager.workflow_id[:8] if self.phase_manager.workflow_id else 'None'}")
        else:
            logger.info(f"[DIAGNOSTIC CYCLE] phase_manager is None")

        # Get all active agents
        agents = self.agent_manager.get_active_agents()
        logger.info(f"Trajectory monitoring {len(agents)} active agents")

        # Phase 1: Guardian Analysis (Parallel)
        guardian_summaries = []
        guardian_tasks = []

        for agent in agents:
            # Create async task for each Guardian analysis
            task = asyncio.create_task(
                self._guardian_analysis_for_agent(agent)
            )
            guardian_tasks.append(task)

        # Wait for all Guardian analyses to complete
        if guardian_tasks:
            guardian_results = await asyncio.gather(*guardian_tasks, return_exceptions=True)

            # Filter out exceptions and None results
            guardian_summaries = [
                result for result in guardian_results
                if result and not isinstance(result, Exception)
            ]

            # Log any exceptions
            for i, result in enumerate(guardian_results):
                if isinstance(result, Exception):
                    logger.error(f"Guardian analysis failed for agent {agents[i].id}: {result}")

        # Debug: Log what we collected
        logger.info(f"DEBUG - Collected {len(guardian_summaries)} Guardian summaries")
        for i, summary in enumerate(guardian_summaries):
            if summary:
                logger.info(f"DEBUG - Summary {i}: agent_id={summary.get('agent_id')}, "
                           f"has_trajectory_summary={bool(summary.get('trajectory_summary'))}")

        # Phase 2: Conductor Analysis (if we have summaries)
        if guardian_summaries:
            try:
                logger.info(f"DEBUG - Passing {len(guardian_summaries)} summaries to Conductor")
                conductor_analysis = await self.conductor.analyze_system_state(
                    guardian_summaries
                )

                # Log system status
                logger.info(f"System Status: {conductor_analysis['system_status']}")

                # Save Conductor analysis to dedicated table
                await self._save_conductor_analysis(conductor_analysis)

                # Execute conductor decisions
                if conductor_analysis.get('decisions'):
                    await self.conductor.execute_decisions(
                        conductor_analysis['decisions']
                    )

                # Generate and log detailed report if needed
                if conductor_analysis.get('coherence', {}).get('score', 1.0) < 0.5:
                    report = await self.conductor.generate_detailed_report(conductor_analysis)
                    logger.warning(f"Low system coherence detected:\n{report}")

            except Exception as e:
                logger.error(f"Conductor analysis failed: {e}")

        # Clean up orphaned tmux sessions
        try:
            await self._cleanup_orphaned_tmux_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up orphaned tmux sessions: {e}")

        # Check phase progression if workflow is active
        if self.phase_manager and self.phase_manager.workflow_id:
            try:
                await self._check_phase_progression()
            except Exception as e:
                logger.error(f"Error checking phase progression: {e}")

        # Check if workflow is stuck and needs diagnostic agent
        logger.info(f"[DIAGNOSTIC] Checking if diagnostic agent needed...")
        logger.info(f"[DIAGNOSTIC] phase_manager exists: {self.phase_manager is not None}")
        logger.info(f"[DIAGNOSTIC] workflow_id: {self.phase_manager.workflow_id[:8] if (self.phase_manager and self.phase_manager.workflow_id) else 'N/A'}")

        # DEBUG: Check database for active workflows
        session = self.db_manager.get_session()
        try:
            from src.core.database import Workflow
            active_workflows = session.query(Workflow).filter_by(status='active').all()
            logger.info(f"[DIAGNOSTIC] Active workflows in database: {len(active_workflows)}")
            for wf in active_workflows:
                task_count = session.query(Task).filter_by(workflow_id=wf.id).count()
                done_count = session.query(Task).filter_by(workflow_id=wf.id, status='done').count()
                failed_count = session.query(Task).filter_by(workflow_id=wf.id, status='failed').count()
                active_count = session.query(Task).filter(
                    Task.workflow_id == wf.id,
                    Task.status.in_(['pending', 'assigned', 'in_progress'])
                ).count()
                logger.info(f"[DIAGNOSTIC]   - {wf.name} (ID: {wf.id[:8]}..., {task_count} total: {done_count} done, {failed_count} failed, {active_count} active)")
        finally:
            session.close()

        if self.phase_manager and self.phase_manager.workflow_id:
            logger.info(f"[DIAGNOSTIC] ✅ Conditions met - running diagnostic check for workflow {self.phase_manager.workflow_id[:8]}")
            try:
                await self._check_workflow_stuck_state()
            except Exception as e:
                logger.error(f"[DIAGNOSTIC] Error checking workflow stuck state: {e}")
        else:
            if not self.phase_manager:
                logger.warning(f"[DIAGNOSTIC] ❌ SKIPPED - No phase_manager")
            elif not self.phase_manager.workflow_id:
                logger.warning(f"[DIAGNOSTIC] ❌ SKIPPED - phase_manager.workflow_id is None")
                logger.warning(f"[DIAGNOSTIC] 💡 This likely means there's an active workflow in the DB that wasn't loaded on startup")

    async def _guardian_analysis_for_agent(self, agent: Agent) -> Optional[Dict[str, Any]]:
        """Perform Guardian analysis for a single agent.

        Args:
            agent: Agent to analyze

        Returns:
            Guardian analysis result or None if failed
        """
        try:
            # Skip agents that are too young (grace period for spin-up)
            agent_age_seconds = (datetime.utcnow() - agent.created_at).total_seconds()
            if agent_age_seconds < self.config.guardian_min_agent_age_seconds:
                logger.debug(
                    f"Skipping Guardian analysis for agent {agent.id} "
                    f"(age: {agent_age_seconds:.0f}s, min: {self.config.guardian_min_agent_age_seconds}s)"
                )
                return None

            # Special handling for agents with missing tmux sessions
            if agent.tmux_session_name and not self.agent_manager.tmux_server.has_session(agent.tmux_session_name):
                logger.warning(f"Agent {agent.id} has missing tmux session {agent.tmux_session_name}, recreating")
                await self._handle_missing_tmux_session(agent)
                return None

            # Get agent output
            tmux_output = self.agent_manager.get_agent_output(
                agent.id,
                lines=self.config.tmux_output_lines,
            )

            if not tmux_output:
                logger.warning(f"No output from agent {agent.id}")
                return None

            # Get past summaries for this agent
            past_summaries = self._get_past_summaries_for_agent(agent.id)

            # Perform Guardian analysis with trajectory thinking
            analysis = await self.guardian.analyze_agent_with_trajectory(
                agent=agent,
                tmux_output=tmux_output,
                past_summaries=past_summaries,
            )

            # Cache the summary
            self.guardian_summaries_cache[agent.id] = {
                "summary": analysis,
                "timestamp": datetime.utcnow(),
            }

            # Execute steering if needed
            if analysis.get('needs_steering', False):
                await self.guardian.steer_agent(
                    agent=agent,
                    steering_type=analysis.get('steering_type', 'general'),
                    message=analysis.get('steering_message'),  # Guardian should map from steering_recommendation
                )

            # Update agent health based on trajectory alignment
            await self._update_agent_health_from_trajectory(agent, analysis)

            return analysis

        except Exception as e:
            logger.error(f"Guardian analysis failed for agent {agent.id}: {e}")
            return None

    def _get_past_summaries_for_agent(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get past Guardian summaries for an agent.

        Args:
            agent_id: Agent ID
            limit: Maximum number of summaries to return

        Returns:
            List of past summaries
        """
        session = self.db_manager.get_session()
        try:
            # Get past Guardian summaries from dedicated table
            analyses = session.query(GuardianAnalysis).filter(
                GuardianAnalysis.agent_id == agent_id
            ).order_by(GuardianAnalysis.timestamp.desc()).limit(limit).all()

            summaries = []
            for analysis in reversed(analyses):  # Reverse to get chronological order
                # Convert to dict format expected by Guardian
                summary = {
                    'current_phase': analysis.current_phase,
                    'trajectory_aligned': analysis.trajectory_aligned,
                    'alignment_score': analysis.alignment_score,
                    'needs_steering': analysis.needs_steering,
                    'steering_type': analysis.steering_type,
                    'trajectory_summary': analysis.trajectory_summary,
                    'accumulated_goal': analysis.accumulated_goal,
                    'timestamp': analysis.timestamp.isoformat() if analysis.timestamp else None
                }
                summaries.append(summary)

            # If new tables don't have data yet, fallback to old AgentLog method
            if not summaries:
                logs = session.query(AgentLog).filter(
                    AgentLog.agent_id == agent_id,
                    AgentLog.log_type.in_(['guardian_analysis', 'guardian_summary'])
                ).order_by(AgentLog.created_at.desc()).limit(limit).all()

                for log in reversed(logs):
                    if log.details:
                        summaries.append(log.details)

            return summaries

        finally:
            session.close()

    async def _update_agent_health_from_trajectory(self, agent: Agent, analysis: Dict[str, Any]):
        """Update agent health based on trajectory analysis.

        Args:
            agent: Agent to update
            analysis: Guardian analysis result
        """
        session = self.db_manager.get_session()
        try:
            db_agent = session.query(Agent).filter_by(id=agent.id).first()
            if not db_agent:
                return

            # Update health based on trajectory alignment
            if analysis.get('trajectory_aligned', True):
                # Agent is on track - reset failures
                db_agent.health_check_failures = 0
                db_agent.last_activity = datetime.utcnow()
            else:
                # Agent is off track - increment failures
                alignment_score = analysis.get('alignment_score', 0.5)
                if alignment_score < 0.3:
                    db_agent.health_check_failures = max(
                        db_agent.health_check_failures + 2,
                        self.config.max_health_check_failures
                    )
                elif alignment_score < 0.5:
                    db_agent.health_check_failures += 1

            # Save to dedicated Guardian analysis table
            guardian_analysis = GuardianAnalysis(
                agent_id=agent.id,
                current_phase=analysis.get('current_phase'),
                trajectory_aligned=analysis.get('trajectory_aligned', True),
                alignment_score=analysis.get('alignment_score', 1.0),
                needs_steering=analysis.get('needs_steering', False),
                steering_type=analysis.get('steering_type'),
                steering_recommendation=analysis.get('steering_recommendation'),
                trajectory_summary=analysis.get('trajectory_summary', 'No summary'),
                last_claude_message_marker=analysis.get('last_claude_message_marker'),  # NEW
                accumulated_goal=analysis.get('accumulated_goal'),
                current_focus=analysis.get('current_focus'),
                session_duration=analysis.get('session_duration'),
                conversation_length=analysis.get('conversation_length'),
                details=analysis
            )
            session.add(guardian_analysis)

            # Also keep a simplified log entry for backwards compatibility
            summary_log = AgentLog(
                agent_id=agent.id,
                log_type='guardian_analysis',
                message=f"Guardian: {analysis.get('current_phase', 'unknown')} phase, "
                       f"score={analysis.get('alignment_score', 0):.2f}, "
                       f"aligned={analysis.get('trajectory_aligned', False)}",
                details={'guardian_analysis_id': guardian_analysis.id}  # Reference to the full analysis
            )
            session.add(summary_log)
            session.commit()

        finally:
            session.close()

    async def _save_conductor_analysis(self, analysis: Dict[str, Any]):
        """Save Conductor analysis to dedicated table.

        Args:
            analysis: Conductor analysis result
        """
        session = self.db_manager.get_session()
        try:
            # Extract duplicate info
            duplicates = analysis.get('duplicates', [])
            coherence_info = analysis.get('coherence', {})
            decisions = analysis.get('decisions', [])

            # Count decision types
            termination_count = sum(1 for d in decisions if d.get('type') == 'terminate_duplicate')
            coordination_count = sum(1 for d in decisions if d.get('type') == 'coordinate_resources')

            # Save main Conductor analysis
            conductor_analysis = ConductorAnalysis(
                coherence_score=coherence_info.get('score', 0.7),
                num_agents=analysis.get('num_agents', 0),
                system_status=analysis.get('system_status', 'Unknown'),
                duplicate_count=len(duplicates),
                termination_count=termination_count,
                coordination_count=coordination_count,
                details=analysis
            )
            session.add(conductor_analysis)
            session.flush()  # Get the ID

            # Save detected duplicates
            for dup in duplicates:
                duplicate_entry = DetectedDuplicate(
                    conductor_analysis_id=conductor_analysis.id,
                    agent1_id=dup.get('agent1'),
                    agent2_id=dup.get('agent2'),
                    similarity_score=dup.get('similarity', 0.0),
                    work_description=dup.get('work', 'Unknown duplicate work')
                )
                session.add(duplicate_entry)

            # Also keep a log entry for backwards compatibility
            log_entry = AgentLog(
                agent_id=None,  # System-level log
                log_type='conductor_analysis',
                message=f"Conductor: coherence={coherence_info.get('score', 0):.2f}, "
                       f"{len(duplicates)} duplicates, {analysis.get('system_status', 'Unknown')[:50]}",
                details={'conductor_analysis_id': conductor_analysis.id}
            )
            session.add(log_entry)

            session.commit()
            logger.debug(f"Saved Conductor analysis ID {conductor_analysis.id}")

        except Exception as e:
            logger.error(f"Failed to save Conductor analysis: {e}")
            session.rollback()
        finally:
            session.close()

    async def _check_agent(self, agent: Agent):
        """Check a single agent's health (fallback method).

        Args:
            agent: Agent to check
        """
        # This is now a fallback method - Guardian analysis handles most of this
        # Only used if Guardian analysis is disabled or fails

        # Check task timeout
        if self._is_task_timed_out(agent):
            logger.warning(f"Agent {agent.id} task timed out")
            await self._handle_timeout(agent)

    def _is_agent_responsive(self, agent: Agent) -> bool:
        """Check if agent is responsive.

        Args:
            agent: Agent to check

        Returns:
            True if responsive
        """
        # Check if tmux session exists first
        if agent.tmux_session_name:
            if not self.agent_manager.tmux_server.has_session(agent.tmux_session_name):
                logger.warning(f"Agent {agent.id} tmux session {agent.tmux_session_name} missing")
                return False

        # Check last activity time
        if agent.last_activity:
            time_since_activity = datetime.utcnow() - agent.last_activity
            max_idle = timedelta(minutes=self.config.stuck_detection_minutes)

            if time_since_activity > max_idle:
                return False

        # Check tmux output for activity
        output = self.agent_manager.get_agent_output(agent.id, lines=50)
        if not output:
            return False

        # Check for stuck patterns
        cli_agent = get_cli_agent(agent.cli_type)
        if cli_agent.is_stuck(output):
            return False

        return True

    def _is_task_timed_out(self, agent: Agent) -> bool:
        """Check if agent's task has timed out.

        Args:
            agent: Agent to check

        Returns:
            True if timed out
        """
        session = self.db_manager.get_session()
        task = session.query(Task).filter_by(id=agent.current_task_id).first()
        session.close()

        if not task or not task.started_at:
            return False

        # Calculate timeout based on complexity
        complexity = task.estimated_complexity or 5
        timeout_minutes = self.config.agent_timeout_minutes * (1 + complexity / 10)

        time_on_task = datetime.utcnow() - task.started_at
        return time_on_task > timedelta(minutes=timeout_minutes)

    async def _handle_stuck_agent(self, agent: Agent):
        """Handle a stuck agent with trajectory-based intervention.

        Args:
            agent: Stuck agent
        """
        logger.info(f"Handling stuck agent {agent.id} with trajectory analysis")

        # Build accumulated context for better understanding
        accumulated_context = self.trajectory_context.build_accumulated_context(
            agent_id=agent.id,
            include_full_history=True,
        )

        # Check for specific issues in trajectory
        blockers = accumulated_context.get('discovered_blockers', [])
        if blockers:
            logger.info(f"Agent {agent.id} has blockers: {blockers}")

            # Try to provide targeted help for blockers
            for blocker in blockers[:3]:  # Address top 3 blockers
                message = f"I see you're blocked on: {blocker}. Try a different approach or create a sub-task if it's complex."
                await self.guardian.steer_agent(
                    agent=agent,
                    steering_type='stuck',
                    message=message,
                )

        # If no specific blockers, use general intervention
        else:
            # Fallback to old intelligent monitor
            analysis = await self.intelligent_monitor.analyze_agent_state(agent)
            await self.intelligent_monitor.execute_intervention(agent, analysis)

    async def _handle_missing_tmux_session(self, agent: Agent):
        """Handle an agent with a missing tmux session by restarting it.

        Args:
            agent: Agent with missing tmux session
        """
        logger.info(f"Handling missing tmux session for agent {agent.id}")

        # Use the restart agent functionality which will recreate the tmux session
        await self.agent_manager.restart_agent(
            agent.id,
            f"Tmux session {agent.tmux_session_name} was missing, recreating"
        )

    async def _check_phase_progression(self):
        """Check workflow phases for progression needs."""
        logger.debug("Checking phase progression")

        # Get current phase status
        workflow_status = self.phase_manager.get_workflow_status()
        if not workflow_status or "error" in workflow_status:
            return

        phases = workflow_status.get("phases", [])

        for phase_info in phases:
            if phase_info["status"] == "in_progress":
                # Get detailed phase from database
                session = self.db_manager.get_session()
                try:
                    from src.core.database import Phase
                    phase = session.query(Phase).filter_by(
                        workflow_id=self.phase_manager.workflow_id,
                        order=phase_info["order"]
                    ).first()

                    if not phase:
                        continue

                    # Check if phase is complete
                    if self.phase_manager.check_phase_completion(phase.id):
                        logger.info(f"Phase {phase.name} appears complete, checking for next phase tasks")

                        # Check if we should create next phase task
                        if self.phase_manager.should_create_next_phase_task(phase.id):
                            await self._create_next_phase_task(phase)

                        # Mark phase as complete
                        self.phase_manager.mark_phase_complete(
                            phase.id,
                            f"Phase completed with {phase_info['tasks']['completed']} tasks"
                        )

                finally:
                    session.close()

    async def _create_next_phase_task(self, current_phase):
        """Create initial task for next phase.

        Args:
            current_phase: The current completed phase
        """
        session = self.db_manager.get_session()
        try:
            from src.core.database import Phase
            import uuid

            # Find next phase
            next_phase = session.query(Phase).filter(
                Phase.workflow_id == current_phase.workflow_id,
                Phase.order > current_phase.order
            ).order_by(Phase.order).first()

            if not next_phase:
                logger.info("No next phase found, workflow may be complete")
                return

            # Create task for next phase based on its instructions
            task_description = f"Execute {next_phase.name}: {next_phase.description}"
            done_definition = " AND ".join(next_phase.done_definitions) if next_phase.done_definitions else "Complete phase objectives"

            # Create task
            task = Task(
                id=str(uuid.uuid4()),
                raw_description=task_description,
                enriched_description=task_description,
                done_definition=done_definition,
                status="pending",
                priority="high",
                phase_id=next_phase.id,
                workflow_id=next_phase.workflow_id,
                created_by_agent_id="monitor",  # Created by monitor
            )

            session.add(task)
            session.commit()

            logger.info(f"Created initial task for next phase: {next_phase.name}")

            # Log the action
            log_entry = AgentLog(
                agent_id="monitor",
                log_type="intervention",
                message=f"Auto-created task for phase {next_phase.name} after {current_phase.name} completion",
                details={"task_id": task.id, "phase_id": next_phase.id}
            )
            session.add(log_entry)
            session.commit()

        except Exception as e:
            logger.error(f"Failed to create next phase task: {e}")
            session.rollback()
        finally:
            session.close()

    async def _handle_timeout(self, agent: Agent):
        """Handle a timed-out agent.

        Args:
            agent: Timed-out agent
        """
        logger.warning(f"Handling timeout for agent {agent.id}")

        # Force analysis with timeout context
        analysis = {
            "state": AgentState.UNRECOVERABLE.value,
            "decision": MonitoringDecision.RECREATE.value,
            "message": "",
            "reasoning": "Task timed out, creating new agent with fresh approach",
            "confidence": 0.9,
        }

        await self.intelligent_monitor.execute_intervention(agent, analysis)

    async def _cleanup_orphaned_tmux_sessions(self):
        """Clean up tmux sessions that don't have corresponding active agents."""
        logger.debug("Starting orphaned tmux session cleanup")

        try:
            # Get all tmux sessions that start with 'agent' (the new naming convention)
            agent_sessions = []
            for session in self.agent_manager.tmux_server.sessions:
                if session.name.startswith('agent'):
                    agent_sessions.append(session.name)

            if not agent_sessions:
                logger.debug("No agent tmux sessions found")
                return

            logger.debug(f"Found {len(agent_sessions)} agent tmux sessions: {agent_sessions}")

            # Get all active agent session names from database
            session = self.db_manager.get_session()
            try:
                active_agents = session.query(Agent).filter(
                    Agent.status.in_(['working', 'pending', 'assigned'])
                ).all()

                active_session_names = {
                    agent.tmux_session_name for agent in active_agents
                    if agent.tmux_session_name
                }

                logger.debug(f"Found {len(active_session_names)} active agent sessions: {active_session_names}")

            finally:
                session.close()

            # Find orphaned sessions (exist in tmux but not in database)
            orphaned_sessions = []
            for session_name in agent_sessions:
                if session_name not in active_session_names:
                    orphaned_sessions.append(session_name)

            if not orphaned_sessions:
                logger.debug("No orphaned tmux sessions found")
                return

            logger.info(f"Found {len(orphaned_sessions)} orphaned tmux sessions: {orphaned_sessions}")

            # Kill orphaned sessions
            killed_count = 0
            for session_name in orphaned_sessions:
                try:
                    # Find and kill the session
                    for tmux_sess in self.agent_manager.tmux_server.sessions:
                        if tmux_sess.name == session_name:
                            tmux_sess.kill_session()
                            logger.info(f"Killed orphaned tmux session: {session_name}")
                            killed_count += 1
                            break
                except Exception as e:
                    logger.warning(f"Failed to kill orphaned session {session_name}: {e}")

            if killed_count > 0:
                logger.info(f"Successfully cleaned up {killed_count} orphaned tmux sessions")

        except Exception as e:
            logger.error(f"Error during tmux session cleanup: {e}")
            raise

    async def _check_workflow_stuck_state(self):
        """Check if workflow is stuck and needs diagnostic agent.

        Triggers diagnostic agent if:
        1. Active workflow exists
        2. Task count > 0
        3. All tasks are finished (done/failed/duplicated)
        4. No validated result submitted
        5. Cooldown period has passed since last diagnostic run
        """
        logger.warning("[DIAGNOSTIC MONITOR] ============================================")
        logger.warning("[DIAGNOSTIC MONITOR] 🔍 _check_workflow_stuck_state() CALLED!")
        logger.warning("[DIAGNOSTIC MONITOR] ============================================")
        logger.info("[DIAGNOSTIC MONITOR] Starting workflow stuck state check...")

        # Condition tracking for debug report
        conditions = {
            "enabled": self.config.diagnostic_agent_enabled,
            "workflow_exists": False,
            "has_tasks": False,
            "all_tasks_finished": False,
            "no_validated_result": False,
            "cooldown_passed": False,
            "stuck_long_enough": False,
        }

        if not self.config.diagnostic_agent_enabled:
            logger.info("[DIAGNOSTIC MONITOR] ❌ Diagnostic agent disabled in config")
            self._log_diagnostic_status_report(conditions, trigger=False, reason="Disabled in config")
            return

        if not self.phase_manager or not self.phase_manager.workflow_id:
            logger.info("[DIAGNOSTIC MONITOR] ❌ No active workflow")
            self._log_diagnostic_status_report(conditions, trigger=False, reason="No active workflow")
            return

        conditions["workflow_exists"] = True
        workflow_id = self.phase_manager.workflow_id
        logger.info(f"[DIAGNOSTIC MONITOR] ✅ Workflow exists: {workflow_id[:8]}")

        session = self.db_manager.get_session()
        try:
            # Step 1: Check if we have tasks
            from src.core.database import Task, WorkflowResult, DiagnosticRun

            tasks = session.query(Task).filter(
                Task.workflow_id == workflow_id
            ).all()

            if not tasks:
                logger.info("[DIAGNOSTIC MONITOR] ❌ No tasks in workflow yet")
                self._log_diagnostic_status_report(conditions, trigger=False, reason="No tasks in workflow")
                return

            conditions["has_tasks"] = True
            logger.info(f"[DIAGNOSTIC MONITOR] ✅ Has tasks: {len(tasks)} total")

            # Step 2: Check if all tasks are finished
            active_statuses = ['pending', 'assigned', 'in_progress',
                              'under_review', 'validation_in_progress']
            active_tasks = [t for t in tasks if t.status in active_statuses]
            finished_tasks = [t for t in tasks if t.status not in active_statuses]

            if active_tasks:
                logger.info(f"[DIAGNOSTIC MONITOR] ❌ Tasks still active: {len(active_tasks)} active, {len(finished_tasks)} finished")
                self._log_diagnostic_status_report(conditions, trigger=False,
                                                   reason=f"{len(active_tasks)} active tasks remaining")
                return

            conditions["all_tasks_finished"] = True
            logger.info(f"[DIAGNOSTIC MONITOR] ✅ All tasks finished: {len(finished_tasks)} tasks")

            # Step 3: Check if we have a validated result
            validated_result = session.query(WorkflowResult).filter(
                WorkflowResult.workflow_id == workflow_id,
                WorkflowResult.status == 'validated'
            ).first()

            if validated_result:
                logger.info(f"[DIAGNOSTIC MONITOR] ❌ Workflow has validated result: {validated_result.id[:8]}")
                self._log_diagnostic_status_report(conditions, trigger=False, reason="Validated result exists")
                return

            conditions["no_validated_result"] = True

            # Check for any results (validated or not)
            all_results = session.query(WorkflowResult).filter(
                WorkflowResult.workflow_id == workflow_id
            ).all()
            if all_results:
                logger.info(f"[DIAGNOSTIC MONITOR] ✅ No validated result ({len(all_results)} unvalidated results exist)")
            else:
                logger.info("[DIAGNOSTIC MONITOR] ✅ No validated result (no results submitted)")

            # Step 4: Check cooldown period
            last_diagnostic = session.query(DiagnosticRun).filter(
                DiagnosticRun.workflow_id == workflow_id
            ).order_by(DiagnosticRun.triggered_at.desc()).first()

            if last_diagnostic:
                time_since_last = (datetime.utcnow() - last_diagnostic.triggered_at).total_seconds()
                if time_since_last < self.config.diagnostic_cooldown_seconds:
                    logger.info(f"[DIAGNOSTIC MONITOR] ❌ Cooldown active: {time_since_last:.0f}s / {self.config.diagnostic_cooldown_seconds}s required")
                    self._log_diagnostic_status_report(conditions, trigger=False,
                                                       reason=f"Cooldown active ({time_since_last:.0f}s < {self.config.diagnostic_cooldown_seconds}s)")
                    return
                else:
                    logger.info(f"[DIAGNOSTIC MONITOR] ✅ Cooldown passed: {time_since_last:.0f}s since last diagnostic")
            else:
                logger.info("[DIAGNOSTIC MONITOR] ✅ Cooldown passed: No previous diagnostic runs")

            conditions["cooldown_passed"] = True

            # Step 5: Check how long we've been stuck
            latest_task_time = max(
                (t.completed_at or t.created_at for t in tasks if t.completed_at or t.created_at),
                default=None
            )

            stuck_time = 0
            if latest_task_time:
                stuck_time = (datetime.utcnow() - latest_task_time).total_seconds()
                if stuck_time < self.config.diagnostic_min_stuck_time_seconds:
                    logger.info(f"[DIAGNOSTIC MONITOR] ❌ Not stuck long enough: {stuck_time:.0f}s / {self.config.diagnostic_min_stuck_time_seconds}s required")
                    self._log_diagnostic_status_report(conditions, trigger=False,
                                                       reason=f"Not stuck long enough ({stuck_time:.0f}s < {self.config.diagnostic_min_stuck_time_seconds}s)")
                    return
                else:
                    logger.info(f"[DIAGNOSTIC MONITOR] ✅ Stuck long enough: {stuck_time:.0f}s since last activity")
            else:
                logger.warning("[DIAGNOSTIC MONITOR] ⚠️  Could not determine stuck time (no task timestamps)")

            conditions["stuck_long_enough"] = True

            # ALL CONDITIONS MET - Trigger diagnostic agent
            logger.warning(f"[DIAGNOSTIC MONITOR] 🚨 WORKFLOW STUCK DETECTED - All conditions met!")
            logger.warning(f"[DIAGNOSTIC MONITOR] 🔥 Stuck for {stuck_time:.0f}s with no progress")
            self._log_diagnostic_status_report(conditions, trigger=True, stuck_time=stuck_time)

            await self._create_diagnostic_agent(workflow_id, tasks, stuck_time)

        except Exception as e:
            logger.error(f"[DIAGNOSTIC MONITOR] ❌ Error checking workflow stuck state: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()

    def _log_diagnostic_status_report(self, conditions: Dict[str, bool], trigger: bool, reason: str = None, stuck_time: float = 0):
        """Log a status report of all diagnostic conditions.

        Args:
            conditions: Dictionary of condition name -> boolean
            trigger: Whether diagnostic agent was triggered
            reason: Reason for not triggering (if trigger=False)
            stuck_time: How long stuck (if trigger=True)
        """
        logger.info("[DIAGNOSTIC MONITOR] ═══════════════════════════════════════")
        logger.info("[DIAGNOSTIC MONITOR] DIAGNOSTIC STATUS REPORT")
        logger.info("[DIAGNOSTIC MONITOR] ───────────────────────────────────────")

        # Show all conditions
        logger.info(f"[DIAGNOSTIC MONITOR] Enabled:              {'✅' if conditions['enabled'] else '❌'}")
        logger.info(f"[DIAGNOSTIC MONITOR] Workflow Exists:      {'✅' if conditions['workflow_exists'] else '❌'}")
        logger.info(f"[DIAGNOSTIC MONITOR] Has Tasks:            {'✅' if conditions['has_tasks'] else '❌'}")
        logger.info(f"[DIAGNOSTIC MONITOR] All Tasks Finished:   {'✅' if conditions['all_tasks_finished'] else '❌'}")
        logger.info(f"[DIAGNOSTIC MONITOR] No Validated Result:  {'✅' if conditions['no_validated_result'] else '❌'}")
        logger.info(f"[DIAGNOSTIC MONITOR] Cooldown Passed:      {'✅' if conditions['cooldown_passed'] else '❌'}")
        logger.info(f"[DIAGNOSTIC MONITOR] Stuck Long Enough:    {'✅' if conditions['stuck_long_enough'] else '❌'}")

        logger.info("[DIAGNOSTIC MONITOR] ───────────────────────────────────────")

        if trigger:
            logger.warning(f"[DIAGNOSTIC MONITOR] 🚨 RESULT: TRIGGERING DIAGNOSTIC AGENT")
            logger.warning(f"[DIAGNOSTIC MONITOR] 🔥 Stuck Time: {stuck_time:.0f}s")
        else:
            logger.info(f"[DIAGNOSTIC MONITOR] ✋ RESULT: NOT TRIGGERING")
            if reason:
                logger.info(f"[DIAGNOSTIC MONITOR] 📋 Reason: {reason}")

        logger.info("[DIAGNOSTIC MONITOR] ═══════════════════════════════════════")

    async def _create_diagnostic_agent(self, workflow_id: str, workflow_tasks: List, stuck_time: float):
        """Create and spawn a diagnostic agent.

        Args:
            workflow_id: ID of stuck workflow
            workflow_tasks: All tasks in the workflow
            stuck_time: How long we've been stuck (seconds)
        """
        import uuid
        from src.core.database import Task, DiagnosticRun

        logger.info(f"[DIAGNOSTIC MONITOR] 🔍 Creating diagnostic agent for workflow {workflow_id[:8]}")

        session = self.db_manager.get_session()
        try:
            # Gather context for diagnostic agent
            logger.info("[DIAGNOSTIC MONITOR] Gathering diagnostic context...")
            context = await self._gather_diagnostic_context(workflow_id, workflow_tasks, stuck_time)
            logger.info(f"[DIAGNOSTIC MONITOR] Context gathered: {len(context['phases_summary'])} phases, {len(context['agents_summary'])} agents reviewed")

            # Create diagnostic task
            task_id = str(uuid.uuid4())
            diagnostic_task = Task(
                id=task_id,
                raw_description="DIAGNOSTIC: Analyze why workflow has stalled and create tasks to progress toward goal",
                enriched_description=f"Diagnostic analysis for workflow {workflow_id[:8]} - {len(workflow_tasks)} tasks completed, stuck for {stuck_time:.0f}s",
                done_definition="Created 1-5 new tasks with clear phase assignments and completion criteria to push workflow toward its goal",
                status="pending",
                priority="high",
                workflow_id=workflow_id,
                created_by_agent_id="monitor",
                phase_id=None,  # Diagnostic tasks are phase-agnostic
            )
            session.add(diagnostic_task)
            session.flush()
            logger.info(f"[DIAGNOSTIC MONITOR] Created diagnostic task: {task_id[:8]}")

            # Create diagnostic run record
            run_id = str(uuid.uuid4())
            diagnostic_run = DiagnosticRun(
                id=run_id,
                workflow_id=workflow_id,
                diagnostic_task_id=task_id,
                total_tasks_at_trigger=len(workflow_tasks),
                done_tasks_at_trigger=len([t for t in workflow_tasks if t.status == 'done']),
                failed_tasks_at_trigger=len([t for t in workflow_tasks if t.status == 'failed']),
                time_since_last_task_seconds=int(stuck_time),
                workflow_goal=context['workflow_goal'],
                phases_analyzed=context['phases_summary'],
                agents_reviewed=context['agents_summary'],
                status="created",
            )
            session.add(diagnostic_run)
            session.commit()
            logger.info(f"[DIAGNOSTIC MONITOR] Created diagnostic run: {run_id[:8]}")

            # Generate diagnostic prompt
            logger.info("[DIAGNOSTIC MONITOR] Generating diagnostic prompt...")
            diagnostic_prompt = await self._generate_diagnostic_prompt(context)
            prompt_size = len(diagnostic_prompt)
            logger.info(f"[DIAGNOSTIC MONITOR] Prompt generated: {prompt_size} characters")

            # Spawn diagnostic agent (no worktree, works in main repo)
            enriched_data = {
                'enriched_description': diagnostic_task.enriched_description,
                'completion_criteria': [diagnostic_task.done_definition],
                'diagnostic_context': context,
                'validation_prompt': diagnostic_prompt,  # Use validation_prompt field for custom prompt
            }

            logger.info("[DIAGNOSTIC MONITOR] Spawning diagnostic agent...")
            agent = await self.agent_manager.create_agent_for_task(
                task=diagnostic_task,
                enriched_data=enriched_data,
                memories=[],  # Diagnostic agent gets everything in prompt
                project_context="",
                agent_type="diagnostic",
                use_existing_worktree=True,
                working_directory=str(self.config.main_repo_path),  # Use main repo
            )

            # Update diagnostic run with agent ID
            diagnostic_run.diagnostic_agent_id = agent.id
            diagnostic_run.status = "running"
            session.commit()

            logger.info(f"[DIAGNOSTIC MONITOR] ✅ Diagnostic agent created successfully!")
            logger.info(f"[DIAGNOSTIC MONITOR] Agent ID: {agent.id[:8]}")
            logger.info(f"[DIAGNOSTIC MONITOR] Task ID: {task_id[:8]}")
            logger.info(f"[DIAGNOSTIC MONITOR] Run ID: {run_id[:8]}")
            logger.info(f"[DIAGNOSTIC MONITOR] Workflow: {workflow_id[:8]}")

        except Exception as e:
            logger.error(f"[DIAGNOSTIC MONITOR] ❌ Failed to create diagnostic agent: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

    async def _gather_diagnostic_context(self, workflow_id: str, workflow_tasks: List, stuck_time: float) -> Dict[str, Any]:
        """Gather all context needed for diagnostic agent.

        Returns:
            Dictionary with:
            - workflow_goal
            - phases_summary
            - recent_agents_history
            - conductor_overviews
            - workflow_status
            - submitted_results
        """
        from src.core.database import Agent, GuardianAnalysis, ConductorAnalysis, WorkflowResult, Phase

        session = self.db_manager.get_session()
        try:
            # Get workflow config
            workflow_config = self.phase_manager.get_workflow_config(workflow_id)
            workflow_goal = workflow_config.result_criteria if workflow_config else "Unknown goal"

            # Get all phases
            phases = session.query(Phase).filter(
                Phase.workflow_id == workflow_id
            ).order_by(Phase.order).all()

            phases_summary = []
            for phase in phases:
                phases_summary.append({
                    'id': phase.id,
                    'name': phase.name,
                    'order': phase.order,
                    'description': phase.description,
                    'done_definitions': phase.done_definitions,
                    'task_count': len([t for t in workflow_tasks if t.phase_id == phase.id]),
                    'done_task_count': len([t for t in workflow_tasks if t.phase_id == phase.id and t.status == 'done']),
                })

            # Get recent agents (last N completed/failed)
            task_ids = [t.id for t in workflow_tasks]
            recent_agents = session.query(Agent).filter(
                Agent.current_task_id.in_(task_ids),
                Agent.status.in_(['terminated'])
            ).order_by(Agent.created_at.desc()).limit(self.config.diagnostic_max_agents_to_analyze).all()

            agents_summary = []
            for agent in recent_agents:
                task = session.query(Task).filter_by(id=agent.current_task_id).first()
                if task:
                    agents_summary.append({
                        'agent_id': agent.id,
                        'task_id': task.id,
                        'task_description': task.enriched_description or task.raw_description,
                        'task_status': task.status,
                        'completion_notes': task.completion_notes,
                        'failure_reason': task.failure_reason,
                        'phase_id': task.phase_id,
                        'created_at': agent.created_at.isoformat(),
                        'agent_type': agent.agent_type,
                    })

            # Get recent Conductor analyses
            conductor_analyses = session.query(ConductorAnalysis).order_by(
                ConductorAnalysis.timestamp.desc()
            ).limit(self.config.diagnostic_max_conductor_analyses).all()

            conductor_overviews = []
            for analysis in conductor_analyses:
                conductor_overviews.append({
                    'timestamp': analysis.timestamp.isoformat(),
                    'system_status': analysis.system_status,
                    'coherence_score': analysis.coherence_score,
                    'num_agents': analysis.num_agents,
                    'duplicate_count': analysis.duplicate_count,
                })

            # Get submitted results (even if rejected)
            submitted_results = session.query(WorkflowResult).filter(
                WorkflowResult.workflow_id == workflow_id
            ).all()

            results_summary = []
            for result in submitted_results:
                results_summary.append({
                    'result_id': result.id,
                    'status': result.status,
                    'submitted_at': result.created_at.isoformat() if result.created_at else None,
                    'validation_feedback': result.validation_feedback,
                    'agent_id': result.agent_id,
                })

            # Calculate task statistics by phase
            tasks_by_phase = {}
            for phase in phases:
                phase_tasks = [t for t in workflow_tasks if t.phase_id == phase.id]
                tasks_by_phase[phase.name] = {
                    'total': len(phase_tasks),
                    'done': len([t for t in phase_tasks if t.status == 'done']),
                    'failed': len([t for t in phase_tasks if t.status == 'failed']),
                }

            return {
                'workflow_goal': workflow_goal,
                'workflow_id': workflow_id,
                'phases_summary': phases_summary,
                'agents_summary': agents_summary,
                'conductor_overviews': conductor_overviews,
                'submitted_results': results_summary,
                'total_tasks': len(workflow_tasks),
                'tasks_by_phase': tasks_by_phase,
                'time_since_last_task': stuck_time,
            }

        finally:
            session.close()

    async def _generate_diagnostic_prompt(self, context: Dict[str, Any]) -> str:
        """Generate diagnostic prompt from template.

        Args:
            context: Diagnostic context dictionary

        Returns:
            Formatted diagnostic prompt
        """
        from pathlib import Path

        # Load template
        template_path = Path(__file__).parent.parent / "prompts" / "diagnostic_agent_analysis.md"
        with open(template_path, 'r') as f:
            template = f.read()

        # Format phases info
        phases_info = []
        for phase in context['phases_summary']:
            phases_info.append(f"""
### Phase {phase['order']}: {phase['name']} (ID: {phase['id'][:8]})

**Description**: {phase['description']}

**Done Definitions**:
{chr(10).join(f"- {d}" for d in phase['done_definitions'])}

**Progress**: {phase['done_task_count']}/{phase['task_count']} tasks completed
""")

        # Format agent history
        agents_history = []
        for i, agent in enumerate(context['agents_summary'], 1):
            status_marker = "✅" if agent['task_status'] == 'done' else "❌"
            agents_history.append(f"""
**Agent {i}** (ID: {agent['agent_id'][:8]}, Type: {agent['agent_type']})
- **Task**: {agent['task_description']}
- **Status**: {status_marker} {agent['task_status']}
- **Phase**: {agent['phase_id'][:8] if agent['phase_id'] else 'None'}
- **Completed at**: {agent['created_at']}
{f"- **Notes**: {agent['completion_notes']}" if agent['completion_notes'] else ""}
{f"- **Failure reason**: {agent['failure_reason']}" if agent['failure_reason'] else ""}
""")

        # Format conductor overviews
        conductor_overviews = []
        for i, overview in enumerate(context['conductor_overviews'], 1):
            conductor_overviews.append(f"""
**Analysis {i}** ({overview['timestamp']}):
- System status: {overview['system_status']}
- Coherence score: {overview['coherence_score']:.2f}
- Active agents: {overview['num_agents']}
- Duplicates detected: {overview['duplicate_count']}
""")

        # Format tasks by phase
        tasks_by_phase_str = []
        for phase_name, stats in context['tasks_by_phase'].items():
            tasks_by_phase_str.append(
                f"  - {phase_name}: {stats['done']}/{stats['total']} done, {stats['failed']} failed"
            )

        # Format submitted results
        if context['submitted_results']:
            results_info = []
            for result in context['submitted_results']:
                status_marker = "✅" if result['status'] == 'validated' else "❌"
                results_info.append(f"""
- {status_marker} Result {result['result_id'][:8]}: {result['status']}
  - Submitted: {result['submitted_at']}
  - Feedback: {result['validation_feedback'] or 'None'}
""")
            submitted_results_info = '\n'.join(results_info)
        else:
            submitted_results_info = "No results have been submitted yet."

        # Calculate stuck time formatting
        stuck_seconds = context.get('time_since_last_task', 0)
        if stuck_seconds >= 3600:
            stuck_time_formatted = f"{stuck_seconds/3600:.1f} hours"
        elif stuck_seconds >= 60:
            stuck_time_formatted = f"{stuck_seconds/60:.1f} minutes"
        else:
            stuck_time_formatted = f"{stuck_seconds} seconds"

        # Replace placeholders
        prompt = template.format(
            workflow_goal=context['workflow_goal'],
            workflow_id=context['workflow_id'],
            phases_info='\n'.join(phases_info),
            agent_count=len(context['agents_summary']),
            agents_history='\n'.join(agents_history) if agents_history else "No agents have run yet.",
            conductor_overviews='\n'.join(conductor_overviews) if conductor_overviews else "No conductor analyses available.",
            total_tasks=context['total_tasks'],
            tasks_by_phase='\n'.join(tasks_by_phase_str),
            stuck_time_formatted=stuck_time_formatted,
            submitted_results_info=submitted_results_info,
            agent_id="{agent_id}",  # Will be replaced by agent manager
            task_id="{task_id}",  # Will be replaced by agent manager
        )

        return prompt