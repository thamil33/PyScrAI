# pyscrai/engines/actor_engine.py
"""
ActorEngine for PyScrAI.

This engine is responsible for simulating characters with specific
personality traits and behaviors. It extends the BaseEngine and
utilizes an Agno Agent for LLM interactions, configured during initialization.
"""
import os
import logging # Added for explicit logger
from typing import Any, Dict, List, Optional

from agno.agent import Agent # Base Agent for type hinting
from agno.models.message import Message
from agno.run.response import RunResponse # To type hint agent responses

from .base_engine import BaseEngine
# Assuming event schemas will be defined here or imported for type hinting later
# from ..databases.models.schemas import QueuedEventResponse, EventStatusUpdate

# Initialize a logger for this module
logger = logging.getLogger(__name__)


class ActorEngine(BaseEngine):
    """
    ActorEngine for character simulation.

    Inherits from BaseEngine and implements character-specific logic,
    including personality configuration and event processing.

    Attributes:
        personality_traits (Optional[str]): A description of the character's
                                            personality.
        character_name (str): The name of the character this engine represents.
    """

    async def initialize(self, register_with_server: bool = True) -> None:
        """
        Initializes the ActorEngine, including the underlying Agno agent
        and personality configuration.

        Args:
            register_with_server (bool): Whether to register the engine with the server.
        """
        if self.initialized:
            self.logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) already initialized.")
            return

        # Call the parent's initialize method, passing the argument
        await super().initialize(register_with_server=register_with_server) 

        if self.agent:
            self._configure_agent_personality() # Ensure this method exists and is correctly named
            self.logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) fully initialized.")
        else:
            # BaseEngine's initialize should log errors if agent creation fails
            self.logger.error(f"Agent not initialized in BaseEngine for ActorEngine '{self.engine_name}'. Personality not configured.")
        # self.initialized is set by BaseEngine

            self.logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) already initialized.")
            return

        # Call the parent's initialize method, passing the argument
        await super().initialize(register_with_server=register_with_server) 
        
        if self.agent:
            self._configure_agent_personality() # Ensure this method exists and is correctly named
            self.logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) fully initialized.")
        else:
            # BaseEngine's initialize should log errors if agent creation fails
            self.logger.error(f"Agent not initialized in BaseEngine for ActorEngine '{self.engine_name}'. Personality not configured.")
        # self.initialized is set by BaseEngine


    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "ActorEngine",
        description: Optional[str] = "Simulates a character in a scenario.",
        personality_traits: Optional[str] = "A neutral and helpful character.",
        character_name: str = "Character", # Made non-optional, default "Character"
        storage_path: Optional[str] = None, # For BaseEngine
        model_provider: str = "openrouter", # For BaseEngine
        **kwargs: Any, # To catch any other BaseEngine or future params
    ):
        """
        Initializes the ActorEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the Agno Agent.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            personality_traits (Optional[str]): Text describing the character's personality.
            character_name (str): The name of the character.
            storage_path (Optional[str]): Path for the agent's storage (e.g., SQLite file).
            model_provider (str): The provider for the LLM model (e.g., 'openrouter', 'lmstudio').
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent_config=agent_config,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            storage_path=storage_path,
            model_provider=model_provider,
            engine_type="Actor", # Explicitly set engine type
            **kwargs,
        )
        self.personality_traits: Optional[str] = personality_traits
        self.character_name: str = character_name
        
        # Store actor-specific attributes in the shared state
        self.state["character_name"] = self.character_name
        self.state["personality_traits"] = self.personality_traits

        logger.info(f"ActorEngine '{self.engine_name}' for character '{self.character_name}' configured. Call initialize() to activate.")

    async def initialize(self) -> None:
        """
        Initializes the ActorEngine, including the underlying Agno agent
        and personality configuration.
        """
        if self.initialized:
            logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) already initialized.")
            return

        await super().initialize() # This creates and initializes self.agent
        
        if self.agent:
            self._configure_agent_personality()
            logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) fully initialized.")
        else:
            logger.error(f"Agent initialization failed for ActorEngine '{self.engine_name}'. Personality not configured.")
            # self.initialized will remain False if super().initialize() failed to set self.agent

    def _configure_agent_personality(self) -> None:
        """
        Configures the underlying Agno Agent with the character's personality traits.
        This is typically done by setting or augmenting the agent's system message.
        This method should be called after the agent has been initialized.
        """
        if not self.agent: # self.agent is an instance of agno.Agent
            logger.warning(f"Agno agent not available for {self.character_name}. Cannot configure personality.")
            return

        base_system_message_content = ""
        # Agno Agent's system_message can be a string, Message, or callable
        if self.agent.system_message:
            if isinstance(self.agent.system_message, Message):
                base_system_message_content = self.agent.system_message.get_content_as_str()
            elif callable(self.agent.system_message):
                try:
                    # Attempt to call with agent if it's part of its signature
                    base_system_message_content = self.agent.system_message(agent=self.agent)
                except TypeError:
                    # Fallback if it doesn't take agent
                    base_system_message_content = self.agent.system_message()
            else: # It's a string
                base_system_message_content = str(self.agent.system_message)
        
        personality_prompt = f"You are playing the role of {self.character_name}. "
        if self.personality_traits:
            personality_prompt += f"Your personality is: {self.personality_traits}. "
        personality_prompt += "Respond in character, embodying this personality in your actions and dialogue. Be concise and stay in character."

        # Prepend personality to existing system message or set it if none exists
        if base_system_message_content and base_system_message_content.strip():
            self.agent.system_message = f"{personality_prompt}\n\nOriginal context: {base_system_message_content}"
        else:
            self.agent.system_message = personality_prompt
        
        logger.info(f"Configured personality for {self.character_name} ({self.engine_name}).")
        logger.debug(f"New system message for {self.character_name}: {self.agent.system_message}")

    def _setup_tools(self) -> List[Any]:
        """
        Sets up tools specific to the ActorEngine.
        Currently, no actor-specific tools are defined.

        Returns:
            List[Any]: An empty list of tools.
        """
        # Example: If actors had specific tools like "CheckInventory" or "PerformAction"
        # from agno.tools.function import FunctionTool
        # def check_inventory_func(item_name: str) -> str:
        #     """Checks if the character has a specific item in their inventory."""
        #     inventory = self.state.get("inventory", {})
        #     if item_name in inventory and inventory[item_name] > 0:
        #         return f"Yes, {self.character_name} has {item_name}."
        #     return f"No, {self.character_name} does not have {item_name}."
        #
        # check_inventory_tool = FunctionTool(fn=check_inventory_func)
        # return [check_inventory_tool]
        logger.debug(f"ActorEngine '{self.engine_name}' setup tools: None")
        return []

    async def process(self, event_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an event payload and generates a response based on the character's role
        and personality. This is the primary method for engine interaction.

        Args:
            event_payload (Dict[str, Any]): Data associated with the event.
                                         Expected to contain 'prompt' for the LLM.
            **kwargs: Additional keyword arguments for the Agno Agent's arun method.

        Returns:
            Dict[str, Any]: A dictionary containing the agent's response ('content')
                            and any errors ('error').
        """
        if not self.initialized or not self.agent:
            logger.error(f"ActorEngine '{self.engine_name}' ({self.character_name}) not initialized. Cannot process event.")
            return {"content": None, "error": "Engine not initialized"}

        logger.info(
            f"{self.engine_name} ({self.character_name}) processing event payload."
        )
        logger.debug(f"Event payload: {event_payload}")

        prompt = event_payload.get("prompt")
        if not prompt:
            logger.warning("No 'prompt' found in event_payload for ActorEngine.")
            return {"content": None, "error": "No prompt provided in event payload"}

        # The personality is handled by the agent's system message.
        # The prompt is the direct input that the character should react to.
        # No need to prepend "As {self.character_name}" here if system message is well-defined.
        
        try:
            # Use the agent's arun method for asynchronous execution
            # The message to agent is simply the prompt it needs to react to.
            response: Optional[RunResponse] = await self.agent.arun(message=str(prompt), **kwargs)
            
            if response and response.content:
                logger.debug(f"{self.character_name} raw response: {response.content}")
                # Update any actor-specific state based on the response if needed
                # For example, if the response indicates a change in mood or inventory.
                # self.update_state("last_response", response.content)
                return {"content": response.content, "error": None}
            else:
                logger.warning(f"{self.character_name} produced no content in response.")
                return {"content": None, "error": "Agent produced no content"}
        except Exception as e:
            logger.error(f"Error during {self.engine_name} ({self.character_name}) run: {e}", exc_info=True)
            return {"content": None, "error": str(e)}

    # The get_state and load_state methods from the original ActorEngine
    # are now largely handled by BaseEngine's self.state, export_state, and import_state.
    # ActorEngine-specific state (character_name, personality_traits) is added to self.state
    # in __init__ and would be loaded if BaseEngine.import_state is called with a state
    # dictionary containing these keys.
    # If more complex actor-specific state logic is needed, these can be overridden.

    # Example of how to run this engine (for testing or direct use)
    # This would typically be part of a larger orchestration system.
