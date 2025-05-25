# pyscrai/engines/narrator_engine.py
"""
NarratorEngine for PyScrAI.

This engine is responsible for world-building, scene description,
and providing narrative context. It extends the BaseEngine and
utilizes an Agno Agent for LLM interactions.
"""
import os
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.message import Message
from agno.run.response import RunResponse

from .base_engine import BaseEngine


class NarratorEngine(BaseEngine):
    """
    NarratorEngine for describing scenes and world-building.

    Attributes:
        narrative_style (Optional[str]): A description of the narrator's style
                                         (e.g., "omniscient, descriptive",
                                         "first-person, mysterious").
                                         This will be incorporated into the
                                         Agno Agent's system message.
    """

    def __init__(
        self,
        agent: Agent,
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "NarratorEngine",
        description: Optional[str] = "Describes scenes and provides narrative context.",
        narrative_style: Optional[str] = "A clear and objective third-person omniscient narrator.",
        **kwargs: Any,
    ):
        """
        Initializes the NarratorEngine.

        Args:
            agent (Agent): The Agno Agent to be used for LLM interactions.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            narrative_style (Optional[str]): Text describing the narrator's style.
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent=agent,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            **kwargs,
        )
        self.narrative_style: Optional[str] = narrative_style

        # Configure the underlying Agno Agent with the narrative style
        self._configure_agent_style()

    def _configure_agent_style(self) -> None:
        """
        Configures the underlying Agno Agent with the narrator's style.
        """
        if self.agent is None:
            self.logger.warning("Agno agent not initialized. Cannot configure narrative style.")
            return

        base_system_message = self.agent.system_message or ""
        if isinstance(base_system_message, Message):
            base_system_message_content = base_system_message.get_content_as_str()
        elif callable(base_system_message):
            try:
                base_system_message_content = base_system_message(agent=self.agent)
            except TypeError:
                base_system_message_content = base_system_message()
        else:
            base_system_message_content = str(base_system_message)

        style_prompt = "You are the narrator. "
        if self.narrative_style:
            style_prompt += f"Your narrative style is: {self.narrative_style}. "
        style_prompt += "Describe scenes, events, and provide context accordingly."

        if base_system_message_content:
            self.agent.system_message = f"{style_prompt}\n\n{base_system_message_content}"
        else:
            self.agent.system_message = style_prompt
        
        self.logger.info(f"Configured narrative style for {self.engine_name}.")
        self.logger.debug(f"New system message for NarratorEngine: {self.agent.system_message}")

    def process_event(
        self, event_type: str, event_data: Dict[str, Any], **kwargs: Any
    ) -> Optional[RunResponse]:
        """
        Processes an event and generates a narrative description.

        Args:
            event_type (str): The type of event (e.g., "describe_scene", "narrate_action").
            event_data (Dict[str, Any]): Data associated with the event.
                                         Expected to contain 'prompt' for the LLM.
            **kwargs: Additional keyword arguments for the Agno Agent's run method.

        Returns:
            Optional[RunResponse]: The response from the Agno Agent, or None if an error occurs.
        """
        self.logger.info(f"{self.engine_name} processing event: {event_type}")
        self.logger.debug(f"Event data: {event_data}")

        if self.agent is None:
            self.logger.error("Agno agent not initialized for NarratorEngine.")
            return None

        prompt = event_data.get("prompt")
        if not prompt:
            self.logger.warning("No 'prompt' found in event_data for NarratorEngine.")
            return None

        # The prompt here is what the narrator should describe or elaborate on.
        # The narrative style is handled by the agent's system message.
        message_to_agent = f"Narrate the following: {prompt}"

        try:
            response = self.agent.run(message=message_to_agent, **kwargs)
            self.logger.debug(f"Narrator raw response: {response.content if response else 'None'}") # type: ignore
            return response # type: ignore
        except Exception as e:
            self.logger.error(f"Error during {self.engine_name} run: {e}")
            return None

    async def aprocess_event(
        self, event_type: str, event_data: Dict[str, Any], **kwargs: Any
    ) -> Optional[RunResponse]:
        """
        Asynchronously processes an event and generates a narrative description.

        Args:
            event_type (str): The type of event.
            event_data (Dict[str, Any]): Data associated with the event.
            **kwargs: Additional keyword arguments for the Agno Agent's arun method.

        Returns:
            Optional[RunResponse]: The asynchronous response from the Agno Agent.
        """
        self.logger.info(f"{self.engine_name} asynchronously processing event: {event_type}")
        self.logger.debug(f"Async event data: {event_data}")

        if self.agent is None:
            self.logger.error("Agno agent not initialized for NarratorEngine (async).")
            return None

        prompt = event_data.get("prompt")
        if not prompt:
            self.logger.warning("No 'prompt' found in event_data for NarratorEngine (async).")
            return None

        message_to_agent = f"Narrate the following: {prompt}"

        try:
            response = await self.agent.arun(message=message_to_agent, **kwargs)
            self.logger.debug(f"Narrator async raw response: {response.content if response else 'None'}") # type: ignore
            return response # type: ignore
        except Exception as e:
            self.logger.error(f"Error during async {self.engine_name} run: {e}")
            return None

    def get_state(self) -> Dict[str, Any]:
        """
        Gets the current state of the NarratorEngine.

        Returns:
            Dict[str, Any]: The current state of the engine.
        """
        base_state = super().get_state()
        base_state.update(
            {
                "narrative_style": self.narrative_style,
                # Potentially add more narrator-specific state here
            }
        )
        return base_state

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Loads the state into the NarratorEngine.

        Args:
            state (Dict[str, Any]): The state to load.
        """
        super().load_state(state)
        self.narrative_style = state.get("narrative_style", self.narrative_style)
        # Re-configure style in case it was loaded
        self._configure_agent_style()
        self.logger.info(f"Loaded state for {self.engine_name}.")


