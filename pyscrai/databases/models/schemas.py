"""
Pydantic schemas for API validation and serialization aligned with universal generic templates and custom engines
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, ConfigDict, Field
from .template_validators import EngineType, RuntimeOverridePolicy


# Agent Template Schemas
class AgentTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    engine_type: EngineType
    personality_config: Dict[str, Any] = {}
    llm_config: Dict[str, Any] = {}
    tools_config: Dict[str, Any] = {}
    runtime_overrides: Optional[Dict[str, Any]] = None
    engine_specific_config: Optional[Dict[str, Any]] = None


class AgentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    engine_type: Optional[EngineType] = None
    personality_config: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools_config: Optional[Dict[str, Any]] = None
    runtime_overrides: Optional[Dict[str, Any]] = None
    engine_specific_config: Optional[Dict[str, Any]] = None


class AgentTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    engine_type: str
    personality_config: Dict[str, Any]
    llm_config: Dict[str, Any]
    tools_config: Dict[str, Any]
    runtime_overrides: Optional[Dict[str, Any]]
    engine_specific_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Agent Instance Schemas
class AgentInstanceCreate(BaseModel):
    template_id: int
    scenario_run_id: int
    instance_name: str
    runtime_config: Dict[str, Any] = {}
    engine_overrides: Optional[Dict[str, Any]] = None


class AgentInstanceUpdate(BaseModel):
    instance_name: Optional[str] = None
    runtime_config: Optional[Dict[str, Any]] = None
    engine_overrides: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class AgentInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    template_id: int
    scenario_run_id: int
    instance_name: str
    runtime_config: Dict[str, Any]
    engine_overrides: Optional[Dict[str, Any]]
    state: Dict[str, Any]
    engine_type: str
    status: str
    created_at: datetime
    last_activity: Optional[datetime]


# Scenario Template Schemas
class ScenarioTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = {}
    agent_roles: Dict[str, Any] = {}
    event_flow: Dict[str, Any] = {}
    runtime_customization: Optional[Dict[str, Any]] = None


class ScenarioTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    agent_roles: Optional[Dict[str, Any]] = None
    event_flow: Optional[Dict[str, Any]] = None
    runtime_customization: Optional[Dict[str, Any]] = None


class ScenarioTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    agent_roles: Dict[str, Any]
    event_flow: Dict[str, Any]
    runtime_customization: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Scenario Run Schemas
class ScenarioRunCreate(BaseModel):
    template_id: int
    name: str
    config: Dict[str, Any] = {}
    runtime_customizations: Optional[Dict[str, Any]] = None


class ScenarioRunUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class ScenarioRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    template_id: int
    name: str
    status: str
    config: Dict[str, Any]
    runtime_customizations: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


# Event Schemas
class EventTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_category: str = "custom"
    data_schema: Dict[str, Any] = {}
    validation_rules: Optional[Dict[str, Any]] = None


class EventTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_category: Optional[str] = None
    data_schema: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None


class EventTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    event_category: str
    data_schema: Dict[str, Any]
    validation_rules: Optional[Dict[str, Any]]
    created_at: datetime


class EventInstanceCreate(BaseModel):
    event_type_id: int
    scenario_run_id: int
    agent_instance_id: Optional[int] = None
    source_agent_id: Optional[int] = None
    target_agent_id: Optional[int] = None
    data: Dict[str, Any] = {}
    priority: int = Field(default=5, ge=1, le=10)


class EventInstanceUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    processing_result: Optional[Dict[str, Any]] = None
    error_info: Optional[Dict[str, Any]] = None


class EventInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type_id: int
    scenario_run_id: int
    agent_instance_id: Optional[int]
    source_agent_id: Optional[int]
    target_agent_id: Optional[int]
    data: Dict[str, Any]
    status: str
    priority: int
    processing_result: Optional[Dict[str, Any]]
    error_info: Optional[Dict[str, Any]]
    timestamp: datetime
    processed_at: Optional[datetime]


# Execution Log Schemas
class ExecutionLogCreate(BaseModel):
    scenario_run_id: int
    agent_instance_id: Optional[int] = None
    event_instance_id: Optional[int] = None
    engine_type: Optional[str] = None
    level: str
    message: str
    data: Dict[str, Any] = {}
    context: Optional[Dict[str, Any]] = None


class ExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    scenario_run_id: int
    agent_instance_id: Optional[int]
    event_instance_id: Optional[int]
    engine_type: Optional[str]
    level: str
    message: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]]
    timestamp: datetime


# Engine Management Schemas
class ResourceLimits(BaseModel):
    max_concurrent_events: int = Field(gt=0)
    memory_limit_mb: Optional[int] = Field(gt=0)
    cpu_limit_percent: Optional[int] = Field(ge=1, le=100)
    max_processing_time_seconds: Optional[int] = Field(gt=0)


class EngineCapabilities(BaseModel):
    supported_event_types: List[str] = Field(min_length=1)
    max_concurrent_agents: int = Field(gt=0)
    supports_streaming: bool = False
    supports_memory_persistence: bool = True
    custom_capabilities: Dict[str, Any] = Field(default_factory=dict)


class EngineRegistration(BaseModel):
    engine_type: EngineType = Field(..., description="Type of engine being registered")
    engine_id: str = Field(min_length=1, description="Unique identifier for this engine instance")
    capabilities: EngineCapabilities
    resource_limits: ResourceLimits
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EngineHeartbeat(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    current_workload: int = Field(ge=0)
    resource_utilization: Dict[str, float] = {}
    active_agents: int = Field(ge=0)
    processed_events_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    last_error: Optional[str] = None


class EngineStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    engine_type: str
    status: str
    last_heartbeat: datetime
    current_workload: int
    active_agents: int
    processed_events_count: int
    error_count: int
    capabilities: Dict[str, Any]
    resource_limits: Dict[str, Any]
    engine_metadata: Dict[str, Any]
    performance_metrics: Optional[Dict[str, Any]]


class EventQueueRequest(BaseModel):
    engine_type: EngineType
    engine_id: str
    max_events: int = Field(gt=0, le=100)
    priority_filter: Optional[List[int]] = None
    event_type_filter: Optional[List[str]] = None


class EventStatusUpdate(BaseModel):
    event_id: int
    status: Literal["processing", "completed", "failed", "retrying"]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None
    retry_count: Optional[int] = None


class QueuedEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type_id: int
    scenario_run_id: int
    agent_instance_id: Optional[int]
    status: str
    priority: int
    data: Dict[str, Any]
    assigned_engine_id: Optional[str]
    processing_attempts: int
    created_at: datetime
    assigned_at: Optional[datetime]


# Template Validation Schemas
class TemplateValidationRequest(BaseModel):
    template_type: Literal["agent", "scenario"]
    template_data: Dict[str, Any]
    strict_validation: bool = True


class ValidationError(BaseModel):
    field: str
    message: str
    error_type: str
    invalid_value: Optional[Any] = None


class TemplateValidationResponse(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)


# Runtime Configuration Schemas
class RuntimeConfigurationRequest(BaseModel):
    agent_instance_id: int
    configuration_updates: Dict[str, Any]
    override_policies: Optional[Dict[str, RuntimeOverridePolicy]] = None
    validate_before_apply: bool = True


class RuntimeConfigurationResponse(BaseModel):
    success: bool
    applied_changes: Dict[str, Any]
    rejected_changes: Dict[str, str] = Field(default_factory=dict)
    current_configuration: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)


# Analytics and Metrics Schemas
class ScenarioMetrics(BaseModel):
    total_events: int = 0
    completed_events: int = 0
    failed_events: int = 0
    average_processing_time_ms: float = 0.0
    agent_interaction_count: int = 0
    scenario_health_score: float = 1.0
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class AgentMetrics(BaseModel):
    messages_sent: int = 0
    messages_received: int = 0
    tools_used: int = 0
    average_response_time_ms: float = 0.0
    error_count: int = 0
    memory_usage_mb: float = 0.0
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class EngineMetrics(BaseModel):
    events_processed: int = 0
    average_processing_time_ms: float = 0.0
    error_rate: float = 0.0
    resource_utilization: Dict[str, float] = Field(default_factory=dict)
    throughput_events_per_second: float = 0.0
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class SystemMetricsResponse(BaseModel):
    scenario_metrics: Dict[int, ScenarioMetrics] = Field(default_factory=dict)
    agent_metrics: Dict[int, AgentMetrics] = Field(default_factory=dict)
    engine_metrics: Dict[str, EngineMetrics] = Field(default_factory=dict)
    system_health: Literal["healthy", "degraded", "critical"] = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)


# Bulk Operations Schemas
class BulkAgentCreate(BaseModel):
    agents: List[AgentInstanceCreate]
    scenario_run_id: int
    fail_on_error: bool = True


class BulkAgentResponse(BaseModel):
    successful: List[AgentInstanceResponse] = Field(default_factory=list)
    failed: List[Dict[str, Any]] = Field(default_factory=list)
    total_requested: int
    total_successful: int
    total_failed: int


class BulkEventCreate(BaseModel):
    events: List[EventInstanceCreate]
    scenario_run_id: int
    fail_on_error: bool = False


class BulkEventResponse(BaseModel):
    successful: List[EventInstanceResponse] = Field(default_factory=list)
    failed: List[Dict[str, Any]] = Field(default_factory=list)
    total_requested: int
    total_successful: int
    total_failed: int
