"""
Agent Runtime System for PyScrAI

Connects AgentInstances to appropriate engines and manages their lifecycle
during scenario execution. This is the core component for Agent-Engine Integration.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Type
from sqlalchemy.orm import Session

from pyscrai.databases.models import AgentInstance, AgentTemplate, ScenarioRun
from pyscrai.engines.base_engine import BaseEngine
from pyscrai.engines.actor_engine import ActorEngine
from pyscrai.engines.narrator_engine import NarratorEngine
from pyscrai.engines.analyst_engine import AnalystEngine


class AgentRuntime:
    """
    Runtime system that manages the connection between AgentInstances and their engines.
    Handles agent lifecycle, context sharing, and engine coordination.
    """
    
    def __init__(self, db: Session, storage_base_path: str = "./data/agent_storage"):
        """
        Initialize the Agent Runtime.
        
        Args:
            db: Database session for agent operations
            storage_base_path: Base path for agent storage files
        """
        self.db = db
        self.storage_base_path = storage_base_path
        # Import AgentFactory dynamically to avoid circular imports
        from ..factories.agent_factory import AgentFactory
        self.agent_factory = AgentFactory(db)
        self.active_agents: Dict[int, Dict[str, Any]] = {}  # agent_instance_id -> runtime info
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Engine type mapping
        self.engine_types: Dict[str, Type[BaseEngine]] = {
            "actor": ActorEngine,
            "narrator": NarratorEngine, 
            "analyst": AnalystEngine,
            "base": BaseEngine
        }
        
        self.logger.info("AgentRuntime initialized")
    
    async def start_agent(
        self, 
        agent_instance_id: int, 
        engine_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Start an agent instance with its appropriate engine.
        
        Args:
            agent_instance_id: ID of the agent instance to start
            engine_type: Override engine type (if None, determined from template)
            context: Initial context to pass to the agent
            
        Returns:
            True if agent started successfully, False otherwise
        """
        try:
            # Get agent instance from database
            instance = self.agent_factory.get_instance(agent_instance_id)
            if not instance:
                self.logger.error(f"Agent instance {agent_instance_id} not found")
                return False
            
            # Determine engine type
            if not engine_type:
                engine_type = self._determine_engine_type(instance)
            
            # Create storage path for this agent
            storage_path = f"{self.storage_base_path}/agent_{agent_instance_id}.db"
            
            # Create engine directly since we have simplified the system
            engine_class = self.engine_types.get(engine_type, BaseEngine)
            
            # Create agent config from instance
            agent_config = {
                "instance_id": agent_instance_id,
                "template_name": instance.template.name,
                "personality_config": instance.template.personality_config or {},
                "runtime_config": instance.runtime_config or {}
            }
            
            # Create engine instance
            engine = engine_class(
                agent_config=agent_config,
                engine_name=f"{instance.instance_name}_{engine_type}",
                storage_path=storage_path
            )
            
            await engine.initialize()
            
            # Store runtime information
            runtime_info = {
                "instance": instance,
                "engine": engine,
                "engine_type": engine_type,
                "storage_path": storage_path,
                "context": context or {},
                "started_at": asyncio.get_event_loop().time(),
                "status": "active"
            }
            
            self.active_agents[agent_instance_id] = runtime_info
            
            # Update agent instance state
            self.agent_factory.update_instance_state(
                agent_instance_id, 
                {
                    "runtime_status": "active",
                    "engine_type": engine_type,
                    "engine_id": engine.engine_id
                }
            )
            
            self.logger.info(f"Agent {agent_instance_id} started with {engine_type} engine")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start agent {agent_instance_id}: {e}", exc_info=True)
            return False
    
    async def stop_agent(self, agent_instance_id: int) -> bool:
        """
        Stop an active agent and clean up its resources.
        
        Args:
            agent_instance_id: ID of the agent instance to stop
            
        Returns:
            True if agent stopped successfully, False otherwise
        """
        try:
            if agent_instance_id not in self.active_agents:
                self.logger.warning(f"Agent {agent_instance_id} is not active")
                return False
            
            runtime_info = self.active_agents[agent_instance_id]
            engine = runtime_info["engine"]
            
            # Close engine resources
            await engine.shutdown()
            
            # Update agent instance state
            self.agent_factory.update_instance_state(
                agent_instance_id,
                {
                    "runtime_status": "stopped",
                    "stopped_at": asyncio.get_event_loop().time()
                }
            )
            
            # Remove from active agents
            del self.active_agents[agent_instance_id]
            
            self.logger.info(f"Agent {agent_instance_id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent {agent_instance_id}: {e}", exc_info=True)
            return False
    
    async def send_message_to_agent(
        self, 
        agent_instance_id: int, 
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to an active agent and get its response.
        
        Args:
            agent_instance_id: ID of the target agent
            message: Message to send
            context: Additional context for the message
            
        Returns:
            Agent's response or None if failed
        """
        try:
            if agent_instance_id not in self.active_agents:
                self.logger.error(f"Agent {agent_instance_id} is not active")
                return None
            
            runtime_info = self.active_agents[agent_instance_id]
            engine = runtime_info["engine"]
            
            # Merge context
            full_context = {**runtime_info["context"], **(context or {})}
            
            # Add context to message if provided
            if full_context:
                contextual_message = f"Context: {full_context}\n\nMessage: {message}"
            else:
                contextual_message = message
            
            # Send message to engine
            response = await engine.run(contextual_message)
            
            # Update agent context with response
            if response.get("content"):
                runtime_info["context"]["last_response"] = response["content"]
                runtime_info["context"]["last_interaction"] = asyncio.get_event_loop().time()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to send message to agent {agent_instance_id}: {e}", exc_info=True)
            return None
    
    async def update_agent_context(
        self, 
        agent_instance_id: int, 
        context_update: Dict[str, Any]
    ) -> bool:
        """
        Update the context for an active agent.
        
        Args:
            agent_instance_id: ID of the agent to update
            context_update: Context data to merge
            
        Returns:
            True if context updated successfully, False otherwise
        """
        try:
            if agent_instance_id not in self.active_agents:
                self.logger.error(f"Agent {agent_instance_id} is not active")
                return False
            
            runtime_info = self.active_agents[agent_instance_id]
            runtime_info["context"].update(context_update)
            
            # Also update database state
            self.agent_factory.update_instance_state(
                agent_instance_id,
                {"runtime_context": runtime_info["context"]}
            )
            
            self.logger.debug(f"Updated context for agent {agent_instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update context for agent {agent_instance_id}: {e}", exc_info=True)
            return False
    
    def get_agent_context(self, agent_instance_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the current context for an active agent.
        
        Args:
            agent_instance_id: ID of the agent
            
        Returns:
            Agent's current context or None if not found
        """
        if agent_instance_id not in self.active_agents:
            return None
        
        return self.active_agents[agent_instance_id]["context"].copy()
    
    def list_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active agents and their status.
        
        Returns:
            List of agent information dictionaries
        """
        active_list = []
        for agent_id, runtime_info in self.active_agents.items():
            instance = runtime_info["instance"]
            active_list.append({
                "agent_instance_id": agent_id,
                "instance_name": instance.instance_name,
                "template_name": instance.template.name,
                "engine_type": runtime_info["engine_type"],
                "engine_id": runtime_info["engine"].engine_id,
                "status": runtime_info["status"],
                "started_at": runtime_info["started_at"]
            })
        
        return active_list
    
    async def start_scenario_agents(self, scenario_run_id: int) -> Dict[int, bool]:
        """
        Start all agents for a given scenario run.
        
        Args:
            scenario_run_id: ID of the scenario run
            
        Returns:
            Dictionary mapping agent_instance_id to success status
        """
        results = {}
        
        try:
            # Get all agent instances for this scenario
            instances = self.agent_factory.list_instances_for_scenario(scenario_run_id)
            
            # Start each agent
            for instance in instances:
                success = await self.start_agent(instance.id)
                results[instance.id] = success
                
                if success:
                    self.logger.info(f"Started agent {instance.instance_name} (ID: {instance.id})")
                else:
                    self.logger.error(f"Failed to start agent {instance.instance_name} (ID: {instance.id})")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to start scenario agents for run {scenario_run_id}: {e}", exc_info=True)
            return results
    
    async def stop_scenario_agents(self, scenario_run_id: int) -> Dict[int, bool]:
        """
        Stop all agents for a given scenario run.
        
        Args:
            scenario_run_id: ID of the scenario run
            
        Returns:
            Dictionary mapping agent_instance_id to success status
        """
        results = {}
        
        try:
            # Find all active agents for this scenario
            scenario_agents = []
            for agent_id, runtime_info in self.active_agents.items():
                if runtime_info["instance"].scenario_run_id == scenario_run_id:
                    scenario_agents.append(agent_id)
            
            # Stop each agent
            for agent_id in scenario_agents:
                success = await self.stop_agent(agent_id)
                results[agent_id] = success
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to stop scenario agents for run {scenario_run_id}: {e}", exc_info=True)
            return results
    
    def _determine_engine_type(self, instance: AgentInstance) -> str:
        """
        Determine the appropriate engine type for an agent instance.
        
        Args:
            instance: The agent instance
            
        Returns:
            Engine type string
        """
        # Check if engine type is specified in runtime config
        if instance.runtime_config and "engine_type" in instance.runtime_config:
            return instance.runtime_config["engine_type"]
        
        # Check template configuration
        template = instance.template
        if template.personality_config and "preferred_engine" in template.personality_config:
            return template.personality_config["preferred_engine"]
        
        # Default based on template name patterns
        template_name = template.name.lower()
        if "actor" in template_name or "character" in template_name:
            return "actor"
        elif "narrator" in template_name or "storyteller" in template_name:
            return "narrator"
        elif "analyst" in template_name or "observer" in template_name:
            return "analyst"
        
        # Default to base engine
        return "base"
    
    async def shutdown(self):
        """
        Shutdown the runtime and stop all active agents.
        """
        self.logger.info("Shutting down AgentRuntime...")
        
        # Stop all active agents
        agent_ids = list(self.active_agents.keys())
        for agent_id in agent_ids:
            await self.stop_agent(agent_id)
        
        self.logger.info("AgentRuntime shutdown complete")
