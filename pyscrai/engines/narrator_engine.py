# pyscrai/engines/narrator_engine.py
"""
NarratorEngine for PyScrAI.

This engine is responsible for world-building, scene description,
and providing narrative context. It extends the BaseEngine and
utilizes an Agno Agent for LLM interactions, configured with a specific narrative style.
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from agno.agent import Agent # Base Agent for type hinting
from agno.models.message import Message
from agno.run.response import RunResponse # To type hint agent responses

from .base_engine import BaseEngine
# from ..databases.models.schemas import QueuedEventResponse, EventStatusUpdate # For future use

# Initialize a logger for this module
logger = logging.getLogger(__name__)

class NarratorEngine(BaseEngine):
    """
    NarratorEngine for describing scenes and world-building.

    Attributes:
        narrative_style (Optional[str]): A description of the narrator's style
                                         (e.g., "omniscient, descriptive",
                                         "first-person, mysterious").
    """

    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "NarratorEngine",
        description: Optional[str] = "Describes scenes and provides narrative context.",
        narrative_style: Optional[str] = "A clear and objective third-person omniscient narrator.",
        storage_path: Optional[str] = None,
        model_provider: str = "openrouter",
        **kwargs: Any,
    ):
        """
        Initializes the NarratorEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the Agno Agent.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            narrative_style (Optional[str]): Text describing the narrator's style.
            storage_path (Optional[str]): Path for the agent's storage.
            model_provider (str): The provider for the LLM model.
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent_config=agent_config,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            engine_type="Narrator", # Explicitly set engine type
            storage_path=storage_path,
            model_provider=model_provider,
            **kwargs,
        )
        self.narrative_style: Optional[str] = narrative_style
        
        # Store narrator-specific attributes in the shared state
        self.state["narrative_style"] = self.narrative_style
        
        logger.info(f"NarratorEngine '{self.engine_name}' configured with style: '{self.narrative_style}'. Call initialize() to activate.")

    async def initialize(self) -> None:
        """
        Initializes the NarratorEngine, including the underlying Agno agent
        and its narrative style configuration.
        """
        if self.initialized:
            logger.info(f"NarratorEngine '{self.engine_name}' already initialized.")
            return

        await super().initialize() # Creates and initializes self.agent
        
        if self.agent:
            self._configure_agent_style()
            logger.info(f"NarratorEngine '{self.engine_name}' fully initialized.")
        else:
            logger.error(f"Agent initialization failed for NarratorEngine '{self.engine_name}'. Narrative style not configured.")

    def _configure_agent_style(self) -> None:
        """
        Configures the underlying Agno Agent with the narrator's style.
        This method should be called after the agent has been initialized.
        """
        if not self.agent:
            logger.warning(f"Agno agent not available for {self.engine_name}. Cannot configure narrative style.")
            return

        base_system_message_content = ""
        if self.agent.system_message:
            if isinstance(self.agent.system_message, Message):
                base_system_message_content = self.agent.system_message.get_content_as_str()
            elif callable(self.agent.system_message):
                try:
                    base_system_message_content = self.agent.system_message(agent=self.agent)
                except TypeError:
                    base_system_message_content = self.agent.system_message()
            else:
                base_system_message_content = str(self.agent.system_message)

        style_prompt = "You are the Narrator of a story or simulation. Your role is to describe scenes, events, character actions, and provide overall context to create an immersive experience."
        if self.narrative_style:
            style_prompt += f" Your specific narrative style is: {self.narrative_style}."
        style_prompt += " Deliver your descriptions vividly and appropriately for the given situation."

        if base_system_message_content and base_system_message_content.strip():
            self.agent.system_message = f"{style_prompt}\n\nOriginal context: {base_system_message_content}"
        else:
            self.agent.system_message = style_prompt
        
        logger.info(f"Configured narrative style for {self.engine_name}.")
        logger.debug(f"New system message for {self.engine_name}: {self.agent.system_message}")

    def _setup_tools(self) -> List[Any]:
        """
        Sets up tools specific to the NarratorEngine.
        For example, tools to access world state, character locations, or time of day.
        Currently, no narrator-specific tools are defined.

        Returns:
            List[Any]: An empty list of tools.
        """
        # Example:
        # from agno.tools.function import FunctionTool
        # def get_current_time_func() -> str:
        #     """Returns the current in-simulation time."""
        #     return self.state.get("simulation_time", "an unknown time")
        # time_tool = FunctionTool(fn=get_current_time_func)
        # return [time_tool]
        logger.debug(f"NarratorEngine '{self.engine_name}' setup tools: None")
        return []

    async def process(self, event_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an event payload and generates a narrative description.

        Args:
            event_payload (Dict[str, Any]): Data associated with the event.
                                         Expected to contain 'prompt' for the LLM,
                                         which details what needs to be narrated.
            **kwargs: Additional keyword arguments for the Agno Agent's arun method.

        Returns:
            Dict[str, Any]: A dictionary containing the 'content' of the narration
                            and any 'error' messages.
        """
        if not self.initialized or not self.agent:
            logger.error(f"NarratorEngine '{self.engine_name}' not initialized. Cannot process event.")
            return {"content": None, "error": "Engine not initialized"}

        logger.info(f"{self.engine_name} processing event payload for narration.")
        logger.debug(f"Event payload: {event_payload}")

        prompt_for_narration = event_payload.get("prompt")
        if not prompt_for_narration:
            logger.warning("No 'prompt' found in event_payload for NarratorEngine.")
            return {"content": None, "error": "No prompt provided in event payload for narration"}

        # The narrative style is handled by the agent's system message.
        # The prompt is the direct input detailing what the narrator should describe.
        message_to_agent = f"Please narrate the following situation or event: {prompt_for_narration}"

        try:
            response: Optional[RunResponse] = await self.agent.arun(message=message_to_agent, **kwargs)
            
            if response and response.content:
                logger.debug(f"{self.engine_name} raw narration response: {response.content[:200]}...") # Log snippet
                return {"content": response.content, "error": None}
            else:
                logger.warning(f"{self.engine_name} produced no content in narration response.")
                return {"content": None, "error": "Agent produced no content for narration"}
        except Exception as e:
            logger.error(f"Error during {self.engine_name} narration run: {e}", exc_info=True)
            return {"content": None, "error": str(e)}

async def main_narrator_example():
    """Example usage of the NarratorEngine."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
        print("Error: OPENAI_API_KEY or OPENROUTER_API_KEY not found.")
        return

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    narrator_agent_config = {
        "model_config": {
            "id": "openai/gpt-3.5-turbo", # "meta-llama/llama-3.1-8b-instruct:free", 
            "temperature": 0.8, # Slightly higher for more creative narration
        },
        "personality_config": {
            "name": "Storyteller AI",
            "description": "An AI agent that narrates events and scenes.",
            "instructions": "You are a helpful AI assistant.", # Base instructions
        },
    }

    story_narrator = NarratorEngine(
        agent_config=narrator_agent_config,
        engine_name="WorldNarrator",
        narrative_style="dramatic and suspenseful, with a focus on atmosphere and character emotions.",
        description="Narrates the simulation, focusing on drama and atmosphere.",
        storage_path="narrator_engine_storage.db",
        model_provider="openrouter"
    )

    await story_narrator.initialize()

    if not story_narrator.initialized or not story_narrator.agent:
        logger.error("Failed to initialize story_narrator. Exiting example.")
        return

    scene_description_prompt = "The old mansion stands silhouetted against a stormy sky. Rain lashes down, and a lone light flickers in an upstairs window. Describe the sense of foreboding."
    event_payload_scene = {"prompt": scene_description_prompt}
    
    logger.info(f"\n--- Simulating narration event for {story_narrator.engine_name} ---")
    narration_result = await story_narrator.process(event_payload_scene)

    if narration_result["content"]:
        logger.info(f"\n{story_narrator.engine_name} narrates:\n{narration_result['content']}")
    else:
        logger.error(f"\n{story_narrator.engine_name} had no narration or an error occurred: {narration_result['error']}")
    
    # State export/import example
    exported_state = story_narrator.export_state()
    logger.info(f"\n--- Exported NarratorEngine State ---\n{exported_state}")

    new_narrator_config = narrator_agent_config.copy()
    loaded_narrator = NarratorEngine(
        agent_config=new_narrator_config,
        storage_path="loaded_narrator_storage.db"
    )
    loaded_narrator.import_state(exported_state)
    await loaded_narrator.initialize()

    logger.info(f"Loaded narrator style: {loaded_narrator.state.get('narrative_style')}")
    logger.info(f"Loaded narrator system prompt: {loaded_narrator.agent.system_message if loaded_narrator.agent else 'Agent not loaded'}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main_narrator_example())
