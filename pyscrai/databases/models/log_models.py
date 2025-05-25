"""
Logging-related database models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


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
