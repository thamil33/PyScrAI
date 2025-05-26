"""
Memory System for PyScrAI

Handles agent memory persistence, retrieval, and management.
Provides both short-term and long-term memory capabilities for agents.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..databases.models import AgentInstance, ExecutionLog


class MemoryEntry:
    """Represents a single memory entry for an agent."""
    
    def __init__(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = None  # Will be set when stored
        self.content = content
        self.memory_type = memory_type  # episodic, semantic, procedural
        self.importance = max(0.0, min(1.0, importance))  # Clamp between 0 and 1
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.access_count = 0
        self.decay_factor = 1.0  # For memory decay simulation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory entry to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "decay_factor": self.decay_factor
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create memory entry from dictionary."""
        entry = cls(
            content=data["content"],
            memory_type=data.get("memory_type", "episodic"),
            importance=data.get("importance", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        entry.id = data.get("id")
        entry.created_at = datetime.fromisoformat(data["created_at"])
        entry.last_accessed = datetime.fromisoformat(data["last_accessed"])
        entry.access_count = data.get("access_count", 0)
        entry.decay_factor = data.get("decay_factor", 1.0)
        return entry
    
    def update_access(self):
        """Update access information when memory is retrieved."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def calculate_relevance(self, query_tags: List[str] = None) -> float:
        """Calculate relevance score based on importance, recency, and tags."""
        # Base relevance from importance
        relevance = self.importance
        
        # Recency factor (more recent memories are more relevant)
        hours_since_creation = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        recency_factor = max(0.1, 1.0 - (hours_since_creation / (24 * 7)))  # Decay over a week
        
        # Access frequency factor
        frequency_factor = min(1.0, self.access_count / 10.0)  # Cap at 10 accesses
        
        # Tag matching factor
        tag_factor = 1.0
        if query_tags and self.tags:
            matching_tags = set(query_tags) & set(self.tags)
            tag_factor = 1.0 + (len(matching_tags) / len(self.tags))
        
        # Combine factors
        relevance = relevance * recency_factor * (1.0 + frequency_factor * 0.2) * tag_factor * self.decay_factor
        
        return min(1.0, relevance)


class AgentMemorySystem:
    """Memory system for a single agent instance."""
    
    def __init__(self, agent_instance_id: int, db: Session, max_memories: int = 1000):
        """
        Initialize agent memory system.
        
        Args:
            agent_instance_id: ID of the agent instance
            db: Database session
            max_memories: Maximum number of memories to keep in active memory
        """
        self.agent_instance_id = agent_instance_id
        self.db = db
        self.max_memories = max_memories
        self.memories: Dict[int, MemoryEntry] = {}  # memory_id -> MemoryEntry
        self.next_memory_id = 1
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_instance_id}")
        
        # Memory organization
        self.episodic_memories: List[int] = []  # Chronological events
        self.semantic_memories: List[int] = []  # Facts and knowledge
        self.procedural_memories: List[int] = []  # Skills and procedures
        
        self.logger.info(f"AgentMemorySystem initialized for agent {agent_instance_id}")
    
    async def load_memories_from_storage(self) -> bool:
        """Load existing memories from database storage."""
        try:
            # Get agent instance
            agent_instance = self.db.query(AgentInstance).filter(
                AgentInstance.id == self.agent_instance_id
            ).first()
            
            if not agent_instance:
                self.logger.error(f"Agent instance {self.agent_instance_id} not found")
                return False
            
            # Load memories from agent state
            if agent_instance.state and "memories" in agent_instance.state:
                memories_data = agent_instance.state["memories"]
                
                for memory_data in memories_data:
                    memory = MemoryEntry.from_dict(memory_data)
                    memory.id = self.next_memory_id
                    self.memories[memory.id] = memory
                    
                    # Organize by type
                    if memory.memory_type == "episodic":
                        self.episodic_memories.append(memory.id)
                    elif memory.memory_type == "semantic":
                        self.semantic_memories.append(memory.id)
                    elif memory.memory_type == "procedural":
                        self.procedural_memories.append(memory.id)
                    
                    self.next_memory_id += 1
                
                self.logger.info(f"Loaded {len(self.memories)} memories for agent {self.agent_instance_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load memories: {e}", exc_info=True)
            return False
    
    async def save_memories_to_storage(self) -> bool:
        """Save current memories to database storage."""
        try:
            # Convert memories to serializable format
            memories_data = [memory.to_dict() for memory in self.memories.values()]
            
            # Update agent state
            agent_instance = self.db.query(AgentInstance).filter(
                AgentInstance.id == self.agent_instance_id
            ).first()
            
            if not agent_instance:
                self.logger.error(f"Agent instance {self.agent_instance_id} not found")
                return False
            
            if not agent_instance.state:
                agent_instance.state = {}
            
            agent_instance.state["memories"] = memories_data
            agent_instance.state["memory_stats"] = {
                "total_memories": len(self.memories),
                "episodic_count": len(self.episodic_memories),
                "semantic_count": len(self.semantic_memories),
                "procedural_count": len(self.procedural_memories),
                "last_saved": datetime.utcnow().isoformat()
            }
            
            self.db.commit()
            
            self.logger.debug(f"Saved {len(self.memories)} memories for agent {self.agent_instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save memories: {e}", exc_info=True)
            return False
    
    async def add_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a new memory entry.
        
        Args:
            content: Memory content
            memory_type: Type of memory (episodic, semantic, procedural)
            importance: Importance score (0.0 to 1.0)
            tags: Tags for categorization
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        try:
            # Create memory entry
            memory = MemoryEntry(
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags,
                metadata=metadata
            )
            memory.id = self.next_memory_id
            
            # Store memory
            self.memories[memory.id] = memory
            
            # Organize by type
            if memory_type == "episodic":
                self.episodic_memories.append(memory.id)
            elif memory_type == "semantic":
                self.semantic_memories.append(memory.id)
            elif memory_type == "procedural":
                self.procedural_memories.append(memory.id)
            
            self.next_memory_id += 1
            
            # Check if we need to prune old memories
            if len(self.memories) > self.max_memories:
                await self._prune_memories()
            
            # Save to storage
            await self.save_memories_to_storage()
            
            self.logger.debug(f"Added {memory_type} memory {memory.id}: {content[:50]}...")
            return memory.id
            
        except Exception as e:
            self.logger.error(f"Failed to add memory: {e}", exc_info=True)
            return -1
    
    async def retrieve_memories(
        self,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_relevance: float = 0.1
    ) -> List[MemoryEntry]:
        """
        Retrieve memories based on query criteria.
        
        Args:
            query: Text query for content matching
            memory_type: Filter by memory type
            tags: Filter by tags
            limit: Maximum number of memories to return
            min_relevance: Minimum relevance score
            
        Returns:
            List of relevant memory entries
        """
        try:
            relevant_memories = []
            
            # Filter memories by type if specified
            memory_ids = []
            if memory_type == "episodic":
                memory_ids = self.episodic_memories
            elif memory_type == "semantic":
                memory_ids = self.semantic_memories
            elif memory_type == "procedural":
                memory_ids = self.procedural_memories
            else:
                memory_ids = list(self.memories.keys())
            
            # Score and filter memories
            for memory_id in memory_ids:
                if memory_id not in self.memories:
                    continue
                
                memory = self.memories[memory_id]
                
                # Calculate relevance
                relevance = memory.calculate_relevance(tags)
                
                # Text matching if query provided
                if query:
                    query_lower = query.lower()
                    content_lower = memory.content.lower()
                    
                    # Simple text matching (could be enhanced with embeddings)
                    if query_lower in content_lower:
                        relevance *= 1.5  # Boost for direct text match
                    elif any(word in content_lower for word in query_lower.split()):
                        relevance *= 1.2  # Boost for word matches
                
                # Tag filtering
                if tags and memory.tags:
                    if not any(tag in memory.tags for tag in tags):
                        continue
                
                # Check minimum relevance
                if relevance >= min_relevance:
                    relevant_memories.append((memory, relevance))
                    memory.update_access()  # Update access info
            
            # Sort by relevance and limit
            relevant_memories.sort(key=lambda x: x[1], reverse=True)
            result = [memory for memory, _ in relevant_memories[:limit]]
            
            self.logger.debug(f"Retrieved {len(result)} memories for query: {query}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            return []
    
    async def get_recent_memories(self, hours: int = 24, limit: int = 20) -> List[MemoryEntry]:
        """Get recent memories within the specified time window."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_memories = []
        for memory in self.memories.values():
            if memory.created_at >= cutoff_time:
                recent_memories.append(memory)
                memory.update_access()
        
        # Sort by creation time (most recent first)
        recent_memories.sort(key=lambda x: x.created_at, reverse=True)
        
        return recent_memories[:limit]
    
    async def get_important_memories(self, min_importance: float = 0.7, limit: int = 20) -> List[MemoryEntry]:
        """Get memories above a certain importance threshold."""
        important_memories = []
        
        for memory in self.memories.values():
            if memory.importance >= min_importance:
                important_memories.append(memory)
                memory.update_access()
        
        # Sort by importance (highest first)
        important_memories.sort(key=lambda x: x.importance, reverse=True)
        
        return important_memories[:limit]
    
    async def update_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update an existing memory entry."""
        try:
            if memory_id not in self.memories:
                self.logger.warning(f"Memory {memory_id} not found")
                return False
            
            memory = self.memories[memory_id]
            
            if content is not None:
                memory.content = content
            if importance is not None:
                memory.importance = max(0.0, min(1.0, importance))
            if tags is not None:
                memory.tags = tags
            if metadata is not None:
                memory.metadata.update(metadata)
            
            # Save to storage
            await self.save_memories_to_storage()
            
            self.logger.debug(f"Updated memory {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update memory {memory_id}: {e}", exc_info=True)
            return False
    
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory entry."""
        try:
            if memory_id not in self.memories:
                self.logger.warning(f"Memory {memory_id} not found")
                return False
            
            memory = self.memories[memory_id]
            
            # Remove from type lists
            if memory.memory_type == "episodic" and memory_id in self.episodic_memories:
                self.episodic_memories.remove(memory_id)
            elif memory.memory_type == "semantic" and memory_id in self.semantic_memories:
                self.semantic_memories.remove(memory_id)
            elif memory.memory_type == "procedural" and memory_id in self.procedural_memories:
                self.procedural_memories.remove(memory_id)
            
            # Remove from main storage
            del self.memories[memory_id]
            
            # Save to storage
            await self.save_memories_to_storage()
            
            self.logger.debug(f"Deleted memory {memory_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete memory {memory_id}: {e}", exc_info=True)
            return False
    
    async def _prune_memories(self):
        """Remove least important/relevant memories when at capacity."""
        if len(self.memories) <= self.max_memories:
            return
        
        # Calculate relevance scores for all memories
        memory_scores = []
        for memory_id, memory in self.memories.items():
            relevance = memory.calculate_relevance()
            memory_scores.append((memory_id, relevance))
        
        # Sort by relevance (lowest first)
        memory_scores.sort(key=lambda x: x[1])
        
        # Remove the least relevant memories
        memories_to_remove = len(self.memories) - self.max_memories + 10  # Remove a few extra
        for i in range(memories_to_remove):
            if i < len(memory_scores):
                memory_id = memory_scores[i][0]
                await self.delete_memory(memory_id)
        
        self.logger.info(f"Pruned {memories_to_remove} memories for agent {self.agent_instance_id}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent's memory."""
        return {
            "total_memories": len(self.memories),
            "episodic_count": len(self.episodic_memories),
            "semantic_count": len(self.semantic_memories),
            "procedural_count": len(self.procedural_memories),
            "average_importance": sum(m.importance for m in self.memories.values()) / len(self.memories) if self.memories else 0,
            "most_accessed": max(self.memories.values(), key=lambda x: x.access_count) if self.memories else None,
            "oldest_memory": min(self.memories.values(), key=lambda x: x.created_at) if self.memories else None,
            "newest_memory": max(self.memories.values(), key=lambda x: x.created_at) if self.memories else None
        }


class GlobalMemorySystem:
    """Global memory system that manages memory for all agents."""
    
    def __init__(self, db: Session):
        """
        Initialize global memory system.
        
        Args:
            db: Database session
        """
        self.db = db
        self.agent_memories: Dict[int, AgentMemorySystem] = {}  # agent_id -> memory system
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("GlobalMemorySystem initialized")
    
    async def get_agent_memory_system(self, agent_instance_id: int) -> AgentMemorySystem:
        """Get or create memory system for an agent."""
        if agent_instance_id not in self.agent_memories:
            memory_system = AgentMemorySystem(agent_instance_id, self.db)
            await memory_system.load_memories_from_storage()
            self.agent_memories[agent_instance_id] = memory_system
        
        return self.agent_memories[agent_instance_id]
    
    async def cleanup_agent_memory(self, agent_instance_id: int) -> bool:
        """Clean up memory system for an agent."""
        try:
            if agent_instance_id in self.agent_memories:
                memory_system = self.agent_memories[agent_instance_id]
                await memory_system.save_memories_to_storage()
                del self.agent_memories[agent_instance_id]
                
                self.logger.info(f"Cleaned up memory system for agent {agent_instance_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup agent memory {agent_instance_id}: {e}", exc_info=True)
            return False
    
    async def save_all_memories(self) -> bool:
        """Save all active memory systems to storage."""
        try:
            for agent_id, memory_system in self.agent_memories.items():
                await memory_system.save_memories_to_storage()
            
            self.logger.info(f"Saved memories for {len(self.agent_memories)} agents")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save all memories: {e}", exc_info=True)
            return False
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global memory statistics."""
        total_memories = 0
        total_agents = len(self.agent_memories)
        
        for memory_system in self.agent_memories.values():
            total_memories += len(memory_system.memories)
        
        return {
            "active_agents": total_agents,
            "total_memories": total_memories,
            "average_memories_per_agent": total_memories / total_agents if total_agents > 0 else 0,
            "agent_details": {
                agent_id: memory_system.get_memory_stats()
                for agent_id, memory_system in self.agent_memories.items()
            }
        }
