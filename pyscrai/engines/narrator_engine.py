"""
NarratorEngine for PyScrAI.

This engine is responsible for providing narrative context and descriptions
for scenarios. It extends the BaseEngine and focuses on storytelling and
scene-setting capabilities.
"""
import logging
from typing import Any, Dict, List, Optional

from pyscrai.engines.base_engine import BaseEngine
from pyscrai.factories.llm_factory import get_llm_instance

# Initialize a logger for this module
logger = logging.getLogger(__name__)


class NarratorEngine(BaseEngine):
    """
    NarratorEngine for narrative generation.

    Inherits from BaseEngine and implements narrative-specific logic,
    including scene description and story progression.

    Attributes:
        narrative_style (Optional[str]): The style of narration to use.
        perspective (str): The narrative perspective (first, second, third person).
    """
    
    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "NarratorEngine",
        description: Optional[str] = "Provides narrative context and descriptions.",
        narrative_style: Optional[str] = "descriptive and engaging",
        perspective: str = "third_person",
        storage_path: Optional[str] = None,
        model_provider: str = "openai",
        **kwargs: Any,
    ):
        """
        Initializes the NarratorEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the agent.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            narrative_style (Optional[str]): The style of narration.
            perspective (str): The narrative perspective.
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
            engine_type="Narrator",
            **kwargs,
        )
        self.narrative_style: Optional[str] = narrative_style
        self.perspective: str = perspective
        
        # Store narrator-specific attributes in the shared state
        self.state["narrative_style"] = self.narrative_style
        self.state["perspective"] = self.perspective

        logger.info(f"NarratorEngine '{self.engine_name}' configured with {self.perspective} perspective.")

    async def initialize(self) -> None:
        """
        Initializes the NarratorEngine.
        """
        if self.initialized:
            logger.info(f"NarratorEngine '{self.engine_name}' already initialized.")
            return

        await super().initialize()
        
        if self.initialized:
            logger.info(f"NarratorEngine '{self.engine_name}' fully initialized.")
        else:
            logger.error(f"NarratorEngine '{self.engine_name}' initialization failed.")

    def _setup_tools(self) -> List[Any]:
        """
        Sets up tools specific to the NarratorEngine.
        Currently, no narrator-specific tools are defined.

        Returns:
            List[Any]: An empty list of tools.
        """
        logger.debug(f"NarratorEngine '{self.engine_name}' setup tools: None")
        return []

    async def process(self, event_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an external event (e.g., a system trigger to describe a scene)
        and generates narrative content. This content is then published as an event.

        Args:
            event_payload (Dict[str, Any]): Data associated with the event.
                                         Expected to contain 'prompt' or 'scene_details' for narration.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing the direct response content
                            (if any, for immediate return) and any errors.
                            The main output for scenario flow is published via event.
        """
        if not self.initialized:
            logger.error(f"NarratorEngine '{self.engine_name}' not initialized.")
            return {"content": None, "error": "Engine not initialized"}

        logger.info(f"{self.engine_name} processing narrative event.")
        logger.debug(f"Event payload: {event_payload}")

        # Adapt to various ways a scene might be described in the payload
        prompt_data = event_payload.get("prompt") or \
                      event_payload.get("scene_details") or \
                      event_payload.get("description")

        if not prompt_data:
            logger.warning("No 'prompt', 'scene_details', or 'description' found in event_payload for NarratorEngine.")
            return {"content": None, "error": "No narrative prompt provided"}
        
        # If prompt_data is a dict, try to extract a meaningful string, otherwise use as is
        if isinstance(prompt_data, dict):
            narrative_input = prompt_data.get("summary", str(prompt_data))
        else:
            narrative_input = str(prompt_data)

        try:
            narrative_prompt_for_llm = self._create_narrative_prompt(narrative_input)
            
            try:
                llm = get_llm_instance(provider=self.model_provider)
                ai_response = await llm.agenerate(narrative_prompt_for_llm)
                
                if hasattr(ai_response, 'content'):
                    narrative_text = ai_response.content
                elif isinstance(ai_response, str):
                    narrative_text = ai_response
                else:
                    narrative_text = str(ai_response)
                    
            except Exception as llm_error:
                logger.warning(f"LLM call failed for narrator: {llm_error}. Using fallback response.")
                narrative_text = self._generate_fallback_narrative(narrative_input) # Renamed for clarity
            
            # Publish the narrative content as an event
            await self.publish_event(
                event_type="scene_description_generated", # Generic event type from the narrator
                event_data={
                    "description": narrative_text,
                    "style": self.narrative_style,
                    "perspective": self.perspective
                }
            )
            
            logger.debug(f"Narrator generated description: {narrative_text}")
            # Direct return might be a summary or the full text, depending on design
            return {"content": f"[Narrator]: {narrative_text}", "error": None}
            
        except Exception as e:
            logger.error(f"Error during {self.engine_name} processing: {e}", exc_info=True)
            return {"content": None, "error": str(e)}

    def _create_narrative_prompt(self, scene_input: str) -> str:
        """
        Creates a narrative-specific prompt incorporating style and perspective.
        
        Args:
            scene_input (str): The original prompt or scene description
            
        Returns:
            str: Enhanced prompt with narrative context
        """
        perspective_instruction = {
            "first_person": "Narrate in first person (I, me, my)",
            "second_person": "Narrate in second person (you, your)",
            "third_person": "Narrate in third person (he, she, they, it)"
        }.get(self.perspective, "Narrate in third person")
        
        narrative_context = f"As a narrator with a {self.narrative_style} style, {perspective_instruction}. "
        narrative_context += f"Provide narrative description for the following: {scene_input}"
        
        return narrative_context

    def _generate_fallback_narrative(self, scene_input: str) -> str: # Renamed from _generate_narrative_response
        """
        Generates a fallback narrative response if the LLM fails.
        """
        perspective_prefix = {
            "first_person": "I observe",
            "second_person": "You find yourself in",
            "third_person": "The scene unfolds as"
        }.get(self.perspective, "The scene unfolds as")
        
        narrative_response = f"{perspective_prefix} a situation where {scene_input}. "
        narrative_response += "The atmosphere is charged with possibility, and every detail seems significant in this moment."
        
        return narrative_response

    async def handle_delivered_event(self, event_type: str, event_data: Dict[str, Any], sender_id: Optional[str] = None) -> None:
        """
        Handles events delivered to this narrator engine.
        Overrides BaseEngine.handle_delivered_event.
        """
        await super().handle_delivered_event(event_type, event_data, sender_id) # Call base for logging etc.
        logger.info(f"NarratorEngine '{self.engine_name}' received event: Type='{event_type}', Sender='{sender_id}'")
        logger.debug(f"Event data: {event_data}")

        # Example: If the system requests a scene update based on an action
        if event_type == "request_scene_update": # This type would be set by EngineManager
            action_description = event_data.get("action_summary", "something happened")
            context = event_data.get("context", {})
            
            logger.info(f"Narrator to describe scene after: '{action_description}'")
            
            # Formulate a prompt for the LLM to generate a new scene description
            try:
                # Construct a prompt for the LLM
                # Context might include previous scene, characters present, etc.
                scene_update_prompt_text = f"Following the action '{action_description}', describe the current scene. Context: {context}"
                narrative_llm_prompt = self._create_narrative_prompt(scene_update_prompt_text)

                llm = get_llm_instance(provider=self.model_provider)
                ai_response = await llm.agenerate(narrative_llm_prompt)

                if hasattr(ai_response, 'content'):
                    narrative_text = ai_response.content
                elif isinstance(ai_response, str):
                    narrative_text = ai_response
                else:
                    narrative_text = str(ai_response)

                # Publish the new scene description
                await self.publish_event(
                    event_type="scene_description_generated",
                    event_data={
                        "description": narrative_text,
                        "style": self.narrative_style,
                        "perspective": self.perspective,
                        "triggered_by_action": action_description # Optional context
                    }
                )
                logger.info(f"Narrator describes: '{narrative_text}'")

            except Exception as e:
                logger.error(f"Error during {self.engine_name} handling delivered event '{event_type}': {e}", exc_info=True)
        
        # Add more elif blocks here for other event types this narrator should handle
        # e.g., direct requests for lore, specific atmospheric changes, etc.

    def get_narrative_info(self) -> Dict[str, Any]:
        """
        Returns information about the narrator configuration.
        
        Returns:
            Dict[str, Any]: Narrator information
        """
        return {
            "engine_name": self.engine_name,
            "engine_type": self.engine_type,
            "narrative_style": self.narrative_style,
            "perspective": self.perspective
        }

    def set_narrative_style(self, style: str) -> None:
        """
        Updates the narrative style.
        
        Args:
            style (str): New narrative style
        """
        self.narrative_style = style
        self.state["narrative_style"] = style
        logger.info(f"Narrative style updated to: {style}")

    def set_perspective(self, perspective: str) -> None:
        """
        Updates the narrative perspective.
        
        Args:
            perspective (str): New perspective (first_person, second_person, third_person)
        """
        if perspective not in ["first_person", "second_person", "third_person"]:
            logger.warning(f"Invalid perspective: {perspective}. Using third_person.")
            perspective = "third_person"
        
        self.perspective = perspective
        self.state["perspective"] = perspective
        logger.info(f"Narrative perspective updated to: {perspective}")
