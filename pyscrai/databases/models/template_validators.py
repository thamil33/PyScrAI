"""
Enhanced Pydantic models for template validation
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    GROQ = "groq"
    LOCAL = "local"


class LLMConfig(BaseModel):
    """Validation model for LLM configuration"""
    provider: ModelProvider
    model_id: str = Field(..., description="Model identifier (e.g., 'gpt-4', 'claude-3')")
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)

    @field_validator('model_id')
    @classmethod
    def validate_model_id(cls, v):
        if not v:
            raise ValueError("model_id cannot be empty")
        return v


class ToolConfig(BaseModel):
    """Validation model for tool configuration"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class PersonalityConfig(BaseModel):
    """Validation model for agent personality configuration"""
    role: str = Field(..., description="Agent's role or purpose")
    backstory: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    traits: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
    instructions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if not v.strip():
            raise ValueError("role cannot be empty")
        return v


class AgentRole(BaseModel):
    """Validation model for agent roles in scenarios"""
    template_name: str = Field(..., description="Name of the agent template to use")
    role_config: Dict[str, Any] = Field(default_factory=dict)
    required: bool = True


class EventType(str, Enum):
    """Types of events in the scenario flow"""
    TRIGGER = "trigger"
    RESPONSE = "response"
    INTERACTION = "interaction"
    STATE_CHANGE = "state_change"
    ERROR = "error"


class EventDefinition(BaseModel):
    """Validation model for event definitions"""
    type: EventType
    source: Optional[str] = None
    target: Optional[str] = None
    data_schema: Dict[str, Any] = Field(default_factory=dict)
    conditions: Dict[str, Any] = Field(default_factory=dict)


class ScenarioConfig(BaseModel):
    """Validation model for scenario configuration"""
    max_turns: int = Field(100, gt=0)
    timeout_seconds: int = Field(3600, gt=0)
    completion_conditions: Dict[str, Any] = Field(default_factory=dict)
    error_handling: Dict[str, Any] = Field(default_factory=dict)


# Full template validation models that use the above components
class AgentTemplateValidator(BaseModel):
    """Complete validation model for agent templates"""
    name: str
    description: Optional[str] = None
    personality_config: PersonalityConfig
    llm_config: LLMConfig
    tools_config: Dict[str, ToolConfig] = Field(default_factory=dict)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v


class ScenarioTemplateValidator(BaseModel):
    """Complete validation model for scenario templates"""
    name: str
    description: Optional[str] = None
    config: ScenarioConfig
    agent_roles: Dict[str, AgentRole]
    event_flow: Dict[str, EventDefinition]

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v

    @field_validator('agent_roles')
    @classmethod
    def validate_agent_roles(cls, v):
        if not v:
            raise ValueError("at least one agent role must be defined")
        return v
