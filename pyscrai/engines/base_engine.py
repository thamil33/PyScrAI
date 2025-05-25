"""
Abstract base class for all PyScrAI engines
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.models.lmstudio import LMStudio
from agno.storage.sqlite import SqliteStorage
import asyncio
import json


class BaseEngine(ABC):
    """Abstract base class for all PyScrAI engines"""
    
    def __init__(
        self,
        agent_config: Dict[str, Any],
        storage_path: Optional[str] = None,
        model_provider: str = "openrouter"
    ):
        self.agent_config = agent_config
        self.storage_path = storage_path
        self.model_provider = model_provider
        self.agent: Optional[Agent] = None
        self.state: Dict[str, Any] = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize the engine and create the Agno agent"""
        if self.initialized:
            return
        
        # Set up model
        model_config = self.agent_config.get("model_config", {})
        if self.model_provider == "openrouter":
            model = OpenRouter(
                id=model_config.get("id", "meta-llama/llama-3.1-8b-instruct:free"),
                temperature=model_config.get("temperature", 0.7),
                **{k: v for k, v in model_config.items() if k not in ["id", "temperature"]}
            )
        elif self.model_provider == "lmstudio":
            model = LMStudio(
                id=model_config.get("id", "llama-3.1-8b-instruct"),
                **{k: v for k, v in model_config.items() if k != "id"}
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
        
        # Set up storage
        storage = None
        if self.storage_path:
            storage = SqliteStorage(
                db_file=self.storage_path,
                table_name=f"engine_{self.__class__.__name__.lower()}"
            )
        
        # Set up tools
        tools = self._setup_tools()
        
        # Create agent
        personality_config = self.agent_config.get("personality_config", {})
        self.agent = Agent(
            name=personality_config.get("name", "Engine Agent"),
            model=model,
            description=personality_config.get("description", ""),
            instructions=personality_config.get("instructions", ""),
            storage=storage,
            tools=tools,
            **personality_config.get("agent_kwargs", {})
        )
        
        self.initialized = True
    
    @abstractmethod
    def _setup_tools(self) -> List[Any]:
        """Set up tools specific to this engine type"""
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return structured output"""
        pass
    
    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """Run the agent with a message and return structured results"""
        if not self.initialized:
            await self.initialize()
        
        response = await self.agent.arun(message, **kwargs)
        
        # Structure the response
        result = {
            "content": response.content,
            "messages": [msg.dict() for msg in response.messages],
            "metrics": response.metrics.dict() if response.metrics else None,
            "engine_type": self.__class__.__name__,
            "state": self.state
        }
        
        return result
    
    def update_state(self, key: str, value: Any):
        """Update engine state"""
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get value from engine state"""
        return self.state.get(key, default)
    
    def export_state(self) -> str:
        """Export current state as JSON"""
        return json.dumps(self.state, indent=2)
    
    def import_state(self, state_json: str):
        """Import state from JSON"""
        self.state = json.loads(state_json)

