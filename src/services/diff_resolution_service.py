"""Service for AI-driven diff resolution.

Instead of automatic newest-file-wins strategy, this service queues diffs
and uses a dedicated AI agent to resolve them in batches.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.core.database import (
    DatabaseManager,
    PendingDiffResolution,
    MergeConflictResolution,
)
from src.core.simple_config import get_config

logger = logging.getLogger(__name__)


class DiffResolutionService:
    """Service for managing AI-driven diff resolution."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the diff resolution service.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.config = get_config()
        self._llm_provider = None
        self._processing_lock = asyncio.Lock()

    @property
    def llm_provider(self):
        """Lazy-load LLM provider to avoid circular imports."""
        if self._llm_provider is None:
            from src.interfaces.llm_interface import get_llm_provider
            self._llm_provider = get_llm_provider()
        return self._llm_provider

    def queue_diff_for_resolution(
        self,
        merge_agent_id: str,
        worktree_agent_id: str,
        file_path: str,
        parent_content: str,
        child_content: str,
        parent_timestamp: Optional[datetime] = None,
        child_timestamp: Optional[datetime] = None,
        diff_context: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> str:
        """Queue a diff for AI resolution.

        Args:
            merge_agent_id: ID of the agent performing the merge
            worktree_agent_id: ID of the agent whose work created the conflict
            file_path: Path to the conflicted file
            parent_content: Content from main/parent branch
            child_content: Content from agent's worktree
            parent_timestamp: When parent version was last modified
            child_timestamp: When child version was last modified
            diff_context: Optional unified diff for context
            session: Optional database session (creates new one if not provided)

        Returns:
            ID of the queued diff resolution
        """
        own_session = session is None
        if own_session:
            session = self.db_manager.get_session()

        try:
            diff_id = str(uuid.uuid4())
            pending_diff = PendingDiffResolution(
                id=diff_id,
                merge_agent_id=merge_agent_id,
                worktree_agent_id=worktree_agent_id,
                file_path=file_path,
                parent_content=parent_content,
                child_content=child_content,
                parent_timestamp=parent_timestamp,
                child_timestamp=child_timestamp,
                diff_context=diff_context,
                status="pending",
            )
            session.add(pending_diff)

            if own_session:
                session.commit()
            else:
                session.flush()

            logger.info(
                f"[DIFF-QUEUE] Queued diff for resolution: {file_path} "
                f"(merge_agent={merge_agent_id}, worktree_agent={worktree_agent_id})"
            )
            return diff_id

        except Exception as e:
            if own_session:
                session.rollback()
            logger.error(f"[DIFF-QUEUE] Failed to queue diff: {e}")
            raise
        finally:
            if own_session:
                session.close()

    def get_pending_diffs(
        self,
        limit: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> List[PendingDiffResolution]:
        """Get pending diffs waiting for resolution.

        Args:
            limit: Maximum number of diffs to return
            session: Optional database session

        Returns:
            List of pending diff resolutions
        """
        own_session = session is None
        if own_session:
            session = self.db_manager.get_session()

        try:
            query = session.query(PendingDiffResolution).filter(
                PendingDiffResolution.status == "pending"
            ).order_by(PendingDiffResolution.created_at)

            if limit:
                query = query.limit(limit)

            return query.all()

        finally:
            if own_session:
                session.close()

    def get_pending_diff_count(self, session: Optional[Session] = None) -> int:
        """Get count of pending diffs.

        Args:
            session: Optional database session

        Returns:
            Number of pending diffs
        """
        own_session = session is None
        if own_session:
            session = self.db_manager.get_session()

        try:
            return session.query(PendingDiffResolution).filter(
                PendingDiffResolution.status == "pending"
            ).count()
        finally:
            if own_session:
                session.close()

    async def resolve_diff_batch(
        self,
        resolver_agent_id: str,
        batch_size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Resolve a batch of pending diffs using AI.

        Args:
            resolver_agent_id: ID of the agent resolving diffs
            batch_size: Number of diffs to resolve (defaults to config)

        Returns:
            List of resolution results
        """
        if batch_size is None:
            batch_size = self.config.diff_resolution_batch_size

        async with self._processing_lock:
            session = self.db_manager.get_session()
            results = []
            batch_id = str(uuid.uuid4())

            try:
                # Get pending diffs
                pending_diffs = session.query(PendingDiffResolution).filter(
                    PendingDiffResolution.status == "pending"
                ).order_by(
                    PendingDiffResolution.created_at
                ).limit(batch_size).all()

                if not pending_diffs:
                    logger.info("[DIFF-RESOLVE] No pending diffs to resolve")
                    return []

                logger.info(
                    f"[DIFF-RESOLVE] Processing batch of {len(pending_diffs)} diffs "
                    f"(batch_id={batch_id})"
                )

                # Mark diffs as processing
                for diff in pending_diffs:
                    diff.status = "processing"
                    diff.batch_id = batch_id
                session.flush()

                # Resolve each diff
                for diff in pending_diffs:
                    try:
                        result = await self._resolve_single_diff(diff, resolver_agent_id, session)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"[DIFF-RESOLVE] Failed to resolve diff {diff.id}: {e}")
                        diff.status = "failed"
                        results.append({
                            "diff_id": diff.id,
                            "file_path": diff.file_path,
                            "status": "failed",
                            "error": str(e),
                        })

                session.commit()
                logger.info(
                    f"[DIFF-RESOLVE] Batch complete: {len([r for r in results if r['status'] == 'resolved'])} resolved, "
                    f"{len([r for r in results if r['status'] == 'failed'])} failed"
                )
                return results

            except Exception as e:
                session.rollback()
                logger.error(f"[DIFF-RESOLVE] Batch processing failed: {e}")
                raise
            finally:
                session.close()

    async def _resolve_single_diff(
        self,
        diff: PendingDiffResolution,
        resolver_agent_id: str,
        session: Session,
    ) -> Dict[str, Any]:
        """Resolve a single diff using AI.

        Args:
            diff: The pending diff to resolve
            resolver_agent_id: ID of the resolver agent
            session: Database session

        Returns:
            Resolution result dictionary
        """
        logger.info(f"[DIFF-RESOLVE] Resolving diff for file: {diff.file_path}")

        # Build the resolution prompt
        prompt = self._build_resolution_prompt(diff)

        # Call the LLM
        resolution = await self._call_llm_for_resolution(prompt)

        # Update the diff record
        diff.status = "resolved"
        diff.resolution_choice = resolution["choice"]
        diff.resolved_content = resolution["content"]
        diff.resolver_agent_id = resolver_agent_id
        diff.resolution_reasoning = resolution["reasoning"]
        diff.resolved_at = datetime.utcnow()

        # Also create a MergeConflictResolution record for compatibility
        conflict_resolution = MergeConflictResolution(
            id=str(uuid.uuid4()),
            agent_id=diff.worktree_agent_id,
            file_path=diff.file_path,
            parent_modified_at=diff.parent_timestamp,
            child_modified_at=diff.child_timestamp,
            resolution_choice=self._map_resolution_choice(resolution["choice"]),
        )
        session.add(conflict_resolution)

        logger.info(
            f"[DIFF-RESOLVE] Resolved {diff.file_path}: choice={resolution['choice']}"
        )

        return {
            "diff_id": diff.id,
            "file_path": diff.file_path,
            "status": "resolved",
            "resolution_choice": resolution["choice"],
            "reasoning": resolution["reasoning"],
        }

    def _build_resolution_prompt(self, diff: PendingDiffResolution) -> str:
        """Build the prompt for AI diff resolution.

        Args:
            diff: The pending diff to resolve

        Returns:
            The prompt string
        """
        parent_time = diff.parent_timestamp.isoformat() if diff.parent_timestamp else "unknown"
        child_time = diff.child_timestamp.isoformat() if diff.child_timestamp else "unknown"

        prompt = f"""You are a code merge conflict resolution expert. Analyze the following conflict and provide a resolution.

## File: {diff.file_path}

## Parent Version (from main branch)
Last modified: {parent_time}

```
{diff.parent_content[:10000]}
```

## Child Version (from agent's work)
Last modified: {child_time}

```
{diff.child_content[:10000]}
```

{"## Diff Context" if diff.diff_context else ""}
{"```diff" if diff.diff_context else ""}
{diff.diff_context[:5000] if diff.diff_context else ""}
{"```" if diff.diff_context else ""}

## Instructions
1. Analyze both versions carefully
2. Consider the timestamps - newer changes may be more relevant
3. Look for:
   - Semantic conflicts (both changed the same logic)
   - Complementary changes (both added different features)
   - Overlapping changes (partially conflicting edits)

4. Choose one of these resolution strategies:
   - "parent": Use the parent version (main branch wins)
   - "child": Use the child version (agent's work wins)
   - "merged": Create a merged version that incorporates both changes

## Response Format
Respond with a JSON object containing:
{{
    "choice": "parent" | "child" | "merged",
    "reasoning": "Brief explanation of why this choice was made",
    "content": "The resolved file content (required if choice is 'merged', optional otherwise)"
}}

Important: If you choose "merged", you MUST provide the complete merged file content.
"""
        return prompt

    async def _call_llm_for_resolution(self, prompt: str) -> Dict[str, Any]:
        """Call the LLM to resolve a diff.

        Args:
            prompt: The resolution prompt

        Returns:
            Resolution dictionary with choice, reasoning, and optionally content
        """
        import json
        import re
        import os

        try:
            # Use the configured temperature for diff resolution
            temperature = self.config.diff_resolution_temperature

            # Get the LLM provider
            from src.interfaces.multi_provider_llm import MultiProviderLLM

            if isinstance(self.llm_provider, MultiProviderLLM):
                # Use the LangChain client directly for custom calls
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import HumanMessage, SystemMessage

                # Get provider config from the LLM config
                llm_config = self.llm_provider.config.get_llm_config()

                # Use OpenRouter for diff resolution (or fallback to default)
                provider = self.config.diff_resolution_provider or "openrouter"
                model = self.config.diff_resolution_model or "openai/gpt-4o-mini"

                # Get API key
                provider_config = llm_config.providers.get(provider)
                if provider_config:
                    api_key = os.getenv(provider_config.api_key_env)
                    base_url = provider_config.base_url
                else:
                    # Fallback to OpenAI
                    api_key = os.getenv("OPENAI_API_KEY")
                    base_url = None

                # Create the chat model
                chat_model = ChatOpenAI(
                    model=model,
                    temperature=temperature,
                    max_tokens=self.config.diff_resolution_max_tokens,
                    openai_api_key=api_key,
                    openai_api_base=base_url,
                )

                messages = [
                    SystemMessage(content="You are a code merge conflict resolution expert. Always respond with valid JSON."),
                    HumanMessage(content=prompt)
                ]

                response = await chat_model.ainvoke(messages)
                content = response.content
            else:
                # Fallback for single provider
                content = await self._call_single_provider(prompt, temperature)

            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*"choice"[^{}]*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Try parsing the whole content as JSON
                # Handle potential markdown code blocks
                clean_content = content
                if "```json" in clean_content:
                    clean_content = clean_content.split("```json")[1].split("```")[0]
                elif "```" in clean_content:
                    clean_content = clean_content.split("```")[1].split("```")[0]
                result = json.loads(clean_content.strip())

            # Validate required fields
            if "choice" not in result:
                raise ValueError("Response missing 'choice' field")
            if result["choice"] not in ["parent", "child", "merged"]:
                raise ValueError(f"Invalid choice: {result['choice']}")
            if result["choice"] == "merged" and "content" not in result:
                raise ValueError("Merged resolution requires 'content' field")

            return {
                "choice": result["choice"],
                "reasoning": result.get("reasoning", "No reasoning provided"),
                "content": result.get("content"),
            }

        except Exception as e:
            logger.error(f"[DIFF-RESOLVE] LLM call failed: {e}")
            # Fallback to child (prefer agent's work)
            return {
                "choice": "child",
                "reasoning": f"LLM resolution failed ({str(e)}), defaulting to agent's version",
                "content": None,
            }

    async def _call_single_provider(self, prompt: str, temperature: float) -> str:
        """Call a single LLM provider for resolution.

        Args:
            prompt: The resolution prompt
            temperature: Temperature setting

        Returns:
            Response content string
        """
        from src.interfaces.llm_interface import OpenAIProvider

        if isinstance(self.llm_provider, OpenAIProvider):
            response = await self.llm_provider.client.chat.completions.create(
                model=self.llm_provider.model,
                messages=[
                    {"role": "system", "content": "You are a code merge conflict resolution expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=self.config.diff_resolution_max_tokens,
            )
            return response.choices[0].message.content
        else:
            # Generic fallback
            raise NotImplementedError("Single provider diff resolution not implemented for this provider")

    def _map_resolution_choice(self, choice: str) -> str:
        """Map AI resolution choice to MergeConflictResolution format.

        Args:
            choice: The AI's resolution choice

        Returns:
            Compatible resolution choice string
        """
        mapping = {
            "parent": "parent",
            "child": "child",
            "merged": "child",  # Merged is treated as child for compatibility
        }
        return mapping.get(choice, "child")

    def get_resolved_content(
        self,
        diff_id: str,
        session: Optional[Session] = None,
    ) -> Optional[Tuple[str, str]]:
        """Get the resolved content for a diff.

        Args:
            diff_id: ID of the diff
            session: Optional database session

        Returns:
            Tuple of (resolution_choice, resolved_content) or None
        """
        own_session = session is None
        if own_session:
            session = self.db_manager.get_session()

        try:
            diff = session.query(PendingDiffResolution).filter(
                PendingDiffResolution.id == diff_id
            ).first()

            if not diff or diff.status != "resolved":
                return None

            # Return the appropriate content based on resolution choice
            if diff.resolution_choice == "parent":
                return (diff.resolution_choice, diff.parent_content)
            elif diff.resolution_choice == "child":
                return (diff.resolution_choice, diff.child_content)
            elif diff.resolution_choice == "merged":
                return (diff.resolution_choice, diff.resolved_content)
            else:
                return None

        finally:
            if own_session:
                session.close()

    def get_diff_status(
        self,
        diff_id: str,
        session: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the status of a diff resolution.

        Args:
            diff_id: ID of the diff
            session: Optional database session

        Returns:
            Status dictionary or None
        """
        own_session = session is None
        if own_session:
            session = self.db_manager.get_session()

        try:
            diff = session.query(PendingDiffResolution).filter(
                PendingDiffResolution.id == diff_id
            ).first()

            if not diff:
                return None

            return {
                "id": diff.id,
                "file_path": diff.file_path,
                "status": diff.status,
                "batch_id": diff.batch_id,
                "resolution_choice": diff.resolution_choice,
                "resolution_reasoning": diff.resolution_reasoning,
                "created_at": diff.created_at.isoformat() if diff.created_at else None,
                "resolved_at": diff.resolved_at.isoformat() if diff.resolved_at else None,
            }

        finally:
            if own_session:
                session.close()

    def get_all_diffs(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100,
        session: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Get all diffs with optional status filter.

        Args:
            status_filter: Optional status to filter by
            limit: Maximum number of results
            session: Optional database session

        Returns:
            List of diff status dictionaries
        """
        own_session = session is None
        if own_session:
            session = self.db_manager.get_session()

        try:
            query = session.query(PendingDiffResolution)
            if status_filter:
                query = query.filter(PendingDiffResolution.status == status_filter)
            query = query.order_by(PendingDiffResolution.created_at.desc()).limit(limit)

            diffs = query.all()
            return [
                {
                    "id": diff.id,
                    "file_path": diff.file_path,
                    "status": diff.status,
                    "batch_id": diff.batch_id,
                    "merge_agent_id": diff.merge_agent_id,
                    "worktree_agent_id": diff.worktree_agent_id,
                    "resolution_choice": diff.resolution_choice,
                    "resolution_reasoning": diff.resolution_reasoning,
                    "created_at": diff.created_at.isoformat() if diff.created_at else None,
                    "resolved_at": diff.resolved_at.isoformat() if diff.resolved_at else None,
                }
                for diff in diffs
            ]

        finally:
            if own_session:
                session.close()


# Singleton instance
_diff_resolution_service: Optional[DiffResolutionService] = None


def get_diff_resolution_service(db_manager: Optional[DatabaseManager] = None) -> DiffResolutionService:
    """Get or create the diff resolution service singleton.

    Args:
        db_manager: Optional database manager (required on first call)

    Returns:
        DiffResolutionService instance
    """
    global _diff_resolution_service
    if _diff_resolution_service is None:
        if db_manager is None:
            from src.core.database import DatabaseManager
            from src.core.simple_config import get_config
            config = get_config()
            db_manager = DatabaseManager(str(config.database_path))
        _diff_resolution_service = DiffResolutionService(db_manager)
    return _diff_resolution_service
