"""
Agent-related database models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class AgentTemplate(Base):
    """Template for creating agents with specific personalities and behaviors"""
    __tablename__ = "agent_templates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    personality_config = Column(JSON)  # Personality traits, instructions, etc.
    llm_config = Column(JSON)  # Model settings (temperature, etc.)
    tools_config = Column(JSON)  # Available tools
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent_instances = relationship("AgentInstance", back_populates="template")


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
