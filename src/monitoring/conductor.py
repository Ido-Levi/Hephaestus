"""System Conductor for orchestrating multiple agents toward collective goals."""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from src.core.database import DatabaseManager, Agent, Task, AgentLog
from src.agents.manager import AgentManager

logger = logging.getLogger(__name__)


class SystemDecision(Enum):
    """System-level decisions the conductor can make."""
    CONTINUE = "continue"
    TERMINATE_DUPLICATE = "terminate_duplicate"
    COORDINATE_RESOURCES = "coordinate_resources"
    CREATE_MISSING_TASK = "create_missing_task"
    ESCALATE = "escalate"


class Conductor:
    """
    System Conductor that orchestrates all agents toward collective goals.

    This uses the LLM to:
    - Analyze all Guardian summaries collectively
    - Detect duplicate work across agents
    - Ensure system coherence
    - Make termination decisions
    - Provide system-wide status
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        agent_manager: AgentManager,
    ):
        """Initialize System Conductor.

        Args:
            db_manager: Database manager
            agent_manager: Agent manager for operations
        """
        self.db_manager = db_manager
        self.agent_manager = agent_manager

        # Track system state
        self.system_state = {
            "last_analysis": None,
            "duplicate_pairs": [],
            "coherence_score": 0.7,
        }

    async def analyze_system_state(
        self,
        guardian_summaries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Use LLM Conductor session to analyze collective system state.

        This calls the LLM to:
        - Detect duplicate work across agents
        - Check if agents collectively move toward goals
        - Identify resource conflicts
        - Assess overall system coherence
        - Make termination/coordination decisions

        Args:
            guardian_summaries: List of Guardian LLM analysis results

        Returns:
            LLM system-wide analysis and decisions
        """
        # Get the actual model name being used
        model_name = "Unknown"
        llm_provider = None

        try:
            from src.interfaces import get_llm_provider
            llm_provider = get_llm_provider()
            if hasattr(llm_provider, 'get_model_for_component'):
                model_name = llm_provider.get_model_for_component('conductor_analysis')
        except:
            pass

        logger.info(f"Conductor analyzing system with {len(guardian_summaries)} agents using {model_name}")

        if not guardian_summaries:
            return self._get_empty_analysis()

        try:
            # Get LLM provider for analysis
            if not llm_provider:
                from src.interfaces import get_llm_provider
                llm_provider = get_llm_provider()
                if hasattr(llm_provider, 'get_model_for_component'):
                    model_name = llm_provider.get_model_for_component('conductor_analysis')

            # Prepare system goals
            system_goals = {
                "primary": "Complete all assigned tasks efficiently",
                "constraints": "No duplicate work, efficient resource usage",
                "coordination": "All agents working toward collective objectives",
            }

            # Call LLM to analyze system coherence
            # This is the CORE - the LLM does the system analysis, not static checks

            # Log what we're sending to the LLM
            logger.info("=" * 60)
            logger.info(f"🎼 CONDUCTOR {model_name.upper()} PROMPT")
            logger.info("=" * 60)
            logger.info(f"System Goals: {system_goals}")
            logger.info(f"Guardian Summaries Count: {len(guardian_summaries)}")

            # Debug: log the raw guardian summaries
            logger.info("DEBUG - Raw guardian_summaries:")
            for i, summary in enumerate(guardian_summaries):
                logger.info(f"  Summary {i}: {json.dumps(summary, default=str)[:500]}")

            validation_count = 0
            for i, summary in enumerate(guardian_summaries):
                agent_type = summary.get('agent_type', 'unknown')
                if agent_type in ['validator', 'result_validator']:
                    validation_count += 1
                logger.info(f"  Agent {i+1}: {summary.get('agent_id', 'unknown')} - "
                           f"Type: {agent_type}, "
                           f"Phase: {summary.get('current_phase', 'unknown')}, "
                           f"Aligned: {summary.get('trajectory_aligned', 'unknown')}")
            if validation_count > 0:
                logger.info(f"  NOTE: {validation_count} validation agents present (protected from duplicate termination)")
            logger.info("=" * 60)

            gpt5_analysis = await llm_provider.analyze_system_coherence(
                guardian_summaries=guardian_summaries,
                system_goals=system_goals,
            )

            # Log what we got back from the LLM
            logger.info("=" * 60)
            logger.info(f"✅ CONDUCTOR {model_name.upper()} RESPONSE")
            logger.info("=" * 60)
            logger.info(f"Full Response: {gpt5_analysis}")
            logger.info("=" * 60)

            # Extract LLM's decisions
            duplicates = gpt5_analysis.get("duplicates", [])
            coherence_score = gpt5_analysis.get("coherence_score", 0.7)
            termination_recs = gpt5_analysis.get("termination_recommendations", [])
            coordination_needs = gpt5_analysis.get("coordination_needs", [])

            # Convert LLM recommendations to decisions
            decisions = []

            # Handle duplicate terminations
            for term_rec in termination_recs:
                decisions.append({
                    "type": SystemDecision.TERMINATE_DUPLICATE.value,
                    "target": term_rec.get("agent_id"),
                    "reason": term_rec.get("reason", "Duplicate work detected by LLM"),
                    "confidence": 0.9,
                })

            # Handle resource coordination
            for coord_need in coordination_needs:
                decisions.append({
                    "type": SystemDecision.COORDINATE_RESOURCES.value,
                    "agents": coord_need.get("agents", []),
                    "resource": coord_need.get("resource", "unknown"),
                    "action": coord_need.get("action", "coordinate access"),
                    "confidence": 0.8,
                })

            # Handle low coherence
            if coherence_score < 0.5:
                decisions.append({
                    "type": SystemDecision.ESCALATE.value,
                    "reason": "System coherence too low per LLM analysis",
                    "details": gpt5_analysis.get("alignment_issues", []),
                    "confidence": 0.9,
                })

            # Build final result
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "num_agents": len(guardian_summaries),
                "duplicates": duplicates,
                "coherence": {
                    "score": coherence_score,
                    "issues": gpt5_analysis.get("alignment_issues", []),
                },
                "system_status": gpt5_analysis.get("system_summary", "No status"),
                "decisions": decisions,
                "llm_analysis": gpt5_analysis,  # Include full LLM analysis
            }

            # Update system state
            self.system_state.update({
                "last_analysis": datetime.utcnow(),
                "duplicate_pairs": duplicates,
                "coherence_score": coherence_score,
            })

            # Log LLM's analysis
            logger.info(
                f"{model_name} Conductor analysis: coherence={coherence_score:.2f}, "
                f"duplicates={len(duplicates)}, decisions={len(decisions)}"
            )

            return result

        except Exception as e:
            logger.error(f"Conductor analysis failed: {e}")
            return self._get_empty_analysis()

    async def execute_decisions(
        self,
        decisions: List[Dict[str, Any]],
    ):
        """
        Execute conductor decisions.

        This is where the conductor takes action based on the LLM's analysis.
        """
        logger.info(f"Executing {len(decisions)} conductor decisions")

        for decision in decisions:
            try:
                await self._execute_single_decision(decision)
            except Exception as e:
                logger.error(f"Failed to execute decision {decision['type']}: {e}")

    async def _execute_single_decision(self, decision: Dict[str, Any]):
        """Execute a single conductor decision."""
        decision_type = decision["type"]

        if decision_type == SystemDecision.TERMINATE_DUPLICATE.value:
            # Terminate duplicate agent
            agent_id = decision["target"]
            reason = decision["reason"]

            # SAFETY CHECK: Never terminate validation agents
            session = self.db_manager.get_session()
            try:
                agent = session.query(Agent).filter_by(id=agent_id).first()
                if agent and agent.agent_type in ["validator", "result_validator"]:
                    logger.warning(
                        f"SAFETY: Skipping termination of validation agent {agent_id} "
                        f"(type: {agent.agent_type}). Validation agents should not be terminated for duplication."
                    )
                    return  # Skip termination
            finally:
                session.close()

            logger.info(f"Terminating duplicate agent {agent_id}: {reason}")

            # Log the termination
            # session = self.db_manager.get_session()
            # try:
            #     log_entry = AgentLog(
            #         agent_id=agent_id,
            #         log_type="termination",
            #         message=f"Terminated by Conductor: {reason}",
            #         details=decision,
            #     )
            #     session.add(log_entry)
            #     session.commit()
            # finally:
            #     session.close()
            #
            # # Terminate the agent
            # await self.agent_manager.terminate_agent(agent_id)

        elif decision_type == SystemDecision.COORDINATE_RESOURCES.value:
            # Send coordination messages to agents
            agents = decision["agents"]
            resource = decision["resource"]

            for i, agent_id in enumerate(agents):
                # Assign time slots or priorities
                message = f"[CONDUCTOR]: Resource coordination for {resource}. "
                if i == 0:
                    message += "You have priority access."
                else:
                    message += f"Please wait for agent {agents[0]} to complete."

                await self.agent_manager.send_message_to_agent(agent_id, message)

        elif decision_type == SystemDecision.ESCALATE.value:
            # Log escalation for human review
            logger.critical(f"CONDUCTOR ESCALATION: {decision['reason']}")
            logger.critical(f"Details: {decision.get('details', 'None')}")

            # Could trigger alerts, send notifications, etc.

    def get_system_summary(self) -> str:
        """Get a quick system summary."""
        if not self.system_state["last_analysis"]:
            return "System not yet analyzed"

        age = datetime.utcnow() - self.system_state["last_analysis"]
        summary = f"Last analysis: {age.total_seconds():.0f}s ago"

        if self.system_state["duplicate_pairs"]:
            summary += f" | {len(self.system_state['duplicate_pairs'])} duplicates"

        summary += f" | Coherence: {self.system_state['coherence_score']:.2f}"

        return summary

    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Get empty analysis structure when no agents active."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "num_agents": 0,
            "duplicates": [],
            "coherence": {"score": 1.0, "issues": []},
            "system_status": "No agents active",
            "decisions": [],
            "gpt5_analysis": {},
        }

    async def generate_detailed_report(
        self,
        analysis: Dict[str, Any],
    ) -> str:
        """
        Generate detailed human-readable report from LLM analysis.

        This can be displayed in the monitoring dashboard or logs.
        """
        report = []
        report.append("=" * 60)
        report.append("CONDUCTOR LLM SYSTEM ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {analysis['timestamp']}")
        report.append(f"Active Agents: {analysis['num_agents']}")
        report.append("")

        # System Status from LLM
        report.append("SYSTEM STATUS (LLM)")
        report.append("-" * 30)
        report.append(analysis.get("system_status", "No status"))
        report.append("")

        # Coherence section
        report.append("SYSTEM COHERENCE")
        report.append("-" * 30)
        coherence = analysis.get("coherence", {})
        report.append(f"Score: {coherence.get('score', 0):.2f}/1.00")

        if coherence.get("issues"):
            report.append("Issues:")
            for issue in coherence["issues"]:
                report.append(f"  - {issue}")
        report.append("")

        # Duplicates section
        duplicates = analysis.get("duplicates", [])
        if duplicates:
            report.append("DUPLICATE WORK DETECTED")
            report.append("-" * 30)
            for dup in duplicates:
                report.append(f"Agents {dup['agent1']} and {dup['agent2']}:")
                report.append(f"  Similarity: {dup.get('similarity', 0):.2f}")
                report.append(f"  Work: {dup.get('work', 'Unknown')}")
            report.append("")

        # Decisions section
        decisions = analysis.get("decisions", [])
        if decisions:
            report.append("CONDUCTOR DECISIONS")
            report.append("-" * 30)
            for decision in decisions:
                report.append(f"Action: {decision['type']}")
                report.append(f"  Reason: {decision.get('reason', 'N/A')}")
                if decision.get('target'):
                    report.append(f"  Target: {decision['target']}")
                report.append(f"  Confidence: {decision.get('confidence', 0):.2f}")
            report.append("")

        # LLM Full Analysis (if detailed)
        if analysis.get("gpt5_analysis"):
            gpt5 = analysis["gpt5_analysis"]
            if gpt5.get("termination_recommendations"):
                report.append("LLM TERMINATION RECOMMENDATIONS")
                report.append("-" * 30)
                for rec in gpt5["termination_recommendations"]:
                    report.append(f"  Agent: {rec.get('agent_id', 'Unknown')}")
                    report.append(f"  Reason: {rec.get('reason', 'Unknown')}")
                report.append("")

            if gpt5.get("coordination_needs"):
                report.append("LLM COORDINATION NEEDS")
                report.append("-" * 30)
                for need in gpt5["coordination_needs"]:
                    report.append(f"  Resource: {need.get('resource', 'Unknown')}")
                    report.append(f"  Agents: {', '.join(need.get('agents', []))}")
                    report.append(f"  Action: {need.get('action', 'Unknown')}")
                report.append("")

        # Summary
        report.append("=" * 60)
        report.append("END REPORT")
        report.append("=" * 60)

        return "\n".join(report)