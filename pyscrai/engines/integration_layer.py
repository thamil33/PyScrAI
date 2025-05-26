"""
Integration Layer for PyScrAI Agent-Engine Integration

Connects AgentRuntime, ContextManager, MemorySystem, and ToolIntegration
to provide a unified interface for agent management and coordination.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from .agent_runtime import AgentRuntime
from .context_manager import ContextManager
from .memory_system import GlobalMemorySystem
from .tool_integration import GlobalToolIntegration
from ..databases.models import ScenarioRun, AgentInstance


class AgentEngineIntegration:
    """
    Central integration layer that coordinates all Agent-Engine Integration components.
    Provides a unified interface for managing agents, context, memory, and tools.
    """
    
    def __init__(self, db: Session, storage_base_path: str = "./data"):
        """
        Initialize the Agent-Engine Integration layer.
        
        Args:
            db: Database session
            storage_base_path: Base path for agent storage
        """
        self.db = db
        self.storage_base_path = storage_base_path
        
        # Initialize core systems
        self.agent_runtime = AgentRuntime(db, f"{storage_base_path}/agent_storage")
        self.context_manager = ContextManager(db)
        self.memory_system = GlobalMemorySystem(db)
        self.tool_integration = GlobalToolIntegration(db)
        
        # Track active scenarios
        self.active_scenarios: Dict[int, Dict[str, Any]] = {}  # scenario_run_id -> info
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("AgentEngineIntegration initialized")
    
    async def start_scenario(
        self, 
        scenario_run_id: int,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Start a complete scenario with all agents and systems.
        
        Args:
            scenario_run_id: ID of the scenario run
            initial_context: Initial context for the scenario
            
        Returns:
            True if scenario started successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting scenario {scenario_run_id}")
            
            # Initialize scenario context
            context_success = await self.context_manager.initialize_scenario_context(
                scenario_run_id, initial_context
            )
            if not context_success:
                self.logger.error(f"Failed to initialize context for scenario {scenario_run_id}")
                return False
            
            # Start all agents for this scenario
            agent_results = await self.agent_runtime.start_scenario_agents(scenario_run_id)
            
            # Initialize agent contexts and memory systems
            for agent_id, started in agent_results.items():
                if started:
                    # Initialize agent context
                    await self.context_manager.initialize_agent_context(
                        agent_id, scenario_run_id
                    )
                    
                    # Initialize agent memory system
                    memory_system = await self.memory_system.get_agent_memory_system(agent_id)
                    
                    # Get agent tool manager
                    tool_manager = await self.tool_integration.get_agent_tool_manager(agent_id)
                    
                    self.logger.info(f"Initialized systems for agent {agent_id}")
            
            # Track scenario
            self.active_scenarios[scenario_run_id] = {
                "started_agents": [aid for aid, success in agent_results.items() if success],
                "failed_agents": [aid for aid, success in agent_results.items() if not success],
                "started_at": asyncio.get_event_loop().time(),
                "status": "active"
            }
            
            success_count = len([s for s in agent_results.values() if s])
            total_count = len(agent_results)
            
            self.logger.info(f"Scenario {scenario_run_id} started: {success_count}/{total_count} agents")
            return success_count > 0  # Success if at least one agent started
            
        except Exception as e:
            self.logger.error(f"Failed to start scenario {scenario_run_id}: {e}", exc_info=True)
            return False
    
    async def stop_scenario(self, scenario_run_id: int) -> bool:
        """
        Stop a scenario and clean up all associated resources.
        
        Args:
            scenario_run_id: ID of the scenario run
            
        Returns:
            True if scenario stopped successfully, False otherwise
        """
        try:
            self.logger.info(f"Stopping scenario {scenario_run_id}")
            
            if scenario_run_id not in self.active_scenarios:
                self.logger.warning(f"Scenario {scenario_run_id} is not active")
                return False
            
            scenario_info = self.active_scenarios[scenario_run_id]
            
            # Stop all agents
            agent_results = await self.agent_runtime.stop_scenario_agents(scenario_run_id)
            
            # Clean up agent systems
            for agent_id in scenario_info["started_agents"]:
                # Save and cleanup memory
                await self.memory_system.cleanup_agent_memory(agent_id)
                
                # Cleanup tools
                await self.tool_integration.cleanup_agent_tools(agent_id)
            
            # Clean up scenario context
            await self.context_manager.cleanup_scenario_context(scenario_run_id)
            
            # Remove from active scenarios
            del self.active_scenarios[scenario_run_id]
            
            self.logger.info(f"Scenario {scenario_run_id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop scenario {scenario_run_id}: {e}", exc_info=True)
            return False
    
    async def send_agent_message(
        self,
        agent_instance_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        use_memory: bool = True,
        use_tools: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to an agent with full integration support.
        
        Args:
            agent_instance_id: ID of the target agent
            message: Message to send
            context: Additional context
            use_memory: Whether to include memory in context
            use_tools: Whether to allow tool usage
            
        Returns:
            Agent's response with enhanced context
        """
        try:
            # Get agent context
            agent_context = await self.context_manager.get_agent_context(
                agent_instance_id, include_scenario_context=True
            )
            
            if not agent_context:
                self.logger.error(f"No context found for agent {agent_instance_id}")
                return None
            
            # Enhance context with memory if requested
            if use_memory:
                memory_system = await self.memory_system.get_agent_memory_system(agent_instance_id)
                recent_memories = await memory_system.get_recent_memories(hours=24, limit=10)
                
                if recent_memories:
                    agent_context["recent_memories"] = [
                        {
                            "content": mem.content,
                            "importance": mem.importance,
                            "created_at": mem.created_at.isoformat()
                        }
                        for mem in recent_memories
                    ]
            
            # Add tool information if requested
            if use_tools:
                tool_manager = await self.tool_integration.get_agent_tool_manager(agent_instance_id)
                available_tools = await tool_manager.get_available_tools()
                agent_context["available_tools"] = available_tools
            
            # Merge with provided context
            full_context = {**agent_context, **(context or {})}
            
            # Send message to agent
            response = await self.agent_runtime.send_message_to_agent(
                agent_instance_id, message, full_context
            )
            
            if response and response.get("success"):
                # Store interaction in memory
                if use_memory:
                    memory_system = await self.memory_system.get_agent_memory_system(agent_instance_id)
                    await memory_system.add_memory(
                        content=f"User: {message}\nAgent: {response.get('content', '')}",
                        memory_type="episodic",
                        importance=0.6,
                        tags=["interaction", "conversation"]
                    )
                
                # Update agent context
                await self.context_manager.update_agent_context(
                    agent_instance_id,
                    {
                        "last_interaction": {
                            "message": message,
                            "response": response.get("content"),
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    }
                )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to send message to agent {agent_instance_id}: {e}", exc_info=True)
            return None
    
    async def execute_agent_tool(
        self,
        agent_instance_id: int,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool for an agent with full integration support.
        
        Args:
            agent_instance_id: ID of the agent
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Additional context
            
        Returns:
            Tool execution result
        """
        try:
            # Get tool manager
            tool_manager = await self.tool_integration.get_agent_tool_manager(agent_instance_id)
            
            # Execute tool
            result = await tool_manager.execute_tool(tool_name, parameters, context)
            
            # Store tool usage in memory if successful
            if result.get("success"):
                memory_system = await self.memory_system.get_agent_memory_system(agent_instance_id)
                await memory_system.add_memory(
                    content=f"Used tool '{tool_name}' with result: {result.get('result')}",
                    memory_type="procedural",
                    importance=0.4,
                    tags=["tool_usage", tool_name],
                    metadata={"tool_name": tool_name, "parameters": parameters}
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute tool for agent {agent_instance_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def share_context_between_agents(
        self,
        source_agent_id: int,
        target_agent_id: int,
        context_keys: List[str]
    ) -> bool:
        """
        Share context between two agents.
        
        Args:
            source_agent_id: Source agent ID
            target_agent_id: Target agent ID
            context_keys: Keys to share
            
        Returns:
            True if sharing successful
        """
        return await self.context_manager.share_context_between_agents(
            source_agent_id, target_agent_id, context_keys
        )
    
    async def add_shared_memory(
        self,
        scenario_run_id: int,
        memory_content: str,
        source_agent_id: Optional[int] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        Add a memory to the shared scenario memory pool.
        
        Args:
            scenario_run_id: Scenario ID
            memory_content: Memory content
            source_agent_id: Source agent (optional)
            importance: Memory importance
            tags: Memory tags
            
        Returns:
            True if memory added successfully
        """
        memory_data = {
            "content": memory_content,
            "importance": importance,
            "tags": tags or []
        }
        
        return await self.context_manager.add_shared_memory(
            scenario_run_id, memory_data, source_agent_id
        )
    
    def get_scenario_status(self, scenario_run_id: int) -> Optional[Dict[str, Any]]:
        """Get status information for a scenario."""
        if scenario_run_id not in self.active_scenarios:
            return None
        
        scenario_info = self.active_scenarios[scenario_run_id]
        
        # Get additional stats
        context_stats = self.context_manager.get_context_stats()
        memory_stats = self.memory_system.get_global_stats()
        tool_stats = self.tool_integration.get_global_tool_stats()
        
        return {
            "scenario_id": scenario_run_id,
            "status": scenario_info["status"],
            "started_at": scenario_info["started_at"],
            "active_agents": len(scenario_info["started_agents"]),
            "failed_agents": len(scenario_info["failed_agents"]),
            "agent_ids": scenario_info["started_agents"],
            "context_stats": context_stats,
            "memory_stats": memory_stats,
            "tool_stats": tool_stats
        }
    
    def list_active_scenarios(self) -> List[Dict[str, Any]]:
        """Get list of all active scenarios."""
        return [
            self.get_scenario_status(scenario_id)
            for scenario_id in self.active_scenarios.keys()
        ]
    
    async def shutdown(self):
        """Shutdown the integration layer and all subsystems."""
        self.logger.info("Shutting down AgentEngineIntegration...")
        
        # Stop all active scenarios
        scenario_ids = list(self.active_scenarios.keys())
        for scenario_id in scenario_ids:
            await self.stop_scenario(scenario_id)
        
        # Shutdown subsystems
        await self.agent_runtime.shutdown()
        await self.memory_system.save_all_memories()
        
        self.logger.info("AgentEngineIntegration shutdown complete")
