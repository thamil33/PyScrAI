"""
Main framework class for the LangGraph Multi-Agent Simulation Framework.
"""

from typing import Dict, Any, List, Optional, Type, Union
from pathlib import Path
import asyncio
from datetime import datetime

from ..state.simulation_state import SimulationState, AgentState
from ..agents.base_agent import BaseAgent, Command
from ..llm_providers.base_provider import LLMProvider
from ..utils.logging_config import setup_logging, get_logger, get_metrics
from .config import FrameworkConfig, get_config


class SimulationFramework:
    """
    Main framework class for orchestrating multi-agent simulations.
    
    Provides a high-level interface for creating, configuring, and running
    multi-agent simulations with LangGraph workflow orchestration.
    """
    
    def __init__(
        self,
        config: Optional[FrameworkConfig] = None,
        primary_llm: Optional[LLMProvider] = None,
        fallback_llm: Optional[LLMProvider] = None
    ):
        """
        Initialize the simulation framework.
        
        Args:
            config: Framework configuration (loads from env if not provided)
            primary_llm: Primary LLM provider
            fallback_llm: Fallback LLM provider
        """
        self.config = config or get_config()
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm
        
        # Set up logging and metrics
        self._setup_logging()
        self.logger = get_logger("simulation_framework")
        self.metrics = get_metrics()
        
        # Initialize framework
        self.config.create_state_directory()
        self._validate_configuration()
        
        # Runtime state
        self.active_simulations: Dict[str, SimulationState] = {}
        self.registered_agents: Dict[str, Type[BaseAgent]] = {}
        self.registered_modules: Dict[str, Any] = {}
        
        self.logger.info("Framework initialized", config=self.config.model_dump())
    
    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        log_file = None
        if self.config.state.directory:
            log_file = self.config.state.directory / "framework.log"
        
        setup_logging(
            level=self.config.log_level,
            log_file=log_file,
            enable_structured=True,
            enable_metrics=self.config.enable_metrics
        )
    
    def _validate_configuration(self) -> None:
        """Validate framework configuration."""
        if not self.config.validate_llm_providers() and not (self.primary_llm or self.fallback_llm):
            raise ValueError(
                "At least one LLM provider must be configured either in config or passed directly"
            )
        
        self.logger.info("Configuration validated successfully")
    
    async def create_simulation(
        self,
        simulation_id: Optional[str] = None,
        module_name: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> SimulationState:
        """
        Create a new simulation.
        
        Args:
            simulation_id: Optional custom simulation ID
            module_name: Name of the module to use
            initial_context: Initial shared context
            
        Returns:
            New simulation state
        """
        state = SimulationState(
            simulation_id=simulation_id,
            module_name=module_name,
            shared_context=initial_context or {}
        )
        
        self.active_simulations[state.simulation_id] = state
        
        self.logger.info(
            "Simulation created",
            simulation_id=state.simulation_id,
            module=module_name
        )
        
        self.metrics.increment("simulations_created", module=module_name or "unknown")
        
        return state
    
    async def add_agent_to_simulation(
        self,
        simulation_id: str,
        agent: BaseAgent,
        auto_initialize: bool = True
    ) -> None:
        """
        Add an agent to a simulation.
        
        Args:
            simulation_id: Target simulation ID
            agent: Agent instance to add
            auto_initialize: Whether to automatically initialize the agent
        """
        if simulation_id not in self.active_simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        state = self.active_simulations[simulation_id]
        
        # Create agent state entry
        agent_state = AgentState(
            name=agent.name,
            agent_type=agent.agent_type,
            configuration=agent.personality_config
        )
        
        state.add_agent(agent_state)
        
        if auto_initialize:
            await agent.initialize(state)
        
        self.logger.info(
            "Agent added to simulation",
            simulation_id=simulation_id,
            agent=agent.name,
            agent_type=agent.agent_type
        )
        
        self.metrics.increment("agents_added", agent_type=agent.agent_type)
    
    async def run_simulation_step(
        self,
        simulation_id: str,
        agent: BaseAgent,
        max_retries: int = 3
    ) -> Command:
        """
        Run a single simulation step with an agent.
        
        Args:
            simulation_id: Target simulation ID
            agent: Agent to execute
            max_retries: Maximum retry attempts on error
            
        Returns:
            Command returned by the agent
        """
        if simulation_id not in self.active_simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        state = self.active_simulations[simulation_id]
        
        for attempt in range(max_retries + 1):
            try:
                start_time = datetime.now()
                
                # Update active agent
                state.active_agent = agent.name
                
                # Process with agent
                command = await agent.process(state)
                
                # Record timing
                duration = (datetime.now() - start_time).total_seconds()
                self.metrics.timing("agent_processing_time", duration, agent=agent.name)
                
                # Apply any state updates from command
                if command.updates:
                    for key, value in command.updates.items():
                        if hasattr(state, key):
                            setattr(state, key, value)
                
                # Add message if provided
                if command.message:
                    from ..state.simulation_state import Message
                    message = Message(
                        sender=agent.name,
                        content=command.message,
                        metadata=command.metadata
                    )
                    state.add_message(message)
                
                self.logger.info(
                    "Simulation step completed",
                    simulation_id=simulation_id,
                    agent=agent.name,
                    action=command.action,
                    duration=duration
                )
                
                return command
                
            except Exception as error:
                self.logger.error(
                    "Simulation step failed",
                    simulation_id=simulation_id,
                    agent=agent.name,
                    attempt=attempt + 1,
                    error=str(error)
                )
                
                if attempt < max_retries:
                    continue
                
                # Handle error through agent
                command = await agent.handle_error(error, state)
                return command
        
        # Should not reach here, but safety fallback
        return Command(action="error", message="Max retries exceeded")
    
    async def save_simulation(self, simulation_id: str, file_path: Optional[Path] = None) -> Path:
        """
        Save simulation state to file.
        
        Args:
            simulation_id: Simulation to save
            file_path: Optional custom file path
            
        Returns:
            Path where simulation was saved
        """
        if simulation_id not in self.active_simulations:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        state = self.active_simulations[simulation_id]
        
        if not file_path:
            file_path = self.config.state.directory / f"{simulation_id}.json"
        
        state.save_to_file(file_path)
        
        self.logger.info(
            "Simulation saved",
            simulation_id=simulation_id,
            file_path=str(file_path)
        )
        
        return file_path
    
    async def load_simulation(self, file_path: Path) -> str:
        """
        Load simulation state from file.
        
        Args:
            file_path: Path to simulation file
            
        Returns:
            Loaded simulation ID
        """
        state = SimulationState.load_from_file(file_path)
        self.active_simulations[state.simulation_id] = state
        
        self.logger.info(
            "Simulation loaded",
            simulation_id=state.simulation_id,
            file_path=str(file_path)
        )
        
        return state.simulation_id
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """Get simulation state by ID."""
        return self.active_simulations.get(simulation_id)
    
    def list_simulations(self) -> List[str]:
        """List active simulation IDs."""
        return list(self.active_simulations.keys())
    
    async def cleanup_simulation(self, simulation_id: str) -> None:
        """
        Clean up and remove a simulation.
        
        Args:
            simulation_id: Simulation to clean up
        """
        if simulation_id in self.active_simulations:
            state = self.active_simulations[simulation_id]
            
            # Mark as completed if still running
            if state.status == "running":
                state.complete_simulation()
            
            # Remove from active simulations
            del self.active_simulations[simulation_id]
            
            self.logger.info("Simulation cleaned up", simulation_id=simulation_id)
    
    def register_agent_type(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent type for use in simulations."""
        self.registered_agents[name] = agent_class
        self.logger.info("Agent type registered", name=name, agent_class=agent_class.__name__)
    
    def register_module(self, name: str, module: Any) -> None:
        """Register a simulation module."""
        self.registered_modules[name] = module
        self.logger.info("Module registered", name=name)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        return {
            "active_simulations": len(self.active_simulations),
            "registered_agents": len(self.registered_agents),
            "registered_modules": len(self.registered_modules),
            "metrics": self.metrics.get_metrics()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on framework and providers."""
        health = {
            "framework": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_simulations": len(self.active_simulations),
            "providers": {}
        }
        
        # Check LLM providers
        if self.primary_llm:
            try:
                health["providers"]["primary"] = await self.primary_llm.health_check()
            except Exception as e:
                health["providers"]["primary"] = f"error: {str(e)}"
        
        if self.fallback_llm:
            try:
                health["providers"]["fallback"] = await self.fallback_llm.health_check()
            except Exception as e:
                health["providers"]["fallback"] = f"error: {str(e)}"
        
        return health
