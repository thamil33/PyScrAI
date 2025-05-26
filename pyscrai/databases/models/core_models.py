"""
Core database models for agents and scenarios
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class AgentTemplate(Base):
    """Template for creating agents with specific personalities and behaviors"""
    __tablename__ = "agent_templates"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    engine_type = Column(String(50), nullable=False)  # actor, analyst, narrator
    personality_config = Column(JSON)  # Personality traits, instructions, etc.
    llm_config = Column(JSON)  # Model settings (temperature, etc.)
    tools_config = Column(JSON)  # Available tools
    runtime_overrides = Column(JSON)  # Runtime override policies
    engine_specific_config = Column(JSON)  # Engine-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent_instances = relationship("AgentInstance", back_populates="template", cascade="all, delete-orphan")


class ScenarioTemplate(Base):
    """Template for scenarios with agent configurations and flow"""
    __tablename__ = "scenario_templates"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    config = Column(JSON)  # Scenario configuration
    agent_roles = Column(JSON)  # Required agent roles and their templates
    event_flow = Column(JSON)  # Predefined event sequence
    runtime_customization = Column(JSON)  # Runtime customization options
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scenario_runs = relationship("ScenarioRun", back_populates="template", cascade="all, delete-orphan")


class AgentInstance(Base):
    """Runtime instance of an agent created from a template"""
    __tablename__ = "agent_instances"
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("agent_templates.id"))
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id"))
    instance_name = Column(String(100))
    runtime_config = Column(JSON)  # Override configurations
    state = Column(JSON)  # Current agent state
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template = relationship("AgentTemplate", back_populates="agent_instances")
    scenario_run = relationship("ScenarioRun", back_populates="agent_instances")
    logs = relationship("ExecutionLog", back_populates="agent_instance", cascade="all, delete-orphan")
    sent_events = relationship("EventInstance", foreign_keys="[EventInstance.source_agent_id]", back_populates="source_agent", cascade="all, delete-orphan")
    received_events = relationship("EventInstance", foreign_keys="[EventInstance.target_agent_id]", back_populates="target_agent", cascade="all, delete-orphan")


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
    agent_instances = relationship("AgentInstance", back_populates="scenario_run", cascade="all, delete-orphan")
    events = relationship("EventInstance", back_populates="scenario_run", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="scenario_run", cascade="all, delete-orphan")
