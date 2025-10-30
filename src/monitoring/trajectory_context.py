"""Trajectory context management for accumulated agent understanding."""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.database import DatabaseManager, AgentLog, Task

logger = logging.getLogger(__name__)


class TrajectoryContext:
    """
    Manages accumulated context for agents using trajectory thinking.

    This class implements the core concept from the tamagotchi trajectory thinking:
    - Build accumulated understanding from entire conversation
    - Track constraints that persist until lifted
    - Resolve references like "this/that"
    - Understand the complete journey, not just current state
    """

    def __init__(self, db_manager: DatabaseManager):
        """Initialize TrajectoryContext manager.

        Args:
            db_manager: Database manager for accessing agent logs
        """
        self.db_manager = db_manager

        # Cache for performance
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=5)

    def build_accumulated_context(
        self,
        agent_id: str,
        include_full_history: bool = True,
    ) -> Dict[str, Any]:
        """
        Build complete accumulated context for an agent.

        This is the core method that builds understanding from the ENTIRE
        conversation, not just recent messages.

        Args:
            agent_id: Agent ID to build context for
            include_full_history: Whether to include full conversation history

        Returns:
            Complete accumulated context including goals, constraints, references
        """
        logger.debug(f"Building accumulated context for agent {agent_id}")

        # Check cache first
        if agent_id in self.context_cache:
            cached = self.context_cache[agent_id]
            if cached["timestamp"] > datetime.utcnow() - self.cache_ttl:
                return cached["context"]

        session = self.db_manager.get_session()
        try:
            # Get all logs for complete understanding
            logs = session.query(AgentLog).filter_by(
                agent_id=agent_id
            ).order_by(AgentLog.created_at).all()

            if not logs:
                logger.warning(f"No logs found for agent {agent_id}")
                return self._get_empty_context()

            # Get task for initial context
            first_log = logs[0]
            task = None
            if hasattr(first_log, 'details') and first_log.details:
                task_id = first_log.details.get('task_id')
                if task_id:
                    task = session.query(Task).filter_by(id=task_id).first()

            # Build conversation history
            conversation = self._build_conversation_history(logs, include_full_history)

            # Extract accumulated understanding
            context = {
                # Core trajectory elements
                "overall_goal": self._extract_overall_goal(conversation, task),
                "evolved_goals": self._track_goal_evolution(conversation),
                "constraints": self._extract_persistent_constraints(conversation),
                "lifted_constraints": self._identify_lifted_constraints(conversation),
                "standing_instructions": self._extract_standing_instructions(conversation),

                # Reference resolution
                "references": self._resolve_references(conversation),
                "context_markers": self._extract_context_markers(conversation),

                # Journey tracking
                "phases_completed": self._identify_completed_phases(conversation),
                "current_focus": self._determine_current_focus(conversation),
                "attempted_approaches": self._extract_attempted_approaches(conversation),
                "discovered_blockers": self._find_discovered_blockers(conversation),

                # Meta information
                "conversation_length": len(conversation),
                "session_duration": self._calculate_session_duration(logs),
                "last_activity": logs[-1].created_at if logs else datetime.utcnow(),
                "agent_id": agent_id,
            }

            # Add task-specific context
            if task:
                context["task_id"] = task.id
                context["task_description"] = task.enriched_description or task.raw_description
                context["done_definition"] = task.done_definition
                context["task_complexity"] = task.estimated_complexity or 5

            # Cache the context
            self.context_cache[agent_id] = {
                "context": context,
                "timestamp": datetime.utcnow(),
            }

            return context

        finally:
            session.close()

    def _build_conversation_history(
        self,
        logs: List[AgentLog],
        include_full: bool,
    ) -> List[Dict[str, Any]]:
        """Build structured conversation history from logs."""
        conversation = []

        for log in logs:
            entry = {
                "type": log.log_type,
                "content": log.message,
                "timestamp": log.created_at,
                "details": log.details or {},
            }

            # Add to conversation based on log type
            if log.log_type in ["input", "output", "message", "steering"]:
                conversation.append(entry)
            elif log.log_type == "intervention" and log.details:
                # Include interventions as they affect trajectory
                conversation.append({
                    **entry,
                    "intervention_type": log.details.get("type", "unknown"),
                })

        # Limit history if requested (but keep key messages)
        if not include_full and len(conversation) > 200:
            # Keep first 50, last 100, and all interventions
            important = conversation[:50]
            recent = conversation[-100:]
            interventions = [c for c in conversation[50:-100] if c.get("intervention_type")]

            conversation = important + interventions + recent
            logger.debug(f"Limited conversation from {len(logs)} to {len(conversation)} entries")

        return conversation

    def _extract_overall_goal(
        self,
        conversation: List[Dict[str, Any]],
        task: Optional[Task],
    ) -> str:
        """Extract the overall accumulated goal from conversation."""
        # Start with task description if available
        if task:
            base_goal = task.enriched_description or task.raw_description
        else:
            base_goal = "Complete assigned task"

        # Look for goal refinements in conversation
        goal_patterns = [
            r"(?:the goal is|we need to|task is to|objective:)\s*(.+?)(?:\.|$)",
            r"(?:implement|create|build|fix|add|update)\s+(.+?)(?:\.|$)",
            r"(?:working on|focused on|trying to)\s+(.+?)(?:\.|$)",
        ]

        refined_goals = []
        for entry in conversation:
            content_lower = entry["content"].lower()
            for pattern in goal_patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                refined_goals.extend(matches)

        # Find most recent significant goal statement
        if refined_goals and len(refined_goals) > 0:
            # Use the most detailed recent goal
            recent_goal = max(refined_goals[-5:], key=len) if refined_goals else base_goal
            if len(recent_goal) > len(base_goal) * 0.5:  # If it's substantial enough
                return recent_goal.strip().capitalize()

        return base_goal

    def _track_goal_evolution(self, conversation: List[Dict[str, Any]]) -> List[str]:
        """Track how the goal evolved over the conversation."""
        goals = []

        # Patterns that indicate goal evolution
        evolution_patterns = [
            r"(?:now|next|then) (?:we need to|let's|I'll)\s+(.+?)(?:\.|$)",
            r"(?:actually|instead|rather),?\s+(?:we should|let's)\s+(.+?)(?:\.|$)",
            r"(?:changing|switching|pivoting) (?:to|towards?)\s+(.+?)(?:\.|$)",
        ]

        for entry in conversation:
            for pattern in evolution_patterns:
                matches = re.findall(pattern, entry["content"], re.IGNORECASE)
                for match in matches:
                    if match and len(match) > 20:  # Substantial goal statement
                        goals.append(match.strip())

        return goals[-5:] if goals else []  # Keep last 5 goal evolutions

    def _extract_persistent_constraints(
        self,
        conversation: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract constraints that persist until explicitly lifted."""
        constraints = []

        # Patterns for constraint detection
        constraint_patterns = [
            r"(?:don't|do not|never|avoid|without)\s+(.+?)(?:\.|$)",
            r"(?:only use|must use|should use)\s+(.+?)(?:\.|$)",
            r"(?:keep|make sure|ensure)\s+(?:it's|it is|things? are)\s+(.+?)(?:\.|$)",
            r"(?:constraint:|requirement:|rule:)\s*(.+?)(?:\.|$)",
        ]

        for entry in conversation:
            content = entry["content"]
            for pattern in constraint_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Clean and normalize constraint
                    constraint = match.strip().lower()
                    if len(constraint) > 10 and constraint not in constraints:
                        constraints.append(constraint)

        # Filter out lifted constraints
        lifted = self._identify_lifted_constraints(conversation)
        active_constraints = [c for c in constraints if c not in lifted]

        return active_constraints[:10]  # Keep top 10 most relevant

    def _identify_lifted_constraints(
        self,
        conversation: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify constraints that have been explicitly lifted."""
        lifted = []

        # Patterns for lifted constraints
        lift_patterns = [
            r"(?:you can now|feel free to|go ahead and)\s+(.+?)(?:\.|$)",
            r"(?:constraint lifted:|no longer need to:|don't worry about)\s+(.+?)(?:\.|$)",
            r"(?:ignore|disregard) (?:the )? (?:previous )?(?:constraint|rule) (?:about )?\s+(.+?)(?:\.|$)",
        ]

        for entry in conversation:
            for pattern in lift_patterns:
                matches = re.findall(pattern, entry["content"], re.IGNORECASE)
                lifted.extend([m.strip().lower() for m in matches])

        return lifted

    def _extract_standing_instructions(
        self,
        conversation: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract standing instructions that apply throughout."""
        instructions = []

        instruction_patterns = [
            r"(?:always|make sure to|remember to)\s+(.+?)(?:\.|$)",
            r"(?:for all|throughout|during)\s+(?:this task|the implementation),?\s+(.+?)(?:\.|$)",
            r"(?:important:|note:|remember:)\s*(.+?)(?:\.|$)",
        ]

        for entry in conversation[:20]:  # Focus on early instructions
            for pattern in instruction_patterns:
                matches = re.findall(pattern, entry["content"], re.IGNORECASE)
                for match in matches:
                    instruction = match.strip()
                    if len(instruction) > 15 and instruction not in instructions:
                        instructions.append(instruction)

        return instructions[:5]  # Keep top 5 standing instructions

    def _resolve_references(
        self,
        conversation: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Resolve 'this/that/it' references from conversation context."""
        references = {}

        # Track recent nouns/concepts that could be referenced
        recent_concepts = []

        for i, entry in enumerate(conversation):
            content = entry["content"]

            # Extract potential reference targets (nouns, files, functions, etc.)
            concept_patterns = [
                r"(?:file|function|class|module|component|feature|bug|error|issue)\s+called\s+(\S+)",
                r"(?:the|a)\s+(\w+\.(?:py|js|ts|tsx|jsx|java|go|rs|cpp|c|h))",
                r"(?:implement|create|fix|update|modify)\s+(?:the\s+)?(\w+(?:\s+\w+)?)",
            ]

            for pattern in concept_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                recent_concepts.extend(matches)

            # Keep only last 10 concepts
            recent_concepts = recent_concepts[-10:]

            # Look for reference usage and resolve
            ref_patterns = [
                r"\b(this|that|it)\s+(.+?)(?:\.|,|$)",
                r"(?:do|implement|fix|update)\s+(this|that|it)\b",
            ]

            for pattern in ref_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    ref_word = match[0] if isinstance(match, tuple) else match
                    # Resolve to most recent concept
                    if recent_concepts:
                        references[f"{ref_word}_{i}"] = recent_concepts[-1]

        return references

    def _extract_context_markers(
        self,
        conversation: List[Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        """Extract important context markers from conversation."""
        markers = defaultdict(list)

        # Different types of context markers
        marker_patterns = {
            "decisions": r"(?:decided to|chose|selected|going with)\s+(.+?)(?:\.|$)",
            "discoveries": r"(?:found|discovered|realized|noticed)\s+(?:that\s+)?(.+?)(?:\.|$)",
            "blockers": r"(?:blocked by|stuck on|can't|cannot)\s+(.+?)(?:\.|$)",
            "completions": r"(?:completed|finished|done with)\s+(.+?)(?:\.|$)",
        }

        for entry in conversation:
            for marker_type, pattern in marker_patterns.items():
                matches = re.findall(pattern, entry["content"], re.IGNORECASE)
                for match in matches:
                    if len(match) > 10:  # Meaningful marker
                        markers[marker_type].append(match.strip())

        # Limit each type to most recent/relevant
        for marker_type in markers:
            markers[marker_type] = markers[marker_type][-5:]

        return dict(markers)

    def _identify_completed_phases(
        self,
        conversation: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify which phases have been completed."""
        completed = []

        completion_patterns = [
            r"(?:completed|finished|done)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+phase",
            r"(\w+(?:\s+\w+)?)\s+phase\s+(?:is\s+)?(?:complete|done|finished)",
            r"(?:exploration|planning|implementation|testing|verification)\s+(?:is\s+)?(?:complete|done)",
        ]

        for entry in conversation:
            for pattern in completion_patterns:
                matches = re.findall(pattern, entry["content"], re.IGNORECASE)
                for match in matches:
                    phase = match.strip().lower()
                    if phase and phase not in completed:
                        completed.append(phase)

        return completed

    def _determine_current_focus(
        self,
        conversation: List[Dict[str, Any]],
    ) -> str:
        """Determine current focus from recent conversation."""
        if not conversation:
            return "initializing"

        # Look at last 10 messages for current focus
        recent = conversation[-10:] if len(conversation) > 10 else conversation

        focus_keywords = {
            "exploring": ["reading", "examining", "looking at", "exploring"],
            "implementing": ["creating", "writing", "implementing", "coding"],
            "debugging": ["error", "bug", "issue", "problem", "fixing"],
            "testing": ["test", "verify", "check", "validate"],
            "planning": ["plan", "approach", "design", "architect"],
        }

        # Count occurrences in recent messages
        focus_scores = defaultdict(int)
        for entry in recent:
            content_lower = entry["content"].lower()
            for focus, keywords in focus_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        focus_scores[focus] += 1

        # Return highest scoring focus
        if focus_scores:
            return max(focus_scores, key=focus_scores.get)

        return "working"

    def _extract_attempted_approaches(
        self,
        conversation: List[Dict[str, Any]],
    ) -> List[str]:
        """Extract approaches that have been attempted."""
        approaches = []

        approach_patterns = [
            r"(?:trying|attempting|going to try)\s+(.+?)(?:\.|$)",
            r"(?:approach:|strategy:|plan:)\s*(.+?)(?:\.|$)",
            r"(?:let me|I'll|I will)\s+(.+?)(?:\.|$)",
        ]

        for entry in conversation:
            for pattern in approach_patterns:
                matches = re.findall(pattern, entry["content"], re.IGNORECASE)
                for match in matches:
                    if len(match) > 20:  # Substantial approach description
                        approaches.append(match.strip())

        return approaches[-10:] if approaches else []  # Last 10 approaches

    def _find_discovered_blockers(
        self,
        conversation: List[Dict[str, Any]],
    ) -> List[str]:
        """Find blockers discovered during the conversation."""
        blockers = []

        blocker_patterns = [
            r"(?:blocked by|stuck on|waiting for)\s+(.+?)(?:\.|$)",
            r"(?:can't|cannot|unable to)\s+(.+?)(?:\.|$)",
            r"(?:error:|issue:|problem:)\s*(.+?)(?:\.|$)",
        ]

        for entry in conversation:
            for pattern in blocker_patterns:
                matches = re.findall(pattern, entry["content"], re.IGNORECASE)
                for match in matches:
                    blocker = match.strip()
                    if len(blocker) > 10 and blocker not in blockers:
                        blockers.append(blocker)

        return blockers[:10]  # Top 10 blockers

    def _calculate_session_duration(self, logs: List[AgentLog]) -> timedelta:
        """Calculate total session duration."""
        if not logs:
            return timedelta(0)

        first_log = logs[0]
        last_log = logs[-1]
        return last_log.created_at - first_log.created_at

    def _get_empty_context(self) -> Dict[str, Any]:
        """Get empty context structure."""
        return {
            "overall_goal": "Unknown",
            "evolved_goals": [],
            "constraints": [],
            "lifted_constraints": [],
            "standing_instructions": [],
            "references": {},
            "context_markers": {},
            "phases_completed": [],
            "current_focus": "initializing",
            "attempted_approaches": [],
            "discovered_blockers": [],
            "conversation_length": 0,
            "session_duration": timedelta(0),
            "last_activity": datetime.utcnow(),
            "agent_id": None,
        }

    def check_constraint_violations(
        self,
        action: str,
        constraints: List[str],
    ) -> Tuple[bool, List[str]]:
        """
        Check if an action violates any constraints.

        Args:
            action: The action being taken
            constraints: List of active constraints

        Returns:
            Tuple of (has_violations, list_of_violations)
        """
        violations = []
        action_lower = action.lower()

        for constraint in constraints:
            constraint_lower = constraint.lower()

            # Check for direct violations
            violation_checks = [
                ("no external" in constraint_lower and "pip install" in action_lower),
                ("no external" in constraint_lower and "npm install" in action_lower),
                ("simple" in constraint_lower and any(term in action_lower for term in ["factory", "abstract", "framework"])),
                ("don't write" in constraint_lower and any(term in action_lower for term in ["creating", "writing", "implementing"])),
                ("avoid" in constraint_lower and any(
                    avoided in action_lower
                    for avoided in constraint_lower.split("avoid")[1].split()
                )),
            ]

            if any(violation_checks):
                violations.append(constraint)

        return (len(violations) > 0, violations)

    def get_trajectory_summary(self, agent_id: str) -> str:
        """
        Get a concise trajectory summary for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Trajectory summary string
        """
        context = self.build_accumulated_context(agent_id, include_full_history=False)

        summary_parts = [
            f"Goal: {context['overall_goal'][:100]}",
            f"Focus: {context['current_focus']}",
            f"Duration: {str(context['session_duration']).split('.')[0]}",
        ]

        if context['constraints']:
            summary_parts.append(f"Constraints: {len(context['constraints'])}")

        if context['discovered_blockers']:
            summary_parts.append(f"Blockers: {len(context['discovered_blockers'])}")

        return " | ".join(summary_parts)

    def clear_cache(self, agent_id: Optional[str] = None):
        """Clear context cache."""
        if agent_id:
            if agent_id in self.context_cache:
                del self.context_cache[agent_id]
        else:
            self.context_cache.clear()