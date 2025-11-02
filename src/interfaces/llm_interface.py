"""Abstract interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import logging
import asyncio
from src.monitoring.models import GuardianTrajectoryAnalysis, ConductorSystemAnalysis

logger = logging.getLogger(__name__)


class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
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
            Dictionary containing:
                - enriched_description: Clear, unambiguous task description
                - completion_criteria: Specific completion criteria
                - agent_prompt: Suggested system prompt for agent
                - required_capabilities: List of required capabilities
                - estimated_complexity: Complexity score (1-10)
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
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
            Dictionary containing:
                - state: Agent state (healthy/stuck_waiting/stuck_error/stuck_confused/unrecoverable)
                - decision: Action to take (continue/nudge/answer/restart/recreate)
                - message: Message to send if nudge/answer
                - reasoning: Brief explanation
                - confidence: Confidence score (0-1)
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the model being used.

        Returns:
            Model name
        """
        pass

    @abstractmethod
    async def analyze_agent_trajectory(
        self,
        agent_output: str,
        accumulated_context: Dict[str, Any],
        past_summaries: List[Dict[str, Any]],
        task_info: Dict[str, Any],
        last_message_marker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze agent using trajectory thinking.

        This method implements trajectory thinking from the tamagotchi system:
        - Builds understanding from ENTIRE conversation
        - Tracks persistent constraints and goals
        - Detects trajectory alignment
        - Provides targeted steering recommendations

        Args:
            agent_output: Recent agent output
            accumulated_context: Full accumulated context from conversation
            past_summaries: Previous Guardian summaries
            task_info: Current task information
            last_message_marker: Optional marker from previous cycle to identify new content

        Returns:
            Dictionary containing:
                - current_phase: Current work phase
                - trajectory_aligned: Whether agent is on track
                - alignment_issues: List of alignment problems
                - steering_recommendation: Steering message if needed
                - progress_estimate: Estimated progress percentage
                - last_claude_message_marker: Marker for next cycle
        """
        pass

    @abstractmethod
    async def analyze_system_coherence(
        self,
        guardian_summaries: List[Dict[str, Any]],
        system_goals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze system-wide coherence from Guardian summaries.

        This method is used by the Conductor to:
        - Detect duplicate work across agents
        - Check collective progress
        - Identify resource conflicts
        - Ensure system coherence

        Args:
            guardian_summaries: All Guardian analysis results
            system_goals: Overall system goals

        Returns:
            Dictionary containing:
                - duplicates: List of duplicate work pairs
                - coherence_score: System coherence score (0-1)
                - termination_recommendations: Agents to terminate
                - coordination_needs: Resource coordination requirements
        """
        pass


class OpenAIProvider(LLMProviderInterface):
    """OpenAI GPT implementation."""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", embedding_model: str = "text-embedding-ada-002"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use for completions
            embedding_model: Model to use for embeddings
        """
        import openai
        import httpx

        # Create client with explicit httpx client to avoid proxy parameter issues
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            http_client=httpx.AsyncClient()
        )
        self.model = model
        self.embedding_model = embedding_model

    async def enrich_task(
        self,
        task_description: str,
        done_definition: str,
        context: List[str],
        phase_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich task using GPT."""
        prompt = f"""Given this task request, analyze and enrich it with clear specifications.

Task: {task_description}
Done Definition: {done_definition}
Context: {' '.join(context[:10])}  # Limit context to avoid token overflow"""

        if phase_context:
            prompt += f"""

Phase Context:
{phase_context}"""

        prompt += """

Generate a JSON response with:
1. "enriched_description": A clear, unambiguous task description
2. "completion_criteria": Specific, measurable completion criteria (list)
3. "agent_prompt": A focused system prompt for the agent executing this task
4. "required_capabilities": List of required capabilities (e.g., "file_editing", "code_analysis")
5. "estimated_complexity": Integer 1-10 indicating task complexity

Ensure the enriched description is actionable and the completion criteria are specific and verifiable."""

        if phase_context:
            prompt += "\nConsider the phase context when determining complexity and requirements."

        try:
            # Build kwargs based on model type
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a task analysis expert for an AI orchestration system."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
            }

            # Use max_completion_tokens for newer models, max_tokens for older ones
            if "gpt-4o" in self.model or "gpt-5" in self.model or "o1" in self.model:
                kwargs["max_completion_tokens"] = 16000
            else:
                kwargs["max_tokens"] = 16000

            response = await self.client.chat.completions.create(**kwargs)

            result = json.loads(response.choices[0].message.content)
            logger.debug(f"Task enriched successfully: {result.get('enriched_description', '')[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Failed to enrich task: {e}")
            # Return a basic enrichment as fallback
            return {
                "enriched_description": task_description,
                "completion_criteria": [done_definition],
                "agent_prompt": f"Complete this task: {task_description}",
                "required_capabilities": ["general"],
                "estimated_complexity": 5,
            }

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text[:8000],  # Limit input length
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback (3072 for text-embedding-3-large)
            return [0.0] * 3072

    async def analyze_agent_state(
        self,
        agent_output: str,
        task_info: Dict[str, Any],
        project_context: str,
    ) -> Dict[str, Any]:
        """Analyze agent state using GPT."""
        prompt = f"""Analyze this AI agent's current state and decide on the appropriate action.

AGENT OUTPUT (Last 200 lines):
```
{agent_output}
```

TASK INFO:
- Description: {task_info.get('description', 'Unknown')}
- Completion Criteria: {task_info.get('done_definition', 'Unknown')}
- Time on Task: {task_info.get('time_elapsed', 0)} minutes

PROJECT CONTEXT:
{project_context}

Based on the agent's output, determine:
1. Agent state: healthy/stuck_waiting/stuck_error/stuck_confused/unrecoverable
2. Decision: continue/nudge/answer/restart/recreate
3. If nudge/answer, what message would help?
4. Brief reasoning for the decision
5. Confidence level (0-1)

Return as JSON with keys: state, decision, message, reasoning, confidence"""

        try:
            # Build kwargs based on model type
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an AI agent monitoring expert."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
            }

            # Use max_completion_tokens for newer models, max_tokens for older ones
            if "gpt-4o" in self.model or "gpt-5" in self.model or "o1" in self.model:
                kwargs["max_completion_tokens"] = 16000
            else:
                kwargs["max_tokens"] = 16000

            response = await self.client.chat.completions.create(**kwargs)

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Failed to analyze agent state: {e}")
            return {
                "state": "healthy",
                "decision": "continue",
                "message": "",
                "reasoning": "Analysis failed, assuming healthy",
                "confidence": 0.3,
            }

    async def generate_agent_prompt(
        self,
        task: Dict[str, Any],
        memories: List[Dict[str, Any]],
        project_context: str,
    ) -> str:
        """Generate agent system prompt."""
        memory_context = "\n".join([
            f"- {mem.get('content', '')[:200]}"
            for mem in memories[:10]
        ])

        return f"""You are an AI agent in the Hephaestus orchestration system.

═══ TASK ═══
{task.get('enriched_description', task.get('description', ''))}

COMPLETION CRITERIA:
{task.get('done_definition', 'Complete the assigned task')}

═══ PRE-LOADED CONTEXT ═══
Top 10 relevant memories (use qdrant-find for more):
{memory_context}

PROJECT:
{project_context}

═══ AVAILABLE TOOLS ═══

Hephaestus MCP (task management):
• create_task - Create sub-tasks (MUST set parent_task_id="{task.get('id', 'unknown')}")
• update_task_status - Mark done/failed when complete (REQUIRED)
• save_memory - Save discoveries for other agents

Qdrant MCP (memory search):
• qdrant-find - Search agent memories semantically
  Use when: encountering errors, needing implementation details, finding related work
  Example: "qdrant-find 'PostgreSQL connection timeout solutions'"
  Note: Pre-loaded context covers most needs; search for specifics

═══ WORKFLOW ═══
1. Work on your task using pre-loaded context
2. Use qdrant-find if you need specific information (errors, patterns, implementations)
3. Save important discoveries via save_memory (error fixes, decisions, warnings)
4. Call update_task_status when done (status='done') or failed (status='failed')

IDs: Agent={task.get('agent_id', 'unknown')} | Task={task.get('id', 'unknown')}"""

    async def analyze_agent_trajectory(
        self,
        agent_output: str,
        accumulated_context: Dict[str, Any],
        past_summaries: List[Dict[str, Any]],
        task_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze agent using trajectory thinking with structured prompts."""
        # Use the prompt loader to get properly formatted prompt
        from src.monitoring.prompt_loader import prompt_loader

        prompt = prompt_loader.format_guardian_prompt(
            accumulated_context=accumulated_context,
            past_summaries=past_summaries,
            task_info=task_info,
            agent_output=agent_output,
        )

        for attempt in range(3):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a trajectory analysis expert using accumulated context thinking."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": GuardianTrajectoryAnalysis,
                }

                if "gpt-4o" in self.model or "gpt-5" in self.model or "o1" in self.model:
                    kwargs["max_completion_tokens"] = 16000
                else:
                    kwargs["max_tokens"] = 16000

                response = await self.client.beta.chat.completions.parse(**kwargs)

                # Return the parsed Pydantic model as dict
                return response.choices[0].message.parsed.model_dump()

            except Exception as e:
                logger.error(f"Failed to analyze trajectory (attempt {attempt + 1}/3): {e}")
                if attempt == 2:  # Last attempt
                    # Return fallback with proper structure
                    fallback = GuardianTrajectoryAnalysis(
                        current_phase="unknown",
                        trajectory_aligned=True,
                        alignment_score=0.5,
                        alignment_issues=[],
                        needs_steering=False,
                        steering_type=None,
                        steering_recommendation=None,
                        trajectory_summary="Analysis failed after 3 attempts"
                    )
                    return fallback.model_dump()
                await asyncio.sleep(1)  # Brief delay before retry

    async def analyze_system_coherence(
        self,
        guardian_summaries: List[Dict[str, Any]],
        system_goals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze system-wide coherence from Guardian summaries with structured prompts."""
        # Use the prompt loader to get properly formatted prompt
        from src.monitoring.prompt_loader import prompt_loader

        prompt = prompt_loader.format_conductor_prompt(
            guardian_summaries=guardian_summaries,
            system_goals=system_goals,
        )

        for attempt in range(3):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a system orchestration expert analyzing multi-agent coherence."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": ConductorSystemAnalysis,
                }

                if "gpt-4o" in self.model or "gpt-5" in self.model or "o1" in self.model:
                    kwargs["max_completion_tokens"] = 16000
                else:
                    kwargs["max_tokens"] = 16000

                response = await self.client.beta.chat.completions.parse(**kwargs)

                # Return the parsed Pydantic model as dict
                return response.choices[0].message.parsed.model_dump()

            except Exception as e:
                logger.error(f"Failed to analyze system coherence (attempt {attempt + 1}/3): {e}")
                if attempt == 2:  # Last attempt
                    # Return fallback with proper structure
                    fallback = ConductorSystemAnalysis(
                        coherence_score=0.7,
                        duplicates=[],
                        alignment_issues=[],
                        termination_recommendations=[],
                        coordination_needs=[],
                        system_summary="Analysis failed after 3 attempts - assuming moderate coherence"
                    )
                    return fallback.model_dump()
                await asyncio.sleep(1)  # Brief delay before retry

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model


