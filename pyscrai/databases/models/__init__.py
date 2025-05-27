"""
Database models for PyScrAI - Universal Templates and Custom Engines
"""

# Import base first
from .base import Base

# Then import models in dependency order
from .core_models import AgentTemplate, ScenarioTemplate, AgentInstance, ScenarioRun
from .execution_models import EventType, EventInstance, ExecutionLog, EngineState, QueuedEvent, SystemMetrics, TemplateUsage

# Export all models for easy importing
__all__ = [
    "Base",
    # Core template models
    "AgentTemplate",
    "ScenarioTemplate",
    # Execution models
    "AgentInstance", 
    "ScenarioRun",
    "EventType",
    "EventInstance",
    "ExecutionLog",
    "EngineState",
    "QueuedEvent",
    "SystemMetrics",
    "TemplateUsage"
]
