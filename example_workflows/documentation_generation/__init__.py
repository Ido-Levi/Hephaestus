"""
Documentation Generation Workflow

A workflow for generating comprehensive documentation for existing codebases.
Discovers components, checks existing docs, and generates/updates markdown documentation.
"""

from example_workflows.documentation_generation.phases import (
    DOC_GEN_PHASES,
    DOC_GEN_CONFIG,
    DOC_GEN_LAUNCH_TEMPLATE,
)

__all__ = [
    "DOC_GEN_PHASES",
    "DOC_GEN_CONFIG",
    "DOC_GEN_LAUNCH_TEMPLATE",
]
