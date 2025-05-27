# pyscrai/databases/models/core_models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base # Assuming Base is defined in base.py in the same directory
import datetime # It seems you're using datetime.utcnow, so ensure datetime is imported

# Your full package path to models might be slightly different if 'pyscrai' is not the top-level
# directory Python sees for imports, but assuming it is:
CORE_MODELS_PATH = "pyscrai.databases.models.core_models"
EXECUTION_MODELS_PATH = "pyscrai.databases.models.execution_models"

class AgentTemplate(Base):
    __tablename__ = "agent_templates"
    __table_args__ = {'extend_existing': True} # This is fine
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    engine_type = Column(String(50), nullable=False)
    personality_config = Column(JSON)
    llm_config = Column(JSON)
    tools_config = Column(JSON)
    runtime_overrides = Column(JSON)
    engine_specific_config = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    agent_instances = relationship(f"{CORE_MODELS_PATH}.AgentInstance", back_populates="template", cascade="all, delete-orphan")

class ScenarioTemplate(Base):
    __tablename__ = "scenario_templates"
    __table_args__ = {'extend_existing': True} # This is fine
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    config = Column(JSON)
    agent_roles = Column(JSON)
    event_flow = Column(JSON)
    runtime_customization = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    scenario_runs = relationship(f"{CORE_MODELS_PATH}.ScenarioRun", back_populates="template", cascade="all, delete-orphan")

class AgentInstance(Base):
    __tablename__ = "agent_instances"
    # If AgentInstance also had __table_args__ with extend_existing=True, ensure it's there.
    # Otherwise, if it's defined only once, it's not needed.
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("agent_templates.id")) # Use fully qualified FK
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id")) # Use fully qualified FK
    instance_name = Column(String(100))
    runtime_config = Column(JSON)
    state = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    template = relationship(f"{CORE_MODELS_PATH}.AgentTemplate", back_populates="agent_instances")
    scenario_run = relationship(f"{CORE_MODELS_PATH}.ScenarioRun", back_populates="agent_instances")
    
    logs = relationship(f"{EXECUTION_MODELS_PATH}.ExecutionLog", back_populates="agent_instance", cascade="all, delete-orphan")
    # For EventInstance, ensure its foreign keys are also fully qualified if they refer to this table by string
    sent_events = relationship(f"{EXECUTION_MODELS_PATH}.EventInstance", foreign_keys=f"[{EXECUTION_MODELS_PATH}.EventInstance.source_agent_id]", back_populates="source_agent", cascade="all, delete-orphan")
    received_events = relationship(f"{EXECUTION_MODELS_PATH}.EventInstance", foreign_keys=f"[{EXECUTION_MODELS_PATH}.EventInstance.target_agent_id]", back_populates="target_agent", cascade="all, delete-orphan")

class ScenarioRun(Base):
    __tablename__ = "scenario_runs"
    # If ScenarioRun also had __table_args__ with extend_existing=True, ensure it's there.
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("scenario_templates.id")) # Use fully qualified FK
    name = Column(String(100))
    status = Column(String(20), default="pending")
    config = Column(JSON)
    results = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    template = relationship(f"{CORE_MODELS_PATH}.ScenarioTemplate", back_populates="scenario_runs")
    agent_instances = relationship(f"{CORE_MODELS_PATH}.AgentInstance", back_populates="scenario_run", cascade="all, delete-orphan")
    events = relationship(f"{EXECUTION_MODELS_PATH}.EventInstance", back_populates="scenario_run", cascade="all, delete-orphan")
    logs = relationship(f"{EXECUTION_MODELS_PATH}.ExecutionLog", back_populates="scenario_run", cascade="all, delete-orphan")