if __name__ == "__main__":
    # This is a simple example of how to use the NarratorEngine.

    # --- Configuration ---
    # 1. Configure the LLM model (e.g., OpenAI)
    try:
        from agno.models.openai import OpenAIChat
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not found in environment variables.")
            print("Please set it to run this example: export OPENAI_API_KEY='your_key_here'")
            exit()
        llm_model = OpenAIChat(model="gpt-3.5-turbo")
    except ImportError:
        print("OpenAI library not found. Please install it: pip install openai")
        exit()
    except Exception as e:
        print(f"Failed to initialize OpenAI model: {e}")
        exit()

    # 2. Create an Agno Agent
    narrator_agent = Agent(
        model=llm_model,
        debug_mode=True,
        system_message="You are a storyteller."
    )

    # 3. Create a NarratorEngine instance
    story_narrator = NarratorEngine(
        agent=narrator_agent,
        engine_name="StoryNarrator",
        narrative_style="epic and grand, focusing on sensory details and foreshadowing.",
        description="Narrates the unfolding events of a fantasy epic.",
    )

    # --- Simulate an event ---
    print(f"\n--- Simulating event for {story_narrator.engine_name} ---")
    event_data_scene = {"prompt": "The heroes enter a dark, ancient forest. Describe what they see, hear, and feel."}
    
    # Synchronous example
    response = story_narrator.process_event("describe_scene", event_data_scene)

    if response and response.content:
        print(f"\n{story_narrator.engine_name} narrates: {response.content}")
    else:
        print(f"\n{story_narrator.engine_name} had no response or an error occurred.")

    # --- Example of saving and loading state (simplified) ---
    print("\n--- Saving and Loading State Example ---")
    current_state = story_narrator.get_state()
    print(f"Saved state: {current_state}")

    # Create a new engine instance and load state
    new_narrator_agent = Agent(model=llm_model)
    loaded_narrator = NarratorEngine(agent=new_narrator_agent)
    loaded_narrator.load_state(current_state)
    print(f"Loaded narrator name: {loaded_narrator.engine_name}")
    print(f"Loaded narrative style: {loaded_narrator.narrative_style}")

    # Test the loaded narrator
    event_data_action = {"prompt": "A sudden storm begins to brew overhead as the old bridge creaks ominously."}
    loaded_response = loaded_narrator.process_event("narrate_action", event_data_action)
    if loaded_response and loaded_response.content:
        print(f"\nLoaded {loaded_narrator.engine_name} narrates: {loaded_response.content}")
    else:
        print(f"\nLoaded {loaded_narrator.engine_name} had no response or an error occurred.")

    # Asynchronous example (requires an event loop to run)
    async def run_async_example():
        print(f"\n--- Simulating async event for {story_narrator.engine_name} ---")
        async_response = await story_narrator.aprocess_event("describe_scene", event_data_scene)
        if async_response and async_response.content:
            print(f"\nAsync {story_narrator.engine_name} narrates: {async_response.content}")
        else:
            print(f"\nAsync {story_narrator.engine_name} had no response or an error occurred.")

    # To run the async example:
    # import asyncio
    # asyncio.run(run_async_example())
