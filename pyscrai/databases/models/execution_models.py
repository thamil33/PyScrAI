"""
Execution models for runtime instances, events, and logging aligned with universal templates and custom engines
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from .base import Base


class AgentInstance(Base):
    """Runtime instance of an agent created from a template - aligned with custom engines"""
    __tablename__ = "agent_instances"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("agent_templates.id"), nullable=False)
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id"), nullable=False)
    instance_name = Column(String(100), nullable=False)
    engine_type = Column(String(50), nullable=False)  # actor, analyst, narrator
    status = Column(String(20), default="initialized")  # initialized, active, paused, completed, failed
    
    # Configuration and state
    runtime_config = Column(JSON, default=dict)  # Runtime configuration overrides
    engine_overrides = Column(JSON, default=dict)  # Engine-specific runtime overrides
    state = Column(JSON, default=dict)  # Current agent state and memory
    
    # Performance metrics
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    tools_used = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template = relationship("AgentTemplate", back_populates="agent_instances")
    scenario_run = relationship("ScenarioRun", back_populates="agent_instances")
    logs = relationship("ExecutionLog", back_populates="agent_instance", cascade="all, delete-orphan")
    sent_events = relationship("EventInstance", foreign_keys="[EventInstance.source_agent_id]", 
                              back_populates="source_agent", cascade="all, delete-orphan")
    received_events = relationship("EventInstance", foreign_keys="[EventInstance.target_agent_id]", 
                                  back_populates="target_agent", cascade="all, delete-orphan")


class ScenarioRun(Base):
    """Execution instance of a scenario - enhanced for universal templates"""
    __tablename__ = "scenario_runs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("scenario_templates.id"), nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")  # pending, initializing, running, paused, completed, failed
    
    # Configuration and customization
    config = Column(JSON, default=dict)  # Runtime configuration
    runtime_customizations = Column(JSON, default=dict)  # Applied runtime customizations
    results = Column(JSON, default=dict)  # Execution results and outcomes
    metrics = Column(JSON, default=dict)  # Performance and interaction metrics
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    template = relationship("ScenarioTemplate", back_populates="scenario_runs")
    agent_instances = relationship("AgentInstance", back_populates="scenario_run", cascade="all, delete-orphan")
    events = relationship("EventInstance", back_populates="scenario_run", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="scenario_run", cascade="all, delete-orphan")


class EventType(Base):
    """Event type definitions for the universal template system"""
    __tablename__ = "event_types"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    event_category = Column(String(50), default="custom")  # system, narrative, interaction, analysis, custom
    data_schema = Column(JSON, default=dict)  # Expected data structure
    validation_rules = Column(JSON, default=dict)  # Validation rules for event data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event_instances = relationship("EventInstance", back_populates="event_type", cascade="all, delete-orphan")


class EventInstance(Base):
    """Individual event instances in scenario execution"""
    __tablename__ = "event_instances"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"), nullable=False)
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id"), nullable=False)
    
    # Agent relationships (optional - some events may be system-level)
    agent_instance_id = Column(Integer, ForeignKey("agent_instances.id"))  # Primary agent for this event
    source_agent_id = Column(Integer, ForeignKey("agent_instances.id"))  # Source agent (for interactions)
    target_agent_id = Column(Integer, ForeignKey("agent_instances.id"))  # Target agent (for interactions)
    
    # Event data and processing
    data = Column(JSON, default=dict)  # Event payload
    status = Column(String(20), default="pending")  # pending, processing, completed, failed, retrying
    priority = Column(Integer, default=5)  # 1-10, higher = more priority
    processing_result = Column(JSON, default=dict)  # Result of processing
    error_info = Column(JSON, default=dict)  # Error details if failed
    
    # Processing metadata
    assigned_engine_id = Column(String(100))  # Which engine is processing this
    processing_attempts = Column(Integer, default=0)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime)
    processed_at = Column(DateTime)
    
    # Relationships
    event_type = relationship("EventType", back_populates="event_instances")
    scenario_run = relationship("ScenarioRun", back_populates="events")
    agent_instance = relationship("AgentInstance", foreign_keys=[agent_instance_id])
    source_agent = relationship("AgentInstance", foreign_keys=[source_agent_id], back_populates="sent_events")
    target_agent = relationship("AgentInstance", foreign_keys=[target_agent_id], back_populates="received_events")


class ExecutionLog(Base):
    """Comprehensive logging for scenario execution and debugging"""
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True)
    scenario_run_id = Column(Integer, ForeignKey("scenario_runs.id"), nullable=False)
    agent_instance_id = Column(Integer, ForeignKey("agent_instances.id"))
    event_instance_id = Column(Integer, ForeignKey("event_instances.id"))
    
    # Log classification
    engine_type = Column(String(50))  # Which engine generated this log
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    
    # Structured data
    data = Column(JSON, default=dict)  # Additional structured data
    context = Column(JSON, default=dict)  # Execution context at time of log
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scenario_run = relationship("ScenarioRun", back_populates="logs")
    agent_instance = relationship("AgentInstance", back_populates="logs")


class EngineState(Base):
    """State tracking for custom engines in the system"""
    __tablename__ = "engine_states"
    
    id = Column(String(100), primary_key=True)  # Unique engine identifier
    engine_type = Column(String(50), nullable=False)  # actor, analyst, narrator
    status = Column(String(20), default="healthy")  # healthy, degraded, unhealthy, offline
    
    # Engine metadata
    capabilities = Column(JSON, default=dict)  # Engine capabilities
    resource_limits = Column(JSON, default=dict)  # Resource constraints
    engine_metadata = Column(JSON, default=dict)  # Additional engine info
    
    # Performance tracking
    current_workload = Column(Integer, default=0)
    active_agents = Column(Integer, default=0)
    processed_events_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    performance_metrics = Column(JSON, default=dict)
    
    # Timestamps
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class QueuedEvent(Base):
    """Event queue for engine processing"""
    __tablename__ = "queued_events"
    
    id = Column(Integer, primary_key=True)
    event_instance_id = Column(Integer, ForeignKey("event_instances.id"), nullable=False)
    engine_type = Column(String(50), nullable=False)  # Target engine type
    priority = Column(Integer, default=5)  # Processing priority
    
    # Queue management
    status = Column(String(20), default="queued")  # queued, assigned, processing, completed, failed
    assigned_engine_id = Column(String(100))  # Which specific engine instance
    processing_attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    event_instance = relationship("EventInstance")


class SystemMetrics(Base):
    """System-wide metrics and analytics"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True)
    metric_type = Column(String(50), nullable=False)  # scenario, agent, engine, system
    entity_id = Column(String(100))  # ID of the entity being measured
    
    # Metric data
    metrics_data = Column(JSON, default=dict)  # The actual metrics
    aggregation_period = Column(String(20), default="realtime")  # realtime, hourly, daily
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)
    period_end = Column(DateTime)


class TemplateUsage(Base):
    """Track usage and performance of templates"""
    __tablename__ = "template_usage"
    
    id = Column(Integer, primary_key=True)
    template_type = Column(String(20), nullable=False)  # agent, scenario
    template_id = Column(Integer, nullable=False)
    template_name = Column(String(100), nullable=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    average_execution_time = Column(Float, default=0.0)
    
    # Performance metrics
    performance_data = Column(JSON, default=dict)
    
    # Timestamps
    first_used = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
