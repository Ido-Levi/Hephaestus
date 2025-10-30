"""
Open Source Bug Bounty workflow for Hephaestus.

This workflow systematically discovers, investigates, and exploits security vulnerabilities
in open source projects for HackerOne submission.
"""

from .phases import BUGBOUNTY_PHASES, BUGBOUNTY_WORKFLOW_CONFIG

__all__ = ['BUGBOUNTY_PHASES', 'BUGBOUNTY_WORKFLOW_CONFIG']