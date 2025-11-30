"""Git worktree isolation manager for agents."""

import os
import shutil
import uuid
import logging
import fcntl
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import git
from git import Repo, GitCommandError
from sqlalchemy.orm import Session

from src.core.database import (
    DatabaseManager,
    AgentWorktree,
    WorktreeCommit,
    MergeConflictResolution,
)
from src.core.simple_config import get_config

logger = logging.getLogger(__name__)


class MergeStatus(Enum):
    """Enum for worktree merge status."""
    ACTIVE = "active"
    MERGED = "merged"
    ABANDONED = "abandoned"
    CLEANED = "cleaned"


class CommitType(Enum):
    """Enum for commit types."""
    PARENT_CHECKPOINT = "parent_checkpoint"
    VALIDATION_READY = "validation_ready"
    FINAL = "final"
    AUTO_SAVE = "auto_save"
    CONFLICT_RESOLUTION = "conflict_resolution"


@dataclass
class WorktreeInfo:
    """Data class for worktree information."""
    agent_id: str
    worktree_path: str
    branch_name: str
    parent_agent_id: Optional[str]
    parent_commit_sha: str
    base_commit_sha: str
    merge_status: MergeStatus
    created_at: str
    merged_at: Optional[str] = None
    merge_commit_sha: Optional[str] = None


@dataclass
class ConflictResolution:
    """Data class for conflict resolution details."""
    agent_id: str
    file_path: str
    parent_timestamp: str
    child_timestamp: str
    resolution_choice: str  # "parent", "child", or "tie_child"
    resolved_at: str
    commit_sha: str


@dataclass
class MergeResult:
    """Data class for merge operation results."""
    status: str  # "success", "conflict_resolved"
    merged_to: str  # branch name
    commit_sha: str
    conflicts_resolved: List[ConflictResolution]
    resolution_strategy: str
    total_conflicts: int
    resolution_time_ms: int


