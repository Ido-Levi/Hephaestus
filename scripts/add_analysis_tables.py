#!/usr/bin/env python3
"""Add dedicated tables for Guardian and Conductor analyses."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.simple_config import get_config

Base = declarative_base()


class GuardianAnalysis(Base):
    """Dedicated table for Guardian trajectory analyses."""
    __tablename__ = "guardian_analyses"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Trajectory analysis fields
    current_phase = Column(String)
    trajectory_aligned = Column(Boolean)
    alignment_score = Column(Float, index=True)
    needs_steering = Column(Boolean, index=True)
    steering_type = Column(String)
    steering_recommendation = Column(Text)
    trajectory_summary = Column(Text)

    # Accumulated context fields
    accumulated_goal = Column(Text)
    current_focus = Column(String)
    session_duration = Column(String)
    conversation_length = Column(Integer)

    # Full analysis details as JSON for reference
    details = Column(JSON)

    # Relationships
    agent = relationship("Agent", back_populates="guardian_analyses")


class ConductorAnalysis(Base):
    """Dedicated table for Conductor system analyses."""
    __tablename__ = "conductor_analyses"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # System coherence fields
    coherence_score = Column(Float, index=True)
    num_agents = Column(Integer)
    system_status = Column(Text)

    # Duplicate detection
    duplicate_count = Column(Integer)

    # Decision counts
    termination_count = Column(Integer)
    coordination_count = Column(Integer)

    # Full analysis as JSON
    details = Column(JSON)


class DetectedDuplicate(Base):
    """Table for tracking detected duplicate work."""
    __tablename__ = "detected_duplicates"

    id = Column(Integer, primary_key=True)
    conductor_analysis_id = Column(Integer, ForeignKey("conductor_analyses.id"))
    agent1_id = Column(String, ForeignKey("agents.id"))
    agent2_id = Column(String, ForeignKey("agents.id"))
    similarity_score = Column(Float)
    work_description = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conductor_analysis = relationship("ConductorAnalysis", backref="duplicates")
    agent1 = relationship("Agent", foreign_keys=[agent1_id])
    agent2 = relationship("Agent", foreign_keys=[agent2_id])


class SteeringIntervention(Base):
    """Table for tracking steering interventions."""
    __tablename__ = "steering_interventions"

    id = Column(Integer, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    guardian_analysis_id = Column(Integer, ForeignKey("guardian_analyses.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    steering_type = Column(String)
    message = Column(Text)
    was_successful = Column(Boolean)

    # Relationships
    agent = relationship("Agent", backref="interventions")
    guardian_analysis = relationship("GuardianAnalysis", backref="interventions")


def add_tables():
    """Add the new analysis tables to the existing database."""
    config = get_config()
    engine = create_engine(f'sqlite:///{config.database_path}')

    # Create all tables
    Base.metadata.create_all(engine)

    print(f"✅ Added analysis tables to {config.database_path}")
    print("   - guardian_analyses")
    print("   - conductor_analyses")
    print("   - detected_duplicates")
    print("   - steering_interventions")


if __name__ == "__main__":
    add_tables()