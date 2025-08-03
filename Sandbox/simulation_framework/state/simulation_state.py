"""
Core simulation state management for the framework.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field
import json
import uuid


class Message(BaseModel):
    """Represents a single message in the conversation log."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str  # Agent name or "human"
    recipient: Optional[str] = None  # Target agent or "all"
    content: str
    message_type: str = "text"  # text, system, error, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    """State information for a single agent."""
    name: str
    agent_type: str
    status: str = "active"  # active, idle, error, finished
    last_action: Optional[str] = None
    last_action_timestamp: Optional[datetime] = None
    memory: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    error_count: int = 0
    total_messages: int = 0


class SimulationState(BaseModel):
    """Core simulation state that persists across the simulation lifecycle."""
    
    # Core identification
    simulation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int = 1
    
    # Agent management
    agents: Dict[str, AgentState] = Field(default_factory=dict)
    active_agent: Optional[str] = None
    
    # Conversation and context
    conversation_log: List[Message] = Field(default_factory=list)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Human-in-the-loop
    user_input: Optional[str] = None
    awaiting_human_input: bool = False
    human_arbitration_needed: bool = False
    arbitration_reason: Optional[str] = None
    
    # Module-specific data
    module_name: Optional[str] = None
    module_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Simulation control
    status: str = "initialized"  # initialized, running, paused, completed, error
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Metadata and metrics
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    def add_agent(self, agent_state: AgentState) -> None:
        """Add an agent to the simulation."""
        self.agents[agent_state.name] = agent_state
        self.version += 1
    
    def update_agent(self, agent_name: str, **updates) -> None:
        """Update agent state."""
        if agent_name in self.agents:
            for key, value in updates.items():
                if hasattr(self.agents[agent_name], key):
                    setattr(self.agents[agent_name], key, value)
            self.version += 1
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation log."""
        self.conversation_log.append(message)
        
        # Update sender's message count
        if message.sender in self.agents:
            self.agents[message.sender].total_messages += 1
            self.agents[message.sender].last_action = "message"
            self.agents[message.sender].last_action_timestamp = message.timestamp
        
        self.version += 1
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get the most recent messages."""
        return self.conversation_log[-limit:] if self.conversation_log else []
    
    def get_messages_by_agent(self, agent_name: str) -> List[Message]:
        """Get all messages from a specific agent."""
        return [msg for msg in self.conversation_log if msg.sender == agent_name]
    
    def set_human_arbitration(self, reason: str) -> None:
        """Request human arbitration."""
        self.human_arbitration_needed = True
        self.arbitration_reason = reason
        self.status = "paused"
        self.version += 1
    
    def clear_human_arbitration(self) -> None:
        """Clear human arbitration request."""
        self.human_arbitration_needed = False
        self.arbitration_reason = None
        self.awaiting_human_input = False
        self.user_input = None
        self.version += 1
    
    def start_simulation(self) -> None:
        """Mark simulation as started."""
        self.status = "running"
        self.start_time = datetime.now()
        self.version += 1
    
    def complete_simulation(self) -> None:
        """Mark simulation as completed."""
        self.status = "completed"
        self.end_time = datetime.now()
        self.version += 1
    
    def error_simulation(self, error_message: str) -> None:
        """Mark simulation as errored."""
        self.status = "error"
        self.error_message = error_message
        self.end_time = datetime.now()
        self.version += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationState":
        """Create from dictionary."""
        return cls.model_validate(data)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save state to JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> "SimulationState":
        """Load state from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def create_checkpoint(self) -> Dict[str, Any]:
        """Create a checkpoint of current state."""
        checkpoint = self.to_dict()
        checkpoint['checkpoint_timestamp'] = datetime.now().isoformat()
        checkpoint['checkpoint_version'] = self.version
        return checkpoint
    
    @classmethod
    def restore_from_checkpoint(cls, checkpoint: Dict[str, Any]) -> "SimulationState":
        """Restore state from checkpoint."""
        # Remove checkpoint metadata
        data = checkpoint.copy()
        data.pop('checkpoint_timestamp', None)
        data.pop('checkpoint_version', None)
        return cls.from_dict(data)
