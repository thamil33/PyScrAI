# pyscrai/engines/actor_engine.py
"""
ActorEngine for PyScrAI.

This engine is responsible for simulating characters with specific
personality traits and behaviors. It extends the BaseEngine and
utilizes an Agno Agent for LLM interactions.
"""
import os

from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.message import Message
from agno.run.response import RunResponse

from .base_engine import BaseEngine


class ActorEngine(BaseEngine):
    """
    ActorEngine for character simulation.

    Attributes:
        personality_traits (Optional[str]): A description of the character's
                                            personality, influencing its responses.
                                            This will be incorporated into the
                                            Agno Agent's system message or instructions.
        character_name (Optional[str]): The name of the character this engine represents.
    """

    def __init__(
        self,
        agent: Agent,
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "ActorEngine",
        description: Optional[str] = "Simulates a character in a scenario.",
        personality_traits: Optional[str] = "A neutral and helpful character.",
        character_name: Optional[str] = "Character",
        **kwargs: Any,
    ):
        """
        Initializes the ActorEngine.

        Args:
            agent (Agent): The Agno Agent to be used for LLM interactions.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            personality_traits (Optional[str]): Text describing the character's personality.
            character_name (Optional[str]): The name of the character.
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent=agent,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            **kwargs,
        )
        self.personality_traits: Optional[str] = personality_traits
        self.character_name: Optional[str] = character_name or "Character"

        # Configure the underlying Agno Agent with personality traits
        self._configure_agent_personality()

    def _configure_agent_personality(self) -> None:
        """
        Configures the underlying Agno Agent with the character's personality traits.
        This is typically done by setting or augmenting the agent's system message
        or instructions.
        """
        if self.agent is None:
            self.logger.warning("Agno agent not initialized. Cannot configure personality.")
            return

        # Construct a system message incorporating personality
        # This is a basic example; more sophisticated prompting might be needed.
        base_system_message = self.agent.system_message or ""
        if isinstance(base_system_message, Message):
            base_system_message_content = base_system_message.get_content_as_str()
        elif callable(base_system_message):
            # Assuming the callable takes the agent as an argument
            try:
                base_system_message_content = base_system_message(agent=self.agent)
            except TypeError:
                base_system_message_content = base_system_message()
        else:
            base_system_message_content = str(base_system_message)


        personality_prompt = f"You are {self.character_name}. "
        if self.personality_traits:
            personality_prompt += f"Your personality is: {self.personality_traits}. "
        personality_prompt += "Respond in character, embodying this personality in your actions and dialogue."

        # Prepend personality to existing system message or set it if none exists
        if base_system_message_content:
            self.agent.system_message = f"{personality_prompt}\n\n{base_system_message_content}"
        else:
            self.agent.system_message = personality_prompt
        
        self.logger.info(f"Configured personality for {self.character_name} ({self.engine_name}).")
        self.logger.debug(f"New system message for {self.character_name}: {self.agent.system_message}")


    def process_event(
        self, event_type: str, event_data: Dict[str, Any], **kwargs: Any
    ) -> Optional[RunResponse]:
        """
        Processes an event and generates a response based on the character's role
        and personality.

        Args:
            event_type (str): The type of event (e.g., "dialogue_prompt", "action_request").
            event_data (Dict[str, Any]): Data associated with the event.
                                         Expected to contain 'prompt' for the LLM.
            **kwargs: Additional keyword arguments for the Agno Agent's run method.

        Returns:
            Optional[RunResponse]: The response from the Agno Agent, or None if an error occurs.
        """
        self.logger.info(
            f"{self.engine_name} ({self.character_name}) processing event: {event_type}"
        )
        self.logger.debug(f"Event data: {event_data}")

        if self.agent is None:
            self.logger.error("Agno agent not initialized for ActorEngine.")
            return None

        prompt = event_data.get("prompt")
        if not prompt:
            self.logger.warning("No 'prompt' found in event_data for ActorEngine.")
            return None

        # Construct a message for the agent
        # The prompt here is the direct input that the character should react to.
        # The personality is handled by the agent's system message.
        message_to_agent = f"As {self.character_name}, respond to the following: {prompt}"

        try:
            # Use the agent's run method
            # Pass through any additional kwargs like 'stream'
            response = self.agent.run(message=message_to_agent, **kwargs)
            self.logger.debug(f"{self.character_name} raw response: {response.content if response else 'None'}") # type: ignore
            return response # type: ignore
        except Exception as e:
            self.logger.error(f"Error during {self.engine_name} ({self.character_name}) run: {e}")
            return None

    async def aprocess_event(
        self, event_type: str, event_data: Dict[str, Any], **kwargs: Any
    ) -> Optional[RunResponse]:
        """
        Asynchronously processes an event and generates a response.

        Args:
            event_type (str): The type of event.
            event_data (Dict[str, Any]): Data associated with the event.
            **kwargs: Additional keyword arguments for the Agno Agent's arun method.

        Returns:
            Optional[RunResponse]: The asynchronous response from the Agno Agent.
        """
        self.logger.info(
            f"{self.engine_name} ({self.character_name}) asynchronously processing event: {event_type}"
        )
        self.logger.debug(f"Async event data: {event_data}")

        if self.agent is None:
            self.logger.error("Agno agent not initialized for ActorEngine (async).")
            return None

        prompt = event_data.get("prompt")
        if not prompt:
            self.logger.warning("No 'prompt' found in event_data for ActorEngine (async).")
            return None

        message_to_agent = f"As {self.character_name}, respond to the following: {prompt}"

        try:
            # Use the agent's arun method for asynchronous execution
            response = await self.agent.arun(message=message_to_agent, **kwargs)
            self.logger.debug(f"{self.character_name} async raw response: {response.content if response else 'None'}") # type: ignore
            return response # type: ignore
        except Exception as e:
            self.logger.error(f"Error during async {self.engine_name} ({self.character_name}) run: {e}")
            return None

    def get_state(self) -> Dict[str, Any]:
        """
        Gets the current state of the ActorEngine.

        Returns:
            Dict[str, Any]: The current state of the engine.
        """
        base_state = super().get_state()
        base_state.update(
            {
                "personality_traits": self.personality_traits,
                "character_name": self.character_name,
                # Potentially add more actor-specific state here
            }
        )
        return base_state

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Loads the state into the ActorEngine.

        Args:
            state (Dict[str, Any]): The state to load.
        """
        super().load_state(state)
        self.personality_traits = state.get("personality_traits", self.personality_traits)
        self.character_name = state.get("character_name", self.character_name)
        # Re-configure personality in case it was loaded
        self._configure_agent_personality()
        self.logger.info(f"Loaded state for {self.engine_name} ({self.character_name}).")

