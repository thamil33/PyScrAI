# pyscrai/engines/base_engine.py
"""
Abstract base class for all PyScrAI engines.
Provides core functionalities including Agno agent initialization,
state management, and basic API interaction capabilities.
"""

import asyncio
import json
import logging
import os # For API base URL
import uuid # For generating unique engine IDs
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx # For asynchronous HTTP requests
from agno.agent import Agent
from agno.models.lmstudio import LMStudio
from agno.models.openrouter import OpenRouter
from agno.storage.sqlite import SqliteStorage

# Assuming Pydantic schemas for API interaction are in this path
# Adjust the import path if schemas are located elsewhere
from ..databases.models.schemas import (
    EngineHeartbeat,
    EngineRegistration,
    # EngineStateResponse, # For fetching state
    EventStatusUpdate,
    QueuedEventResponse,
    ResourceLimits, # Used by EngineRegistration
)

# Default API base URL - can be overridden by environment variable
PYSCRAI_API_BASE_URL = os.getenv("PYSCRAI_API_BASE_URL", "http://localhost:8000/api/v1")

class BaseEngine(ABC):
    """
    Abstract base class for all PyScrAI engines.

    Handles agent initialization, state persistence, and provides
    methods for interacting with the PyScrAI database API.
    """

    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = None, # Made optional, class name can be default
        engine_type: str = "BaseEngine", # Specific type (e.g., "Actor", "Narrator")
        description: Optional[str] = "A PyScrAI processing engine.",
        storage_path: Optional[str] = None,
        model_provider: str = "openrouter",
        api_base_url: Optional[str] = None, # Allow overriding API URL
    ):
        """
        Initializes the BaseEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the Agno Agent.
            engine_id (Optional[str]): A unique identifier for the engine.
                                       If None, a new UUID will be generated.
            engine_name (Optional[str]): A human-readable name for the engine.
                                         Defaults to the class name.
            engine_type (str): The specific type of the engine (e.g., "Actor").
            description (Optional[str]): A brief description of the engine's purpose.
            storage_path (Optional[str]): Path for the agent's storage (e.g., SQLite file).
            model_provider (str): The provider for the LLM model.
            api_base_url (Optional[str]): The base URL for the PyScrAI API.
                                          Defaults to PYSCRAI_API_BASE_URL.
        """
        self.engine_id: str = engine_id or str(uuid.uuid4())
        self.engine_name: str = engine_name or self.__class__.__name__
        self.engine_type: str = engine_type
        self.description: Optional[str] = description        
        self.agent_config: Dict[str, Any] = agent_config
        self.storage_path: Optional[str] = storage_path
        self.model_provider: str = model_provider
        
        self.agent: Optional[Agent] = None
        self.state: Dict[str, Any] = {}  # Initialize as empty dict
        self.initialized: bool = False
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        
        self.api_base_url: str = api_base_url or PYSCRAI_API_BASE_URL
        self.http_client: Optional[httpx.AsyncClient] = None
        
        self.logger.info(
            f"Engine '{self.engine_name}' (ID: {self.engine_id}, Type: {self.engine_type}) created. "
            f"Call initialize() to activate."
        )

    async def initialize_api_client(self) -> None:
        """Initializes the asynchronous HTTP client for API communication."""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(base_url=self.api_base_url, timeout=30.0)
            self.logger.info(f"HTTP client initialized for API: {self.api_base_url}")
        else:
            self.logger.info("HTTP client already initialized.")

    async def close_api_client(self) -> None:
        """Closes the asynchronous HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
            self.logger.info("HTTP client closed.")

    async def initialize(self, register_with_server: bool = True) -> None:
        """
        Initialize the engine: set up the Agno agent, API client,
        and optionally register with the server.
        """
        if self.initialized:
            self.logger.info(f"Engine '{self.engine_name}' already initialized.")
            return

        self.logger.info(f"Initializing engine '{self.engine_name}'...")
        await self.initialize_api_client()

        # Set up model
        model_config = self.agent_config.get("model_config", {})
        if self.model_provider == "openrouter":
            model = OpenRouter(
                id=model_config.get("id", "meta-llama/llama-3.1-8b-instruct:free"),
                temperature=model_config.get("temperature", 0.7),
                **{k: v for k, v in model_config.items() if k not in ["id", "temperature"]},
            )
        elif self.model_provider == "lmstudio":
            model_id = model_config.get("id")
            if not model_id:
                self.logger.warning("LMStudio model ID not provided in agent_config.model_config.id, agent might not function.")
            model = LMStudio(
                id=model_id, # type: ignore
                base_url=model_config.get("base_url"), # LMStudio specific
                 **{k: v for k, v in model_config.items() if k not in ["id", "base_url"]},
            )
        else:
            self.logger.error(f"Unsupported model provider: {self.model_provider}")
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

        # Set up storage
        storage = None
        if self.storage_path:
            storage_table_name = f"engine_{self.engine_name.lower().replace(' ', '_')}" # Simpler table name
            storage = SqliteStorage(
                db_file=self.storage_path,
                table_name=storage_table_name
            )
            self.logger.info(f"Agent storage configured at '{self.storage_path}' with table '{storage_table_name}'.")

        # Set up tools
        tools = self._setup_tools()

        # Create agent
        personality_config = self.agent_config.get("personality_config", {})
        try:
            self.agent = Agent(
                name=personality_config.get("name", f"{self.engine_name} Agent"),
                model=model,
                description=personality_config.get("description", self.description),
                instructions=personality_config.get("instructions", ""),
                storage=storage,
                tools=tools,
                **personality_config.get("agent_kwargs", {}),
            )
            self.logger.info(f"Agno Agent '{self.agent.name}' created for engine '{self.engine_name}'.")
        except Exception as e:
            self.logger.error(f"Failed to create Agno Agent for '{self.engine_name}': {e}", exc_info=True)
            # self.initialized remains False
            return


        if register_with_server:
            # Placeholder for capabilities and resource limits - should be defined by specialized engines
            # or passed in config.
            capabilities = self.state.get("capabilities", [self.engine_type, "general_processing"])
            resource_limits_config = self.state.get("resource_limits", {"max_concurrent_events": 1, "memory_limit_mb": 512})
            
            # Ensure resource_limits_config is a dict for ResourceLimits
            if not isinstance(resource_limits_config, dict):
                self.logger.warning("resource_limits in state is not a dict, using defaults.")
                resource_limits_config = {"max_concurrent_events": 1, "memory_limit_mb": 512}

            reg_success = await self.register_engine_instance(
                capabilities=capabilities,
                resource_limits_dict=resource_limits_config
            )
            if not reg_success:
                self.logger.warning(f"Engine '{self.engine_name}' failed to register with the server.")
                # Decide if this is a critical failure. For now, we'll allow initialization to proceed.
            else:
                 # Fetch state from server after registration to sync
                await self.fetch_engine_state_from_server()

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

    async def run_agent_interaction(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Directly run the Agno agent with a message and return structured results.
        This is more for direct testing or specific agent interactions outside the event loop.
        """
        if not self.initialized or not self.agent:
            self.logger.error(f"Engine '{self.engine_name}' or its agent is not initialized. Cannot run interaction.")
            await self.initialize() # Attempt to initialize if not already
            if not self.initialized or not self.agent: # Check again
                 return {"content": None, "error": "Engine or agent not initialized"}


        self.logger.debug(f"Running agent interaction for '{self.engine_name}' with message: '{message[:50]}...'")
        try:
            response = await self.agent.arun(message, **kwargs)
            
            result = {
                "content": response.content if response else None,
                "messages": [msg.dict() for msg in response.messages] if response else [],
                "metrics": response.metrics.dict() if response and response.metrics else None,
                "error": None
            }
            self.logger.debug(f"Agent interaction for '{self.engine_name}' completed.")
            return result
        except Exception as e:
            self.logger.error(f"Error during agent interaction for '{self.engine_name}': {e}", exc_info=True)
            return {"content": None, "error": str(e)}

    async def run(self, message: str) -> Dict[str, Any]:
        """
        Run the agent with a message and return structured results in the expected format.
        This is the primary interface expected by tests and external consumers.
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.agent:
            self.logger.error(f"Engine '{self.engine_name}' agent is not initialized. Cannot run.")
            return {
                "content": None,
                "engine_type": self.__class__.__name__,
                "messages": [],
                "metrics": {},
                "state": self.state,
                "error": "Agent not initialized"
            }

        try:
            response = await self.agent.arun(message)
            return {
                "content": response.content,
                "engine_type": self.__class__.__name__,
                "messages": [m.dict() for m in response.messages],
                "metrics": response.metrics.dict(),
                "state": self.state,
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
            return json.dumps(self.state, indent=2, default=str) # Add default=str for non-serializable types like datetime
        except TypeError as e:
            self.logger.error(f"Error serializing state to JSON: {e}", exc_info=True)
            return "{}" # Return empty JSON on error

    def import_state(self, state_json: str) -> None:
        """Import state from a JSON string, updating the engine's internal state."""
        try:
            loaded_state = json.loads(state_json)
            self.state.update(loaded_state) # Merge, don't overwrite, to preserve initial state keys
            
            # Ensure core attributes are also updated from the loaded state if present
            self.engine_id = self.state.get("engine_id", self.engine_id)
            self.engine_name = self.state.get("engine_name", self.engine_name)
            self.engine_type = self.state.get("engine_type", self.engine_type)
            self.description = self.state.get("description", self.description)
            
            self.logger.info(f"State imported successfully for engine '{self.engine_name}'.")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding state JSON: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Error importing state: {e}", exc_info=True)

    # --- API Interaction Methods ---

    async def register_engine_instance(self, capabilities: List[str], resource_limits_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Registers this engine instance with the PyScrAI server.

        Args:
            capabilities (List[str]): List of capabilities this engine offers.
            resource_limits_dict (Dict[str, Any]): Dictionary for resource limits.

        Returns:
            Optional[Dict[str, Any]]: The server's response data (usually EngineStateResponse)
                                      or None if registration fails.
        """
        if not self.http_client:
            self.logger.error("HTTP client not initialized. Cannot register engine.")
            return None

        try:
            # Ensure resource_limits_dict can be parsed by ResourceLimits
            resource_limits = ResourceLimits(**resource_limits_dict)
            registration_payload = EngineRegistration(
                engine_type=self.engine_type,
                capabilities=capabilities,
                resource_limits=resource_limits,
                # The API might expect engine_id in the payload for idempotent registration
                # or it might generate one. For now, we assume the server handles it.
                # If engine_id needs to be sent:
                # engine_id=self.engine_id # Add this to EngineRegistration schema if needed
            )
            endpoint = "/engine-instances/" # POST to this endpoint
            
            self.logger.info(f"Registering engine '{self.engine_name}' (ID: {self.engine_id}) at {self.api_base_url}{endpoint}...")
            response = await self.http_client.post(
                endpoint,
                json=registration_payload.model_dump()
            )
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            
            response_data = response.json()
            self.logger.info(f"Engine '{self.engine_name}' registered successfully. Server response: {response_data}")
            
            # Update engine_id if the server assigned/confirmed one different from a generated one.
            # Also update other relevant fields from the response.
            if "id" in response_data and response_data["id"] != self.engine_id:
                self.logger.info(f"Engine ID updated by server from {self.engine_id} to {response_data['id']}")
                self.engine_id = response_data["id"]
                self.state["engine_id"] = self.engine_id # Keep state consistent
            
            # Potentially update other state based on EngineStateResponse from server
            self.state.update(response_data) # Merge server state
            return response_data

        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error during engine registration: {e.response.status_code} - {e.response.text}", exc_info=True)
        except httpx.RequestError as e:
            self.logger.error(f"Request error during engine registration: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Unexpected error during engine registration: {e}", exc_info=True)
        return None

    async def send_heartbeat(self, status: str, current_workload: int, resource_utilization: Dict[str, float]) -> bool:
        """
        Sends a heartbeat signal to the PyScrAI server.

        Args:
            status (str): Current status of the engine (e.g., "idle", "processing").
            current_workload (int): Number of active tasks.
            resource_utilization (Dict[str, float]): Resource usage (e.g., {"cpu": 0.5, "memory": 0.3}).

        Returns:
            bool: True if heartbeat was sent successfully, False otherwise.
        """
        if not self.http_client:
            self.logger.error("HTTP client not initialized. Cannot send heartbeat.")
            return False
        if not self.engine_id: # Should be set by now
            self.logger.error("Engine ID not set. Cannot send heartbeat.")
            return False

        try:
            heartbeat_payload = EngineHeartbeat(
                status=status,
                current_workload=current_workload,
                resource_utilization=resource_utilization,
            )
            endpoint = f"/engine-instances/{self.engine_id}/heartbeat"
            
            self.logger.debug(f"Sending heartbeat for engine '{self.engine_name}' (ID: {self.engine_id})...")
            response = await self.http_client.put(
                endpoint,
                json=heartbeat_payload.model_dump()
            )
            response.raise_for_status()
            self.logger.debug(f"Heartbeat sent successfully for engine '{self.engine_name}'.")
            return True
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error sending heartbeat: {e.response.status_code} - {e.response.text}", exc_info=True)
        except httpx.RequestError as e:
            self.logger.error(f"Request error sending heartbeat: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Unexpected error sending heartbeat: {e}", exc_info=True)
        return False

    async def update_engine_state_on_server(self) -> bool:
        """
        Persists the current engine's internal state to the server.
        """
        if not self.http_client or not self.engine_id:
            self.logger.error("HTTP client or engine ID not initialized. Cannot update state on server.")
            return False

        try:
            state_payload_json = self.export_state() # Get current state as JSON string
            # The API expects a JSON object, not a string. So, parse it back.
            state_payload_dict = json.loads(state_payload_json)

            endpoint = f"/engine-instances/{self.engine_id}/state"
            self.logger.debug(f"Updating engine state on server for '{self.engine_name}' (ID: {self.engine_id})...")
            response = await self.http_client.put(endpoint, json=state_payload_dict)
            response.raise_for_status()
            self.logger.info(f"Engine state updated on server for '{self.engine_name}'.")
            return True
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error updating server state: {e.response.status_code} - {e.response.text}", exc_info=True)
        except httpx.RequestError as e:
            self.logger.error(f"Request error updating server state: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Unexpected error updating server state: {e}", exc_info=True)
        return False

    async def fetch_engine_state_from_server(self) -> bool:
        """
        Fetches the engine's state from the server and updates the internal state.
        """
        if not self.http_client or not self.engine_id:
            self.logger.error("HTTP client or engine ID not initialized. Cannot fetch state from server.")
            return False
        
        try:
            endpoint = f"/engine-instances/{self.engine_id}/state"
            self.logger.debug(f"Fetching engine state from server for '{self.engine_name}' (ID: {self.engine_id})...")
            response = await self.http_client.get(endpoint)
            response.raise_for_status()
            
            server_state_data = response.json()
            # Assuming the response is the full state dictionary
            self.import_state(json.dumps(server_state_data)) # import_state expects JSON string
            self.logger.info(f"Engine state fetched and imported from server for '{self.engine_name}'.")
            return True
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error fetching server state: {e.response.status_code} - {e.response.text}", exc_info=True)
        except httpx.RequestError as e:
            self.logger.error(f"Request error fetching server state: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Unexpected error fetching server state: {e}", exc_info=True)
        return False

    async def poll_events_from_queue(self, max_events: int = 5) -> Optional[List[QueuedEventResponse]]:
        """
        Polls the event queue for new events relevant to this engine's type.

        Args:
            max_events (int): Maximum number of events to fetch.

        Returns:
            Optional[List[QueuedEventResponse]]: A list of queued events, or None if an error occurs.
        """
        if not self.http_client:
            self.logger.error("HTTP client not initialized. Cannot poll event queue.")
            return None

        try:
            endpoint = f"/events/queue/{self.engine_type}?limit={max_events}"
            self.logger.debug(f"Polling event queue for engine type '{self.engine_type}' (limit: {max_events})...")
            response = await self.http_client.get(endpoint)
            response.raise_for_status()
            
            events_data = response.json()
            queued_events = [QueuedEventResponse(**event) for event in events_data]
            self.logger.info(f"Polled {len(queued_events)} events for engine type '{self.engine_type}'.")
            return queued_events
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error polling event queue: {e.response.status_code} - {e.response.text}", exc_info=True)
        except httpx.RequestError as e:
            self.logger.error(f"Request error polling event queue: {e}", exc_info=True)
        except Exception as e: # Includes Pydantic validation errors
            self.logger.error(f"Unexpected error polling event queue: {e}", exc_info=True)
        return None

    async def update_event_processing_status(
        self, event_id: int, status: str, result: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None
    ) -> bool:
        """
        Updates the status of an event after processing.

        Args:
            event_id (int): The ID of the event to update.
            status (str): The new status (e.g., "completed", "failed").
            result (Optional[Dict[str, Any]]): Processing results if successful.
            error_message (Optional[str]): Error message if processing failed.

        Returns:
            bool: True if the status was updated successfully, False otherwise.
        """
        if not self.http_client:
            self.logger.error("HTTP client not initialized. Cannot update event status.")
            return False

        try:
            status_payload = EventStatusUpdate(status=status, result=result, error=error_message)
            endpoint = f"/events/{event_id}/status"
            
            self.logger.debug(f"Updating status for event ID {event_id} to '{status}'...")
            response = await self.http_client.put(
                endpoint,
                json=status_payload.model_dump(exclude_none=True) # Don't send nulls for optional fields
            )
            response.raise_for_status()
            self.logger.info(f"Status for event ID {event_id} updated to '{status}'.")
            return True
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error updating event status for event {event_id}: {e.response.status_code} - {e.response.text}", exc_info=True)
        except httpx.RequestError as e:
            self.logger.error(f"Request error updating event status for event {event_id}: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Unexpected error updating event status for event {event_id}: {e}", exc_info=True)
        return False

    async def main_loop(self, poll_interval: int = 5):
        """
        Main operational loop for the engine.
        Polls for events, processes them, and sends heartbeats.
        """
        if not self.initialized:
            self.logger.error(f"Engine '{self.engine_name}' cannot start main loop: not initialized.")
            return

        self.logger.info(f"Engine '{self.engine_name}' starting main loop with poll interval {poll_interval}s.")
        try:
            while True: # Loop indefinitely until explicitly stopped or an unrecoverable error
                # 1. Poll for events
                queued_events = await self.poll_events_from_queue(max_events=self.state.get("resource_limits", {}).get("max_concurrent_events", 1))
                
                current_workload = 0
                if queued_events:
                    current_workload = len(queued_events)
                    for event in queued_events:
                        self.logger.info(f"Processing event ID: {event.id}, Type ID: {event.event_type_id}")
                        try:
                            # Mark as processing immediately (optional, depends on API design)
                            # await self.update_event_processing_status(event.id, "processing")

                            processing_result = await self.process(event.data) # Specialized engine implements process
                            
                            if processing_result.get("error"):
                                await self.update_event_processing_status(
                                    event_id=event.id,
                                    status="failed",
                                    error_message=str(processing_result["error"])
                                )
                            else:
                                await self.update_event_processing_status(
                                    event_id=event.id,
                                    status="completed",
                                    result=processing_result # This is the content from the engine's process method
                                )
                        except Exception as e:
                            self.logger.error(f"Critical error processing event ID {event.id}: {e}", exc_info=True)
                            await self.update_event_processing_status(event.id, "failed", error_message=f"Critical engine error: {str(e)}")
                
                # 2. Send heartbeat
                # TODO: Implement actual resource utilization monitoring
                resource_util = {"cpu": 0.0, "memory_mb": 0.0} 
                await self.send_heartbeat(
                    status="idle" if current_workload == 0 else "processing",
                    current_workload=current_workload,
                    resource_utilization=resource_util
                )
                
                # 3. Persist state periodically (optional, or on significant changes)
                # await self.update_engine_state_on_server()

                await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            self.logger.info(f"Main loop for engine '{self.engine_name}' cancelled.")
        except Exception as e:
            self.logger.critical(f"Critical error in main loop for engine '{self.engine_name}': {e}", exc_info=True)
        finally:
            self.logger.info(f"Engine '{self.engine_name}' shutting down main loop.")
            await self.close_api_client()

