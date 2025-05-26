"""
Enhanced Pydantic models for template validation aligned with universal generic templates and custom engines
"""

from typing import Dict, List, Optional, Union, Any, Literal
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


class EngineType(str, Enum):
    """Supported engine types for agents"""
    ACTOR = "actor"
    ANALYST = "analyst"
    NARRATOR = "narrator"


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

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("tool name cannot be empty")
        return v


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


class RuntimeOverridePolicy(str, Enum):
    """Policies for runtime overrides"""
    OVERRIDE_ALLOWED = "override_allowed"
    MERGE_ALLOWED = "merge_allowed"
    APPEND_ALLOWED = "append_allowed"
    FORBIDDEN = "forbidden"


class RuntimeOverrides(BaseModel):
    """Validation model for runtime override configurations"""
    personality_config: Optional[Dict[str, RuntimeOverridePolicy]] = None
    llm_config: Optional[Dict[str, RuntimeOverridePolicy]] = None
    tools_config: Optional[Dict[str, RuntimeOverridePolicy]] = None
    # Engine-specific overrides
    narrative_style: Optional[RuntimeOverridePolicy] = None
    perspective: Optional[RuntimeOverridePolicy] = None
    analysis_focus: Optional[RuntimeOverridePolicy] = None
    metrics_tracked: Optional[RuntimeOverridePolicy] = None
    character_traits: Optional[RuntimeOverridePolicy] = None


class AgentRole(BaseModel):
    """Validation model for agent roles in scenarios"""
    template_name: str = Field(..., description="Name of the agent template to use")
    role_config: Dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    engine_type: EngineType = Field(..., description="Engine type for this role")

    @field_validator('template_name')
    @classmethod
    def validate_template_name(cls, v):
        if not v.strip():
            raise ValueError("template_name cannot be empty")
        return v


class EventType(str, Enum):
    """Types of events in the scenario flow"""
    SYSTEM = "system"
    TRIGGER = "trigger"
    NARRATIVE = "narrative"
    INTERACTION = "interaction"
    ANALYSIS = "analysis"
    STATE_CHANGE = "state_change"
    ERROR = "error"


class EventCondition(BaseModel):
    """Validation model for event conditions"""
    trigger: str = Field(..., description="What triggers this event")
    required: Optional[bool] = None
    required_if: Optional[str] = None
    repeatable: Optional[bool] = None
    max_iterations: Optional[Union[int, str]] = None
    n: Optional[int] = None  # For "every_n_turns" type triggers
    final: Optional[bool] = None


class EventDefinition(BaseModel):
    """Validation model for event definitions"""
    type: EventType
    source: str = Field(..., description="Source of the event")
    target: str = Field(..., description="Target of the event")
    data_schema: Dict[str, str] = Field(default_factory=dict, description="Schema for event data")
    conditions: EventCondition

    @field_validator('source', 'target')
    @classmethod
    def validate_source_target(cls, v):
        if not v.strip():
            raise ValueError("source and target cannot be empty")
        return v


class InteractionRules(BaseModel):
    """Validation model for interaction rules"""
    turn_based: bool = True
    allow_interruptions: bool = False
    require_responses: bool = True


class CompletionConditions(BaseModel):
    """Validation model for scenario completion conditions"""
    natural_conclusion: bool = True
    max_turns_reached: bool = True
    timeout_reached: bool = True
    custom_conditions: Dict[str, Any] = Field(default_factory=dict)


class ErrorHandling(BaseModel):
    """Validation model for error handling configuration"""
    retry_attempts: int = Field(3, ge=0)
    fallback_responses: bool = True
    graceful_degradation: bool = True
    custom_handlers: Dict[str, Any] = Field(default_factory=dict)


class ScenarioConfig(BaseModel):
    """Validation model for scenario configuration"""
    max_turns: int = Field(100, gt=0)
    timeout_seconds: int = Field(3600, gt=0)
    completion_conditions: CompletionConditions = Field(default_factory=CompletionConditions)
    error_handling: ErrorHandling = Field(default_factory=ErrorHandling)
    interaction_rules: InteractionRules = Field(default_factory=InteractionRules)


class RuntimeCustomization(BaseModel):
    """Validation model for runtime customization options"""
    agent_personalities: Literal["configurable", "fixed"] = "configurable"
    conversation_topic: Literal["configurable", "fixed"] = "configurable"
    interaction_style: Literal["configurable", "fixed"] = "configurable"
    completion_criteria: Literal["configurable", "fixed"] = "configurable"
    custom_fields: Dict[str, Literal["configurable", "fixed"]] = Field(default_factory=dict)