async def main_actor_example():
    """Example usage of the ActorEngine."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
        print("Error: OPENAI_API_KEY or OPENROUTER_API_KEY not found.")
        print("Please set one to run this example.")
        return

    # Configure logging for the example
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


    # 1. Define Agent Configuration
    # Using OpenRouter by default as per BaseEngine
    actor_agent_config = {
        "model_config": {
            "id": "openai/gpt-3.5-turbo", # Example model on OpenRouter
            "temperature": 0.7,
            # Add other OpenRouter/OpenAI specific params if needed
        },
        "personality_config": { # This part is used by Agno Agent directly
            "name": "Captain Pegleg Pete", # Will be overridden by ActorEngine's character_name for system prompt
            "description": "An AI agent simulating a pirate captain.", # Generic agent description
            "instructions": "You are a helpful AI assistant.", # Generic instructions, will be augmented by personality
        },
        # "agent_kwargs": {"debug_mode": True} # Optional: for Agno agent
    }

    # 2. Create an ActorEngine instance
    pirate_actor = ActorEngine(
        agent_config=actor_agent_config,
        engine_name="PirateActor",
        character_name="Captain Pegleg Pete",
        personality_traits="A gruff, treasure-obsessed pirate with a penchant for saying 'Arrr!' and a secret soft spot for parrots.",
        description="Simulates Captain Pegleg Pete, a notorious pirate.",
        storage_path="pirate_actor_storage.db", # Example storage
        model_provider="openrouter" # or "lmstudio" if configured
    )

    # 3. Initialize the engine (and its Agno agent)
    await pirate_actor.initialize()

    if not pirate_actor.initialized or not pirate_actor.agent:
        logger.error("Failed to initialize pirate_actor. Exiting example.")
        return

    # --- Simulate an event ---
    logger.info(f"\n--- Simulating event for {pirate_actor.character_name} ---")
    event_payload_dialogue = {"prompt": "Another pirate challenges you for your map to Treasure Island!"}
    
    response_data = await pirate_actor.process(event_payload_dialogue)

    if response_data["content"]:
        logger.info(f"\n{pirate_actor.character_name} says: {response_data['content']}")
    else:
        logger.error(f"\n{pirate_actor.character_name} had no response or an error occurred: {response_data['error']}")

    # --- Example of state (simplified) ---
    logger.info("\n--- State Example ---")
    # BaseEngine's state now includes character_name and personality_traits
    current_state_json = pirate_actor.export_state()
    logger.info(f"Exported state: {current_state_json}")

    # Create a new engine instance and load state
    new_actor_agent_config = actor_agent_config.copy() # Use the same config
    loaded_pirate_actor = ActorEngine(
        agent_config=new_actor_agent_config,
        character_name="Captain Pegleg Pete", # Needs to be passed for re-configuration
        personality_traits="A gruff pirate.", # Can be different if state overrides it
        storage_path="loaded_pirate_actor_storage.db"
    )
    # Manually import state (in a real scenario, this might come from DB)
    loaded_pirate_actor.import_state(current_state_json)
    await loaded_pirate_actor.initialize() # Initialize to create agent and apply personality

    logger.info(f"Loaded actor name from state: {loaded_pirate_actor.state.get('character_name')}")
    logger.info(f"Loaded personality from state: {loaded_pirate_actor.state.get('personality_traits')}")
    logger.info(f"Loaded actor's direct attribute name: {loaded_pirate_actor.character_name}")


    # Test the loaded actor
    event_payload_threat = {"prompt": "A kraken appears! What do you do?"}
    loaded_response_data = await loaded_pirate_actor.process(event_payload_threat)
    if loaded_response_data["content"]:
        logger.info(f"\nLoaded {loaded_pirate_actor.character_name} responds: {loaded_response_data['content']}")
    else:
        logger.error(f"\nLoaded {loaded_pirate_actor.character_name} had no response or an error: {loaded_response_data['error']}")

if __name__ == "__main__":
    # To run the async example:
    import asyncio
    # Basic logging setup for the example run
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main_actor_example())

