from engines.base_engine import BaseEngine

from typing import Optional, List, Dict, Any
from pyscrai.llm_factory import get_agno_llm_instance
from agno.agent import Agent as AgnoAgent # Assuming this is the correct import for Agno's Agent

# Example of how a specialized engine might inherit from BaseEngine:

class ActorEngine(BaseEngine):
    def __init__(self, character_profile: Dict[str, Any], **kwargs):
        # Example: Construct instructions based on character_profile
        instructions = [
            f"You are {character_profile.get('name', 'a character')}.",
            f"Your personality is: {character_profile.get('personality', 'neutral')}.",
            # Add more instructions based on the profile
        ]
        super().__init__(
            agent_name=f"ActorEngine_{character_profile.get('name', 'Unknown')}",
            agent_instructions=instructions,
            **kwargs
        )
        self.character_profile = character_profile

    def simulate_dialogue(self, situation: str) -> str:
        # Custom method for this engine
        prompt = f"Given the situation: '{situation}', how would you respond?"
        response = self.run(prompt) # or self.agent.run(prompt)
        return response.content # Assuming Agno's run response has a content attribute

if __name__ == "__main__":
    # This is for demonstration; actual use would be through PyScrAI's orchestration
    try:
        # Test with default provider (ensure .env or env vars are set)
        engine = BaseEngine(
            agent_name="TestEngineDefault",
            agent_instructions=["You are a helpful test assistant."],
            show_tool_calls=True
        )
        engine.print_response("Hello, who are you?")

        # Test overriding to OpenRouter
        or_engine = BaseEngine(
            agent_name="TestEngineOpenRouter",
            llm_provider_override="openrouter",
            llm_model_id_override="meta-llama/llama-4-maverick:free", # A free model for testing
            agent_instructions=["You are an OpenRouter-powered test assistant."],
            model_params={"temperature": 0.7}
        )
        or_engine.print_response("Tell me a joke, using openrotuer.")

        # Test overriding to LMStudio (requires LMStudio server running)
        # lm_engine = BaseEngine(
        #     agent_name="TestEngineLMStudio",
        #     llm_provider_override="lmstudio",
        #     llm_model_id_override="Meta-Llama-3-8B-Instruct-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf", # Example model
        #     agent_instructions=["You are an LMStudio-powered test assistant."]
        # )
        # lm_engine.print_response("What is the capital of France, using LMStudio?")

    except Exception as e:
        print(f"An error occurred during engine testing: {e}")