class AnthropicProvider(LLMProviderInterface):
    """Anthropic Claude implementation."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use
        """
        import anthropic

        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def enrich_task(
        self,
        task_description: str,
        done_definition: str,
        context: List[str],
        phase_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich task using Claude."""
        phase_info = f"\n\nPhase Context:\n{phase_context}" if phase_context else ""
        prompt = f"""Analyze and enrich this task for an AI agent orchestration system.

Task: {task_description}
Done Definition: {done_definition}
Context: {' '.join(context[:10])}{phase_info}

Provide a JSON response with these exact keys:
- enriched_description: Clear, unambiguous task description
- completion_criteria: List of specific, measurable criteria
- agent_prompt: System prompt for the executing agent
- required_capabilities: List of required capabilities
- estimated_complexity: Integer 1-10

Make the description actionable and criteria verifiable."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16000,
            )

            # Claude returns text, so we need to parse JSON from it
            content = response.content[0].text
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.error(f"Failed to enrich task with Claude: {e}")
            return {
                "enriched_description": task_description,
                "completion_criteria": [done_definition],
                "agent_prompt": f"Complete this task: {task_description}",
                "required_capabilities": ["general"],
                "estimated_complexity": 5,
            }

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding.

        Note: Claude doesn't provide embeddings directly, so we'd need to use
        a separate service or fallback to OpenAI for embeddings.
        """
        logger.warning("Claude doesn't provide embeddings, using placeholder")
        # In production, you'd want to use a dedicated embedding service
        return [0.0] * 1536

    async def analyze_agent_state(
        self,
        agent_output: str,
        task_info: Dict[str, Any],
        project_context: str,
    ) -> Dict[str, Any]:
        """Analyze agent state using Claude."""
        # Similar implementation to OpenAI
        # Implementation details omitted for brevity
        return {
            "state": "healthy",
            "decision": "continue",
            "message": "",
            "reasoning": "Default response",
            "confidence": 0.5,
        }

    async def generate_agent_prompt(
        self,
        task: Dict[str, Any],
        memories: List[Dict[str, Any]],
        project_context: str,
    ) -> str:
        """Generate agent system prompt."""
        memory_context = "\n".join([
            f"- {mem.get('content', '')[:200]}"
            for mem in memories[:10]
        ])

        return f"""You are an AI agent in the Hephaestus orchestration system.

