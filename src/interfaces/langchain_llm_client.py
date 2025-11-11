"""LangChain-based multi-provider LLM client for Hephaestus."""

import logging
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
import json
import asyncio
from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI, OpenAIEmbeddings, AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from typing import Optional as Opt

from src.monitoring.models import GuardianTrajectoryAnalysis, ConductorSystemAnalysis

logger = logging.getLogger(__name__)



class ModelAssignment(BaseModel):
    """Model assignment configuration."""
    provider: str
    model: str
    openrouter_provider: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000


class ProviderConfig(BaseModel):
    """Provider configuration."""
    api_key_env: str
    base_url: Optional[str] = None
    models: List[Any]


class LLMConfig(BaseModel):
    """Complete LLM configuration."""
    embedding_model: str = "text-embedding-3-small"
    providers: Dict[str, ProviderConfig]
    model_assignments: Dict[str, ModelAssignment]


class ComponentType(Enum):
    """Component types for model routing."""
    TASK_ENRICHMENT = "task_enrichment"
    AGENT_MONITORING = "agent_monitoring"
    GUARDIAN_ANALYSIS = "guardian_analysis"
    CONDUCTOR_ANALYSIS = "conductor_analysis"
    AGENT_PROMPTS = "agent_prompts"


class LangChainLLMClient:
    """Multi-provider LLM client using LangChain."""

    def __init__(self, config: LLMConfig):
        """Initialize the LangChain LLM client.

        Args:
            config: LLM configuration with providers and model assignments
        """
        self.config = config
        self._models: Dict[str, Any] = {}
        self._embedding_model = None

        logger.info("="*60)
        logger.info("🚀 Initializing Multi-Provider LLM Client")
        logger.info("="*60)
        self._initialize_models()
        logger.info("✅ Multi-Provider LLM Client initialized successfully")
        logger.info("="*60)

    def _initialize_models(self):
        """Initialize all configured models."""
        import os

        # Initialize embedding model based on configured provider
        embedding_provider = getattr(self.config, 'embedding_provider', 'openai')
        logger.info(f"Initializing embedding model: {self.config.embedding_model} (provider: {embedding_provider})")

        if embedding_provider == "openai":
            openai_provider = self.config.providers.get("openai")
            if openai_provider:
                openai_key = os.getenv(openai_provider.api_key_env)
                if openai_key:
                    self._embedding_model = OpenAIEmbeddings(
                        model=self.config.embedding_model,
                        openai_api_key=openai_key
                    )
                    logger.info(f"  ✓ Embedding model initialized: OpenAI {self.config.embedding_model}")

        elif embedding_provider == "azure_openai":
            azure_provider = self.config.providers.get("azure_openai")
            if azure_provider:
                azure_key = os.getenv(azure_provider.api_key_env)
                azure_endpoint = azure_provider.base_url
                if azure_key and azure_endpoint:
                    api_version = azure_provider.api_version or "2024-02-01"
                    self._embedding_model = AzureOpenAIEmbeddings(
                        model=self.config.embedding_model,
                        azure_deployment=self.config.embedding_model,
                        azure_endpoint=azure_endpoint,
                        api_version=api_version,
                        api_key=azure_key
                    )
                    logger.info(f"  ✓ Embedding model initialized: Azure OpenAI {self.config.embedding_model}")
                else:
                    logger.warning(f"Azure OpenAI embedding configuration incomplete (key or endpoint missing)")

        elif embedding_provider == "google_ai":
            google_provider = self.config.providers.get("google_ai")
            if google_provider:
                google_key = os.getenv(google_provider.api_key_env)
                if google_key:
                    self._embedding_model = GoogleGenerativeAIEmbeddings(
                        model=self.config.embedding_model,  # e.g., "models/embedding-001"
                        google_api_key=google_key
                    )
                    logger.info(f"  ✓ Embedding model initialized: Google AI {self.config.embedding_model}")
                else:
                    logger.warning(f"Google AI embedding configuration incomplete (key missing)")

        if not self._embedding_model:
            logger.warning(f"Embedding model not initialized for provider: {embedding_provider}")

        # Initialize models for each component
        logger.info(f"Configuring models for {len(self.config.model_assignments)} components:")
        for component_name, assignment in self.config.model_assignments.items():
            model_key = f"{component_name}_{assignment.provider}_{assignment.model}"

            if model_key not in self._models:
                model = self._create_model(assignment)
                if model:
                    self._models[model_key] = model
                    provider_info = f"{assignment.provider}"
                    if hasattr(assignment, 'openrouter_provider') and assignment.openrouter_provider:
                        provider_info += f" (via {assignment.openrouter_provider})"
                    logger.info(f"  ✓ {component_name}: {assignment.model} [{provider_info}]")

    def _create_model(self, assignment: ModelAssignment):
        """Create a model instance based on assignment.

        Args:
            assignment: Model assignment configuration

        Returns:
            Configured model instance or None if creation fails
        """
        import os

        provider = assignment.provider
        provider_config = self.config.providers.get(provider)

        if not provider_config:
            logger.error(f"Provider {provider} not configured")
            return None

        api_key = os.getenv(provider_config.api_key_env)
        if not api_key:
            logger.error(f"API key not found for {provider}")
            return None

        try:
            if provider == "openai":
                kwargs = {
                    "model": assignment.model,
                    "max_tokens": assignment.max_tokens,
                    "openai_api_key": api_key
                }

                # GPT-5 models only support temperature=1.0 (no other values allowed)
                # For other models, use the configured temperature
                if assignment.model.startswith("gpt-5"):
                    kwargs["temperature"] = 1.0
                else:
                    kwargs["temperature"] = assignment.temperature

                return ChatOpenAI(**kwargs)

            elif provider == "groq":
                return ChatGroq(
                    model=assignment.model,
                    temperature=assignment.temperature,
                    max_tokens=assignment.max_tokens,
                    groq_api_key=api_key
                )

            elif provider == "openrouter":
                # OpenRouter uses the model name directly
                model_name = assignment.model

                # Build provider routing parameter for OpenRouter using extra_body
                # extra_body allows passing custom parameters to OpenRouter's API
                model_kwargs = {}
                if assignment.openrouter_provider:
                    # Capitalize provider name (e.g., "cerebras" -> "Cerebras")
                    provider_name = assignment.openrouter_provider.capitalize()

                    # OpenRouter provider routing via extra_body
                    # This passes custom parameters through to OpenRouter without the OpenAI SDK rejecting them
                    model_kwargs["extra_body"] = {
                        "provider": {
                            "order": [provider_name],
                            "allow_fallbacks": False  # Force only the specified provider
                        }
                    }
                    logger.info(f"OpenRouter configured with provider routing: {provider_name} (order: [{provider_name}], fallbacks: disabled)")

                return ChatOpenAI(
                    model=model_name,
                    temperature=assignment.temperature,
                    max_tokens=assignment.max_tokens,
                    openai_api_key=api_key,
                    base_url=provider_config.base_url or "https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "https://github.com/hephaestus",
                        "X-Title": "Hephaestus Multi-Provider LLM"
                    },
                    model_kwargs=model_kwargs  # extra_body gets passed through to the API
                )

            elif provider == "azure_openai":
                # Azure OpenAI uses deployment names (configured in Azure portal) instead of model names
                # Requires azure_endpoint, api_version, and azure_deployment parameters
                azure_endpoint = provider_config.base_url
                if not azure_endpoint:
                    logger.error(f"Azure OpenAI requires base_url (azure_endpoint) in configuration")
                    return None

                api_version = provider_config.api_version or "2024-02-01"
                logger.info(f"Creating Azure OpenAI model with deployment: {assignment.model}, endpoint: {azure_endpoint}, api_version: {api_version}")

                return AzureChatOpenAI(
                    model=assignment.model,  # This is the deployment name in Azure
                    azure_deployment=assignment.model,
                    api_version=api_version,
                    azure_endpoint=azure_endpoint,
                    api_key=api_key,
                    temperature=assignment.temperature,
                    max_tokens=assignment.max_tokens
                )

            elif provider == "google_ai":
                # Google AI Studio (Gemini) - simpler than Vertex AI, just needs API key
                logger.info(f"Creating Google AI model: {assignment.model}")

                return ChatGoogleGenerativeAI(
                    model=assignment.model,  # e.g., "gemini-2.5-flash", "gemini-1.5-pro"
                    google_api_key=api_key,
                    temperature=assignment.temperature,
                    max_tokens=assignment.max_tokens
                )

            else:
                logger.error(f"Unknown provider: {provider}")
                return None

        except Exception as e:
            logger.error(f"Failed to create model for {provider}: {e}")
            return None

    def _get_model_for_component(self, component: ComponentType):
        """Get the appropriate model for a component.

        Args:
            component: Component type

        Returns:
            Model instance or None
        """
        component_name = component.value
        assignment = self.config.model_assignments.get(component_name)

        if not assignment:
            logger.error(f"No model assignment for component {component_name}")
            return None

        model_key = f"{component_name}_{assignment.provider}_{assignment.model}"
        return self._models.get(model_key)

    async def enrich_task(
        self,
        task_description: str,
        done_definition: str,
        context: List[str],
        phase_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enrich a task with LLM analysis using assigned model.

        Args:
            task_description: Raw task description
            done_definition: What constitutes task completion
            context: Relevant context from memory
            phase_context: Optional phase context

        Returns:
            Dictionary with enriched task information
        """
        assignment = self.config.model_assignments.get('task_enrichment')
        logger.info(f"🔵 [LLM CALL] enrich_task | Provider: {assignment.provider} | Model: {assignment.model}")

        model = self._get_model_for_component(ComponentType.TASK_ENRICHMENT)
        if not model:
            logger.warning("⚠️ [LLM CALL] No model available for task_enrichment, using fallback")
            return self._default_task_enrichment(task_description, done_definition)

        prompt = self._build_task_enrichment_prompt(
            task_description, done_definition, context, phase_context
        )

        messages = [
            SystemMessage(content="You are a task analysis expert for an AI orchestration system."),
            HumanMessage(content=prompt)
        ]

        try:
            response = await model.ainvoke(messages)
            parser = JsonOutputParser()
            result = parser.parse(response.content)

            logger.info(f"✅ [LLM CALL] enrich_task completed | Provider: {assignment.provider} | Model: {assignment.model}")
            return result

        except Exception as e:
            logger.error(f"❌ [LLM CALL] enrich_task failed | Provider: {assignment.provider} | Model: {assignment.model} | Error: {e}")
            return self._default_task_enrichment(task_description, done_definition)

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
        """Use LLM to resolve ticket clarification conflicts.

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
        # Get appropriate model for clarification (reuse task enrichment component)
        model = self._get_model_for_component(ComponentType.TASK_ENRICHMENT)
        if not model:
            logger.error("No model available for ticket clarification")
            return "❌ LLM model not available for clarification. Please check system configuration."

        # Build prompt from template
        prompt = self._build_ticket_clarification_prompt(
            ticket_id=ticket_id,
            conflict_description=conflict_description,
            context=context,
            potential_solutions=potential_solutions,
            ticket_details=ticket_details,
            related_tickets=related_tickets,
            active_tasks=active_tasks
        )

        # Create messages
        messages = [
            SystemMessage(content="You are a ticket clarification arbitrator specialized in resolving conflicts and ambiguities in software development requirements."),
            HumanMessage(content=prompt)
        ]

        try:
            # Invoke model with longer timeout for reasoning
            response = await model.ainvoke(messages)

            logger.info(f"Ticket clarification resolved successfully for {ticket_id} using {self.config.model_assignments['task_enrichment'].model}")
            return response.content

        except Exception as e:
            logger.error(f"Failed to resolve ticket clarification: {e}")
            return f"❌ Failed to generate clarification due to error: {str(e)}\n\nPlease try again or seek manual clarification."

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        logger.debug(f"🔵 [LLM CALL] generate_embedding | Provider: openai | Model: {self.config.embedding_model}")

        if not self._embedding_model:
            logger.error("❌ [LLM CALL] Embedding model not initialized")
            return [0.0] * 1536

        try:
            embedding = await self._embedding_model.aembed_query(text[:8000])
            logger.debug(f"✅ [LLM CALL] generate_embedding completed | Provider: openai | Model: {self.config.embedding_model}")
            return embedding
        except Exception as e:
            logger.error(f"❌ [LLM CALL] generate_embedding failed | Provider: openai | Model: {self.config.embedding_model} | Error: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536

    async def analyze_agent_state(
        self,
        agent_output: str,
        task_info: Dict[str, Any],
        project_context: str,
    ) -> Dict[str, Any]:
        """Analyze agent state for monitoring decisions.

        Args:
            agent_output: Recent output from agent
            task_info: Current task information
            project_context: Project-wide context

        Returns:
            Dictionary with state analysis
        """
        model = self._get_model_for_component(ComponentType.AGENT_MONITORING)
        if not model:
            return self._default_agent_state()

        prompt = self._build_agent_state_prompt(agent_output, task_info, project_context)

        messages = [
            SystemMessage(content="You are an AI agent monitoring expert."),
            HumanMessage(content=prompt)
        ]

        try:
            response = await model.ainvoke(messages)
            parser = JsonOutputParser()
            result = parser.parse(response.content)

            logger.debug(f"Agent state analyzed using {self.config.model_assignments['agent_monitoring'].model}")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze agent state: {e}")
            return self._default_agent_state()

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
        model = self._get_model_for_component(ComponentType.AGENT_PROMPTS)
        if not model:
            return self._default_agent_prompt(task, memories, project_context)

        # For prompt generation, we can directly return the formatted prompt
        # without needing LLM generation
        return self._default_agent_prompt(task, memories, project_context)

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
            accumulated_context: Full accumulated context
            past_summaries: Previous Guardian summaries
            task_info: Current task information
            last_message_marker: Optional marker from previous cycle

        Returns:
            Dictionary with trajectory analysis
        """
        assignment = self.config.model_assignments.get('guardian_analysis')
        logger.info(f"🔵 [LLM CALL] Guardian analyze_agent_trajectory | Provider: {assignment.provider} | Model: {assignment.model}")

        model = self._get_model_for_component(ComponentType.GUARDIAN_ANALYSIS)
        if not model:
            logger.warning("⚠️ [LLM CALL] No model available for guardian_analysis, using fallback")
            return self._default_trajectory_analysis()

        from src.monitoring.prompt_loader import prompt_loader

        prompt = prompt_loader.format_guardian_prompt(
            accumulated_context=accumulated_context,
            past_summaries=past_summaries,
            task_info=task_info,
            agent_output=agent_output,
            last_message_marker=last_message_marker,  # NEW
        )

        messages = [
            SystemMessage(content="You are a trajectory analysis expert using accumulated context thinking."),
            HumanMessage(content=prompt)
        ]

        for attempt in range(3):
            try:
                response = await model.ainvoke(messages)

                # Parse the response as structured output
                parser = JsonOutputParser()
                result = parser.parse(response.content)

                logger.info(f"✅ [LLM CALL] Guardian analyze_agent_trajectory completed | Provider: {assignment.provider} | Model: {assignment.model}")
                return result

            except Exception as e:
                logger.error(f"❌ [LLM CALL] Guardian analyze_agent_trajectory failed (attempt {attempt + 1}/3) | Provider: {assignment.provider} | Model: {assignment.model} | Error: {e}")
                if attempt == 2:
                    logger.warning("⚠️ [LLM CALL] Guardian analyze_agent_trajectory exhausted retries, using fallback")
                    return self._default_trajectory_analysis()
                await asyncio.sleep(1)

    async def analyze_system_coherence(
        self,
        guardian_summaries: List[Dict[str, Any]],
        system_goals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze system-wide coherence.

        Args:
            guardian_summaries: All Guardian analysis results
            system_goals: Overall system goals

        Returns:
            Dictionary with coherence analysis
        """
        assignment = self.config.model_assignments.get('conductor_analysis')
        logger.info(f"🔵 [LLM CALL] Conductor analyze_system_coherence | Provider: {assignment.provider} | Model: {assignment.model}")

        model = self._get_model_for_component(ComponentType.CONDUCTOR_ANALYSIS)
        if not model:
            logger.warning("⚠️ [LLM CALL] No model available for conductor_analysis, using fallback")
            return self._default_coherence_analysis()

        from src.monitoring.prompt_loader import prompt_loader

        prompt = prompt_loader.format_conductor_prompt(
            guardian_summaries=guardian_summaries,
            system_goals=system_goals,
        )

        messages = [
            SystemMessage(content="You are a system orchestration expert analyzing multi-agent coherence."),
            HumanMessage(content=prompt)
        ]

        for attempt in range(3):
            try:
                response = await model.ainvoke(messages)

                # Parse the response as structured output
                parser = JsonOutputParser()
                result = parser.parse(response.content)

                logger.info(f"✅ [LLM CALL] Conductor analyze_system_coherence completed | Provider: {assignment.provider} | Model: {assignment.model}")
                return result

            except Exception as e:
                logger.error(f"❌ [LLM CALL] Conductor analyze_system_coherence failed (attempt {attempt + 1}/3) | Provider: {assignment.provider} | Model: {assignment.model} | Error: {e}")
                if attempt == 2:
                    logger.warning("⚠️ [LLM CALL] Conductor analyze_system_coherence exhausted retries, using fallback")
                    return self._default_coherence_analysis()
                await asyncio.sleep(1)

    def get_model_name(self, component: ComponentType) -> str:
        """Get the name of the model being used for a component.

        Args:
            component: Component type

        Returns:
            Model name or "unknown"
        """
        assignment = self.config.model_assignments.get(component.value)
        if assignment:
            # Return the model name with provider info for clarity
            if assignment.openrouter_provider:
                return f"{assignment.model} (via {assignment.openrouter_provider})"
            return assignment.model
        return "unknown"

    # Helper methods for building prompts
    def _build_task_enrichment_prompt(
        self,
        task_description: str,
        done_definition: str,
        context: List[str],
        phase_context: Optional[str] = None
    ) -> str:
        """Build prompt for task enrichment."""
        prompt = f"""Given this task request, analyze and enrich it with clear specifications.

Task: {task_description}
Done Definition: {done_definition}
Context: {' '.join(context[:10])}"""

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

        return prompt

    def _build_ticket_clarification_prompt(
        self,
        ticket_id: str,
        conflict_description: str,
        context: str,
        potential_solutions: List[str],
        ticket_details: Dict[str, Any],
        related_tickets: List[Dict[str, Any]],
        active_tasks: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for ticket clarification using structured template."""
        from pathlib import Path

        # Load template from src/prompts/ticket_clarification_prompt.md
        template_path = Path(__file__).parent.parent / "prompts" / "ticket_clarification_prompt.md"

        try:
            with open(template_path, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            logger.error(f"Ticket clarification prompt template not found at {template_path}")
            # Fallback to a basic prompt
            return self._build_fallback_clarification_prompt(
                ticket_id, conflict_description, context, potential_solutions, ticket_details
            )

        # Format related tickets (60 most recent)
        tickets_context = "\n".join([
            f"[{t['ticket_id'][:12]}] ({t['status']}) {t['priority']} - {t['title']}\n"
            f"  Type: {t['ticket_type']}\n"
            f"  Description: {t['description'][:150]}..."
            for t in related_tickets[:60]
        ])

        if not tickets_context:
            tickets_context = "No other tickets found in the system."

        # Format active tasks (60 most recent)
        tasks_context = "\n".join([
            f"[{t['id'][:8]}] ({t['status']}) Phase {t.get('phase_id', 'N/A')} - {t['description'][:150]}..."
            for t in active_tasks[:60]
        ])

        if not tasks_context:
            tasks_context = "No active tasks found in the system."

        # Format potential solutions with numbering
        if potential_solutions:
            solutions_text = "\n".join([
                f"{i+1}. {sol}" for i, sol in enumerate(potential_solutions)
            ])
        else:
            solutions_text = "(Agent did not provide potential solutions)"

        # Fill template with all context
        try:
            prompt = template.format(
                ticket_id=ticket_id,
                ticket_title=ticket_details.get('title', 'Unknown'),
                ticket_description=ticket_details.get('description', 'No description provided'),
                ticket_status=ticket_details.get('status', 'unknown'),
                ticket_priority=ticket_details.get('priority', 'unknown'),
                agent_id=ticket_details.get('assigned_agent_id', 'unassigned'),
                conflict_description=conflict_description,
                context=context if context else "(No additional context provided)",
                potential_solutions=solutions_text,
                related_tickets=tickets_context,
                active_tasks=tasks_context
            )
            return prompt
        except Exception as e:
            logger.error(f"Failed to format ticket clarification template: {e}")
            return self._build_fallback_clarification_prompt(
                ticket_id, conflict_description, context, potential_solutions, ticket_details
            )

    def _build_fallback_clarification_prompt(
        self,
        ticket_id: str,
        conflict_description: str,
        context: str,
        potential_solutions: List[str],
        ticket_details: Dict[str, Any]
    ) -> str:
        """Fallback prompt when template is unavailable."""
        solutions_text = "\n".join([f"{i+1}. {sol}" for i, sol in enumerate(potential_solutions)]) if potential_solutions else "No solutions provided"

        return f"""You are a ticket clarification arbitrator. An agent has encountered a conflict or ambiguity in their ticket requirements.

TICKET: {ticket_id}
TITLE: {ticket_details.get('title', 'Unknown')}
DESCRIPTION: {ticket_details.get('description', 'No description')}

CONFLICT DESCRIBED BY AGENT:
{conflict_description}

ADDITIONAL CONTEXT:
{context if context else 'None provided'}

POTENTIAL SOLUTIONS AGENT IS CONSIDERING:
{solutions_text}

Provide a clear, detailed resolution in markdown format that includes:
1. Analysis of the conflict
2. Evaluation of the proposed solutions
3. Your recommended resolution with rationale
4. Specific ticket updates needed
5. Specific file changes needed
6. What the agent should avoid

Be decisive and provide actionable guidance to prevent the agent from creating infinite tasks."""

    def _build_agent_state_prompt(
        self,
        agent_output: str,
        task_info: Dict[str, Any],
        project_context: str
    ) -> str:
        """Build prompt for agent state analysis."""
        return f"""Analyze this AI agent's current state and decide on the appropriate action.

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

    # Default/fallback methods
    def _default_task_enrichment(self, task_description: str, done_definition: str) -> Dict[str, Any]:
        """Default task enrichment when model unavailable."""
        return {
            "enriched_description": task_description,
            "completion_criteria": [done_definition],
            "agent_prompt": f"Complete this task: {task_description}",
            "required_capabilities": ["general"],
            "estimated_complexity": 5,
        }

    def _default_agent_state(self) -> Dict[str, Any]:
        """Default agent state when model unavailable."""
        return {
            "state": "healthy",
            "decision": "continue",
            "message": "",
            "reasoning": "Analysis unavailable, assuming healthy",
            "confidence": 0.3,
        }

    def _default_agent_prompt(
        self,
        task: Dict[str, Any],
        memories: List[Dict[str, Any]],
        project_context: str
    ) -> str:
        """Generate default agent prompt."""
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

    def _default_trajectory_analysis(self) -> Dict[str, Any]:
        """Default trajectory analysis when model unavailable."""
        return {
            "current_phase": "unknown",
            "trajectory_aligned": True,
            "alignment_score": 0.5,
            "alignment_issues": [],
            "needs_steering": False,
            "steering_type": None,
            "steering_recommendation": None,
            "trajectory_summary": "Analysis unavailable"
        }

    def _default_coherence_analysis(self) -> Dict[str, Any]:
        """Default coherence analysis when model unavailable."""
        return {
            "coherence_score": 0.7,
            "duplicates": [],
            "alignment_issues": [],
            "termination_recommendations": [],
            "coordination_needs": [],
            "system_summary": "Analysis unavailable"
        }