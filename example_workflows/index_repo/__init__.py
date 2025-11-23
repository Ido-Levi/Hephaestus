"""
Index Repo Workflow - Codebase Knowledge Extraction

This workflow scans a repository and extracts comprehensive knowledge into the memory system.
It creates memories about project structure, components, code patterns, and how to run/test things.

Other workflows (bug fix, feature development) can then retrieve this knowledge for context.
"""

from example_workflows.index_repo.phases import (
    INDEX_REPO_PHASES,
    INDEX_REPO_CONFIG,
    INDEX_REPO_LAUNCH_TEMPLATE,
)

__all__ = [
    "INDEX_REPO_PHASES",
    "INDEX_REPO_CONFIG",
    "INDEX_REPO_LAUNCH_TEMPLATE",
]
