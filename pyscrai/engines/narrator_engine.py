"""
NarratorEngine for PyScrAI.

This engine is responsible for providing narrative context and descriptions
for scenarios. It extends the BaseEngine and focuses on storytelling and
scene-setting capabilities.
"""
import logging
from typing import Any, Dict, List, Optional

from .base_engine import BaseEngine
from ..factories.llm_factory import get_llm_instance

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
        Processes an event payload and generates narrative content.

        Args:
            event_payload (Dict[str, Any]): Data associated with the event.
                                         Expected to contain 'prompt' or 'scene' for narration.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing the narrative response ('content')
                            and any errors ('error').
        """
        if not self.initialized:
            logger.error(f"NarratorEngine '{self.engine_name}' not initialized.")
            return {"content": None, "error": "Engine not initialized"}

        logger.info(f"{self.engine_name} processing narrative event.")
        logger.debug(f"Event payload: {event_payload}")

        prompt = event_payload.get("prompt") or event_payload.get("scene")
        if not prompt:
            logger.warning("No 'prompt' or 'scene' found in event_payload for NarratorEngine.")
            return {"content": None, "error": "No prompt or scene provided in event payload"}

        try:
            # Create narrative-specific prompt
            narrative_prompt = self._create_narrative_prompt(prompt)
            
            # Use LLM factory to get real AI response
            try:
                llm = get_llm_instance(provider=self.model_provider)
                ai_response = await llm.agenerate(narrative_prompt)
                
                # Extract content from AI response
                if hasattr(ai_response, 'content'):
                    response_content = f"[Narrator]: {ai_response.content}"
                elif isinstance(ai_response, str):
                    response_content = f"[Narrator]: {ai_response}"
                else:
                    response_content = f"[Narrator]: {str(ai_response)}"
                    
            except Exception as llm_error:
                logger.warning(f"LLM call failed for narrator: {llm_error}. Using fallback response.")
                # Fallback to simple response if LLM fails
                response_content = self._generate_narrative_response(prompt)
            
            logger.debug(f"Narrator response: {response_content}")
            return {"content": response_content, "error": None}
            
        except Exception as e:
            logger.error(f"Error during {self.engine_name} processing: {e}", exc_info=True)
            return {"content": None, "error": str(e)}

    def _create_narrative_prompt(self, prompt: str) -> str:
        """
        Creates a narrative-specific prompt incorporating style and perspective.
        
        Args:
            prompt (str): The original prompt or scene description
            
        Returns:
            str: Enhanced prompt with narrative context
        """
        perspective_instruction = {
            "first_person": "Narrate in first person (I, me, my)",
            "second_person": "Narrate in second person (you, your)",
            "third_person": "Narrate in third person (he, she, they, it)"
        }.get(self.perspective, "Narrate in third person")
        
        narrative_context = f"As a narrator with a {self.narrative_style} style, {perspective_instruction}. "
        narrative_context += f"Provide narrative description for: {prompt}"
        
        return narrative_context

    def _generate_narrative_response(self, prompt: str) -> str:
        """
        Generates a narrative response based on the prompt.
        
        Args:
            prompt (str): The scene or situation to narrate
            
        Returns:
            str: Narrative description
        """
        # Simple narrative generation for now
        # In Phase 2, this will use LLM providers
        
        perspective_prefix = {
            "first_person": "I observe",
            "second_person": "You find yourself in",
            "third_person": "The scene unfolds as"
        }.get(self.perspective, "The scene unfolds as")
        
        narrative_response = f"[Narrator - {self.narrative_style} style]: {perspective_prefix} a situation where {prompt}. "
        narrative_response += "The atmosphere is charged with possibility, and every detail seems significant in this moment."
        
        return narrative_response

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
