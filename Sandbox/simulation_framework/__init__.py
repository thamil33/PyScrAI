"""
LangGraph Multi-Agent Simulation Framework

A flexible framework for creating and orchestrating multi-agent simulations
using LangGraph, supporting both cloud (OpenRouter) and local (LM Studio) LLMs.
"""

__version__ = "0.1.0"
__author__ = "LangGraph Multi-Agent Simulation Framework Team"

# Core imports for convenient access
from .core.framework import SimulationFramework
from .core.config import FrameworkConfig
from .state.simulation_state import SimulationState

__all__ = [
    "SimulationFramework",
    "FrameworkConfig", 
    "SimulationState",
]
