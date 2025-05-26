"""
Engine-related database models
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer
from .base import Base


class EngineState(Base):
    """State tracking for engine instances"""
    __tablename__ = "engine_states"
    
    id = Column(String, primary_key=True)  # UUID
    engine_type = Column(String, nullable=False, index=True)  # actor, narrator, analyst
    status = Column(String, nullable=False, index=True)  # active, idle, error
    last_heartbeat = Column(DateTime)
    current_workload = Column(Integer, nullable=False, default=0)    engine_metadata = Column(JSON)  # Configuration and dynamic state
    
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
