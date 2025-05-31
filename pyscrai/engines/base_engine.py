"""
Abstract base class for all PyScrAI engines.
Provides core functionalities including state management and basic API interaction capabilities.
"""

import asyncio
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable

import httpx
from pyscrai.core.models import Event
from sqlalchemy.orm import Session

# Default API base URL - can be overridden by environment variable
PYSCRAI_API_BASE_URL = os.getenv("PYSCRAI_API_BASE_URL", "http://localhost:8000/api/v1")


class BaseEngine(ABC):
    """
    Abstract base class for all PyScrAI engines.

    Handles state persistence and provides methods for interacting with the PyScrAI database API.
    """

    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = None,
        engine_type: str = "BaseEngine",
        description: Optional[str] = "A PyScrAI processing engine.",
        storage_path: Optional[str] = None,
        model_provider: str = "openai",
        api_base_url: Optional[str] = None,
    ):
        """
        Initializes the BaseEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the agent.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): A human-readable name for the engine.
            engine_type (str): The specific type of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            storage_path (Optional[str]): Path for the agent's storage.
            model_provider (str): The provider for the LLM model.
            api_base_url (Optional[str]): The base URL for the PyScrAI API.
        """
        self.engine_id: str = engine_id or str(uuid.uuid4())
        self.engine_name: str = engine_name or self.__class__.__name__
        self.engine_type: str = engine_type
        self.description: Optional[str] = description
        self.agent_config: Dict[str, Any] = agent_config
        self.storage_path: Optional[str] = storage_path
        self.model_provider: str = model_provider
        
        self.state: Dict[str, Any] = {}
        self.initialized: bool = False
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        
        self.api_base_url: str = api_base_url or PYSCRAI_API_BASE_URL
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Event bus for inter-agent communication
        self.event_bus = None
        self.event_publisher: Optional[Callable] = None
        
        # Store core attributes in state
        self.state.update({
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_type": self.engine_type,
            "description": self.description,
            "model_provider": self.model_provider,
            "instance_id": agent_config.get("instance_id")
        })
        
        self.logger.info(
            f"Engine '{self.engine_name}' (ID: {self.engine_id}, Type: {self.engine_type}) created."
        )

    async def initialize_api_client(self) -> None:
        """Initializes the asynchronous HTTP client for API communication."""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(base_url=self.api_base_url, timeout=30.0)
            self.logger.info(f"HTTP client initialized for API: {self.api_base_url}")

    async def close_api_client(self) -> None:
        """Closes the asynchronous HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
            self.logger.info("HTTP client closed.")

    async def initialize(self) -> None:
        """
        Initialize the engine: set up API client and mark as initialized.
        """
        if self.initialized:
            self.logger.info(f"Engine '{self.engine_name}' already initialized.")
            return

        self.logger.info(f"Initializing engine '{self.engine_name}'...")
        await self.initialize_api_client()

        # Set up tools
        tools = self._setup_tools()
        self.state["tools"] = [str(tool) for tool in tools]  # Store tool info

        self.initialized = True
        self.logger.info(f"Engine '{self.engine_name}' (ID: {self.engine_id}) initialized successfully.")

    @abstractmethod
    def _setup_tools(self) -> List[Any]:
        """Set up tools specific to this engine type. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def process(self, event_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Process an event payload. Must be implemented by subclasses.
        This is the primary method for engine interaction with incoming events.
        """
        pass

    @abstractmethod
    async def handle_delivered_event(self, event: Event, scenario_context: Dict[str, Any], db_session: Session) -> None:
        """
        Handles an event delivered by the EngineManager.
        Subclasses must implement this method to react to relevant events.
        """
        pass

    async def run(self, message: str) -> Dict[str, Any]:
        """
        Run the engine with a message and return structured results.
        This is the primary interface expected by tests and external consumers.
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Process the message as an event payload
            event_payload = {"prompt": message}
            result = await self.process(event_payload)
            
            return {
                "content": result.get("content"),
                "engine_type": self.__class__.__name__,
                "messages": [],  # Placeholder for future message tracking
                "metrics": {},   # Placeholder for future metrics
                "state": self.state,
                "error": result.get("error")
            }
        except Exception as e:
            self.logger.error(f"Error during run for '{self.engine_name}': {e}", exc_info=True)
            return {
                "content": None,
                "engine_type": self.__class__.__name__,
                "messages": [],
                "metrics": {},
                "state": self.state,
                "error": str(e)
            }

    def update_internal_state(self, key: str, value: Any) -> None:
        """Update engine's internal state dictionary."""
        self.state[key] = value
        self.logger.debug(f"State updated: {key} = {value}")

    def get_internal_state(self, key: str, default: Any = None) -> Any:
        """Get value from engine's internal state dictionary."""
        return self.state.get(key, default)

    def export_state(self) -> str:
        """Export current state as a JSON string."""
        try:
            return json.dumps(self.state, indent=2, default=str)
        except TypeError as e:
            self.logger.error(f"Error serializing state to JSON: {e}", exc_info=True)
            return "{}"

    def import_state(self, state_json: str) -> None:
        """Import state from a JSON string, updating the engine's internal state."""
        try:
            loaded_state = json.loads(state_json)
            self.state.update(loaded_state)
            
            # Update core attributes from loaded state if present
            self.engine_id = self.state.get("engine_id", self.engine_id)
            self.engine_name = self.state.get("engine_name", self.engine_name)
            self.engine_type = self.state.get("engine_type", self.engine_type)
            self.description = self.state.get("description", self.description)
            
            self.logger.info(f"State imported successfully for engine '{self.engine_name}'.")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding state JSON: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error importing state: {e}", exc_info=True)

    async def shutdown(self) -> None:
        """Shutdown the engine and clean up resources."""
        self.logger.info(f"Shutting down engine '{self.engine_name}'...")
        await self.close_api_client()
        self.initialized = False
        self.logger.info(f"Engine '{self.engine_name}' shutdown complete.")

    def get_engine_info(self) -> Dict[str, Any]:
        """
        Returns basic information about the engine.
        
        Returns:
            Dict[str, Any]: Engine information
        """
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_type": self.engine_type,
            "description": self.description,
            "model_provider": self.model_provider,
            "initialized": self.initialized
        }

    async def set_event_bus(self, event_bus) -> None:
        """
        Set the event bus for inter-agent communication.
        
        Args:
            event_bus: EventBus instance for publishing events
        """
        self.event_bus = event_bus
        self.logger.info("Event bus set for engine")
    
    async def set_event_publisher(self, publisher_func: Callable) -> None:
        """
        Set the event publisher function for the engine.
        
        Args:
            publisher_func: Function to call for publishing events
        """
        self.event_publisher = publisher_func
        self.logger.info("Event publisher function set")
    
    async def publish_action_output(
        self, 
        scenario_run_id: int,
        output_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Publish an action output event to the event bus.
        
        Args:
            scenario_run_id: ID of the scenario this event belongs to
            output_type: Type of output (e.g., "message", "description")
            data: Payload data for the event
            
        Returns:
            True if event was published successfully
        """
        if not self.event_bus:
            self.logger.error("Cannot publish event: Event bus not set")
            return False
        
        agent_id = self.agent_config.get("instance_id")
        if not agent_id:
            self.logger.error("Cannot publish event: No agent instance ID in config")
            return False
        
        # Create standard event payload
        event_payload = {
            "scenario_run_id": scenario_run_id,
            "source_agent_id": agent_id,
            "output_type": output_type,
            "data": data
        }
        
        # Publish to the event bus
        self.event_bus.publish("agent.action.output", event_payload)
        self.logger.info(f"Published {output_type} event for scenario {scenario_run_id}")
        return True
    
    async def handle_delivered_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle an event delivered to this engine from another agent or the system.
        
        Args:
            event_type: Type of event received
            event_data: Event payload data
        """
        self.logger.info(f"Received event of type {event_type}")
        
        # BaseEngine doesn't have specific event handling logic
        # Subclasses should override this with appropriate behavior
        pass
