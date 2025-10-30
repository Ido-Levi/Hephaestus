"""
PRD to Software Builder Workflow

A fully generic, self-building Hephaestus workflow that takes a PRD
(Product Requirements Document) and builds working software.

Works for any type of software project: web apps, CLIs, libraries,
microservices, mobile backends, and more.
"""

from .phases import PRD_PHASES, PRD_WORKFLOW_CONFIG

__all__ = ["PRD_PHASES", "PRD_WORKFLOW_CONFIG"]
