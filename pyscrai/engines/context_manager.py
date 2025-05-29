"""
Context Manager for PyScrAI

Manages shared context between agents in a scenario, enabling context passing
and maintaining scenario-wide state information.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from sqlalchemy.orm import Session

from pyscrai.databases.models import ScenarioRun, AgentInstance, ExecutionLog


class ContextManager:
    """
    Manages shared context and state information across agents in a scenario.
    Provides context isolation, sharing mechanisms, and persistence.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the Context Manager.
        
        Args:
            db: Database session for persistence
        """
        self.db = db
        self.scenario_contexts: Dict[int, Dict[str, Any]] = {}  # scenario_run_id -> context
        self.agent_contexts: Dict[int, Dict[str, Any]] = {}  # agent_instance_id -> context
        self.shared_memories: Dict[int, List[Dict[str, Any]]] = {}  # scenario_run_id -> memories
        self.context_locks: Dict[int, asyncio.Lock] = {}  # scenario_run_id -> lock
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("ContextManager initialized")
    
    async def initialize_scenario_context(
        self, 
        scenario_run_id: int, 
        initial_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Initialize context for a new scenario run.
        
        Args:
            scenario_run_id: ID of the scenario run
            initial_context: Initial context data
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Get scenario run from database
            scenario_run = self.db.query(ScenarioRun).filter(
                ScenarioRun.id == scenario_run_id
            ).first()
            
            if not scenario_run:
                self.logger.error(f"Scenario run {scenario_run_id} not found")
                return False
            
            # Create context lock
            self.context_locks[scenario_run_id] = asyncio.Lock()
            
            # Initialize scenario context
            context = {
                "scenario_id": scenario_run_id,
                "scenario_name": scenario_run.name,
                "template_name": scenario_run.template.name if scenario_run.template else "Unknown",
                "started_at": datetime.utcnow().isoformat(),
                "status": scenario_run.status,
                "config": scenario_run.config or {},
                "global_state": {},
                "event_history": [],
                "agent_interactions": [],
                **(initial_context or {})
            }
            
            self.scenario_contexts[scenario_run_id] = context
            self.shared_memories[scenario_run_id] = []
            
            # Log initialization
            await self._log_context_event(
                scenario_run_id, 
                "CONTEXT_INITIALIZED", 
                {"initial_context_keys": list(context.keys())}
            )
            
            self.logger.info(f"Initialized context for scenario {scenario_run_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scenario context {scenario_run_id}: {e}", exc_info=True)
            return False
    
    async def get_scenario_context(
        self, 
        scenario_run_id: int, 
        keys: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get scenario context, optionally filtered by keys.
        
        Args:
            scenario_run_id: ID of the scenario run
            keys: Specific keys to retrieve (if None, returns all)
            
        Returns:
            Context dictionary or None if not found
        """
        if scenario_run_id not in self.scenario_contexts:
            self.logger.warning(f"Scenario context {scenario_run_id} not found")
            return None
        
        context = self.scenario_contexts[scenario_run_id]
        
        if keys:
            return {k: context.get(k) for k in keys if k in context}
        
        return context.copy()
    
    async def update_scenario_context(
        self, 
        scenario_run_id: int, 
        context_update: Dict[str, Any],
        merge_deep: bool = True
    ) -> bool:
        """
        Update scenario context with new data.
        
        Args:
            scenario_run_id: ID of the scenario run
            context_update: Data to update
            merge_deep: Whether to deep merge nested dictionaries
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if scenario_run_id not in self.scenario_contexts:
                self.logger.error(f"Scenario context {scenario_run_id} not found")
                return False
            
            # Use lock to prevent concurrent modifications
            async with self.context_locks[scenario_run_id]:
                context = self.scenario_contexts[scenario_run_id]
                
                if merge_deep:
                    self._deep_merge(context, context_update)
                else:
                    context.update(context_update)
                
                # Update timestamp
                context["last_updated"] = datetime.utcnow().isoformat()
                
                # Log update
                await self._log_context_event(
                    scenario_run_id,
                    "CONTEXT_UPDATED",
                    {"updated_keys": list(context_update.keys())}
                )
            
            self.logger.debug(f"Updated scenario context {scenario_run_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update scenario context {scenario_run_id}: {e}", exc_info=True)
            return False
    
    async def initialize_agent_context(
        self, 
        agent_instance_id: int, 
        scenario_run_id: int,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Initialize context for an agent instance.
        
        Args:
            agent_instance_id: ID of the agent instance
            scenario_run_id: ID of the scenario run
            initial_context: Initial context data
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Get agent instance from database
            agent_instance = self.db.query(AgentInstance).filter(
                AgentInstance.id == agent_instance_id
            ).first()
            
            if not agent_instance:
                self.logger.error(f"Agent instance {agent_instance_id} not found")
                return False
            
            # Initialize agent context
            context = {
                "agent_id": agent_instance_id,
                "agent_name": agent_instance.instance_name,
                "template_name": agent_instance.template.name,
                "scenario_id": scenario_run_id,
                "created_at": datetime.utcnow().isoformat(),
                "private_state": {},
                "memory": [],
                "interaction_history": [],
                "current_goals": [],
                "knowledge_base": {},
                **(initial_context or {})
            }
            
            self.agent_contexts[agent_instance_id] = context
            
            # Log initialization
            await self._log_context_event(
                scenario_run_id,
                "AGENT_CONTEXT_INITIALIZED",
                {
                    "agent_id": agent_instance_id,
                    "agent_name": agent_instance.instance_name
                }
            )
            
            self.logger.info(f"Initialized context for agent {agent_instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent context {agent_instance_id}: {e}", exc_info=True)
            return False
    
    async def get_agent_context(
        self, 
        agent_instance_id: int,
        include_scenario_context: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get agent context, optionally including scenario context.
        
        Args:
            agent_instance_id: ID of the agent instance
            include_scenario_context: Whether to include scenario-wide context
            
        Returns:
            Combined context dictionary or None if not found
        """
        if agent_instance_id not in self.agent_contexts:
            self.logger.warning(f"Agent context {agent_instance_id} not found")
            return None
        
        agent_context = self.agent_contexts[agent_instance_id].copy()
        
        if include_scenario_context:
            scenario_id = agent_context.get("scenario_id")
            if scenario_id and scenario_id in self.scenario_contexts:
                scenario_context = self.scenario_contexts[scenario_id].copy()
                # Merge scenario context, with agent context taking precedence
                combined_context = {**scenario_context, **agent_context}
                combined_context["scenario_context"] = scenario_context
                return combined_context
        
        return agent_context
    
    async def update_agent_context(
        self, 
        agent_instance_id: int, 
        context_update: Dict[str, Any]
    ) -> bool:
        """
        Update agent context with new data.
        
        Args:
            agent_instance_id: ID of the agent instance
            context_update: Data to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if agent_instance_id not in self.agent_contexts:
                self.logger.error(f"Agent context {agent_instance_id} not found")
                return False
            
            context = self.agent_contexts[agent_instance_id]
            self._deep_merge(context, context_update)
            context["last_updated"] = datetime.utcnow().isoformat()
            
            # Log update to scenario if available
            scenario_id = context.get("scenario_id")
            if scenario_id:
                await self._log_context_event(
                    scenario_id,
                    "AGENT_CONTEXT_UPDATED",
                    {
                        "agent_id": agent_instance_id,
                        "updated_keys": list(context_update.keys())
                    }
                )
            
            self.logger.debug(f"Updated agent context {agent_instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update agent context {agent_instance_id}: {e}", exc_info=True)
            return False
    
    async def add_shared_memory(
        self, 
        scenario_run_id: int, 
        memory: Dict[str, Any],
        source_agent_id: Optional[int] = None
    ) -> bool:
        """
        Add a memory to the shared scenario memory pool.
        
        Args:
            scenario_run_id: ID of the scenario run
            memory: Memory data to add
            source_agent_id: ID of the agent that created this memory
            
        Returns:
            True if memory added successfully, False otherwise
        """
        try:
            if scenario_run_id not in self.shared_memories:
                self.shared_memories[scenario_run_id] = []
            
            memory_entry = {
                "id": len(self.shared_memories[scenario_run_id]) + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "source_agent_id": source_agent_id,
                "content": memory,
                "access_count": 0,
                "tags": memory.get("tags", [])
            }
            
            self.shared_memories[scenario_run_id].append(memory_entry)
            
            # Update scenario context
            await self.update_scenario_context(
                scenario_run_id,
                {"memory_count": len(self.shared_memories[scenario_run_id])}
            )
            
            self.logger.debug(f"Added shared memory to scenario {scenario_run_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add shared memory to scenario {scenario_run_id}: {e}", exc_info=True)
            return False
    
    async def get_shared_memories(
        self, 
        scenario_run_id: int,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get shared memories for a scenario, optionally filtered by tags.
        
        Args:
            scenario_run_id: ID of the scenario run
            tags: Filter by these tags (if None, returns all)
            limit: Maximum number of memories to return
            
        Returns:
            List of memory entries
        """
        if scenario_run_id not in self.shared_memories:
            return []
        
        memories = self.shared_memories[scenario_run_id]
        
        # Filter by tags if provided
        if tags:
            memories = [
                m for m in memories 
                if any(tag in m.get("tags", []) for tag in tags)
            ]
        
        # Sort by timestamp (most recent first)
        memories = sorted(memories, key=lambda x: x["timestamp"], reverse=True)
        
        # Apply limit
        if limit:
            memories = memories[:limit]
        
        # Update access count
        for memory in memories:
            memory["access_count"] += 1
        
        return memories
    
    async def share_context_between_agents(
        self, 
        source_agent_id: int, 
        target_agent_id: int,
        context_keys: List[str]
    ) -> bool:
        """
        Share specific context data between two agents.
        
        Args:
            source_agent_id: ID of the source agent
            target_agent_id: ID of the target agent
            context_keys: Keys to share from source to target
            
        Returns:
            True if sharing successful, False otherwise
        """
        try:
            if source_agent_id not in self.agent_contexts:
                self.logger.error(f"Source agent context {source_agent_id} not found")
                return False
            
            if target_agent_id not in self.agent_contexts:
                self.logger.error(f"Target agent context {target_agent_id} not found")
                return False
            
            source_context = self.agent_contexts[source_agent_id]
            target_context = self.agent_contexts[target_agent_id]
            
            # Extract data to share
            shared_data = {}
            for key in context_keys:
                if key in source_context:
                    shared_data[key] = source_context[key]
            
            # Add to target agent's shared context
            if "shared_from_agents" not in target_context:
                target_context["shared_from_agents"] = {}
            
            target_context["shared_from_agents"][source_agent_id] = {
                "timestamp": datetime.utcnow().isoformat(),
                "data": shared_data
            }
            
            # Log the sharing
            scenario_id = source_context.get("scenario_id")
            if scenario_id:
                await self._log_context_event(
                    scenario_id,
                    "CONTEXT_SHARED",
                    {
                        "source_agent_id": source_agent_id,
                        "target_agent_id": target_agent_id,
                        "shared_keys": context_keys
                    }
                )
            
            self.logger.debug(f"Shared context from agent {source_agent_id} to {target_agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to share context between agents: {e}", exc_info=True)
            return False
    
    async def cleanup_scenario_context(self, scenario_run_id: int) -> bool:
        """
        Clean up context data for a completed scenario.
        
        Args:
            scenario_run_id: ID of the scenario run
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            # Remove scenario context
            if scenario_run_id in self.scenario_contexts:
                del self.scenario_contexts[scenario_run_id]
            
            # Remove shared memories
            if scenario_run_id in self.shared_memories:
                del self.shared_memories[scenario_run_id]
            
            # Remove context lock
            if scenario_run_id in self.context_locks:
                del self.context_locks[scenario_run_id]
            
            # Remove agent contexts for this scenario
            agents_to_remove = []
            for agent_id, context in self.agent_contexts.items():
                if context.get("scenario_id") == scenario_run_id:
                    agents_to_remove.append(agent_id)
            
            for agent_id in agents_to_remove:
                del self.agent_contexts[agent_id]
            
            self.logger.info(f"Cleaned up context for scenario {scenario_run_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup scenario context {scenario_run_id}: {e}", exc_info=True)
            return False
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep merge source dictionary into target dictionary.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    async def _log_context_event(
        self, 
        scenario_run_id: int, 
        event_type: str, 
        data: Dict[str, Any]
    ) -> None:
        """
        Log a context-related event to the database.
        
        Args:
            scenario_run_id: ID of the scenario run
            event_type: Type of event
            data: Event data
        """
        try:
            log_entry = ExecutionLog(
                scenario_run_id=scenario_run_id,
                level="INFO",
                message=f"Context event: {event_type}",
                data={
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    **data
                }
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log context event: {e}", exc_info=True)
    
    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current context usage.
        
        Returns:
            Dictionary with context statistics
        """
        return {
            "active_scenarios": len(self.scenario_contexts),
            "active_agents": len(self.agent_contexts),
            "total_shared_memories": sum(len(memories) for memories in self.shared_memories.values()),
            "scenario_details": [
                {
                    "scenario_id": scenario_id,
                    "agent_count": len([
                        agent_id for agent_id, context in self.agent_contexts.items()
                        if context.get("scenario_id") == scenario_id
                    ]),
                    "memory_count": len(self.shared_memories.get(scenario_id, []))
                }
                for scenario_id in self.scenario_contexts.keys()
            ]
        }