═══ TASK ═══
{task.get('enriched_description', task.get('description', ''))}

COMPLETION CRITERIA:
{task.get('done_definition', 'Complete the assigned task')}

═══ PRE-LOADED CONTEXT ═══
Top 10 relevant memories (use qdrant-find for more):
{memory_context}

PROJECT:
{project_context}

═══ AVAILABLE TOOLS ═══

Hephaestus MCP (task management):
• create_task - Create sub-tasks (MUST set parent_task_id="{task.get('id', 'unknown')}")
• update_task_status - Mark done/failed when complete (REQUIRED)
• save_memory - Save discoveries for other agents

Qdrant MCP (memory search):
• qdrant-find - Search agent memories semantically
  Use when: encountering errors, needing implementation details, finding related work
  Example: "qdrant-find 'PostgreSQL connection timeout solutions'"
  Note: Pre-loaded context covers most needs; search for specifics

═══ WORKFLOW ═══
1. Work on your task using pre-loaded context
2. Use qdrant-find if you need specific information (errors, patterns, implementations)
3. Save important discoveries via save_memory (error fixes, decisions, warnings)
4. Call update_task_status when done (status='done') or failed (status='failed')

IDs: Agent={task.get('agent_id', 'unknown')} | Task={task.get('id', 'unknown')}"""

    async def analyze_agent_trajectory(
        self,
        agent_output: str,
        accumulated_context: Dict[str, Any],
        past_summaries: List[Dict[str, Any]],
        task_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze agent using trajectory thinking."""
        # For now, return default - can be implemented with Claude API later
        logger.warning("Trajectory analysis not fully implemented for Anthropic provider")
        return {
            "current_phase": "implementation",
            "trajectory_aligned": True,
            "alignment_score": 0.7,
            "alignment_issues": [],
            "progress_estimate": 50,
            "needs_steering": False,
            "steering_type": None,
            "steering_recommendation": None,
            "trajectory_summary": "Using default trajectory analysis"
        }

    async def analyze_system_coherence(
        self,
        guardian_summaries: List[Dict[str, Any]],
        system_goals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze system-wide coherence from Guardian summaries."""
        # For now, return default - can be implemented with Claude API later
        logger.warning("System coherence analysis not fully implemented for Anthropic provider")
        return {
            "coherence_score": 0.7,
            "duplicates": [],
            "collective_progress": 50,
            "alignment_issues": [],
            "termination_recommendations": [],
            "coordination_needs": [],
            "system_summary": "Using default coherence analysis"
        }

    def get_model_name(self) -> str:
        """Get model name."""
        return self.model


# Registry for LLM providers
LLM_PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_llm_provider() -> LLMProviderInterface:
    """Get LLM provider instance based on configuration.

    Returns:
        Configured LLM provider instance
    """
    from ..core.llm_config import get_config as get_llm_config
    from ..core.simple_config import get_config

    logger.info("="*60)
    logger.info("🔧 Initializing LLM Provider System")
    logger.info("="*60)

    # Check if we have multi-provider configuration
    try:
        llm_config = get_llm_config()
        # Use non-strict validation to allow partial initialization
        llm_config.validate(strict=False)

        # If we have model assignments, use multi-provider
        if llm_config._llm_config and llm_config._llm_config.model_assignments:
            from .multi_provider_llm import MultiProviderLLM
            logger.info("✅ Using MULTI-PROVIDER LLM configuration (from hephaestus_config.yaml)")
            logger.info("="*60)
            return MultiProviderLLM()
    except Exception as e:
        logger.warning(f"⚠️ Multi-provider config not available, falling back to single provider: {e}")

    # Fallback to single provider configuration
    logger.info("⚠️ Using LEGACY SINGLE-PROVIDER mode")
    config = get_config()
    config.validate()

    logger.info(f"   Provider: {config.llm_provider}")
    logger.info(f"   Model: {config.llm_model}")
    logger.info("="*60)

    provider_class = LLM_PROVIDERS.get(config.llm_provider)
    if not provider_class:
        raise ValueError(f"Unknown LLM provider: {config.llm_provider}")

    api_key = config.get_api_key()
    if not api_key:
        raise ValueError(f"API key not found for provider: {config.llm_provider}")

    if config.llm_provider == "openai":
        return provider_class(
            api_key=api_key,
            model=config.llm_model,
            embedding_model=config.embedding_model
        )
    elif config.llm_provider == "anthropic":
        return provider_class(
            api_key=api_key,
            model=config.llm_model
        )
    else:
        raise ValueError(f"Unsupported provider: {config.llm_provider}")