# Full template validation models that use the above components
class AgentTemplateValidator(BaseModel):
    """Complete validation model for agent templates aligned with universal generic templates"""
    name: str
    description: Optional[str] = None
    engine_type: EngineType = Field(..., description="Engine type for this agent template")
    personality_config: PersonalityConfig
    llm_config: LLMConfig
    tools_config: Dict[str, ToolConfig] = Field(default_factory=dict)
    runtime_overrides: Optional[RuntimeOverrides] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v

    @field_validator('tools_config')
    @classmethod
    def validate_tools_config(cls, v):
        # Validate that tool names in the dict match the tool config names
        for tool_key, tool_config in v.items():
            if tool_key != tool_config.name:
                raise ValueError(f"Tool key '{tool_key}' does not match tool name '{tool_config.name}'")
        return v


class ScenarioTemplateValidator(BaseModel):
    """Complete validation model for scenario templates aligned with universal generic templates"""
    name: str
    description: Optional[str] = None
    config: ScenarioConfig
    agent_roles: Dict[str, AgentRole]
    event_flow: Dict[str, EventDefinition]
    runtime_customization: Optional[RuntimeCustomization] = None

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
        
        # Check for required roles
        required_roles = [role_name for role_name, role in v.items() if role.required]
        if not required_roles:
            raise ValueError("at least one agent role must be marked as required")
        
        return v

    @field_validator('event_flow')
    @classmethod
    def validate_event_flow(cls, v):
        if not v:
            raise ValueError("event_flow cannot be empty")
        
        # Validate that there's at least one system initialization event (system or trigger)
        system_events = [event for event in v.values() if event.type in [EventType.SYSTEM, EventType.TRIGGER]]
        if not system_events:
            raise ValueError("at least one system or trigger event must be defined for scenario initialization")
        
        return v


# Engine-specific validators for specialized configurations
class ActorEngineConfig(BaseModel):
    """Specific configuration for actor engines"""
    character_reasoning: bool = True
    context_window: int = Field(10, gt=0)
    emotional_modeling: bool = False
    relationship_tracking: bool = False


class AnalystEngineConfig(BaseModel):
    """Specific configuration for analyst engines"""
    default_metrics: List[str] = Field(default_factory=lambda: [
        "interaction_count", "response_time", "sentiment_score", "complexity_level"
    ])
    analysis_frequency: int = Field(5, gt=0, description="Analyze every N turns")
    behavioral_patterns: bool = True
    interaction_analysis: bool = True
    insight_generation: bool = True


class NarratorEngineConfig(BaseModel):
    """Specific configuration for narrator engines"""
    sensory_details: bool = True
    atmospheric_focus: bool = True
    smooth_bridging: bool = True
    default_perspective: str = "third_person"
    narrative_style: str = "descriptive"


class EngineSpecificValidator(BaseModel):
    """Validator for engine-specific configurations"""
    actor: Optional[ActorEngineConfig] = None
    analyst: Optional[AnalystEngineConfig] = None
    narrator: Optional[NarratorEngineConfig] = None

    @field_validator('actor', 'analyst', 'narrator')
    @classmethod
    def validate_engine_configs(cls, v, info):
        # Only validate if the config is provided
        return v


# Enhanced template validator that includes engine-specific validation
class UniversalAgentTemplateValidator(AgentTemplateValidator):
    """Enhanced agent template validator with engine-specific validation"""
    engine_specific_config: Optional[EngineSpecificValidator] = None

    @field_validator('engine_specific_config')
    @classmethod
    def validate_engine_specific_config(cls, v, info):
        if v and 'engine_type' in info.data:
            engine_type = info.data['engine_type']
            
            # Ensure only the relevant engine config is provided
            if engine_type == EngineType.ACTOR and v.analyst is not None:
                raise ValueError("analyst config should not be provided for actor engine")
            elif engine_type == EngineType.ACTOR and v.narrator is not None:
                raise ValueError("narrator config should not be provided for actor engine")
            elif engine_type == EngineType.ANALYST and v.actor is not None:
                raise ValueError("actor config should not be provided for analyst engine")
            elif engine_type == EngineType.ANALYST and v.narrator is not None:
                raise ValueError("narrator config should not be provided for analyst engine")
            elif engine_type == EngineType.NARRATOR and v.actor is not None:
                raise ValueError("actor config should not be provided for narrator engine")
            elif engine_type == EngineType.NARRATOR and v.analyst is not None:
                raise ValueError("analyst config should not be provided for narrator engine")
        
        return v
