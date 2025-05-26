"""
Execution-related database models for events, engines, and logging
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class EventType(Base):
    """
    Predefined event types for inter-agent communication.
    These types define the structure and nature of events that can occur within the system.
    """
    __tablename__ = "event_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    schema = Column(JSON)  # JSON schema defining the expected structure of the 'data' field in EventInstance
    category = Column(String)  # Category of event (e.g., 'system', 'agent', 'scenario')
    engine_type = Column(String)  # Specifies the type of engine that typically processes this event type
    created_at = Column(DateTime, default=datetime.utcnow)


class EventInstance(Base):
    """
    Runtime event instances during scenario execution.
    These are specific occurrences of EventTypes, generated during the simulation.
    """
    __tablename__ = "event_instances"

    id = Column(Integer, primary_key=True)
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id"))
    event_type_id = Column(Integer, ForeignKey("event_types.id"))
    source_agent_id = Column(Integer, ForeignKey("agent_instances.id"))
    target_agent_id = Column(Integer, ForeignKey("agent_instances.id"), nullable=True)
    data = Column(JSON)  # The actual payload of the event
    
    # Event processing state
    processed_by_engines = Column(JSON)  # List of engine IDs that have processed this event
    priority = Column(Integer, default=0, server_default='0')  # Event processing priority
    status = Column(String, nullable=False, default='queued', server_default='queued')  # Current status
    lock_until = Column(DateTime, nullable=True)  # Lock expiration timestamp
    locked_by = Column(String, nullable=True)  # ID of the engine holding the lock
    retry_count = Column(Integer, nullable=False, default=0, server_default='0')  # Number of retry attempts
    last_error = Column(String, nullable=True)  # Error message from last failed attempt
    next_retry_time = Column(DateTime, nullable=True)  # When to retry next
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scenario_run = relationship("ScenarioRun", back_populates="events")
    event_type = relationship("EventType")
    source_agent = relationship("AgentInstance", foreign_keys=[source_agent_id], back_populates="sent_events")
    target_agent = relationship("AgentInstance", foreign_keys=[target_agent_id], back_populates="received_events")


class EngineState(Base):
    """State tracking for engine instances"""
    __tablename__ = "engine_states"
    
    id = Column(String, primary_key=True)  # UUID
    engine_type = Column(String, nullable=False, index=True)  # actor, narrator, analyst
    status = Column(String, nullable=False, index=True)  # active, idle, error
    last_heartbeat = Column(DateTime)
    current_workload = Column(Integer, nullable=False, default=0)
    engine_metadata = Column(JSON)  # Configuration and dynamic state
    
    @property
    def static_config(self):
        """Get static configuration from metadata"""
        return self.engine_metadata.get('static_config', {}) if self.engine_metadata else {}
    
    @property
    def dynamic_state(self):
        """Get dynamic state from metadata"""
        return self.engine_metadata.get('dynamic_state', {}) if self.engine_metadata else {}
    
    def update_heartbeat(self):
        """Update the last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()
    
    def is_alive(self, timeout_seconds=300):
        """Check if the engine is still alive based on heartbeat"""
        if not self.last_heartbeat:
            return False
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() < timeout_seconds


class ExecutionLog(Base):
    """Detailed execution logs for debugging and analysis"""
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True)
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id"))
    agent_instance_id = Column(Integer, ForeignKey("agent_instances.id"), nullable=True)
    level = Column(String(10))  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scenario_run = relationship("ScenarioRun", back_populates="logs")
    agent_instance = relationship("AgentInstance", back_populates="logs")
