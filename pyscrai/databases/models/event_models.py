"""
Event-related database models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class EventType(Base):
    """Predefined event types for inter-agent communication"""
    __tablename__ = "event_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    data_schema = Column(JSON)  # JSON schema for event data
    category = Column(String)  # Category of event (e.g., 'system', 'agent', 'scenario')
    engine_type = Column(String)  # Type of engine that can process this event
    created_at = Column(DateTime, default=datetime.utcnow)


class EventInstance(Base):
    """Runtime event instances during scenario execution"""
    __tablename__ = "event_instances"
    
    id = Column(Integer, primary_key=True)
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id"))
    event_type_id = Column(Integer, ForeignKey("event_types.id"))
    source_agent_id = Column(Integer, ForeignKey("agent_instances.id"))
    target_agent_id = Column(Integer, ForeignKey("agent_instances.id"), nullable=True)
    data = Column(JSON)
    processed_by_engines = Column(JSON)  # List of engine IDs that processed this event
    priority = Column(Integer, default=0)  # Event processing priority
    status = Column(String, nullable=False, default='queued')  # queued, processing, completed, failed
    lock_until = Column(DateTime)  # Lock expiration timestamp
    locked_by = Column(String)  # ID of engine instance holding the lock
    retry_count = Column(Integer, nullable=False, default=0)
    last_error = Column(String)
    next_retry_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scenario_run = relationship("ScenarioRun", back_populates="events")
    event_type = relationship("EventType")
    source_agent = relationship("AgentInstance", foreign_keys=[source_agent_id], back_populates="sent_events")
    target_agent = relationship("AgentInstance", foreign_keys=[target_agent_id], back_populates="received_events")