class WorktreeManager:
    """Manager for git worktree isolation."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize worktree manager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.config = get_config()

        # Create base path for worktrees
        self.base_path = self.config.worktree_base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Get main repository
        try:
            self.main_repo = Repo(self.config.main_repo_path)
        except git.InvalidGitRepositoryError:
            logger.error(f"Invalid git repository at {self.config.main_repo_path}")
            raise ValueError(f"Not a git repository: {self.config.main_repo_path}")

        # Create merge lock file path
        self.merge_lock_path = self.base_path / ".merge_lock"

        logger.info(f"WorktreeManager initialized with base path: {self.base_path}")

    def _acquire_merge_lock(self, agent_id: str, timeout: int = 300) -> Any:
        """Acquire exclusive lock for merge operations.

        Args:
            agent_id: Agent ID attempting to acquire lock
            timeout: Maximum seconds to wait for lock

        Returns:
            Lock file handle (must be kept open until release)
        """
        logger.info(f"[GIT-MERGE:{agent_id}] Attempting to acquire merge lock (timeout={timeout}s)")

        # Create lock file if it doesn't exist
        self.merge_lock_path.touch(exist_ok=True)

        lock_file = open(self.merge_lock_path, 'w')
        start_time = time.time()

        while True:
            try:
                # Try to acquire exclusive lock (non-blocking)
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                elapsed = time.time() - start_time
                logger.info(f"[GIT-MERGE:{agent_id}] ✓ Merge lock acquired after {elapsed:.2f}s")
                return lock_file
            except IOError:
                # Lock is held by another process
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    lock_file.close()
                    raise TimeoutError(
                        f"[GIT-MERGE:{agent_id}] Failed to acquire merge lock after {timeout}s"
                    )

                if int(elapsed) % 10 == 0:  # Log every 10 seconds
                    logger.info(
                        f"[GIT-MERGE:{agent_id}] Waiting for merge lock... ({elapsed:.0f}s elapsed)"
                    )
                time.sleep(0.5)

    def _release_merge_lock(self, lock_file: Any, agent_id: str) -> None:
        """Release merge lock.

        Args:
            lock_file: Lock file handle from _acquire_merge_lock
            agent_id: Agent ID releasing the lock
        """
        logger.info(f"[GIT-MERGE:{agent_id}] Releasing merge lock")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            logger.info(f"[GIT-MERGE:{agent_id}] ✓ Merge lock released")
        except Exception as e:
            logger.error(f"[GIT-MERGE:{agent_id}] Error releasing lock: {e}")

    def _complete_stuck_merge(self, agent_id: str, session: Session) -> None:
        """Complete any stuck merge in the main repository.

        This ensures we never lose agent work by completing interrupted merges.

        Args:
            agent_id: Current agent ID (for logging)
            session: Database session for recording resolutions
        """
        merge_head_path = Path(self.main_repo.git_dir) / "MERGE_HEAD"

        if not merge_head_path.exists():
            logger.info(f"[GIT-MERGE:{agent_id}] No stuck merge detected - main repo is clean")
            return

        logger.warning(f"[GIT-MERGE:{agent_id}] ⚠️  STUCK MERGE DETECTED - attempting to complete it")

        try:
            # Read the MERGE_HEAD to see what was being merged
            merge_head_sha = merge_head_path.read_text().strip()
            logger.info(f"[GIT-MERGE:{agent_id}] Stuck merge from commit: {merge_head_sha}")

            # Check current repo status
            logger.info(f"[GIT-MERGE:{agent_id}] Running git status to check repo state")
            status_output = self.main_repo.git.status()
            logger.info(f"[GIT-MERGE:{agent_id}] Git status:\n{status_output}")

            # Get list of unresolved conflicts
            try:
                unresolved_files = self.main_repo.git.diff(
                    "--name-only", "--diff-filter=U"
                ).splitlines()
            except GitCommandError:
                unresolved_files = []

            logger.info(
                f"[GIT-MERGE:{agent_id}] Unresolved conflicts: {len(unresolved_files)} files"
            )

            if unresolved_files:
                logger.warning(
                    f"[GIT-MERGE:{agent_id}] Files with conflicts: {unresolved_files}"
                )

                # We need to resolve these conflicts
                # We'll use newest-wins strategy
                logger.info(
                    f"[GIT-MERGE:{agent_id}] Resolving conflicts using newest_file_wins strategy"
                )

                for file_path in unresolved_files:
                    logger.info(f"[GIT-MERGE:{agent_id}] Resolving conflict in: {file_path}")

                    # Get timestamps
                    parent_timestamp = self._get_file_timestamp(self.main_repo, file_path, "HEAD")
                    child_timestamp = self._get_file_timestamp(self.main_repo, file_path, "MERGE_HEAD")

                    logger.info(
                        f"[GIT-MERGE:{agent_id}]   Parent timestamp: {parent_timestamp}"
                    )
                    logger.info(
                        f"[GIT-MERGE:{agent_id}]   Child timestamp: {child_timestamp}"
                    )

                    # Default to current time if timestamp not found
                    if parent_timestamp is None:
                        parent_timestamp = datetime.utcnow()
                    if child_timestamp is None:
                        child_timestamp = datetime.utcnow()

                    # Determine which version to use
                    # NUCLEAR OPTION: Remove from index, get content, re-add fresh
                    if child_timestamp > parent_timestamp:
                        resolution_choice = "child"
                        ref_to_use = "MERGE_HEAD"
                        logger.info(f"[GIT-MERGE:{agent_id}]   → Using CHILD version (newer)")
                    elif parent_timestamp > child_timestamp:
                        resolution_choice = "parent"
                        ref_to_use = "HEAD"
                        logger.info(f"[GIT-MERGE:{agent_id}]   → Using PARENT version (newer)")
                    else:
                        resolution_choice = "tie_child"
                        ref_to_use = "MERGE_HEAD"
                        logger.info(f"[GIT-MERGE:{agent_id}]   → Timestamps equal, using CHILD version (tiebreaker)")

                    # Nuclear conflict resolution: completely rebuild index entry
                    logger.info(f"[GIT-MERGE:{agent_id}]   Step 1: Removing {file_path} from index entirely")
                    try:
                        self.main_repo.git.rm("--cached", "-f", file_path)
                    except GitCommandError as e:
                        logger.warning(f"[GIT-MERGE:{agent_id}]   Warning on git rm: {e}")

                    logger.info(f"[GIT-MERGE:{agent_id}]   Step 2: Getting content from {ref_to_use}")
                    content = self._get_file_content(self.main_repo, file_path, ref_to_use)

                    logger.info(f"[GIT-MERGE:{agent_id}]   Step 3: Writing content to working directory")
                    self._write_file_content(self.main_repo.working_dir, file_path, content)

                    logger.info(f"[GIT-MERGE:{agent_id}]   Step 4: Adding file fresh to index")
                    self.main_repo.git.add(file_path)

                    # Record resolution in database
                    resolution_record = MergeConflictResolution(
                        id=str(uuid.uuid4()),
                        agent_id="STUCK_MERGE_RECOVERY",
                        file_path=file_path,
                        parent_modified_at=parent_timestamp,
                        child_modified_at=child_timestamp,
                        resolution_choice=resolution_choice
                    )
                    session.add(resolution_record)

                logger.info(f"[GIT-MERGE:{agent_id}] All conflicts resolved, committing")

            else:
                logger.info(
                    f"[GIT-MERGE:{agent_id}] No unresolved conflicts - files already staged"
                )

            # Verify all conflicts are actually resolved in the index
            logger.info(f"[GIT-MERGE:{agent_id}] Verifying all conflicts are cleared from index")
            try:
                still_unresolved = self.main_repo.git.diff("--name-only", "--diff-filter=U").splitlines()
                if still_unresolved:
                    logger.error(
                        f"[GIT-MERGE:{agent_id}] ✗ Still have unresolved conflicts: {still_unresolved}"
                    )
                    # Force add all conflicted files again
                    for file_path in still_unresolved:
                        logger.info(f"[GIT-MERGE:{agent_id}] Force re-adding: {file_path}")
                        self.main_repo.git.add(file_path, force=True)
                else:
                    logger.info(f"[GIT-MERGE:{agent_id}] ✓ All conflicts cleared from index")
            except GitCommandError:
                logger.info(f"[GIT-MERGE:{agent_id}] ✓ No conflicts in index")

            # Commit the merge completion
            logger.info(f"[GIT-MERGE:{agent_id}] Committing stuck merge completion")
            commit_msg = f"[Auto-Recovery] Completed stuck merge from {merge_head_sha[:8]}"
            # Use --no-verify to skip hooks for automated merge recovery
            self.main_repo.git.commit("-m", commit_msg, "--no-verify")

            completed_sha = self.main_repo.head.commit.hexsha
            logger.info(
                f"[GIT-MERGE:{agent_id}] ✓ Stuck merge completed successfully: {completed_sha}"
            )

            # Flush database changes
            session.flush()

        except Exception as e:
            logger.error(
                f"[GIT-MERGE:{agent_id}] ✗ Failed to complete stuck merge: {e}",
                exc_info=True
            )
            raise

    def create_agent_worktree(
        self,
        agent_id: str,
        parent_agent_id: Optional[str] = None,
        base_commit_sha: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create isolated worktree for agent (transparent to agent).

        Args:
            agent_id: Unique agent identifier
            parent_agent_id: Optional parent agent for inheritance
            base_commit_sha: Optional specific commit to create worktree from

        Returns:
            Dict containing working_directory (only field agent sees),
            branch_name, and parent_commit (hidden from agent)
        """
        logger.info(f"[WORKTREE] ========== CREATE_AGENT_WORKTREE START ==========")
        logger.info(f"[WORKTREE] Agent ID: {agent_id}")
        logger.info(f"[WORKTREE] Parent Agent ID: {parent_agent_id}")
        logger.info(f"[WORKTREE] Base Commit SHA: {base_commit_sha}")

        session = self.db_manager.get_session()
        try:
            # Determine which commit to use
            parent_commit_sha = None
            if base_commit_sha:
                # Use specified commit (for validators)
                parent_commit_sha = base_commit_sha
                logger.info(f"[WORKTREE] Using specified base commit {base_commit_sha} for agent {agent_id}")
            elif parent_agent_id:
                # Use parent's latest commit
                logger.info(f"[WORKTREE] Parent agent specified, calling _prepare_parent_commit")
                parent_commit_sha = self._prepare_parent_commit(parent_agent_id, session)
                if not parent_commit_sha:
                    logger.warning(f"[WORKTREE] Parent agent {parent_agent_id} has no commits, falling back to main")
                    parent_commit_sha = self.main_repo.head.commit.hexsha
                    logger.info(f"[WORKTREE] Using main branch HEAD: {parent_commit_sha}")
                else:
                    logger.info(f"[WORKTREE] Got parent commit SHA from _prepare_parent_commit: {parent_commit_sha}")
            else:
                # No parent or base commit, use main branch HEAD
                parent_commit_sha = self.main_repo.head.commit.hexsha
                logger.info(f"[WORKTREE] No parent or base commit, using main HEAD: {parent_commit_sha}")

            # Create branch name
            branch_name = f"{self.config.worktree_branch_prefix}{agent_id}"
            logger.info(f"[WORKTREE] Branch name will be: {branch_name}")

            # Create worktree path
            worktree_path = self.base_path / f"wt_{agent_id}"
            worktree_path_str = str(worktree_path)
            logger.info(f"[WORKTREE] Worktree path will be: {worktree_path_str}")

            # Create branch from parent commit using git command directly
            # This avoids GitPython's cached object state issues when the commit
            # was created by another Repo instance (e.g., in a parent worktree)
            logger.info(f"[WORKTREE] Creating branch {branch_name} from commit {parent_commit_sha}")
            logger.info(f"[WORKTREE] Main repo working dir: {self.main_repo.working_dir}")
            logger.info(f"[WORKTREE] Main repo git dir: {self.main_repo.git_dir}")

            # Verify commit exists before creating branch
            try:
                commit_type = self.main_repo.git.cat_file("-t", parent_commit_sha)
                logger.info(f"[WORKTREE] Verified commit exists, type: {commit_type}")
            except GitCommandError as e:
                logger.error(f"[WORKTREE] Commit {parent_commit_sha} not found in main repo: {e}")
                raise ValueError(f"Commit {parent_commit_sha} not found in repository")

            try:
                # Use git command directly to create branch
                self.main_repo.git.branch(branch_name, parent_commit_sha)
                logger.info(f"[WORKTREE] Branch created successfully")
            except GitCommandError as e:
                if "already exists" in str(e):
                    logger.info(f"[WORKTREE] Branch already exists, deleting and recreating")
                    # Branch exists, delete and recreate
                    self.main_repo.git.branch("-D", branch_name)
                    self.main_repo.git.branch(branch_name, parent_commit_sha)
                    logger.info(f"[WORKTREE] Branch recreated successfully")
                else:
                    logger.error(f"[WORKTREE] Failed to create branch: {e}")
                    raise

            # Create git worktree
            logger.info(f"[WORKTREE] Creating git worktree at {worktree_path_str} for branch {branch_name}")
            try:
                self.main_repo.git.worktree("add", worktree_path_str, branch_name)
                logger.info(f"[WORKTREE] Git worktree created successfully")
            except GitCommandError as e:
                if "already exists" in str(e):
                    logger.info(f"[WORKTREE] Worktree already exists, cleaning up and recreating")
                    # Worktree exists, remove and recreate
                    self._cleanup_worktree(worktree_path_str)
                    self.main_repo.git.worktree("add", worktree_path_str, branch_name)
                    logger.info(f"[WORKTREE] Worktree recreated successfully")
                else:
                    logger.error(f"[WORKTREE] Failed to create worktree: {e}")
                    raise

            # Verify the worktree was created correctly
            if worktree_path.exists():
                logger.info(f"[WORKTREE] Worktree directory exists, checking contents")
                # Open the worktree repo to check its status
                worktree_repo = Repo(worktree_path_str)
                logger.info(f"[WORKTREE] New worktree status:")
                logger.info(f"  - HEAD commit: {worktree_repo.head.commit.hexsha}")

                # Check if HEAD is detached (GitPython raises TypeError, not returns None)
                try:
                    branch_name = worktree_repo.active_branch.name
                    logger.info(f"  - Branch: {branch_name}")
                except TypeError:
                    logger.info(f"  - Branch: DETACHED HEAD")

                # List first few files
                import os
                all_files = []
                for root, dirs, files in os.walk(worktree_path_str):
                    # Skip .git directory
                    if '.git' in root:
                        continue
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), worktree_path_str)
                        all_files.append(rel_path)
                    if len(all_files) > 20:  # Limit to first 20 files
                        break

                logger.info(f"  - Total files in worktree: {len(all_files)}")
                logger.info(f"  - Sample files: {all_files[:10]}{'...' if len(all_files) > 10 else ''}")
            else:
                logger.error(f"[WORKTREE] Worktree directory does not exist after creation!")

            # Record in database
            logger.info(f"[WORKTREE] Recording worktree in database")
            worktree_record = AgentWorktree(
                agent_id=agent_id,
                worktree_path=worktree_path_str,
                branch_name=branch_name,
                parent_agent_id=parent_agent_id,
                parent_commit_sha=parent_commit_sha,
                base_commit_sha=parent_commit_sha,  # Initially same as parent
                merge_status="active"
            )
            session.add(worktree_record)
            session.commit()

            logger.info(f"[WORKTREE] ========== CREATE_AGENT_WORKTREE COMPLETE ==========")

            # Return only what agent needs to see
            return {
                "working_directory": worktree_path_str,  # Only field agent sees
                "branch_name": branch_name,              # Hidden from agent
                "parent_commit": parent_commit_sha       # Hidden from agent
            }

        except Exception as e:
            logger.error(f"Failed to create worktree for agent {agent_id}: {e}")
            session.rollback()
            # Cleanup on failure
            if 'worktree_path_str' in locals():
                self._cleanup_worktree(worktree_path_str)
            raise
        finally:
            session.close()

    def merge_main_into_branch(
        self,
        agent_id: str,
        worktree_path: str,
        branch_name: str
    ) -> Dict[str, Any]:
        """Merge main branch into agent's branch to keep it up-to-date.

        This is called every time an agent starts (including restarts) to ensure
        the agent has the latest changes from main before beginning work.

        Uses the existing "newest file wins" conflict resolution strategy.

        Args:
            agent_id: Agent identifier
            worktree_path: Path to the agent's worktree
            branch_name: Name of the agent's branch

        Returns:
            Dictionary with merge result details
        """
        logger.info(f"[MAIN-MERGE:{agent_id}] ========== MERGE MAIN INTO BRANCH START ==========")
        logger.info(f"[MAIN-MERGE:{agent_id}] Worktree path: {worktree_path}")
        logger.info(f"[MAIN-MERGE:{agent_id}] Branch name: {branch_name}")

        start_time = datetime.utcnow()
        session = self.db_manager.get_session()

        try:
            # Open the worktree repository
            logger.info(f"[MAIN-MERGE:{agent_id}] Opening worktree repository")
            worktree_repo = Repo(worktree_path)

            logger.info(f"[MAIN-MERGE:{agent_id}] Current HEAD: {worktree_repo.head.commit.hexsha}")
            logger.info(f"[MAIN-MERGE:{agent_id}] Current branch: {branch_name}")

            # Get base branch/commit reference from config
            base_ref = self.config.base_branch
            logger.info(f"[MAIN-MERGE:{agent_id}] Base reference: {base_ref}")

            # Try to resolve base_ref - could be branch name or commit SHA
            try:
                # First try as a branch name
                if hasattr(self.main_repo.heads, base_ref):
                    base_commit = self.main_repo.heads[base_ref].commit.hexsha
                    logger.info(f"[MAIN-MERGE:{agent_id}] Resolved '{base_ref}' as branch, commit: {base_commit}")
                else:
                    # Try as commit SHA
                    base_commit = self.main_repo.commit(base_ref).hexsha
                    logger.info(f"[MAIN-MERGE:{agent_id}] Resolved '{base_ref}' as commit SHA: {base_commit}")
            except Exception as e:
                logger.error(f"[MAIN-MERGE:{agent_id}] Failed to resolve base reference '{base_ref}': {e}")
                raise ValueError(f"Invalid base_branch reference: {base_ref}")

            # Check if branch is already up-to-date
            if worktree_repo.head.commit.hexsha == base_commit:
                logger.info(f"[MAIN-MERGE:{agent_id}] Branch is already up-to-date with {base_ref}")
                return {
                    "status": "up_to_date",
                    "merge_commit_sha": worktree_repo.head.commit.hexsha,
                    "conflicts_resolved": [],
                    "total_conflicts": 0,
                    "message": f"Branch already up-to-date with {base_ref}"
                }

            # Attempt to merge base into the current branch
            logger.info(f"[MAIN-MERGE:{agent_id}] Attempting to merge {base_ref} into {branch_name}")

            conflicts_resolved = []
            merge_commit_sha = None

            try:
                # Merge base into current branch (use commit SHA for reliability)
                merge_result = worktree_repo.git.merge(
                    base_commit,
                    no_ff=True,
                    m=f"[Auto-Merge] Merged {base_ref} into {branch_name} for agent {agent_id}"
                )

                # Merge succeeded without conflicts
                merge_commit_sha = worktree_repo.head.commit.hexsha
                status = "success"

                logger.info(f"[MAIN-MERGE:{agent_id}] ✓ Merge completed successfully (no conflicts)")
                logger.info(f"[MAIN-MERGE:{agent_id}] Merge commit: {merge_commit_sha}")

            except GitCommandError as e:
                logger.warning(f"[MAIN-MERGE:{agent_id}] Merge resulted in error: {str(e)[:200]}")

                if "CONFLICT" in str(e):
                    # Conflicts detected - resolve automatically
                    logger.info(f"[MAIN-MERGE:{agent_id}] Conflicts detected - resolving using newest_file_wins")

                    # Use existing conflict resolution logic
                    conflicts_resolved = self._resolve_conflicts_newest_wins(
                        worktree_repo,  # Target repo (where we're merging into)
                        self.main_repo,  # Source repo (main branch)
                        agent_id,
                        session
                    )

                    logger.info(f"[MAIN-MERGE:{agent_id}] ✓ Resolved {len(conflicts_resolved)} conflicts")

                    # Commit the resolution
                    logger.info(f"[MAIN-MERGE:{agent_id}] Committing conflict resolution")
                    # Use --no-verify to skip hooks for automated conflict resolution
                    worktree_repo.git.commit(
                        "-m", f"[Auto-Merge] Resolved conflicts merging main into {branch_name}",
                        "--no-verify"
                    )
                    merge_commit_sha = worktree_repo.head.commit.hexsha
                    status = "conflict_resolved"

                    logger.info(f"[MAIN-MERGE:{agent_id}] ✓ Resolution committed: {merge_commit_sha}")
                else:
                    # Non-conflict error
                    logger.error(f"[MAIN-MERGE:{agent_id}] Merge failed with non-conflict error")
                    raise

            # Calculate resolution time
            resolution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            logger.info(f"[MAIN-MERGE:{agent_id}] ========== MAIN MERGE COMPLETE ==========")
            logger.info(f"[MAIN-MERGE:{agent_id}] Summary:")
            logger.info(f"[MAIN-MERGE:{agent_id}]   - Status: {status}")
            logger.info(f"[MAIN-MERGE:{agent_id}]   - Merge commit: {merge_commit_sha}")
            logger.info(f"[MAIN-MERGE:{agent_id}]   - Conflicts resolved: {len(conflicts_resolved)}")
            logger.info(f"[MAIN-MERGE:{agent_id}]   - Total time: {resolution_time_ms}ms")

            session.close()

            return {
                "status": status,
                "merge_commit_sha": merge_commit_sha,
                "conflicts_resolved": conflicts_resolved,
                "total_conflicts": len(conflicts_resolved),
                "resolution_time_ms": resolution_time_ms,
                "message": f"Successfully merged main into {branch_name}"
            }

        except Exception as e:
            logger.error(
                f"[MAIN-MERGE:{agent_id}] ========== MAIN MERGE FAILED ==========",
                exc_info=True
            )
            logger.error(f"[MAIN-MERGE:{agent_id}] Error: {e}")
            session.close()
            raise

    def commit_for_validation(
        self,
        agent_id: str,
        iteration: int,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create checkpoint commit for validation examination.

        Args:
            agent_id: Agent identifier
            iteration: Validation attempt number
            message: Optional custom commit message

        Returns:
            Dict with commit_sha, files_changed, and message
        """
        logger.info(f"Creating validation commit for agent {agent_id}, iteration {iteration}")

        session = self.db_manager.get_session()
        try:
            # Get worktree info
            worktree = session.query(AgentWorktree).filter_by(
                agent_id=agent_id
            ).first()

            if not worktree:
                raise ValueError(f"No worktree found for agent {agent_id}")

            # Open worktree repository
            worktree_repo = Repo(worktree.worktree_path)

            # Add all changes
            worktree_repo.git.add("-A")

            # Check if there are changes to commit
            if not worktree_repo.is_dirty() and not worktree_repo.untracked_files:
                logger.info(f"No changes to commit for agent {agent_id}")
                return {
                    "commit_sha": worktree_repo.head.commit.hexsha,
                    "files_changed": 0,
                    "message": "No changes"
                }

            # Create commit message
            if message:
                commit_message = f"[Agent {agent_id}] {message}"
            else:
                commit_message = f"[Agent {agent_id}] Iteration {iteration} - Ready for validation"

            # Commit changes
            # Use --no-verify to skip hooks for automated validation checkpoint
            worktree_repo.git.commit("-m", commit_message, "--no-verify")
            commit = worktree_repo.head.commit

            # Get commit stats
            stats = commit.stats.total

            # Record commit in database
            commit_record = WorktreeCommit(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                commit_sha=commit.hexsha,
                commit_type="validation_ready",
                commit_message=commit_message,
                files_changed=stats['files'],
                insertions=stats['insertions'],
                deletions=stats['deletions']
            )
            session.add(commit_record)
            session.commit()

            logger.info(f"Created validation commit {commit.hexsha} for agent {agent_id}")

            return {
                "commit_sha": commit.hexsha,
                "files_changed": stats['files'],
                "message": commit_message
            }

        except Exception as e:
            logger.error(f"Failed to create validation commit: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def merge_to_parent(self, agent_id: str) -> Dict[str, Any]:
        """Merge agent work with automatic newest-file conflict resolution.

        Args:
            agent_id: Agent identifier

        Returns:
            Dict with merge status and details
        """
        logger.info(f"[GIT-MERGE:{agent_id}] ========== MERGE TO PARENT START ==========")

        session = self.db_manager.get_session()
        start_time = datetime.utcnow()
        lock_file = None
        main_repo_stashed = False  # Track if we stashed changes in main repo

        try:
            # ========== STEP 1: ACQUIRE MERGE LOCK ==========
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 1: Acquiring exclusive merge lock")
            lock_file = self._acquire_merge_lock(agent_id)

            # ========== STEP 2: GET WORKTREE INFO ==========
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 2: Fetching worktree info from database")
            worktree = session.query(AgentWorktree).filter_by(
                agent_id=agent_id
            ).first()

            if not worktree:
                raise ValueError(f"[GIT-MERGE:{agent_id}] No worktree found for agent")

            logger.info(f"[GIT-MERGE:{agent_id}] Worktree info:")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Path: {worktree.worktree_path}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Branch: {worktree.branch_name}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Parent commit: {worktree.parent_commit_sha}")

            # ========== STEP 3: COMPLETE ANY STUCK MERGES ==========
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 3: Checking for stuck merges in main repo")
            self._complete_stuck_merge(agent_id, session)

            # ========== STEP 4: SET TARGET BRANCH ==========
            target_branch = self.config.base_branch
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 4: Target branch/commit set to '{target_branch}'")

            # ========== STEP 5: OPEN WORKTREE REPO ==========
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 5: Opening worktree repository")
            worktree_repo = Repo(worktree.worktree_path)

            logger.info(f"[GIT-MERGE:{agent_id}] Worktree repo status:")
            logger.info(f"[GIT-MERGE:{agent_id}]   - HEAD: {worktree_repo.head.commit.hexsha}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Is dirty: {worktree_repo.is_dirty()}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Untracked files: {len(worktree_repo.untracked_files)}")

            # ========== STEP 6: COMMIT UNCOMMITTED CHANGES ==========
            if worktree_repo.is_dirty() or worktree_repo.untracked_files:
                logger.info(f"[GIT-MERGE:{agent_id}] STEP 6: Committing uncommitted changes in worktree")
                logger.info(f"[GIT-MERGE:{agent_id}]   Running 'git add -A'")
                worktree_repo.git.add("-A")

                logger.info(f"[GIT-MERGE:{agent_id}]   Creating final commit")
                # Use --no-verify to skip hooks for automated final commit
                worktree_repo.git.commit(
                    "-m", f"[Agent {agent_id}] Final - Task completed",
                    "--no-verify"
                )
                final_commit = worktree_repo.head.commit

                logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Final commit created: {final_commit.hexsha}")
                logger.info(f"[GIT-MERGE:{agent_id}]     Files changed: {final_commit.stats.total['files']}")

                # Record final commit
                commit_record = WorktreeCommit(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    commit_sha=final_commit.hexsha,
                    commit_type="final",
                    commit_message=f"[Agent {agent_id}] Final - Task completed",
                    files_changed=final_commit.stats.total['files']
                )
                session.add(commit_record)
                logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Final commit recorded in database")
            else:
                logger.info(f"[GIT-MERGE:{agent_id}] STEP 6: No uncommitted changes to commit")

            # Initialize merge tracking
            conflicts_resolved = []
            merge_commit_sha = None

            # ========== STEP 7: STASH & CHECKOUT TARGET BRANCH ==========
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 7: Checking out '{target_branch}' in main repo")
            logger.info(f"[GIT-MERGE:{agent_id}]   Main repo current HEAD: {self.main_repo.head.commit.hexsha}")

            # Check if main repo has uncommitted changes that would block the merge
            if self.main_repo.is_dirty() or self.main_repo.untracked_files:
                logger.warning(f"[GIT-MERGE:{agent_id}]   ⚠️  Main repo has uncommitted changes, stashing them")
                modified_files = [item.a_path for item in self.main_repo.index.diff(None)]
                untracked_files = self.main_repo.untracked_files
                logger.info(f"[GIT-MERGE:{agent_id}]   Modified files: {modified_files}")
                logger.info(f"[GIT-MERGE:{agent_id}]   Untracked files: {untracked_files}")

                # Stash including untracked files
                try:
                    self.main_repo.git.stash("push", "-u", "-m", f"Auto-stash before merge for agent {agent_id}")
                    main_repo_stashed = True
                    logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Changes stashed successfully")
                except GitCommandError as e:
                    logger.warning(f"[GIT-MERGE:{agent_id}]   Stash failed (may be nothing to stash): {e}")

            self.main_repo.heads[target_branch].checkout()

            logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Checked out '{target_branch}'")
            logger.info(f"[GIT-MERGE:{agent_id}]   New HEAD: {self.main_repo.head.commit.hexsha}")
            target_repo = self.main_repo

            # ========== STEP 8: ATTEMPT MERGE ==========
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 8: Attempting to merge '{worktree.branch_name}' into '{target_branch}'")
            logger.info(f"[GIT-MERGE:{agent_id}]   Merge command: git merge --no-ff {worktree.branch_name}")

            try:
                merge_result = target_repo.git.merge(
                    worktree.branch_name,
                    no_ff=True,
                    m=f"Merge agent {agent_id} work into {target_branch}"
                )

                # Merge succeeded without conflicts
                merge_commit_sha = target_repo.head.commit.hexsha
                status = "success"

                logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Merge completed successfully (no conflicts)")
                logger.info(f"[GIT-MERGE:{agent_id}]   Merge commit: {merge_commit_sha}")

            except GitCommandError as e:
                logger.warning(f"[GIT-MERGE:{agent_id}]   ⚠️  Merge resulted in error: {str(e)[:200]}")

                if "CONFLICT" in str(e):
                    # ========== STEP 9: RESOLVE CONFLICTS ==========
                    logger.info(f"[GIT-MERGE:{agent_id}] STEP 9: Conflicts detected - resolving automatically")
                    logger.info(f"[GIT-MERGE:{agent_id}]   Strategy: {self.config.conflict_resolution_strategy}")

                    conflicts_resolved = self._resolve_conflicts_newest_wins(
                        target_repo,
                        worktree_repo,
                        agent_id,
                        session
                    )

                    logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Resolved {len(conflicts_resolved)} conflicts")

                    # Commit resolution
                    logger.info(f"[GIT-MERGE:{agent_id}]   Committing conflict resolution")
                    # Use --no-verify to skip hooks for automated conflict resolution
                    target_repo.git.commit(
                        "-m", f"[Auto-Merge] Resolved conflicts using {self.config.conflict_resolution_strategy}",
                        "--no-verify"
                    )
                    merge_commit_sha = target_repo.head.commit.hexsha
                    status = "conflict_resolved"

                    logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Resolution committed: {merge_commit_sha}")
                else:
                    logger.error(f"[GIT-MERGE:{agent_id}]   ✗ Merge failed with non-conflict error")
                    raise

            # ========== STEP 10: UPDATE DATABASE ==========
            logger.info(f"[GIT-MERGE:{agent_id}] STEP 10: Updating database with merge results")
            worktree.merge_status = "merged"
            worktree.merged_at = datetime.utcnow()
            worktree.merge_commit_sha = merge_commit_sha

            session.commit()
            logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Database updated")

            # Calculate resolution time
            resolution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # ========== STEP 11: RESTORE STASHED CHANGES ==========
            if main_repo_stashed:
                logger.info(f"[GIT-MERGE:{agent_id}] STEP 11: Restoring stashed changes in main repo")
                try:
                    self.main_repo.git.stash("pop")
                    logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Stashed changes restored successfully")
                except GitCommandError as e:
                    # Stash pop might have conflicts - log but don't fail the merge
                    logger.warning(f"[GIT-MERGE:{agent_id}]   ⚠️  Stash pop had issues (may need manual resolution): {e}")

            logger.info(f"[GIT-MERGE:{agent_id}] ========== MERGE COMPLETED SUCCESSFULLY ==========")
            logger.info(f"[GIT-MERGE:{agent_id}] Summary:")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Status: {status}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Merged to: {target_branch}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Commit SHA: {merge_commit_sha}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Conflicts resolved: {len(conflicts_resolved)}")
            logger.info(f"[GIT-MERGE:{agent_id}]   - Total time: {resolution_time_ms}ms")

            return {
                "status": status,
                "merged_to": target_branch,
                "commit_sha": merge_commit_sha,
                "conflicts_resolved": conflicts_resolved,
                "resolution_strategy": self.config.conflict_resolution_strategy,
                "total_conflicts": len(conflicts_resolved),
                "resolution_time_ms": resolution_time_ms
            }

        except Exception as e:
            logger.error(
                f"[GIT-MERGE:{agent_id}] ========== MERGE FAILED ==========",
                exc_info=True
            )
            logger.error(f"[GIT-MERGE:{agent_id}] Error: {e}")
            session.rollback()

            # Restore stashed changes even on failure
            if main_repo_stashed:
                logger.info(f"[GIT-MERGE:{agent_id}] Restoring stashed changes after merge failure")
                try:
                    self.main_repo.git.stash("pop")
                    logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Stashed changes restored")
                except GitCommandError as stash_err:
                    logger.warning(f"[GIT-MERGE:{agent_id}]   ⚠️  Could not restore stash: {stash_err}")

            raise
        finally:
            # ========== CLEANUP: RELEASE LOCK ==========
            if lock_file:
                self._release_merge_lock(lock_file, agent_id)
            session.close()
            logger.info(f"[GIT-MERGE:{agent_id}] ========== MERGE OPERATION END ==========")


    def get_workspace_changes(
        self,
        agent_id: str,
        since_commit: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get diff for validator to examine.

        Args:
            agent_id: Agent identifier
            since_commit: Commit SHA to diff from (defaults to parent commit)

        Returns:
            Dict with file changes and diff details
        """
        logger.debug(f"Getting workspace changes for agent {agent_id}")

        session = self.db_manager.get_session()
        try:
            # Get worktree info
            worktree = session.query(AgentWorktree).filter_by(
                agent_id=agent_id
            ).first()

            if not worktree:
                raise ValueError(f"No worktree found for agent {agent_id}")

            # Open worktree repository
            worktree_repo = Repo(worktree.worktree_path)

            # Determine base commit for comparison
            base_commit = since_commit or worktree.parent_commit_sha

            # Get current HEAD commit
            current_commit = worktree_repo.head.commit

            # Get diff between base and current
            # Note: Order matters - we want to see what changed FROM base TO current
            diff_index = worktree_repo.commit(base_commit).diff(current_commit)

            # Categorize changes
            files_created = []
            files_modified = []
            files_deleted = []

            for diff_item in diff_index:
                if diff_item.new_file:
                    files_created.append(diff_item.b_path)
                elif diff_item.deleted_file:
                    files_deleted.append(diff_item.a_path)
                elif diff_item.renamed_file:
                    files_deleted.append(diff_item.a_path)
                    files_created.append(diff_item.b_path)
                else:
                    files_modified.append(diff_item.b_path or diff_item.a_path)

            # Get detailed diff output
            detailed_diff = worktree_repo.git.diff(base_commit, current_commit.hexsha)

            # Get stats from diff
            try:
                # Get stats for the diff
                diff_stats = worktree_repo.git.diff(base_commit, current_commit.hexsha, '--stat')
                # Parse insertions/deletions from stat output
                insertions = 0
                deletions = 0
                for line in diff_stats.split('\n'):
                    if 'insertion' in line or 'deletion' in line:
                        parts = line.split(',')
                        for part in parts:
                            if 'insertion' in part:
                                insertions = int(part.strip().split()[0])
                            elif 'deletion' in part:
                                deletions = int(part.strip().split()[0])
            except:
                insertions = 0
                deletions = 0

            return {
                "files_created": files_created,
                "files_modified": files_modified,
                "files_deleted": files_deleted,
                "total_changes": len(files_created) + len(files_modified) + len(files_deleted),
                "stats": {
                    "insertions": insertions,
                    "deletions": deletions
                },
                "detailed_diff": detailed_diff
            }

        except Exception as e:
            logger.error(f"Failed to get workspace changes: {e}")
            raise
        finally:
            session.close()

    def cleanup_worktree(self, agent_id: str) -> Dict[str, Any]:
        """Remove worktree after agent completion.

        Args:
            agent_id: Agent identifier

        Returns:
            Dict with cleanup status
        """
        logger.info(f"Cleaning up worktree for agent {agent_id}")

        session = self.db_manager.get_session()
        try:
            # Get worktree info
            worktree = session.query(AgentWorktree).filter_by(
                agent_id=agent_id
            ).first()

            if not worktree:
                logger.warning(f"No worktree found for agent {agent_id}")
                return {
                    "status": "not_found",
                    "branch_preserved": False,
                    "disk_space_freed_mb": 0
                }

            # Calculate disk space before cleanup
            worktree_path = Path(worktree.worktree_path)
            disk_space_mb = 0
            if worktree_path.exists():
                disk_space_mb = self._get_directory_size_mb(worktree_path)

            # Remove git worktree
            try:
                # Use correct syntax for git worktree remove
                self.main_repo.git.worktree("remove", "-f", worktree.worktree_path)
            except GitCommandError as e:
                logger.warning(f"Failed to remove worktree via git: {e}")
                # Force remove directory if git command fails
                if worktree_path.exists():
                    shutil.rmtree(worktree_path, ignore_errors=True)

            # Update database status
            worktree.merge_status = "cleaned"
            worktree.disk_usage_mb = disk_space_mb

            session.commit()

            logger.info(f"Cleaned up worktree for agent {agent_id}, freed {disk_space_mb} MB")

            return {
                "status": "cleaned",
                "branch_preserved": True,  # Branch kept for history
                "disk_space_freed_mb": disk_space_mb
            }

        except Exception as e:
            logger.error(f"Failed to cleanup worktree: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def _prepare_parent_commit(self, parent_id: str, session: Session) -> Optional[str]:
        """Create checkpoint commit for parent before spawning child.

        Args:
            parent_id: Parent agent ID
            session: Database session

        Returns:
            Commit SHA of parent checkpoint, or None
        """
        logger.info(f"[WORKTREE] _prepare_parent_commit: Starting for parent_id={parent_id}")

        # Get parent worktree
        parent_worktree = session.query(AgentWorktree).filter_by(
            agent_id=parent_id
        ).first()

        if not parent_worktree:
            logger.warning(f"[WORKTREE] No worktree found for parent {parent_id}")
            return None

        logger.info(f"[WORKTREE] Parent worktree found at: {parent_worktree.worktree_path}")

        # Open parent worktree repository
        parent_repo = Repo(parent_worktree.worktree_path)

        # Check if parent worktree belongs to the same main repository
        # Worktrees have a .git file pointing to the main repo's .git/worktrees directory
        parent_git_dir = parent_repo.git_dir
        expected_git_base = str(Path(self.main_repo.git_dir).resolve())
        actual_git_base = str(Path(parent_git_dir).parent.parent.resolve())

        logger.info(f"[WORKTREE] Expected git base: {expected_git_base}")
        logger.info(f"[WORKTREE] Actual parent git base: {actual_git_base}")

        if expected_git_base != actual_git_base:
            logger.warning(
                f"[WORKTREE] Parent agent {parent_id} belongs to different repository!\n"
                f"  Parent repo: {actual_git_base}\n"
                f"  Current repo: {expected_git_base}\n"
                f"  Cannot inherit across repositories, falling back to current main branch"
            )
            return None

        # Get detailed status
        is_dirty = parent_repo.is_dirty()
        untracked = parent_repo.untracked_files
        modified = [item.a_path for item in parent_repo.index.diff(None)]
        staged = [item.a_path for item in parent_repo.index.diff("HEAD")]

        logger.info(f"[WORKTREE] Parent repository status:")
        logger.info(f"  - Working directory: {parent_worktree.worktree_path}")

        # Check if HEAD is detached (GitPython raises TypeError, not returns None)
        try:
            current_branch = parent_repo.active_branch.name
            logger.info(f"  - Current branch: {current_branch}")
        except TypeError:
            logger.info(f"  - Current branch: DETACHED HEAD")

        logger.info(f"  - Current HEAD: {parent_repo.head.commit.hexsha}")
        logger.info(f"  - Is dirty: {is_dirty}")
        logger.info(f"  - Untracked files ({len(untracked)}): {untracked[:5]}{'...' if len(untracked) > 5 else ''}")
        logger.info(f"  - Modified files ({len(modified)}): {modified[:5]}{'...' if len(modified) > 5 else ''}")
        logger.info(f"  - Staged files ({len(staged)}): {staged[:5]}{'...' if len(staged) > 5 else ''}")

        # Check if there are changes to commit
        if is_dirty or untracked:
            logger.info(f"[WORKTREE] Parent has uncommitted changes, creating checkpoint commit")

            # Show what we're about to add
            logger.info(f"[WORKTREE] Running 'git add -A' to stage all changes")
            parent_repo.git.add("-A")

            # Check what got staged
            staged_after = [item.a_path for item in parent_repo.index.diff("HEAD")]
            logger.info(f"[WORKTREE] Files staged after add -A ({len(staged_after)}): {staged_after[:10]}{'...' if len(staged_after) > 10 else ''}")

            # Create checkpoint commit
            commit_message = f"[Agent {parent_id}] Checkpoint before spawning child"
            logger.info(f"[WORKTREE] Creating commit with message: {commit_message}")
            # Use --no-verify to skip hooks for automated checkpoint commit
            parent_repo.git.commit("-m", commit_message, "--no-verify")
            checkpoint_commit = parent_repo.head.commit

            # Get commit details
            stats = checkpoint_commit.stats.total
            logger.info(f"[WORKTREE] Checkpoint commit created:")
            logger.info(f"  - SHA: {checkpoint_commit.hexsha}")
            logger.info(f"  - Files changed: {stats.get('files', 0)}")
            logger.info(f"  - Insertions: {stats.get('insertions', 0)}")
            logger.info(f"  - Deletions: {stats.get('deletions', 0)}")

            # Record checkpoint commit
            commit_record = WorktreeCommit(
                id=str(uuid.uuid4()),
                agent_id=parent_id,
                commit_sha=checkpoint_commit.hexsha,
                commit_type="parent_checkpoint",
                commit_message=commit_message,
                files_changed=stats.get('files', 0)
            )
            session.add(commit_record)
            session.flush()  # Flush but don't commit yet

            logger.info(f"[WORKTREE] Parent checkpoint complete, returning SHA: {checkpoint_commit.hexsha}")
            return checkpoint_commit.hexsha
        else:
            # No changes, return current HEAD
            current_sha = parent_repo.head.commit.hexsha
            logger.info(f"[WORKTREE] No uncommitted changes in parent, using current HEAD: {current_sha}")
            return current_sha

    def _resolve_conflicts_newest_wins(
        self,
        main_repo: Repo,
        worktree_repo: Repo,
        agent_id: str,
        session: Session
    ) -> List[Dict[str, Any]]:
        """Resolve conflicts using newest file wins strategy.

        Args:
            main_repo: Main repository with conflicts
            worktree_repo: Agent's worktree repository
            agent_id: Agent identifier
            session: Database session

        Returns:
            List of conflict resolutions
        """
        logger.info(f"[GIT-MERGE:{agent_id}] _resolve_conflicts_newest_wins: Starting conflict resolution")

        conflicts_resolved = []

        # Get list of conflicted files
        logger.info(f"[GIT-MERGE:{agent_id}] Running 'git diff --name-only --diff-filter=U' to find conflicts")
        conflicted_files = main_repo.git.diff("--name-only", "--diff-filter=U").splitlines()

        logger.info(f"[GIT-MERGE:{agent_id}] Found {len(conflicted_files)} conflicted files")
        if conflicted_files:
            logger.info(f"[GIT-MERGE:{agent_id}] Conflicted files: {conflicted_files}")

        for idx, file_path in enumerate(conflicted_files, 1):
            logger.info(f"[GIT-MERGE:{agent_id}] Processing conflict {idx}/{len(conflicted_files)}: {file_path}")

            # Get file timestamps
            logger.info(f"[GIT-MERGE:{agent_id}]   Getting file timestamps...")
            parent_timestamp = self._get_file_timestamp(main_repo, file_path, "HEAD")
            child_timestamp = self._get_file_timestamp(worktree_repo, file_path, "HEAD")

            logger.info(f"[GIT-MERGE:{agent_id}]   Parent (main) timestamp: {parent_timestamp}")
            logger.info(f"[GIT-MERGE:{agent_id}]   Child (agent) timestamp: {child_timestamp}")

            # Default to current time if timestamp not found
            if parent_timestamp is None:
                logger.warning(f"[GIT-MERGE:{agent_id}]   Parent timestamp not found, using current time")
                parent_timestamp = datetime.utcnow()
            if child_timestamp is None:
                logger.warning(f"[GIT-MERGE:{agent_id}]   Child timestamp not found, using current time")
                child_timestamp = datetime.utcnow()

            # Determine which version to use
            # NUCLEAR OPTION: Remove from index, get content, re-add fresh
            if child_timestamp > parent_timestamp:
                resolution_choice = "child"
                logger.info(f"[GIT-MERGE:{agent_id}]   → Resolution: CHILD (child is newer)")
                content = self._get_file_content(worktree_repo, file_path)
            elif parent_timestamp > child_timestamp:
                resolution_choice = "parent"
                logger.info(f"[GIT-MERGE:{agent_id}]   → Resolution: PARENT (parent is newer)")
                content = self._get_file_content(main_repo, file_path, "HEAD")
            else:
                # Same timestamp, prefer child (newer agent)
                resolution_choice = "tie_child"
                logger.info(f"[GIT-MERGE:{agent_id}]   → Resolution: TIE_CHILD (timestamps equal, breaking tie with child)")
                content = self._get_file_content(worktree_repo, file_path)

            # Nuclear conflict resolution: completely rebuild index entry
            logger.info(f"[GIT-MERGE:{agent_id}]   Step 1: Removing {file_path} from index entirely")
            try:
                main_repo.git.rm("--cached", "-f", file_path)
            except GitCommandError as e:
                logger.warning(f"[GIT-MERGE:{agent_id}]   Warning on git rm: {e}")

            logger.info(f"[GIT-MERGE:{agent_id}]   Step 2: Writing resolved content to working directory")
            self._write_file_content(main_repo.working_dir, file_path, content)

            logger.info(f"[GIT-MERGE:{agent_id}]   Step 3: Adding file fresh to index")
            main_repo.git.add(file_path)

            # Record resolution
            resolution_record = MergeConflictResolution(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                file_path=file_path,
                parent_modified_at=parent_timestamp,
                child_modified_at=child_timestamp,
                resolution_choice=resolution_choice
            )
            session.add(resolution_record)
            logger.info(f"[GIT-MERGE:{agent_id}]   ✓ Recorded resolution in database")

            conflicts_resolved.append({
                "file": file_path,
                "resolution": resolution_choice,
                "parent_timestamp": parent_timestamp.isoformat() if parent_timestamp else None,
                "child_timestamp": child_timestamp.isoformat() if child_timestamp else None
            })

        logger.info(f"[GIT-MERGE:{agent_id}] ✓ All {len(conflicted_files)} conflicts resolved")
        session.flush()  # Flush resolutions but don't commit yet
        logger.info(f"[GIT-MERGE:{agent_id}] ✓ Database changes flushed")

        return conflicts_resolved

    def _get_file_timestamp(self, repo: Repo, file_path: str, ref: str = "HEAD") -> Optional[datetime]:
        """Get modification timestamp of a file.

        Args:
            repo: Git repository
            file_path: Path to file
            ref: Git reference (default HEAD)

        Returns:
            Datetime of last modification, or None
        """
        try:
            # Get last commit that modified this file
            commits = list(repo.iter_commits(ref, paths=file_path, max_count=1))
            if commits:
                return datetime.fromtimestamp(commits[0].committed_date)
        except Exception as e:
            logger.warning(f"Failed to get timestamp for {file_path}: {e}")
        return None

    def _get_file_content(self, repo: Repo, file_path: str, ref: str = "HEAD") -> str:
        """Get content of a file from repository.

        Args:
            repo: Git repository
            file_path: Path to file
            ref: Git reference

        Returns:
            File content as string
        """
        try:
            # Try to get from working directory first
            full_path = Path(repo.working_dir) / file_path
            if full_path.exists():
                return full_path.read_text()

            # Get from git
            return repo.git.show(f"{ref}:{file_path}")
        except Exception as e:
            logger.warning(f"Failed to get content for {file_path}: {e}")
            return ""

    def _write_file_content(self, repo_dir: str, file_path: str, content: str) -> None:
        """Write content to a file in repository.

        Args:
            repo_dir: Repository working directory
            file_path: Path to file
            content: Content to write
        """
        full_path = Path(repo_dir) / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    def _cleanup_worktree(self, worktree_path: str) -> None:
        """Force cleanup a worktree.

        Args:
            worktree_path: Path to worktree
        """
        try:
            # Try git worktree remove first
            self.main_repo.git.worktree("remove", worktree_path, force=True)
        except:
            pass

        # Force remove directory
        path = Path(worktree_path)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    def _get_directory_size_mb(self, path: Path) -> int:
        """Get size of directory in MB.

        Args:
            path: Directory path

        Returns:
            Size in megabytes
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        return total_size // (1024 * 1024)  # Convert to MB