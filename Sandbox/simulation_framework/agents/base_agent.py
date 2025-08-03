"""
Base agent implementation for the simulation framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
from pydantic import BaseModel

from ..state.simulation_state import SimulationState, Message, AgentState
from ..llm_providers.base_provider import LLMProvider, LLMRequest
from ..utils.logging_config import get_logger


class Command(BaseModel):
    """Command returned by agents to control workflow execution."""
    action: str  # "continue", "handoff", "human_input", "complete", "error"
    target_agent: Optional[str] = None  # For handoff commands
    message: Optional[str] = None  # Message to add to conversation
    updates: Dict[str, Any] = {}  # State updates to apply
    metadata: Dict[str, Any] = {}  # Additional metadata


class Tool(BaseModel):
    """Base tool definition for agents."""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters."""
        raise NotImplementedError


class AgentMemory:
    """Simple memory system for agents."""
    
    def __init__(self):
        self.short_term: Dict[str, Any] = {}
        self.long_term: Dict[str, Any] = {}
        self.conversation_buffer: List[Message] = []
        self.max_buffer_size = 50
    
    def store_short_term(self, key: str, value: Any) -> None:
        """Store information in short-term memory."""
        self.short_term[key] = value
    
    def store_long_term(self, key: str, value: Any) -> None:
        """Store information in long-term memory."""
        self.long_term[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get information from memory (short-term first, then long-term)."""
        return self.short_term.get(key, self.long_term.get(key, default))
    
    def add_to_buffer(self, message: Message) -> None:
        """Add message to conversation buffer."""
        self.conversation_buffer.append(message)
        if len(self.conversation_buffer) > self.max_buffer_size:
            self.conversation_buffer.pop(0)
    
    def get_recent_context(self, limit: int = 10) -> List[Message]:
        """Get recent conversation context."""
        return self.conversation_buffer[-limit:] if self.conversation_buffer else []
    
    def clear_short_term(self) -> None:
        """Clear short-term memory."""
        self.short_term.clear()


class BaseAgent(ABC):
    """
    Abstract base class for all simulation agents.
    
    Provides common functionality for agent lifecycle, memory management,
    LLM interaction, and tool usage.
    """
    
    def __init__(
        self,
        name: str,
        agent_type: str,
        llm_provider: LLMProvider,
        tools: Optional[List[Tool]] = None,
        personality_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ):
        self.name = name
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.tools = tools or []
        self.personality_config = personality_config or {}
        self.system_prompt = system_prompt
        self.memory = AgentMemory()
        self.logger = get_logger(f"agent.{name}")
        
        # State tracking
        self.state = AgentState(
            name=name,
            agent_type=agent_type,
            configuration=personality_config or {}
        )
    
    @abstractmethod
    async def process(self, state: SimulationState) -> Command:
        """
        Process the current simulation state and return the next command.
        
        Args:
            state: Current simulation state
            
        Returns:
            Command indicating the next action to take
        """
        pass
    
    async def initialize(self, state: SimulationState) -> None:
        """
        Initialize the agent when added to a simulation.
        
        Args:
            state: Current simulation state
        """
        self.logger.info("Agent initialized", agent=self.name, simulation_id=state.simulation_id)
        
        # Update memory with initial context
        if state.shared_context:
            for key, value in state.shared_context.items():
                self.memory.store_long_term(key, value)
    
    async def cleanup(self, state: SimulationState) -> None:
        """
        Clean up agent resources when simulation ends.
        
        Args:
            state: Final simulation state
        """
        self.logger.info("Agent cleaning up", agent=self.name)
        self.memory.clear_short_term()
    
    async def handle_error(self, error: Exception, state: SimulationState) -> Command:
        """
        Handle errors that occur during agent processing.
        
        Args:
            error: The exception that occurred
            state: Current simulation state
            
        Returns:
            Command to handle the error
        """
        self.logger.error("Agent error occurred", agent=self.name, error=str(error))
        self.state.error_count += 1
        
        return Command(
            action="error",
            message=f"Agent {self.name} encountered an error: {str(error)}",
            updates={"error_count": self.state.error_count}
        )
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response using the LLM provider.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional additional context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        # Build system prompt
        system_parts = []
        if self.system_prompt:
            system_parts.append(self.system_prompt)
        
        if self.personality_config:
            personality_prompt = self._build_personality_prompt()
            if personality_prompt:
                system_parts.append(personality_prompt)
        
        if context:
            system_parts.append(f"Context: {context}")
        
        system_prompt = "\n\n".join(system_parts) if system_parts else None
        
        # Create request
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata={"agent": self.name, "agent_type": self.agent_type}
        )
        
        # Generate response
        response = await self.llm_provider.generate(request)
        
        self.logger.debug(
            "Generated response",
            agent=self.name,
            model=response.model_used,
            tokens=response.usage.get("total_tokens") if response.usage else None
        )
        
        return response.content
    
    def _build_personality_prompt(self) -> Optional[str]:
        """Build personality prompt from configuration."""
        if not self.personality_config:
            return None
        
        parts = []
        if "role" in self.personality_config:
            parts.append(f"You are acting as: {self.personality_config['role']}")
        
        if "traits" in self.personality_config:
            traits = self.personality_config["traits"]
            if isinstance(traits, list):
                parts.append(f"Your personality traits: {', '.join(traits)}")
            elif isinstance(traits, str):
                parts.append(f"Your personality: {traits}")
        
        if "goals" in self.personality_config:
            parts.append(f"Your goals: {self.personality_config['goals']}")
        
        if "constraints" in self.personality_config:
            parts.append(f"Your constraints: {self.personality_config['constraints']}")
        
        return "\n".join(parts) if parts else None
    
    def get_conversation_context(self, state: SimulationState, limit: int = 10) -> str:
        """
        Get formatted conversation context for the agent.
        
        Args:
            state: Current simulation state
            limit: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation context
        """
        recent_messages = state.get_recent_messages(limit)
        if not recent_messages:
            return "No previous conversation."
        
        context_parts = []
        for msg in recent_messages:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            context_parts.append(f"[{timestamp}] {msg.sender}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def should_respond(self, state: SimulationState) -> bool:
        """
        Determine if the agent should respond in the current state.
        
        Args:
            state: Current simulation state
            
        Returns:
            True if agent should respond, False otherwise
        """
        # Default logic - override in subclasses for specific behavior
        if state.human_arbitration_needed:
            return False
        
        if state.active_agent and state.active_agent != self.name:
            return False
        
        return True
    
    async def use_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Use a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to use
            parameters: Parameters to pass to the tool
            
        Returns:
            Tool execution result
        """
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        self.logger.info("Using tool", agent=self.name, tool=tool_name, parameters=parameters)
        result = await tool.execute(parameters)
        
        self.memory.store_short_term(f"tool_result_{tool_name}", result)
        return result
    
    def update_state(self, **updates) -> None:
        """Update agent state with new values."""
        for key, value in updates.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        
        self.state.last_action_timestamp = datetime.now()
