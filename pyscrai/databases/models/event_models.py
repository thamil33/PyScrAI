"""
Event-related database models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean # Ensure all necessary types are imported
from sqlalchemy.orm import relationship
from .base import Base # Ensure Base is imported for declarative mapping


class EventType(Base):
    """
    Predefined event types for inter-agent communication.
    These types define the structure and nature of events that can occur within the system.
    """
    __tablename__ = "event_types" # The name of the database table for this model.

    id = Column(Integer, primary_key=True) # Unique identifier for the event type.
    name = Column(String(100), nullable=False, unique=True) # A unique, human-readable name for the event type.
    description = Column(Text) # A detailed description of what this event type represents.
    
    # Changed from data_schema to schema to match the initial migration c15179238652_create_initial_tables.py
    schema = Column(JSON) # JSON schema defining the expected structure of the 'data' field in EventInstance. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/c15179238652_create_initial_tables.py]
    
    # Columns added by migration 2024_05_25_002_add_engine_states.py
    category = Column(String)  # Category of event (e.g., 'system', 'agent', 'scenario'). Helps in organizing and filtering events. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    engine_type = Column(String)  # Specifies the type of engine (e.g., 'actor', 'narrator') that is typically responsible for processing this event type. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    
    created_at = Column(DateTime, default=datetime.utcnow) # Timestamp of when the event type was created.


class EventInstance(Base):
    """
    Runtime event instances during scenario execution.
    These are specific occurrences of EventTypes, generated during the simulation.
    """
    __tablename__ = "event_instances" # The name of the database table for this model.

    id = Column(Integer, primary_key=True) # Unique identifier for this specific event instance.
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id")) # Foreign key linking to the scenario run this event belongs to.
    event_type_id = Column(Integer, ForeignKey("event_types.id")) # Foreign key linking to the EventType that defines this event.
    source_agent_id = Column(Integer, ForeignKey("agent_instances.id")) # Foreign key linking to the agent instance that generated this event.
    target_agent_id = Column(Integer, ForeignKey("agent_instances.id"), nullable=True) # Foreign key linking to the agent instance this event is directed to (can be null if broadcast or system event).
    data = Column(JSON) # The actual payload of the event, conforming to the 'schema' of its EventType.
    
    # Column 'processed' was present in the initial migration but seems to have been replaced/augmented by 'status' and 'processed_by_engines'
    # in the second migration. For clarity, ensure the model reflects the final state after all migrations.
    # processed = Column(Boolean, default=False) # This column is in the first migration [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/c15179238652_create_initial_tables.py] 
    # It's advisable to remove this if 'status' and 'processed_by_engines' serve its purpose to avoid redundancy.
    # If it's still needed, ensure it's handled correctly. For now, assuming it's superseded.

    # Columns added/modified by migration 2024_05_25_002_add_engine_states.py
    processed_by_engines = Column(JSON)  # List of engine IDs that have processed or attempted to process this event. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    priority = Column(Integer, default=0, server_default='0')  # Event processing priority (higher value means higher priority). [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    status = Column(String, nullable=False, default='queued', server_default='queued')  # Current status of the event (e.g., 'queued', 'processing', 'completed', 'failed'). [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    lock_until = Column(DateTime, nullable=True)  # Timestamp indicating when the lock on this event expires. Used to prevent multiple engines from processing the same event. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    locked_by = Column(String, nullable=True)  # ID of the engine instance currently holding the lock on this event. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    retry_count = Column(Integer, nullable=False, default=0, server_default='0') # Number of times processing has been attempted for this event. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    last_error = Column(String, nullable=True) # Stores the error message if the last processing attempt failed. [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    next_retry_time = Column(DateTime, nullable=True) # Timestamp indicating when the next retry attempt should be made (for events with retry logic). [cite: uploaded:thamil33/pyscrai/PyScrAI-33f35871271ff8093e6990175d671656afedc364/pyscrai/databases/alembic/versions/2024_05_25_002_add_engine_states.py]
    
    created_at = Column(DateTime, default=datetime.utcnow) # Timestamp of when this event instance was created.
    
    # Relationships to other models
    # Defines how this model is linked to other SQLAlchemy models.
    scenario_run = relationship("ScenarioRun", back_populates="events")
    event_type = relationship("EventType") # Relationship to EventType to access its details.
    source_agent = relationship("AgentInstance", foreign_keys=[source_agent_id], back_populates="sent_events")
    target_agent = relationship("AgentInstance", foreign_keys=[target_agent_id], back_populates="received_events")

