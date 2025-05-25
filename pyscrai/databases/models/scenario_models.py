"""
Scenario-related database models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class ScenarioTemplate(Base):
    """Template for scenarios with agent configurations and flow"""
    __tablename__ = "scenario_templates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    config = Column(JSON)  # Scenario configuration
    agent_roles = Column(JSON)  # Required agent roles and their templates
    event_flow = Column(JSON)  # Predefined event sequence
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scenario_runs = relationship("ScenarioRun", back_populates="template")


class ScenarioRun(Base):
    """Execution instance of a scenario"""
    __tablename__ = "scenario_runs"
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("scenario_templates.id"))
    name = Column(String(100))
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    config = Column(JSON)  # Runtime configuration
    results = Column(JSON)  # Execution results
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template = relationship("ScenarioTemplate", back_populates="scenario_runs")
    agent_instances = relationship("AgentInstance", back_populates="scenario_run")
    events = relationship("EventInstance", back_populates="scenario_run")
