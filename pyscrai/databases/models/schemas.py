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
class EngineRegistration(BaseModel):
    """Schema for engine instance registration"""
    engine_type: str = Field(..., description="Type of engine (actor/narrator/analyst)")
    capabilities: List[str] = Field(default_factory=list, description="List of engine capabilities")
    resource_limits: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resource limits for the engine instance"
    )


class EngineHeartbeat(BaseModel):
    """Schema for engine heartbeat updates"""
    status: str = Field(..., description="Current engine status")
    current_workload: int = Field(..., description="Number of events currently being processed")
    resource_utilization: Dict[str, float] = Field(
        default_factory=dict,
        description="Current resource usage metrics"
    )


class EngineStateResponse(BaseModel):
    """Schema for engine state responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    engine_type: str
    status: str
    last_heartbeat: Optional[datetime]
    current_workload: int
    metadata: Dict[str, Any]


# Event Processing Schemas
class EventQueueRequest(BaseModel):
    """Schema for requesting events from the queue"""
    engine_type: str
    batch_size: int = Field(default=3, ge=1, le=10)
    capabilities: List[str] = Field(default_factory=list)


class EventStatusUpdate(BaseModel):
    """Schema for updating event status"""
    status: str = Field(..., description="new status (completed/failed)")
    result: Optional[Dict[str, Any]] = Field(
        None, 
        description="Processing result for completed events"
    )
    error: Optional[str] = Field(
        None,
        description="Error message for failed events"
    )


class QueuedEventResponse(BaseModel):
    """Schema for events returned from the queue"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type_id: int
    event_type: str
    priority: int
    data: Dict[str, Any]
    lock_until: datetime
    retry_count: int
