"""Pydantic models for monitoring system responses."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class GuardianTrajectoryAnalysis(BaseModel):
    """Guardian trajectory analysis response model."""

    current_phase: Literal[
        "exploration",
        "information_gathering",
        "planning",
        "implementation",
        "verification",
        "completed",
        "unknown"
    ] = Field(..., description="The agent's current work phase")

    trajectory_aligned: bool = Field(..., description="Whether agent is working toward the accumulated goal")

    alignment_score: float = Field(..., ge=0.0, le=1.0, description="Alignment score from 0.0 to 1.0")

    alignment_issues: List[str] = Field(default_factory=list, description="Specific problems detected")

    needs_steering: bool = Field(..., description="Whether to send a steering message")

    steering_type: Optional[Literal[
        "stuck",
        "drifting",
        "violating_constraints",
        "over_engineering",
        "confused"
    ]] = Field(None, description="Type of issue requiring steering")

    steering_recommendation: Optional[str] = Field(None, description="The exact message to send to the agent (required when needs_steering=True)")

    trajectory_summary: str = Field(..., description="Intelligent summary with context")


class ConductorSystemAnalysis(BaseModel):
    """Conductor system coherence analysis response model."""

    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Overall system coherence score")

    duplicates: List[str] = Field(default_factory=list, description="Agent IDs with duplicate work")

    alignment_issues: List[str] = Field(default_factory=list, description="System-wide alignment problems")

    termination_recommendations: List[str] = Field(default_factory=list, description="Agent IDs recommended for termination")

    coordination_needs: List[str] = Field(default_factory=list, description="Coordination requirements")

    system_summary: str = Field(..., description="Overall system status summary")