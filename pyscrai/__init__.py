"""
PyScrAI:

A refined approach for simulating AI scenarios via a modular and extensible framework.
This package provides tools for creating, managing, and executing AI agents and rich scenarios. 
"""

__version__ = "0.1.0"

from pyscrai.databases import init_database, get_db, get_db_session
from pyscrai.factories import TemplateManager, AgentFactory, ScenarioFactory
from pyscrai.engines.base_engine import BaseEngine
from pyscrai.engines import (
    ContextManager,
    GlobalMemorySystem,
    GlobalToolIntegration,
    AgentEngineIntegration
)
from .utils.config import Config, settings

__all__ = [
    "init_database",
    "get_db",
    "get_db_session", 
    "TemplateManager",
    "AgentFactory",
    "ScenarioFactory",
    "BaseEngine",
    "ContextManager", 
    "GlobalMemorySystem",
    "GlobalToolIntegration",
    "AgentEngineIntegration",
    "Config",
    "settings"
]