if __name__ == "__main__":
    # This is a simple example of how to use the ActorEngine.
    # For a real application, you would likely integrate this with an event loop
    # and a scenario manager.

    # --- Configuration ---
    # 1. Configure the LLM model (e.g., OpenAI)
    # Make sure to set your OPENAI_API_KEY environment variable
    try:
        from agno.models.openai import OpenAIChat
        # It's good practice to ensure API keys are handled securely,
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not found in environment variables.")
            print("Please set it to run this example: export OPENAI_API_KEY='your_key_here'")
            exit()
            exit()
            
        llm_model = OpenAIChat(model="gpt-3.5-turbo")
    except ImportError:
        print("OpenAI library not found. Please install it: pip install openai")
        exit()
    except Exception as e:
        print(f"Failed to initialize OpenAI model: {e}")
        exit()

    # 2. Create an Agno Agent
    actor_agent = Agent(
        model=llm_model,
        debug_mode=True, # Enable debug logs for more insight
        # Initial system message can be generic or overridden by ActorEngine
        system_message="You are an AI character." 
    )

    # 3. Create an ActorEngine instance
    pirate_actor = ActorEngine(
        agent=actor_agent,
        engine_name="PirateActor",
        character_name="Captain Pegleg Pete",
        personality_traits="A gruff, treasure-obsessed pirate with a penchant for saying 'Arrr!' and a secret soft spot for parrots.",
        description="Simulates Captain Pegleg Pete, a notorious pirate.",
    )

    # --- Simulate an event ---
    print(f"\n--- Simulating event for {pirate_actor.character_name} ---")
    event_data_dialogue = {"prompt": "Another pirate challenges you for your map to Treasure Island!"}
    
    # Synchronous example
    response = pirate_actor.process_event("dialogue_prompt", event_data_dialogue)

    if response and response.content:
        print(f"\n{pirate_actor.character_name} says: {response.content}")
    else:
        print(f"\n{pirate_actor.character_name} had no response or an error occurred.")

    # --- Example of saving and loading state (simplified) ---
    print("\n--- Saving and Loading State Example ---")
    current_state = pirate_actor.get_state()
    print(f"Saved state: {current_state}")

    # Create a new engine instance and load state
    new_actor_agent = Agent(model=llm_model)
    loaded_pirate_actor = ActorEngine(agent=new_actor_agent)
    loaded_pirate_actor.load_state(current_state)
    print(f"Loaded actor name: {loaded_pirate_actor.character_name}")
    print(f"Loaded personality: {loaded_pirate_actor.personality_traits}")

    # Test the loaded actor
    event_data_threat = {"prompt": "A kraken appears! What do you do?"}
    loaded_response = loaded_pirate_actor.process_event("action_request", event_data_threat)
    if loaded_response and loaded_response.content:
        print(f"\nLoaded {loaded_pirate_actor.character_name} responds: {loaded_response.content}")
    else:
        print(f"\nLoaded {loaded_pirate_actor.character_name} had no response or an error occurred.")

    # Asynchronous example (requires an event loop to run)
    async def run_async_example():
        print(f"\n--- Simulating async event for {pirate_actor.character_name} ---")
        async_response = await pirate_actor.aprocess_event("dialogue_prompt", event_data_dialogue)
        if async_response and async_response.content:
            print(f"\nAsync {pirate_actor.character_name} says: {async_response.content}")
        else:
            print(f"\nAsync {pirate_actor.character_name} had no response or an error occurred.")

    # To run the async example:
    # import asyncio
    # asyncio.run(run_async_example())
