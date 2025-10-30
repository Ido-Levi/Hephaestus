"""Multi-provider LLM implementation using LangChain."""

from typing import Dict, Any, List, Optional
import logging
import asyncio

from src.interfaces.llm_interface import LLMProviderInterface
from src.interfaces.langchain_llm_client import (
    LangChainLLMClient,
    ComponentType,
    LLMConfig as LangChainConfig,
    ModelAssignment,
    ProviderConfig
)
from src.core.llm_config import get_config

logger = logging.getLogger(__name__)


class MultiProviderLLM(LLMProviderInterface):
    """Multi-provider LLM implementation using LangChain."""

    def __init__(self, config_path: str = "./hephaestus_config.yaml"):
        """Initialize multi-provider LLM.

        Args:
            config_path: Path to configuration file
        """
        self.config = get_config(config_path)
        # Use non-strict validation to allow partial initialization
        self.config.validate(strict=False)

        # Convert to LangChain config format
        llm_config = self.config.get_llm_config()
        self.client = LangChainLLMClient(llm_config)

    async def enrich_task(
        self,
        task_description: str,
        done_definition: str,
        context: List[str],
        phase_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich a task with LLM analysis.

        Args:
            task_description: Raw task description
            done_definition: What constitutes task completion
            context: Relevant context from memory
            phase_context: Optional phase context for workflow-based tasks

        Returns:
            Dictionary containing enriched task information
        """
        return await self.client.enrich_task(
            task_description=task_description,
            done_definition=done_definition,
            context=context,
            phase_context=phase_context
        )

    async def resolve_ticket_clarification(
        self,
        ticket_id: str,
        conflict_description: str,
        context: str,
        potential_solutions: List[str],
        ticket_details: Dict[str, Any],
        related_tickets: List[Dict[str, Any]],
        active_tasks: List[Dict[str, Any]]
    ) -> str:
        """Resolve ticket clarification using LLM arbitration.

        Args:
            ticket_id: ID of the ticket needing clarification
            conflict_description: Description of the conflict or ambiguity
            context: Additional context from the agent
            potential_solutions: List of potential solutions the agent is considering
            ticket_details: Full details of the disputed ticket
            related_tickets: Recent tickets for context (max 60)
            active_tasks: Active tasks for context (max 60)

        Returns:
            Detailed markdown guidance with resolution
        """
        return await self.client.resolve_ticket_clarification(
            ticket_id=ticket_id,
            conflict_description=conflict_description,
            context=context,
            potential_solutions=potential_solutions,
            ticket_details=ticket_details,
            related_tickets=related_tickets,
            active_tasks=active_tasks
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return await self.client.generate_embedding(text)

    async def analyze_agent_state(
        self,
        agent_output: str,
        task_info: Dict[str, Any],
        project_context: str,
    ) -> Dict[str, Any]:
        """Analyze agent state for monitoring decisions.

        Args:
            agent_output: Recent output from agent's tmux session
            task_info: Current task information
            project_context: Project-wide context

        Returns:
            Dictionary containing state analysis
        """
        return await self.client.analyze_agent_state(
            agent_output=agent_output,
            task_info=task_info,
            project_context=project_context
        )

    async def generate_agent_prompt(
        self,
        task: Dict[str, Any],
        memories: List[Dict[str, Any]],
        project_context: str,
    ) -> str:
        """Generate specialized system prompt for an agent.

        Args:
            task: Task information
            memories: Relevant memories from RAG
            project_context: Current project context

        Returns:
            System prompt for the agent
        """
        return await self.client.generate_agent_prompt(
            task=task,
            memories=memories,
            project_context=project_context
        )

    async def analyze_agent_trajectory(
        self,
        agent_output: str,
        accumulated_context: Dict[str, Any],
        past_summaries: List[Dict[str, Any]],
        task_info: Dict[str, Any],
        last_message_marker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze agent using trajectory thinking.

        Args:
            agent_output: Recent agent output
            accumulated_context: Full accumulated context from conversation
            past_summaries: Previous Guardian summaries
            task_info: Current task information
            last_message_marker: Optional marker from previous cycle

        Returns:
            Dictionary containing trajectory analysis
        """
        return await self.client.analyze_agent_trajectory(
            agent_output=agent_output,
            accumulated_context=accumulated_context,
            past_summaries=past_summaries,
            task_info=task_info,
            last_message_marker=last_message_marker,  # NEW
        )

    async def analyze_system_coherence(
        self,
        guardian_summaries: List[Dict[str, Any]],
        system_goals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze system-wide coherence from Guardian summaries.

        Args:
            guardian_summaries: All Guardian analysis results
            system_goals: Overall system goals

        Returns:
            Dictionary containing coherence analysis
        """
        return await self.client.analyze_system_coherence(
            guardian_summaries=guardian_summaries,
            system_goals=system_goals
        )

    def get_model_name(self) -> str:
        """Get the name of the model being used.

        Returns:
            Model name (returns task enrichment model as default)
        """
        return self.client.get_model_name(ComponentType.TASK_ENRICHMENT)

    def get_model_for_component(self, component_name: str) -> str:
        """Get the model being used for a specific component.

        Args:
            component_name: Name of the component

        Returns:
            Model name for the component
        """
        try:
            component = ComponentType(component_name)
            return self.client.get_model_name(component)
        except ValueError:
            return "unknown"