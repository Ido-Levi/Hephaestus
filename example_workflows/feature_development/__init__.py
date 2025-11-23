"""
Feature Development Workflow

A workflow for adding features to existing codebases.
Analyzes the codebase, designs the integration, implements the feature,
and validates it works without breaking existing functionality.
"""

from example_workflows.feature_development.phases import (
    FEATURE_DEV_PHASES,
    FEATURE_DEV_CONFIG,
    FEATURE_DEV_LAUNCH_TEMPLATE,
)

__all__ = [
    "FEATURE_DEV_PHASES",
    "FEATURE_DEV_CONFIG",
    "FEATURE_DEV_LAUNCH_TEMPLATE",
]
