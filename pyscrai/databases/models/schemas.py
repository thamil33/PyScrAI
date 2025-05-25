"""
Pydantic schemas for API validation and serialization
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


# Agent Template Schemas
class AgentTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    personality_config: Dict[str, Any] = {}
    llm_config: Dict[str, Any] = {}
    tools_config: Dict[str, Any] = {}


class AgentTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    personality_config: Optional[Dict[str, Any]] = None
    llm_config: Optional[Dict[str, Any]] = None
    tools_config: Optional[Dict[str, Any]] = None


class AgentTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    personality_config: Dict[str, Any]
    llm_config: Dict[str, Any]
    tools_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Agent Instance Schemas
class AgentInstanceCreate(BaseModel):
    template_id: int
    scenario_run_id: int
    instance_name: str
    runtime_config: Dict[str, Any] = {}


class AgentInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    template_id: int
    scenario_run_id: int
    instance_name: str
    runtime_config: Dict[str, Any]
    state: Dict[str, Any]
    created_at: datetime


# Scenario Template Schemas
class ScenarioTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = {}
    agent_roles: Dict[str, Any] = {}
    event_flow: Dict[str, Any] = {}


class ScenarioTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    agent_roles: Optional[Dict[str, Any]] = None
    event_flow: Optional[Dict[str, Any]] = None


class ScenarioTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    config: Dict[str, Any]
    agent_roles: Dict[str, Any]
    event_flow: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Scenario Run Schemas
class ScenarioRunCreate(BaseModel):
    template_id: int
    name: str
    config: Dict[str, Any] = {}


class ScenarioRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    template_id: int
    name: str
    status: str
    config: Dict[str, Any]
    results: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


# Event Schemas
class EventTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    data_schema: Dict[str, Any] = {}


class EventTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    data_schema: Dict[str, Any]
    created_at: datetime


class EventInstanceCreate(BaseModel):
    event_type_id: int
    scenario_run_id: int
    agent_instance_id: Optional[int] = None
    data: Dict[str, Any] = {}


class EventInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type_id: int
    scenario_run_id: int
    agent_instance_id: Optional[int]
    data: Dict[str, Any]
    timestamp: datetime


# Execution Log Schemas
class ExecutionLogCreate(BaseModel):
    scenario_run_id: int
    agent_instance_id: Optional[int] = None
    event_instance_id: Optional[int] = None
    level: str
    message: str
    data: Dict[str, Any] = {}


class ExecutionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    scenario_run_id: int
    agent_instance_id: Optional[int]
    event_instance_id: Optional[int]
    level: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime


# Engine Management Schemas
class ResourceLimits(BaseModel):
    max_concurrent_events: int = Field(gt=0)
    memory_limit_mb: Optional[int] = Field(gt=0)


class EngineRegistration(BaseModel):
    engine_type: str = Field(min_length=1)
    capabilities: List[str] = Field(min_length=1)
    resource_limits: ResourceLimits


class EngineHeartbeat(BaseModel):
    status: str = Field(min_length=1)
    current_workload: int = Field(ge=0)
    resource_utilization: Dict[str, float] = {}


class EngineStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    engine_type: str
    status: str
    last_heartbeat: datetime
    current_workload: int
    engine_metadata: Dict[str, Any]


class EventQueueRequest(BaseModel):
    engine_type: str
    max_events: int = Field(gt=0, le=100)


class EventStatusUpdate(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class QueuedEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type_id: int
    status: str
    priority: int
    data: Dict[str, Any]
    processed_by_engines: List[str]
    created_at: datetime
