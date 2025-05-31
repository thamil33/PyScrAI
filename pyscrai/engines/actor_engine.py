"""
ActorEngine for PyScrAI.

This engine is responsible for simulating characters with specific
personality traits and behaviors. It extends the BaseEngine and
uses our custom Agent-Engine Integration system.
"""
import logging
from typing import Any, Dict, List, Optional

from pyscrai.engines.base_engine import BaseEngine
from pyscrai.factories.llm_factory import get_llm_instance
from pyscrai.core.models import Event # Added
from sqlalchemy.orm import Session # Added

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
    
    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "ActorEngine",
        description: Optional[str] = "Simulates a character in a scenario.",
        personality_traits: Optional[str] = "A neutral and helpful character.",
        character_name: str = "Character",
        storage_path: Optional[str] = None,
        model_provider: str = "openai",
        **kwargs: Any,
    ):
        """
        Initializes the ActorEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the agent.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            personality_traits (Optional[str]): Text describing the character's personality.
            character_name (str): The name of the character.
            storage_path (Optional[str]): Path for the agent's storage.
            model_provider (str): The provider for the LLM model.
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent_config=agent_config,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            storage_path=storage_path,
            model_provider=model_provider,
            engine_type="Actor",
            **kwargs,
        )
        self.personality_traits: Optional[str] = personality_traits
        self.character_name: str = character_name
        
        # Store actor-specific attributes in the shared state
        self.state["character_name"] = self.character_name
        self.state["personality_traits"] = self.personality_traits

        logger.info(f"ActorEngine '{self.engine_name}' for character '{self.character_name}' configured.")

    async def initialize(self) -> None:
        """
        Initializes the ActorEngine.
        """
        if self.initialized:
            logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) already initialized.")
            return

        await super().initialize()
        
        if self.initialized:
            logger.info(f"ActorEngine '{self.engine_name}' ({self.character_name}) fully initialized.")
        else:
            logger.error(f"ActorEngine '{self.engine_name}' initialization failed.")

    def _setup_tools(self) -> List[Any]:
        """
        Sets up tools specific to the ActorEngine.
        Currently, no actor-specific tools are defined.

        Returns:
            List[Any]: An empty list of tools.
        """
        logger.debug(f"ActorEngine '{self.engine_name}' setup tools: None")
        return []

    async def process(self, event_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an event payload and generates a response based on the character's role
        and personality.

        Args:
            event_payload (Dict[str, Any]): Data associated with the event.
                                         Expected to contain 'prompt' for processing.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing the response ('content')
                            and any errors ('error').
        """
        if not self.initialized:
            logger.error(f"ActorEngine '{self.engine_name}' ({self.character_name}) not initialized.")
            return {"content": None, "error": "Engine not initialized"}

        logger.info(f"{self.engine_name} ({self.character_name}) processing event payload.")
        logger.debug(f"Event payload: {event_payload}")

        prompt = event_payload.get("prompt")
        if not prompt:
            logger.warning("No 'prompt' found in event_payload for ActorEngine.")
            return {"content": None, "error": "No prompt provided in event payload"}

        try:
            # Create character-specific prompt
            character_prompt = self._create_character_prompt(prompt)
            
            # Use LLM factory to get real AI response
            try:
                llm = get_llm_instance(provider=self.model_provider)
                ai_response = await llm.agenerate(character_prompt)
                
                # Extract content from AI response
                if hasattr(ai_response, 'content'):
                    response_content = f"[{self.character_name}]: {ai_response.content}"
                elif isinstance(ai_response, str):
                    response_content = f"[{self.character_name}]: {ai_response}"
                else:
                    response_content = f"[{self.character_name}]: {str(ai_response)}"
                    
            except Exception as llm_error:
                logger.warning(f"LLM call failed for {self.character_name}: {llm_error}. Using fallback response.")
                # Fallback to simple response if LLM fails
                response_content = f"[{self.character_name}]: I understand the situation: '{prompt}'. As a character with traits '{self.personality_traits}', I would respond appropriately to this scenario."
            
            logger.debug(f"{self.character_name} response: {response_content}")
            
            # Publish the actor's speech as an event
            if self.event_publisher:
                speech_event = Event(
                    event_type="actor_speech_generated",
                    payload={
                        "actor_name": self.character_name,
                        "speech": response_content,
                        "original_prompt": prompt,
                        "instance_id": self.agent_config.get("instance_id"),
                        "scenario_id": kwargs.get("scenario_id") # Ensure scenario_id is passed if available
                    },
                    source_agent_id=self.agent_config.get("instance_id"),
                    source_engine_id=self.engine_id
                )
                await self.event_publisher(speech_event)
                logger.info(f"Actor {self.character_name} published actor_speech_generated event.")
            else:
                logger.warning(f"Event publisher not set for ActorEngine {self.character_name}. Cannot publish speech event.")
            
            return {"content": response_content, "error": None}
            
        except Exception as e:
            logger.error(f"Error during {self.engine_name} ({self.character_name}) processing: {e}", exc_info=True)
            return {"content": None, "error": str(e)}

    async def handle_delivered_event(self, event: Event, scenario_context: Dict[str, Any], db_session: Session) -> None:
        """
        Handles an event delivered by the EngineManager.
        For ActorEngine, this typically means processing a prompt or instruction.
        """
        logger.info(f"{self.engine_name} ({self.character_name}) received event {event.event_type} with payload: {event.payload}")
        
        # Extract relevant information for the process method
        # The process method expects a dict, event.payload should be it.
        # We might need to pass scenario_id if process() uses it from kwargs
        scenario_id = scenario_context.get("scenario_run_id")

        if event.payload:
            # Call the existing process method to generate a response and publish an event
            await self.process(event.payload, scenario_id=scenario_id)
        else:
            logger.warning(f"No payload in event {event.event_type} for {self.engine_name} ({self.character_name})")

    def _create_character_prompt(self, prompt: str) -> str:
        """
        Creates a character-specific prompt incorporating personality traits.
        
        Args:
            prompt (str): The original prompt
            
        Returns:
            str: Enhanced prompt with character context
        """
        character_context = f"You are {self.character_name}. "
        if self.personality_traits:
            character_context += f"Your personality: {self.personality_traits}. "
        character_context += f"Respond to this situation in character: {prompt}"
        
        return character_context

    def get_character_info(self) -> Dict[str, Any]:
        """
        Returns information about the character.
        
        Returns:
            Dict[str, Any]: Character information
        """
        return {
            "character_name": self.character_name,
            "personality_traits": self.personality_traits,
            "engine_name": self.engine_name,
            "engine_type": self.engine_type
        }
